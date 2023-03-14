"""
Provides an interface to the GitHub API.

API Reference:  https://docs.github.com/en/rest?apiVersion=2022-11-28
"""
from .http import create_client
from .release import ReleaseClient
