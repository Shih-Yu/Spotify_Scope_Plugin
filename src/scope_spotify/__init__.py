"""Scope Spotify Plugin - Generate AI prompts from music and lyrics."""

import sys

try:
    from scope.core.plugins.hookspecs import hookimpl

    @hookimpl
    def register_pipelines(register):
        """Register the Spotify prompt generator pipeline with Scope."""
        from .pipeline import SpotifyPipeline

        register(SpotifyPipeline)
except ImportError:
    # Scope not installed (e.g. when running the companion lyrics app standalone)
    pass
except Exception as e:
    # Log so server logs show why the plugin failed to load (Scope UI may only show "unknown error")
    print(f"Scope Spotify plugin failed to load: {e}", file=sys.stderr, flush=True)
    raise
