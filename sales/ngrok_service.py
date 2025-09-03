import os
import time
import requests
import logging
import subprocess
import signal
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Make pyngrok optional; only use if available
try:
    from pyngrok import ngrok
except ImportError:
    ngrok = None
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

class NgrokService:
    """
    Service to manage ngrok tunnels for local development
    """
    
    def __init__(self):
        self.tunnel = None
        self.tunnel_url = None
        self._tunnel_started = False
        self._session_active = False
        
    def kill_all_ngrok_processes(self):
        """
        Aggressively kill all ngrok processes system-wide
        """
        killed_processes = 0
        try:
            # First try pyngrok's kill
            try:
                ngrok.kill()
                logger.info("Called pyngrok.kill()")
            except Exception as e:
                logger.debug(f"pyngrok.kill() failed: {e}")
            
            # Kill ngrok processes by name using psutil (if available)
            if PSUTIL_AVAILABLE:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and 'ngrok' in proc.info['name'].lower():
                            logger.info(f"Killing ngrok process: PID {proc.info['pid']}, CMD: {proc.info['cmdline']}")
                            proc.kill()
                            killed_processes += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            else:
                logger.debug("psutil not available, using system commands only")
            
            # Also try system commands as fallback
            try:
                subprocess.run(['pkill', '-f', 'ngrok'], check=False, capture_output=True)
                logger.debug("Executed pkill -f ngrok")
            except Exception:
                pass
                
            # Wait for processes to die
            if killed_processes > 0:
                time.sleep(2)
                logger.info(f"Killed {killed_processes} ngrok processes")
                
        except Exception as e:
            logger.warning(f"Error killing ngrok processes: {e}")
            
        return killed_processes
        
    def start_tunnel(self, port=8000):
        """
        Start ngrok tunnel for the given port - SINGLE TUNNEL ONLY
        
        Args:
            port (int): Local port to tunnel (default: 8000)
            
        Returns:
            str: Public HTTPS URL of the tunnel or None if failed
        """
        # CRITICAL: Only allow ONE tunnel attempt per session
        if self._tunnel_started:
            logger.info(f"Tunnel already exists: {self.tunnel_url}")
            return self.tunnel_url
            
        # Check env var first (set by startup script)
        env_url = os.getenv('NGROK_PUBLIC_URL')
        if env_url:
            logger.info(f"Found existing tunnel in environment: {env_url}")
            self.tunnel_url = env_url
            self._tunnel_started = True
            cache.set('ngrok_tunnel_url', env_url, timeout=3600)
            return env_url
        
        # Check cache for existing tunnel from previous session
        cached_url = cache.get('ngrok_tunnel_url')
        if cached_url:
            logger.info(f"Found existing tunnel in cache: {cached_url}")
            self.tunnel_url = cached_url
            self._tunnel_started = True
            return cached_url
            
        # If we've hit session limit before, don't retry
        if cache.get('ngrok_session_limit_hit', False):
            logger.warning("Previous session limit detected - skipping tunnel creation")
            return None
            
        try:
            # Single attempt only - no retries to prevent ERR_NGROK_108
            logger.info(f"Attempting to start ngrok tunnel on port {port}...")
            
            # Clean kill of any existing processes (but only once)
            try:
                self.kill_all_ngrok_processes()
                time.sleep(2)  # Brief wait for cleanup
            except Exception as cleanup_error:
                logger.debug(f"Cleanup warning: {cleanup_error}")
            
            if not ngrok:
                logger.warning("pyngrok not available - cannot start tunnel from this process")
                return None

            # Configure ngrok to prevent update checks and warnings
            try:
                ngrok.set_auth_token(ngrok.get_default().auth_token)
            except Exception:
                pass  # Continue if auth token setup fails
            
            # Single tunnel creation attempt with timeout
            self.tunnel = ngrok.connect(port, proto="http")
            self.tunnel_url = self.tunnel.public_url
            
            # Ensure HTTPS URL
            if self.tunnel_url.startswith('http://'):
                self.tunnel_url = self.tunnel_url.replace('http://', 'https://')
            
            # Mark as started (prevents future attempts)
            self._tunnel_started = True
            
            # Cache the URL and export to environment for consistency
            cache.set('ngrok_tunnel_url', self.tunnel_url, timeout=3600)
            os.environ['NGROK_PUBLIC_URL'] = self.tunnel_url
            cache.delete('ngrok_session_limit_hit')  # Clear any previous failure marker
            
            logger.info(f"✅ Ngrok tunnel started successfully: {self.tunnel_url}")
            return self.tunnel_url
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle ERR_NGROK_108 specifically
            if 'authentication' in error_msg and ('simultaneous' in error_msg or 'err_ngrok_108' in error_msg):
                logger.error("❌ ERR_NGROK_108: Ngrok session limit reached")
                logger.warning("🚫 Will not attempt tunnel creation again this session")
                cache.set('ngrok_session_limit_hit', True, timeout=3600)
                
            # Handle download/network errors
            elif 'download' in error_msg or 'network' in error_msg or 'connection' in error_msg:
                logger.warning("⚠️ Ngrok download/network issue - system offline")
                
            # Handle timeout errors
            elif 'timeout' in error_msg:
                logger.warning("⚠️ Ngrok startup timed out - possible session conflict")
                
            else:
                logger.error(f"❌ Ngrok failed: {str(e)}")
            
            # Mark as attempted to prevent further tries
            self._tunnel_started = True
            return None
    
    def get_tunnel_url(self):
        """
        Get the current tunnel URL
        
        Returns:
            str: Current tunnel URL or None if no tunnel is active
        """
        # Prefer env var if present
        env_url = os.getenv('NGROK_PUBLIC_URL')
        if env_url:
            cache.set('ngrok_tunnel_url', env_url, timeout=3600)
            self.tunnel_url = env_url
            return env_url

        # First check cache
        cached_url = cache.get('ngrok_tunnel_url')
        if cached_url:
            return cached_url
            
        # Try to infer from Django settings
        try:
            # Prefer explicit CSRF trusted origins that contain ngrok
            for origin in getattr(settings, 'CSRF_TRUSTED_ORIGINS', []) or []:
                if 'ngrok' in origin:
                    inferred = origin.rstrip('/')
                    if not inferred.startswith('http'):
                        inferred = 'https://' + inferred
                    self.tunnel_url = inferred
                    cache.set('ngrok_tunnel_url', self.tunnel_url, timeout=3600)
                    return self.tunnel_url
            # Fallback: check allowed hosts for an ngrok host
            for host in getattr(settings, 'ALLOWED_HOSTS', []) or []:
                if isinstance(host, str) and 'ngrok' in host:
                    inferred = host
                    if inferred.startswith('http://') or inferred.startswith('https://'):
                        base = inferred
                    else:
                        base = f'https://{inferred}'
                    self.tunnel_url = base
                    cache.set('ngrok_tunnel_url', self.tunnel_url, timeout=3600)
                    return self.tunnel_url
        except Exception:
            pass
            
        # Try to get from pyngrok API
        if ngrok:
            try:
                tunnels = ngrok.get_tunnels()
                for tunnel in tunnels:
                    if tunnel.proto == 'https':
                        self.tunnel_url = tunnel.public_url
                        cache.set('ngrok_tunnel_url', self.tunnel_url, timeout=3600)
                        return self.tunnel_url
            except Exception:
                pass
        
        # Try local ngrok API as a last resort
        try:
            resp = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=1)
            data = resp.json()
            for t in data.get('tunnels', []):
                public_url = t.get('public_url', '')
                if public_url.startswith('https://'):
                    self.tunnel_url = public_url
                    cache.set('ngrok_tunnel_url', self.tunnel_url, timeout=3600)
                    return self.tunnel_url
        except Exception:
            pass
            
        return self.tunnel_url
    
    def stop_tunnel(self):
        """
        Stop the ngrok tunnel
        """
        try:
            if self.tunnel:
                ngrok.disconnect(self.tunnel.public_url)
            ngrok.kill()
            
            # Reset state
            self._tunnel_started = False
            self._session_active = False
            self.tunnel = None
            self.tunnel_url = None
            
            # Clear cache
            cache.delete('ngrok_tunnel_url')
            cache.delete('ngrok_session_active')
            logger.info("Ngrok tunnel stopped")
        except Exception as e:
            logger.error(f"Error stopping ngrok tunnel: {str(e)}")
    
    def get_callback_url(self, endpoint="/dashboard/sales/mpesa-callback/"):
        """
        Get the full callback URL for M-Pesa
        
        Args:
            endpoint (str): API endpoint path
            
        Returns:
            str: Full callback URL
        """
        tunnel_url = self.get_tunnel_url()
        if tunnel_url:
            return f"{tunnel_url.rstrip('/')}{endpoint}"
        return None
    
    def is_tunnel_active(self):
        """
        Check if ngrok tunnel is active
        
        Returns:
            bool: True if tunnel is active, False otherwise
        """
        # If environment variable is set, assume active
        if os.getenv('NGROK_PUBLIC_URL'):
            return True
        
        try:
            if ngrok:
                tunnels = ngrok.get_tunnels()
                if len(tunnels) > 0:
                    return True
        except Exception:
            pass
        
        # Try local admin API
        try:
            resp = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=1)
            data = resp.json()
            return any(t.get('public_url', '').startswith('https://') for t in data.get('tunnels', []))
        except Exception:
            return False

# Global instance
ngrok_service = NgrokService()

def get_ngrok_callback_url(endpoint="/dashboard/sales/mpesa-callback/"):
    """
    Helper function to get ngrok callback URL
    
    Args:
        endpoint (str): API endpoint path
        
    Returns:
        str: Full callback URL or None if ngrok is not available
    """
    return ngrok_service.get_callback_url(endpoint)

def ensure_ngrok_tunnel(port=8000):
    """
    Ensure ngrok tunnel is running - SINGLE ATTEMPT ONLY
    
    Args:
        port (int): Local port to tunnel
        
    Returns:
        str: Tunnel URL or None if failed/unavailable
    """
    # Check for existing tunnel first
    existing_url = ngrok_service.get_tunnel_url()
    if existing_url:
        return existing_url
    
    # Check if we've already attempted and failed
    if cache.get('ngrok_session_limit_hit', False):
        logger.debug("Session limit hit previously - not retrying")
        return None
        
    # Single attempt only
    if not ngrok_service._tunnel_started:
        return ngrok_service.start_tunnel(port)
    
    return None