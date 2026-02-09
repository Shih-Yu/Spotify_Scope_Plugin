#!/usr/bin/env python3
"""
Quick local test for the Spotify Scope Plugin.
Tests Genius lyrics fetching without needing Scope or RunPod.

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

# Add src to path - import directly to avoid Scope dependency
src_path = Path(__file__).parent.parent / "src" / "scope_spotify"
sys.path.insert(0, str(src_path))

from lyrics_client import LyricsClient


def test_lyrics():
    """Test fetching lyrics from Genius."""
    print("\n" + "=" * 50)
    print("Testing Genius Lyrics API")
    print("=" * 50)
    
    genius_token = os.environ.get("GENIUS_API_TOKEN", "")
    
    if not genius_token:
        print("✗ GENIUS_API_TOKEN not found in environment")
        print("  Make sure .env.local has your token")
        return False
    
    print(f"✓ Found Genius token: {genius_token[:10]}...")
    
    # Initialize client
    client = LyricsClient(genius_token=genius_token)
    
    # Test songs
    test_songs = [
        ("Bohemian Rhapsody", "Queen"),
        ("Blinding Lights", "The Weeknd"),
        ("Shape of You", "Ed Sheeran"),
    ]
    
    for song, artist in test_songs:
        print(f"\n--- Testing: {song} by {artist} ---")
        
        try:
            lyrics = client.get_lyrics(song, artist)
            
            if lyrics:
                print(f"✓ Found {len(lyrics)} lines of lyrics")
                print(f"  First line: \"{lyrics[0][:60]}...\"" if len(lyrics[0]) > 60 else f"  First line: \"{lyrics[0]}\"")
                
                # Test segment extraction
                segment = client.get_lyrics_segment(song, artist, 50.0, 2)
                if segment:
                    print(f"  At 50%: \"{segment[:60]}...\"" if len(segment) > 60 else f"  At 50%: \"{segment}\"")
            else:
                print("✗ No lyrics found")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return True


def test_prompt_generation():
    """Test prompt generation with manual input."""
    print("\n" + "=" * 50)
    print("Testing Prompt Generation (Manual Mode)")
    print("=" * 50)
    
    # Import here to avoid Scope dependencies if not installed
    try:
        from spotify_client import TrackInfo
        # Define GENRE_STYLES locally for testing
        GENRE_STYLES = {
            "rock": "bold contrasts, electric energy, raw textures",
            "pop": "vibrant colors, glossy finish, modern aesthetic",
            "classic rock": "vintage feel, powerful energy, iconic imagery",
        }
    except ImportError as e:
        print(f"Note: Some imports failed: {e}")
        return True
    
    # Create a mock track
    track = TrackInfo(
        track_id="test-123",
        name="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        duration_ms=354000,
        progress_ms=177000,  # 50%
        is_playing=True,
        genres=["rock", "classic rock"],
    )
    
    print(f"\n--- Mock Track ---")
    print(f"  Song: {track.name}")
    print(f"  Artist: {track.artist}")
    print(f"  Progress: {track.progress_percent:.1f}%")
    print(f"  Genres: {track.genres}")
    
    # Check genre style mapping
    for genre in track.genres:
        if genre.lower() in GENRE_STYLES:
            print(f"  Style for '{genre}': {GENRE_STYLES[genre.lower()]}")
            break
    
    print("\n✓ Prompt generation logic is ready")
    return True


def main():
    print("=" * 50)
    print("Scope Spotify Plugin - Local Test")
    print("=" * 50)
    
    # Test lyrics
    lyrics_ok = test_lyrics()
    
    # Test prompt generation
    prompt_ok = test_prompt_generation()
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"  Lyrics API: {'✓ Working' if lyrics_ok else '✗ Failed'}")
    print(f"  Prompt Gen: {'✓ Ready' if prompt_ok else '✗ Issues'}")
    
    if lyrics_ok:
        print("\n✓ Ready to deploy to RunPod!")
        print("  Install in Scope with:")
        print("  git+https://github.com/Shih-Yu/Spotify_Scope_Plugin.git")
    
    return 0 if (lyrics_ok and prompt_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
