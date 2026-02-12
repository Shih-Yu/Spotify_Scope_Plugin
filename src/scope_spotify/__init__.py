"""Scope Spotify Plugin - Generate AI prompts from music and lyrics."""

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
