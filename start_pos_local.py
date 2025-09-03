#!/usr/bin/env python3
"""
Local POS Startup Script with Ngrok Integration

This script starts ngrok tunnel and Django server for local M-Pesa development.
It ensures that M-Pesa callbacks can reach your local development server.
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# Add the admin directory to Python path
admin_dir = Path(__file__).parent
sys.path.insert(0, str(admin_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')

import django
django.setup()

from sales.ngrok_service import ngrok_service
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class POSServer:
    def __init__(self):
        self.django_process = None
        self.ngrok_tunnel = None
        self.running = False
        
    def start_ngrok(self, port=8000):
        """Start ngrok tunnel with comprehensive offline/download failure handling"""
        logger.info("Checking ngrok availability...")
        
        # Step 1: Check if pyngrok is installed
        try:
            from pyngrok import ngrok
            from pyngrok.exception import PyngrokNgrokError, PyngrokSecurityError
        except ImportError:
            logger.warning("⚠️ pyngrok not installed - M-Pesa callbacks unavailable")
            logger.info("💡 To enable M-Pesa: pip install pyngrok")
            return False
        
        # Step 2: Handle ngrok binary download/update failures
        try:
            # Test if ngrok binary is available without triggering download
            from pyngrok.ngrok import NgrokTunnel
            logger.debug("pyngrok module loaded successfully")
        except Exception as module_error:
            logger.warning(f"⚠️ pyngrok module issue: {module_error}")
            return False
        
        # Step 3: Attempt tunnel creation with comprehensive error handling
        try:
            logger.info(f"Attempting ngrok tunnel creation on port {port}...")
            tunnel_url = ngrok_service.start_tunnel(port)
            
            if tunnel_url:
                # Export to environment for Django process
                os.environ['NGROK_PUBLIC_URL'] = tunnel_url
                logger.info(f"✅ Ngrok tunnel active: {tunnel_url}")
                logger.info(f"🔗 M-Pesa callback URL: {tunnel_url}/dashboard/sales/mpesa-callback/")
                
                # Persist the origin/host into settings.py so CSRF works in forms
                try:
                    settings_path = admin_dir / 'admin' / 'settings.py'
                    settings_text = settings_path.read_text(encoding='utf-8')
                    origin = f"{tunnel_url.rstrip('/')}"
                    # Ensure https origin only
                    if origin.startswith('http://'):
                        origin = origin.replace('http://', 'https://')
                    
                    # Update CSRF_TRUSTED_ORIGINS list
                    if 'CSRF_TRUSTED_ORIGINS' in settings_text:
                        import re
                        def add_origin_list(src_text, list_name, value_to_add):
                            pattern = rf"{list_name}\s*=\s*\[(.*?)\]"
                            def repl(m):
                                inner = m.group(1)
                                # Avoid duplicates
                                if value_to_add in inner:
                                    return m.group(0)
                                # Insert before closing bracket
                                if inner.strip():
                                    return f"{list_name} = [" + inner + f", '{value_to_add}']"
                                else:
                                    return f"{list_name} = ['{value_to_add}']"
                            return re.sub(pattern, repl, src_text, flags=re.S)
                        
                        settings_text = add_origin_list(settings_text, 'CSRF_TRUSTED_ORIGINS', origin)
                    
                    # Update ALLOWED_HOSTS with host part
                    from urllib.parse import urlparse
                    host = urlparse(origin).netloc
                    if 'ALLOWED_HOSTS' in settings_text and host:
                        import re
                        settings_text = add_origin_list(settings_text, 'ALLOWED_HOSTS', host)
                    
                    settings_path.write_text(settings_text, encoding='utf-8')
                    logger.info("🔐 Updated CSRF_TRUSTED_ORIGINS and ALLOWED_HOSTS in settings.py")
                except Exception as e:
                    logger.warning(f"Could not update settings.py with ngrok origin: {e}")
                
                return True
            else:
                logger.info("ℹ️ Ngrok tunnel unavailable - continuing without M-Pesa")
                return False
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Specific error handling for different failure modes
            if 'download' in error_msg or 'installing' in error_msg:
                logger.warning("⚠️ Ngrok download/install failed - system may be offline")
                logger.info("💡 Continuing without M-Pesa support")
                
            elif 'network' in error_msg or 'connection' in error_msg or 'dns' in error_msg:
                logger.warning("⚠️ Network connectivity issue - system offline")
                logger.info("💡 M-Pesa will be unavailable until network is restored")
                
            elif 'authentication' in error_msg and 'simultaneous' in error_msg:
                logger.warning("⚠️ Ngrok session limit (ERR_NGROK_108) - M-Pesa unavailable")
                logger.info("💡 Use: python3 kill_ngrok.py to clean up sessions")
                
            elif 'timeout' in error_msg:
                logger.warning("⚠️ Ngrok startup timeout - possible session conflict")
                
            elif 'permission' in error_msg or 'access' in error_msg:
                logger.warning("⚠️ Ngrok permission issue - check file system access")
                
            else:
                logger.warning(f"⚠️ Ngrok unavailable: {str(e)}")
                
            logger.info("ℹ️ Django server will start without M-Pesa support")
            return False
    
    def run_migrations(self):
        """Run Django migrations"""
        logger.info("Running Django migrations...")
        try:
            result = subprocess.run([
                sys.executable, 'manage.py', 'migrate', '--noinput'
            ], check=True, capture_output=True, text=True)
            logger.info("✅ Migrations completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Migration failed: {e.stderr}")
            return False
    
    def collect_static(self):
        """Collect static files"""
        logger.info("Collecting static files...")
        try:
            result = subprocess.run([
                sys.executable, 'manage.py', 'collectstatic', '--noinput'
            ], check=True, capture_output=True, text=True)
            logger.info("✅ Static files collected successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Static collection failed: {e.stderr}")
            return False
    
    def start_django(self, port=8000):
        """Start Django development server"""
        logger.info(f"Starting Django server on port {port}...")
        try:
            self.django_process = subprocess.Popen([
                sys.executable, 'manage.py', 'runserver', f'0.0.0.0:{port}'
            ])
            
            # Wait a moment for server to start
            time.sleep(3)
            
            if self.django_process.poll() is None:
                logger.info(f"✅ Django server started successfully")
                return True
            else:
                logger.error("❌ Django server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Django server error: {str(e)}")
            return False
    
    def stop(self):
        """Stop all services"""
        logger.info("Stopping services...")
        self.running = False
        
        # Stop Django server
        if self.django_process:
            logger.info("Stopping Django server...")
            self.django_process.terminate()
            try:
                self.django_process.wait(timeout=10)
                logger.info("✅ Django server stopped")
            except subprocess.TimeoutExpired:
                logger.warning("Django server didn't stop gracefully, killing...")
                self.django_process.kill()
        
        # Stop ngrok tunnel
        logger.info("Stopping ngrok tunnel...")
        ngrok_service.stop_tunnel()
        logger.info("✅ Ngrok tunnel stopped")
    
    def run(self, port=8000):
        """Main run method"""
        self.running = True
        
        logger.info("🚀 Starting POS System with M-Pesa Integration")
        logger.info("=" * 60)
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("\n📛 Shutdown signal received...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Step 1: Run migrations
            if not self.run_migrations():
                logger.error("❌ Migration failed, exiting...")
                return False
            
            # Step 2: Collect static files
            if not self.collect_static():
                logger.warning("⚠️ Static collection failed, continuing...")
            
            # Step 3: Start ngrok tunnel (optional - continue if it fails)
            ngrok_success = self.start_ngrok(port)
            if not ngrok_success:
                logger.info("ℹ️ Continuing without ngrok - M-Pesa payments will be unavailable")
                
                # Check if it's a session limit issue and offer cleanup
                from django.core.cache import cache
                if cache.get('ngrok_session_active'):
                    logger.info("💡 If you're seeing ERR_NGROK_108 errors, try running:")
                    logger.info("   python3 kill_ngrok.py")
                    logger.info("   This will clean up conflicting ngrok sessions")
            
            # Step 4: Start Django server
            if not self.start_django(port):
                logger.error("❌ Django server failed to start, exiting...")
                self.stop()
                return False
            
            # Success message
            logger.info("\n" + "=" * 60)
            logger.info("🎉 POS System Started Successfully!")
            logger.info("=" * 60)
            
            tunnel_url = ngrok_service.get_tunnel_url()
            if tunnel_url:
                # Export to environment for downstream Django code
                os.environ['NGROK_PUBLIC_URL'] = tunnel_url
                logger.info(f"🌐 Public URL: {tunnel_url}")
                logger.info(f"💳 M-Pesa Ready: Yes")
                logger.info(f"🏪 POS Interface: {tunnel_url}/dashboard/sales/pos/")
                logger.info(f"📊 Dashboard: {tunnel_url}/dashboard/")
                
                # Persist CSRF origin and host as a fallback if not done earlier
                try:
                    settings_path = admin_dir / 'admin' / 'settings.py'
                    settings_text = settings_path.read_text(encoding='utf-8')
                    origin = f"{tunnel_url.rstrip('/')}"
                    if origin.startswith('http://'):
                        origin = origin.replace('http://', 'https://')
                    from urllib.parse import urlparse
                    host = urlparse(origin).netloc
                    import re
                    def add_origin_list(src_text, list_name, value_to_add):
                        pattern = rf"{list_name}\s*=\s*\[(.*?)\]"
                        def repl(m):
                            inner = m.group(1)
                            if value_to_add in inner:
                                return m.group(0)
                            if inner.strip():
                                return f"{list_name} = [" + inner + f", '{value_to_add}']"
                            else:
                                return f"{list_name} = ['{value_to_add}']"
                        return re.sub(pattern, repl, src_text, flags=re.S)
                    settings_text = add_origin_list(settings_text, 'CSRF_TRUSTED_ORIGINS', origin)
                    if host:
                        settings_text = add_origin_list(settings_text, 'ALLOWED_HOSTS', host)
                    settings_path.write_text(settings_text, encoding='utf-8')
                except Exception as e:
                    logger.debug(f"Skipping settings persistence fallback: {e}")

                # Trigger email notification with the ngrok URL
                try:
                    result = subprocess.run([
                        sys.executable, 'manage.py', 'notify_ngrok_link', f"--url={tunnel_url}"
                    ], check=False, capture_output=True, text=True)
                    if result.returncode == 0:
                        logger.info("📧 Ngrok notification: dispatched")
                    else:
                        logger.warning(f"📧 Ngrok notification failed (code {result.returncode}): {result.stderr.strip()}")
                except Exception as notify_err:
                    logger.warning(f"📧 Ngrok notification error: {notify_err}")
            else:
                logger.info(f"🌐 Local URL: http://localhost:{port}")
                logger.info(f"💳 M-Pesa Ready: No (ngrok not available)")
                logger.info(f"🏪 POS Interface: http://localhost:{port}/dashboard/sales/pos/")
                logger.info(f"📊 Dashboard: http://localhost:{port}/dashboard/")
            logger.info("=" * 60)
            logger.info("Press Ctrl+C to stop the server")
            logger.info("=" * 60)
            
            # Keep the script running
            while self.running:
                time.sleep(1)
                # Check if Django process is still running
                if self.django_process and self.django_process.poll() is not None:
                    logger.error("❌ Django server stopped unexpectedly")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return False
        finally:
            self.stop()
        
        return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start POS system with M-Pesa integration')
    parser.add_argument('--port', type=int, default=8000, help='Port to run Django server (default: 8000)')
    parser.add_argument('--no-ngrok', action='store_true', help='Skip ngrok tunnel (M-Pesa will not work)')
    
    args = parser.parse_args()
    
    # Check if ngrok is available
    try:
        import pyngrok
        ngrok_available = True
    except ImportError:
        ngrok_available = False
        logger.warning("⚠️ pyngrok not installed. M-Pesa callbacks will not work.")
        logger.info("💡 Install with: pip install pyngrok")
    
    if args.no_ngrok:
        logger.info("🚫 Ngrok disabled by user request")
        ngrok_available = False
    
    server = POSServer()
    
    if not ngrok_available:
        # Monkey patch ngrok service to avoid errors
        ngrok_service.start_tunnel = lambda port: None
        ngrok_service.get_tunnel_url = lambda: None
        ngrok_service.stop_tunnel = lambda: None
    
    success = server.run(args.port)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()