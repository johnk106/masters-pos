#!/usr/bin/env python3
"""
Ngrok Session Cleanup Utility

This script aggressively kills all ngrok processes and clears cache to resolve ERR_NGROK_108 errors.
Run this script if you encounter "authentication limited to 1 simultaneous ngrok agent sessions" errors.
"""

import os
import sys
import time
import subprocess
import signal

def kill_ngrok_processes():
    """Kill all ngrok processes using multiple methods"""
    killed_count = 0
    
    print("🔍 Searching for ngrok processes...")
    
    # Method 1: Try psutil if available
    try:
        import psutil
        print("   Using psutil for process management...")
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'ngrok' in proc.info['name'].lower():
                    print(f"   Killing PID {proc.info['pid']}: {proc.info['name']}")
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        if killed_count == 0:
            print("   No ngrok processes found via psutil")
    except ImportError:
        print("   psutil not available, using system commands...")
    
    # Method 2: System commands
    commands = [
        ['pkill', '-f', 'ngrok'],
        ['killall', 'ngrok'],
        ['pgrep', '-f', 'ngrok']  # Just to check what's left
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if cmd[0] == 'pgrep':
                if result.stdout.strip():
                    print(f"   Found remaining ngrok processes: {result.stdout.strip()}")
                else:
                    print("   ✅ No ngrok processes found")
            else:
                if result.returncode == 0:
                    print(f"   ✅ {' '.join(cmd)} executed successfully")
                    killed_count += 1
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"   ⚠️ {' '.join(cmd)} failed: {e}")
    
    return killed_count

def clear_ngrok_cache():
    """Clear Django cache for ngrok-related keys"""
    print("\n🧹 Clearing ngrok cache...")
    
    try:
        # Add Django project to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
        
        import django
        django.setup()
        
        from django.core.cache import cache
        
        # Clear ngrok-related cache keys
        cache_keys = ['ngrok_tunnel_url', 'ngrok_session_active']
        for key in cache_keys:
            cache.delete(key)
            print(f"   ✅ Cleared cache key: {key}")
            
    except Exception as e:
        print(f"   ⚠️ Could not clear Django cache: {e}")

def kill_port_8000():
    """Kill any process using port 8000"""
    print("\n🚪 Checking port 8000...")
    
    try:
        # Find processes using port 8000
        result = subprocess.run(['lsof', '-ti:8000'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    print(f"   Killing process using port 8000: PID {pid}")
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(1)
                    # Force kill if still alive
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Already dead
                except (ValueError, ProcessLookupError):
                    pass
        else:
            print("   ✅ Port 8000 is free")
    except FileNotFoundError:
        print("   ⚠️ lsof not available, skipping port check")

def main():
    """Main cleanup function"""
    print("🚀 Ngrok Session Cleanup Utility")
    print("=" * 50)
    print("This script will kill all ngrok processes and clear cache")
    print("to resolve ERR_NGROK_108 session limit errors.\n")
    
    # Ask for confirmation (unless --force flag is used)
    if len(sys.argv) > 1 and sys.argv[1] in ['--force', '-f']:
        print("🔥 Force mode enabled - proceeding without confirmation")
    else:
        response = input("Do you want to proceed? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Cleanup cancelled")
            return
    
    print("\n🧹 Starting cleanup process...")
    
    # Step 1: Kill ngrok processes
    killed_count = kill_ngrok_processes()
    
    # Step 2: Clear Django cache
    clear_ngrok_cache()
    
    # Step 3: Check port 8000
    kill_port_8000()
    
    # Wait a moment
    print("\n⏳ Waiting for processes to terminate...")
    time.sleep(3)
    
    # Final check
    print("\n🔍 Final verification...")
    try:
        result = subprocess.run(['pgrep', '-f', 'ngrok'], capture_output=True, text=True)
        if result.stdout.strip():
            print(f"   ⚠️ Some ngrok processes may still be running: {result.stdout.strip()}")
            print("   You may need to restart your terminal or reboot your system")
        else:
            print("   ✅ All ngrok processes terminated successfully")
    except FileNotFoundError:
        print("   ⚠️ Cannot verify (pgrep not available)")
    
    print("\n" + "=" * 50)
    print("🎉 Cleanup completed!")
    print("\nNext steps:")
    print("1. Wait 10-15 seconds before starting ngrok again")
    print("2. Run your POS startup script: python3 start_pos_local.py")
    print("3. If issues persist, check: https://dashboard.ngrok.com/agents")
    print("4. Consider upgrading ngrok account for multiple sessions")

if __name__ == '__main__':
    main()