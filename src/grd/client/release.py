from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Release
from .protocols import ResponseStreamable, Streamable

if TYPE_CHECKING:
    from .base import BaseClient


class ReleaseClient:
    """Handles retrieval of releases and assets."""

    def __init__(self, base: BaseClient) -> None:
        self.base = base

    def get_release_by_tag(self, owner: str, repo: str, tag: str) -> Release:
        """Gets a specific release from the repository by tag.

        The returned result may be cached.

        """
        response = self.base.cached_request(
            "GET",
            f"/repos/{owner}/{repo}/releases/tags/{tag}",
            headers=self.base.JSON_HEADERS,
        )
        return Release(**response)

    def get_latest_release(self, owner: str, repo: str) -> Release:
        """Gets the repository's latest release.

        The returned result may be cached.

        """
        response = self.base.cached_request(
            "GET",
            f"/repos/{owner}/{repo}/releases/latest",
            headers=self.base.JSON_HEADERS,
        )
        return Release(**response)

    def stream_asset(self, owner: str, repo: str, asset_id: int) -> Streamable:
        """Returns a stream of bytes for the given asset."""
        request = self.base.client.stream(
            "GET",
            f"/repos/{owner}/{repo}/releases/assets/{asset_id}",
            follow_redirects=True,
            headers={"Accept": "application/octet-stream"},
        )
        return ResponseStreamable(request)
