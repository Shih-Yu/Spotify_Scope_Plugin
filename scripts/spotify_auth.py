#!/usr/bin/env python3
"""
Spotify Authentication Helper for Headless Servers (RunPod, etc.)

Use this script to authenticate with Spotify when running on a server
without a browser. The token will be cached and reused by the plugin.

Usage:
    python spotify_auth.py

You'll need your Spotify API credentials from developer.spotify.com
"""

import os
import sys
from pathlib import Path

# Load .env.local if present (optional)
env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ[key] = value.strip()

# Import spotify_client directly so we don't load scope_spotify/__init__.py (which requires Scope)
scope_spotify_path = Path(__file__).parent.parent / "src" / "scope_spotify"
sys.path.insert(0, str(scope_spotify_path))

from spotify_client import SpotifyClient


def main():
    print("=" * 60)
    print("Spotify Authentication Helper")
    print("=" * 60)
    print()
    
    # Get credentials from env or prompt
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback").strip()
    
    if not client_id:
        client_id = input("Client ID: ").strip()
    if not client_id:
        print("Error: Client ID is required (set SPOTIFY_CLIENT_ID in .env.local or enter here)")
        return 1
    
    if not client_secret:
        client_secret = input("Client Secret: ").strip()
    if not client_secret:
        print("Error: Client Secret is required (set SPOTIFY_CLIENT_SECRET in .env.local or enter here)")
        return 1
    
    if not redirect_uri:
        redirect_uri = input("Redirect URI [http://127.0.0.1:8888/callback]: ").strip() or "http://127.0.0.1:8888/callback"
    else:
        print(f"Using redirect URI from .env.local: {redirect_uri}")
    
    print()
    print("-" * 60)
    
    # Create client
    client = SpotifyClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        headless_mode=True,
    )
    
    # Check if already authenticated
    if client.is_authenticated():
        print("✓ Already authenticated! Token is cached and valid.")
        print(f"  Cache location: {client.cache_path}")
        
        # Test the connection
        print()
        print("Testing connection...")
        try:
            track = client.get_current_track()
            if track:
                print(f"✓ Connected! Now playing: {track.name} by {track.artist}")
            else:
                print("✓ Connected! (No track currently playing)")
        except Exception as e:
            print(f"✗ Connection test failed: {e}")
        
        return 0
    
    # Need to authenticate
    print()
    print("Step 1: Visit this URL in your browser:")
    print()
    auth_url = client.get_auth_url()
    print(f"  {auth_url}")
    print()
    print("Step 2: Log in and authorize the app")
    print()
    print("Step 3: You'll be redirected to a URL like:")
    print("  http://127.0.0.1:8888/callback?code=AQBx...")
    print()
    print("  (The page won't load - that's expected!)")
    print("  Copy the ENTIRE URL from your browser's address bar.")
    print()
    print("-" * 60)
    
    redirect_response = input("Paste the redirect URL here: ").strip()
    
    if not redirect_response:
        print("Error: No URL provided")
        return 1
    
    print()
    print("Completing authentication...")
    
    if client.complete_auth(redirect_response):
        print()
        print("✓ Authentication successful!")
        print(f"  Token cached at: {client.cache_path}")
        print()
        print("The plugin will now use this cached token.")
        print("You can switch to 'spotify' input source in the plugin settings.")
        
        # Test the connection
        print()
        print("Testing connection...")
        try:
            track = client.get_current_track()
            if track:
                print(f"✓ Now playing: {track.name} by {track.artist}")
            else:
                print("✓ Connected! (No track currently playing)")
        except Exception as e:
            print(f"Note: {e}")
        
        return 0
    else:
        print()
        print("✗ Authentication failed. Please try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
