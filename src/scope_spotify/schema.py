"""Configuration schema for the Spotify Prompt Generator pipeline."""

from typing import Literal

from pydantic import Field

from scope.core.pipelines.base_schema import BasePipelineConfig, ModeDefaults, UsageType, ui_field_config

# Template theme preset keys (dropdown).
TemplateTheme = Literal[
    "dreamy_abstract",
    "lyrics_style",
    "music_video",
    "minimal",
    "song_artist",
]


class SpotifyConfig(BasePipelineConfig):
    """Configuration for the Spotify Prompt Generator pipeline.

    Credentials (Client ID, Client Secret, Redirect URI) are set via environment
    variables at setup (e.g. RunPod pod env). See README for SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI.
    """

    pipeline_id = "spotify-prompts"
    pipeline_name = "Spotify Prompt Generator"
    pipeline_description = (
        "Use the current Spotify track as the image prompt. "
        "Use as a PREPROCESSOR with Stream Diffusion (or any image pipeline). "
        "You must enable video or camera input so the preprocessor runs. "
        "Set SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET (and optionally SPOTIFY_REDIRECT_URI) in the environment."
    )

    usage = [UsageType.PREPROCESSOR]
    supports_prompts = True
    modes = {"video": ModeDefaults(default=True), "text": ModeDefaults()}

    # --- Prompt: preset theme (dropdown) ---

    template_theme: TemplateTheme = Field(
        default="dreamy_abstract",
        description="Preset theme for the prompt (Dreamy / abstract, Lyrics + style, Music video, Minimal, Song + artist).",
        json_schema_extra=ui_field_config(
            order=19,
            label="Template theme",
            category="configuration",
        ),
    )

    lyrics_keywords_only: bool = Field(
        default=False,
        description="When on, reduce each lyric line to keyword-like words (strip common words) for stronger visual prompts.",
        json_schema_extra=ui_field_config(
            order=20,
            label="Lyrics as keywords only",
            category="configuration",
        ),
    )

    lyrics_style_rotation_seconds: float = Field(
        default=0.0,
        ge=0.0,
        le=30.0,
        description="Style word rotation: 0 = advance when lyric line changes; >0 = advance every N seconds.",
        json_schema_extra=ui_field_config(
            order=21,
            label="Style rotation interval (sec)",
            category="configuration",
        ),
    )

    lyrics_preview_seconds: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="When >0, show the next lyric line this many seconds early so the visual transitions sooner.",
        json_schema_extra=ui_field_config(
            order=22,
            label="Preview next line (sec)",
            category="configuration",
        ),
    )

    fallback_prompt: str = Field(
        default="Abstract flowing colors and shapes",
        description="Prompt when no track is playing",
        json_schema_extra=ui_field_config(
            order=23,
            label="Fallback Prompt",
            category="configuration",
        ),
    )
