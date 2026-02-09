"""Scope Spotify Plugin - Generate AI prompts from music and lyrics."""

from scope.core.plugins.hookspecs import hookimpl


@hookimpl
def register_pipelines(register):
    """Register the Spotify prompt generator pipeline with Scope."""
    from .pipeline import SpotifyPipeline

    register(SpotifyPipeline)
