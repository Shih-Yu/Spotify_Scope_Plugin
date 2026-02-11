"""Configuration schema for the Spotify Prompt Generator pipeline."""

from pydantic import Field

from scope.core.pipelines.base_schema import BasePipelineConfig, ModeDefaults, UsageType, ui_field_config


class SpotifyConfig(BasePipelineConfig):
    """Configuration for the Spotify Prompt Generator pipeline.

    Minimal: prompt = current Spotify song title (or template). Credentials can be
    set in the Scope UI here or via env vars (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET).
    """

    pipeline_id = "spotify-prompts"
    pipeline_name = "Spotify Prompt Generator"
    pipeline_description = (
        "Use the current Spotify track as the image prompt. "
        "Use as a PREPROCESSOR with Stream Diffusion (or any image pipeline). "
        "You must enable video or camera input so the preprocessor runs."
    )

    usage = [UsageType.PREPROCESSOR]
    supports_prompts = True
    modes = {"video": ModeDefaults(default=True), "text": ModeDefaults()}

    # --- Spotify credentials (UI or env: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET) ---

    spotify_client_id: str = Field(
        default="",
        description="Spotify API Client ID (or set SPOTIFY_CLIENT_ID in env)",
        json_schema_extra=ui_field_config(
            order=10,
            label="Spotify Client ID",
            category="configuration",
        ),
    )

    spotify_client_secret: str = Field(
        default="",
        description="Spotify API Client Secret (or set SPOTIFY_CLIENT_SECRET in env)",
        json_schema_extra=ui_field_config(
            order=11,
            label="Spotify Client Secret",
            category="configuration",
        ),
    )

    spotify_redirect_uri: str = Field(
        default="http://127.0.0.1:8888/callback",
        description="Redirect URI from your Spotify app settings",
        json_schema_extra=ui_field_config(
            order=12,
            label="Redirect URI",
            category="configuration",
        ),
    )

    headless_mode: bool = Field(
        default=True,
        description="On for RunPod/servers (auth via URL + paste); off for local browser popup",
        json_schema_extra=ui_field_config(
            order=13,
            label="Headless/Server Mode",
            category="configuration",
        ),
    )

    # --- Prompt: default = song title only; use {song}, {artist}, optional {lyrics} ---

    prompt_template: str = Field(
        default="{song}",
        description="Prompt template. Use {song}, {artist}, and optionally {lyrics} (when 'Use lyrics' is on).",
        json_schema_extra=ui_field_config(
            order=20,
            label="Prompt Template",
            category="input",
        ),
    )

    use_lyrics: bool = Field(
        default=False,
        description="Add lyrics to the prompt. When on, use 'Synced with song' for time-synced lines (recommended) or plain lyrics.",
        json_schema_extra=ui_field_config(
            order=21,
            label="Use lyrics",
            category="input",
        ),
    )

    use_synced_lyrics: bool = Field(
        default=True,
        description="When 'Use lyrics' is on: sync prompt with current lyric line (LRCLIB). Off = plain lyrics snippet (Lyrics.ovh).",
        json_schema_extra=ui_field_config(
            order=22,
            label="Synced with song",
            category="input",
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
            category="input",
        ),
    )

    fallback_prompt: str = Field(
        default="Abstract flowing colors and shapes",
        description="Prompt when no track is playing",
        json_schema_extra=ui_field_config(
            order=24,
            label="Fallback Prompt",
            category="input",
        ),
    )
