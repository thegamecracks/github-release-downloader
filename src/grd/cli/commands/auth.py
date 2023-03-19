import click

from .main import main
from ..state import CLIState, pass_state

__all__ = ("auth",)


@main.command()
@pass_state
def auth(ctx: CLIState):
    """Update GitHub username and token authentication.

    To get a Personal Access Token, create one at
    https://github.com/settings/tokens.

    """

    with ctx.begin() as session:
        user = ctx.get_user(session)

        click.echo(
            f"GitHub Username: {user.github_username or '<unset>'}\n"
            f"GitHub Token: {'*****' if user.github_token else '<unset>'}"
        )

        ctx.ask_for_auth(user, only_missing=False)
