#!/usr/bin/env python3
"""
Quick local test: load env, optionally run pipeline (needs Scope + Spotify token for real track).

Usage:
    python scripts/test_local.py
"""

import os
import sys
from pathlib import Path

env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()
    print(f"✓ Loaded {env_file}")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    print("Scope Spotify Plugin – minimal test")
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("  Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env.local")
        return 0

    try:
        from scope_spotify.pipeline import SpotifyPipeline
    except ImportError:
        print("  Scope not installed; pip install -e . or run inside Scope")
        return 0

    pipeline = SpotifyPipeline()
    out = pipeline()
    prompt = out.get("prompt", "")
    print(f"  Prompt: {prompt[:80]}...")
    print("  Run spotify_auth.py once if you see fallback and want live track.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
