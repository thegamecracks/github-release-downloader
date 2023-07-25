from __future__ import annotations

from pydantic import BaseModel


class Release(BaseModel):
    """Represents a release for a repository."""

    class Config:
        extras = "allow"

    assets: list[ReleaseAsset]
    id: int
    name: str


class ReleaseAsset(BaseModel):
    """An asset for a given release."""

    class Config:
        extras = "allow"

    id: int
    name: str


Release.model_rebuild()
