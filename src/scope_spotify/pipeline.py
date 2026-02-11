"""Minimal pipeline: current Spotify song title -> one prompt -> preprocessor."""

import logging
import os
from typing import TYPE_CHECKING, Optional

import torch

from scope.core.pipelines.interface import Pipeline, Requirements

from .schema import SpotifyConfig
from .spotify_client import SpotifyClient, TrackInfo

if TYPE_CHECKING:
    from scope.core.pipelines.base_schema import BasePipelineConfig

logger = logging.getLogger(__name__)


class SpotifyPipeline(Pipeline):
    """Preprocessor: get current Spotify track, build one prompt from song title, pass to pipeline."""

    @classmethod
    def get_config_class(cls) -> type["BasePipelineConfig"]:
        return SpotifyConfig

    def __init__(
        self,
        device: torch.device | None = None,
        **kwargs,
    ):
        self.device = (
            device
            if device is not None
            else torch.device("cuda" if torch.cuda.is_available() else "cpu")
        )
        self._spotify_client: Optional[SpotifyClient] = None
        self._spotify_credentials: Optional[tuple] = None

    def prepare(self, **kwargs) -> Requirements:
        return Requirements(input_size=1)

    def _get_spotify_client(self, kwargs: dict) -> SpotifyClient:
        client_id = kwargs.get("spotify_client_id") or os.environ.get("SPOTIFY_CLIENT_ID", "")
        client_secret = kwargs.get("spotify_client_secret") or os.environ.get("SPOTIFY_CLIENT_SECRET", "")
        redirect_uri = kwargs.get("spotify_redirect_uri") or os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
        headless = kwargs.get("headless_mode", True)
        creds = (client_id, client_secret, redirect_uri, headless)
        if self._spotify_client is None or self._spotify_credentials != creds:
            self._spotify_credentials = creds
            self._spotify_client = SpotifyClient(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                headless_mode=headless,
            )
        return self._spotify_client

    def __call__(self, **kwargs) -> dict:
        prompt_template = (
            kwargs.get("prompt_template")
            or os.environ.get("SPOTIFY_PROMPT_TEMPLATE", "Artistic visualization of {song} by {artist}")
        )
        fallback_prompt = (
            kwargs.get("fallback_prompt")
            or os.environ.get("SPOTIFY_FALLBACK_PROMPT", "Abstract flowing colors and shapes")
        )

        try:
            client = self._get_spotify_client(kwargs)
            track = client.get_current_track()
        except Exception as e:
            logger.warning("Spotify get_current_track failed: %s", e)
            track = None

        if track is None or not track.is_playing:
            prompt = fallback_prompt
            logger.warning(
                "Spotify preprocessor: no track playing or API failed. Using fallback. "
                "Check SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and token at ~/.scope-spotify/.spotify_token_cache"
            )
        else:
            try:
                prompt = prompt_template.format(song=track.name, artist=track.artist)
            except KeyError:
                prompt = f"Artistic visualization of {track.name} by {track.artist}"
            logger.info("Spotify preprocessor: prompt from track: %s by %s", track.name, track.artist)

        return self._passthrough(kwargs, prompt)

    def _passthrough(self, kwargs: dict, prompt: str) -> dict:
        video = kwargs.get("video")
        if video is not None and len(video) > 0:
            frames = torch.stack([f.squeeze(0) for f in video], dim=0)
            frames = frames.to(device=self.device, dtype=torch.float32) / 255.0
        else:
            frames = torch.zeros(1, 512, 512, 3, device=self.device)
        return {"video": frames.clamp(0, 1), "prompt": prompt}
