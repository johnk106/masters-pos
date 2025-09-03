#!/usr/bin/env python3
"""
Reset Ngrok Session Limit Cache

This script clears the ngrok session limit cache to allow retrying ngrok tunnel creation.
Use this after you've resolved session conflicts or upgraded your ngrok account.
"""

import os
import sys

# Add the admin directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def reset_ngrok_cache():
    """Reset all ngrok-related cache"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
        
        import django
        django.setup()
        
        from django.core.cache import cache
        
        # Cache keys to clear
        cache_keys = [
            'ngrok_tunnel_url',
            'ngrok_session_limit_hit'
        ]
        
        print("🧹 Clearing ngrok session cache...")
        for key in cache_keys:
            cache.delete(key)
            print(f"   ✅ Cleared: {key}")
        
        print("\n✅ Ngrok session cache cleared!")
        print("🚀 You can now try starting ngrok again:")
        print("   python3 start_pos_local.py")
        
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

def main():
    print("🔄 Ngrok Session Reset Utility")
    print("=" * 40)
    print("This will clear the session limit cache and allow")
    print("ngrok tunnel creation to be attempted again.\n")
    
    response = input("Reset ngrok session cache? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        reset_ngrok_cache()
    else:
        print("❌ Reset cancelled")

if __name__ == '__main__':
    main()