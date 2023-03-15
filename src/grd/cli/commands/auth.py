import click

from .main import main
from ..state import CLIState, pass_state
from ..utils import ask_for_auth

__all__ = ("auth",)


@main.command()
@pass_state
def auth(ctx: CLIState):
    """Update GitHub username and token authentication."""
    from ...database import sessionmaker, get_user

    ctx.setup_database()

    with sessionmaker.begin() as session:
        user = get_user(session)

        click.echo(
            f"GitHub Username: {user.github_username or '<unset>'}\n"
            f"GitHub Token: {'*****' if user.github_token else '<unset>'}"
        )

        ask_for_auth(user, only_missing=False)
