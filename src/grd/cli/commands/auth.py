import click

from .main import main
from ..utils import ask_for_auth

__all__ = ("auth",)


@main.command()
def auth():
    """Update GitHub username and token authentication."""
    from ...database import data_session, get_user

    with data_session.begin() as session:
        user = get_user(session)

        click.echo(
            f"GitHub Username: {user.github_username or '<unset>'}\n"
            f"GitHub Token: {'*****' if user.github_token else '<unset>'}"
        )

        ask_for_auth(user, only_missing=False)
