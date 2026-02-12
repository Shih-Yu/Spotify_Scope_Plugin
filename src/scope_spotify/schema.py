"""Configuration schema for the Spotify Prompt Generator pipeline."""

from typing import Literal

from pydantic import Field

from scope.core.pipelines.base_schema import BasePipelineConfig, ModeDefaults, UsageType, ui_field_config

# Template theme preset keys (dropdown). "custom" = use prompt_template field.
TemplateTheme = Literal[
    "dreamy_abstract",
    "lyrics_style",
    "music_video",
    "minimal",
    "song_artist",
    "custom",
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

    # --- Prompt: preset theme (dropdown) or custom template ---

    template_theme: TemplateTheme = Field(
        default="dreamy_abstract",
        description="Preset theme for the prompt. Choose a style; use Custom to type your own template below.",
        json_schema_extra=ui_field_config(
            order=19,
            label="Template theme",
            category="configuration",
        ),
    )

    prompt_template: str = Field(
        default="{lyrics}",
        description="Prompt template (used when Template theme is Custom). Use {song}, {artist}, {lyrics}.",
        json_schema_extra=ui_field_config(
            order=20,
            label="Prompt Template",
            category="configuration",
        ),
    )

    use_lyrics: bool = Field(
        default=True,
        description="Add lyrics to the prompt. When on, use 'Synced with song' for time-synced lines (recommended) or plain lyrics.",
        json_schema_extra=ui_field_config(
            order=21,
            label="Use lyrics",
            category="configuration",
        ),
    )

    use_synced_lyrics: bool = Field(
        default=True,
        description="When 'Use lyrics' is on: sync prompt with current lyric line (LRCLIB). Off = plain lyrics snippet (Lyrics.ovh).",
        json_schema_extra=ui_field_config(
            order=22,
            label="Synced with song",
            category="configuration",
        ),
    )

    lyrics_max_chars: int = Field(
        default=300,
        ge=0,
        le=2000,
        description="Max characters when using plain lyrics (ignored when synced).",
        json_schema_extra=ui_field_config(
            order=23,
            label="Lyrics max length",
            category="configuration",
        ),
    )

    fallback_prompt: str = Field(
        default="Abstract flowing colors and shapes",
        description="Prompt when no track is playing",
        json_schema_extra=ui_field_config(
            order=24,
            label="Fallback Prompt",
            category="configuration",
        ),
    )
