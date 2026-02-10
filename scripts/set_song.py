#!/usr/bin/env python3
"""
Quick song changer for Scope Spotify Plugin.
Changes take effect immediately - no restart needed!

Usage:
    python set_song.py "Song Title" "Artist" "genre"
    python set_song.py "Bohemian Rhapsody" "Queen" "rock"
    python set_song.py --interactive
    
The config file is at: ~/.scope-spotify/config.json
"""

import argparse
import json
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".scope-spotify" / "config.json"


def load_config():
    """Load current config."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_config(config):
    """Save config to file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


def set_song(title: str, artist: str, genre: str = "", album: str = "", progress: float = 0):
    """Set the current song."""
    config = load_config()
    config.update({
        "song_title": title,
        "artist": artist,
        "genre": genre,
        "album": album or f"{title} Album",
        "progress": progress,
    })
    save_config(config)
    print(f"✓ Now playing: {title} by {artist}")
    print(f"  Genre: {genre or 'not set'}")
    print(f"  Config: {CONFIG_PATH}")


def set_mode(mode: str):
    """Set prompt mode (title or lyrics)."""
    config = load_config()
    config["prompt_mode"] = mode
    save_config(config)
    print(f"✓ Prompt mode set to: {mode}")


def set_progress(progress: float):
    """Set playback progress (0-100)."""
    config = load_config()
    config["progress"] = max(0, min(100, progress))
    save_config(config)
    print(f"✓ Progress set to: {progress}%")


def show_current():
    """Show current configuration."""
    config = load_config()
    print("\n=== Current Configuration ===")
    print(f"  Song:     {config.get('song_title', 'Not set')}")
    print(f"  Artist:   {config.get('artist', 'Not set')}")
    print(f"  Album:    {config.get('album', 'Not set')}")
    print(f"  Genre:    {config.get('genre', 'Not set')}")
    print(f"  Progress: {config.get('progress', 0)}%")
    print(f"  Mode:     {config.get('prompt_mode', 'title')}")
    print(f"  Style:    {config.get('art_style', 'Not set')}")
    print(f"\n  Config file: {CONFIG_PATH}")


def interactive_mode():
    """Interactive song selection."""
    print("\n=== Scope Spotify Plugin - Song Selector ===\n")
    
    show_current()
    
    print("\n--- Set New Song ---")
    title = input("Song title: ").strip()
    if not title:
        print("Cancelled.")
        return
    
    artist = input("Artist: ").strip() or "Unknown Artist"
    genre = input("Genre (rock/pop/electronic/etc): ").strip()
    mode = input("Mode [title/lyrics] (default: lyrics): ").strip() or "lyrics"
    
    config = load_config()
    config.update({
        "song_title": title,
        "artist": artist,
        "genre": genre,
        "prompt_mode": mode,
        "progress": 0,
    })
    save_config(config)
    
    print(f"\n✓ Updated! Now playing: {title} by {artist}")
    print("  Changes take effect immediately - no restart needed!")


def main():
    parser = argparse.ArgumentParser(
        description="Change songs for Scope Spotify Plugin (live, no restart needed)"
    )
    parser.add_argument("title", nargs="?", help="Song title")
    parser.add_argument("artist", nargs="?", help="Artist name")
    parser.add_argument("genre", nargs="?", default="", help="Genre (optional)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("-m", "--mode", choices=["title", "lyrics"], help="Set prompt mode")
    parser.add_argument("-p", "--progress", type=float, help="Set progress (0-100)")
    parser.add_argument("-s", "--show", action="store_true", help="Show current config")
    
    args = parser.parse_args()
    
    if args.show:
        show_current()
    elif args.interactive:
        interactive_mode()
    elif args.mode:
        set_mode(args.mode)
    elif args.progress is not None:
        set_progress(args.progress)
    elif args.title and args.artist:
        set_song(args.title, args.artist, args.genre)
    else:
        parser.print_help()
        print("\nExamples:")
        print('  python set_song.py "Bohemian Rhapsody" "Queen" "rock"')
        print('  python set_song.py "Blinding Lights" "The Weeknd" "pop"')
        print('  python set_song.py --interactive')
        print('  python set_song.py --show')
        print('  python set_song.py --mode lyrics')
        print('  python set_song.py --progress 50')


if __name__ == "__main__":
    main()
