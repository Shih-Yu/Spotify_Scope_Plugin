#!/usr/bin/env python3
"""
Quick local test for the Spotify Scope Plugin.
Tests config loading and prompt generation (manual mode) without Scope or RunPod.

Usage:
    python scripts/test_local.py
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env.local
env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value
    print(f"✓ Loaded environment from {env_file}")

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_spotify_config():
    """Check Spotify env vars (optional for manual mode)."""
    print("\n" + "=" * 50)
    print("Spotify API config")
    print("=" * 50)
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    if client_id and client_secret:
        print(f"✓ SPOTIFY_CLIENT_ID: {client_id[:12]}...")
        print("✓ SPOTIFY_CLIENT_SECRET: set")
        return True
    print("  (Not set — use manual mode or add to .env.local for live Spotify)")
    return True


def test_prompt_generation():
    """Test prompt generation with manual input (requires Scope installed)."""
    print("\n" + "=" * 50)
    print("Prompt generation (manual mode)")
    print("=" * 50)
    try:
        from scope_spotify.spotify_client import TrackInfo
        from scope_spotify.pipeline import SpotifyPipeline
    except ImportError as e:
        print(f"  (Scope not installed — run inside Scope or install scope-core)")
        print(f"  TrackInfo/SpotifyClient can be used standalone.")
        return True

    pipeline = SpotifyPipeline()
    track = TrackInfo(
        track_id="test-123",
        name="Blinding Lights",
        artist="The Weeknd",
        album="After Hours",
        duration_ms=200000,
        progress_ms=100000,
        is_playing=True,
        genres=["pop", "synth-pop"],
    )
    result = pipeline(
        input_source="manual",
        manual_song_title=track.name,
        manual_artist=track.artist,
        manual_album=track.album,
        manual_genre="pop",
        prompt_mode="title",
    )
    prompt = result.get("prompt", "")
    print(f"  Song: {track.name} by {track.artist}")
    print(f"  Prompt: {prompt[:80]}...")
    print("✓ Prompt generation OK")
    return True


def main():
    print("=" * 50)
    print("Scope Spotify Plugin – local test")
    print("=" * 50)
    test_spotify_config()
    ok = test_prompt_generation()
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    print("  Manual mode: ✓ Ready")
    print("  For live Spotify: set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env.local")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
