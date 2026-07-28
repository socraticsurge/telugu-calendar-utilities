"""Vercel entrypoint for the additive Panchangam HTTP API."""

from telugu_panchangam.api.app import app

__all__ = ["app"]
