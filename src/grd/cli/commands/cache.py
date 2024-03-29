from __future__ import annotations

from typing import TYPE_CHECKING

import click

from .main import main
from ..click_types import TimedeltaType
from ..state import CLIState, pass_state

if TYPE_CHECKING:
    import datetime

__all__ = (
    "cache",
    "cache_clear",
    "cache_expire",
    "cache_where",
)


@main.group()
def cache() -> None:
    """Manage the response cache."""


@cache.command(name="clear")
@click.option("-y", "--yes", help="Skip confirmation prompt", is_flag=True)
@pass_state
def cache_clear(ctx: CLIState, yes: bool) -> None:
    """Manually clear the response cache.

    This may be needed if there were release updates for a repository
    that was recently fetched.

    """

    def confirm_clear():
        from InquirerPy import inquirer

        message = "Are you sure you want to clear the response cache?"
        return inquirer.confirm(message).execute()

    cache = ctx.get_response_cache()

    if yes or confirm_clear():
        cache.clear(expired=False)


@cache.command(name="expire")
@click.argument("duration", required=False, type=TimedeltaType())
@click.option("-u", "--unset", is_flag=True)
@pass_state
def cache_expire(ctx: CLIState, duration: datetime.timedelta | None, unset: bool):
    """Sets the automatic cache expiration to the given duration.

    \b
    Examples:
        grd cache expire          # display the current duration
        grd cache expire 1d       # set the expiration to 1 day
        grd cache expire --unset  # disable time-based expiration
                                  # (not recommended)

    """
    with ctx.begin() as session:
        user = ctx.get_user(session)

        if unset:
            user.cache_expiry = None
        elif duration is not None:
            user.cache_expiry = duration
        elif user.cache_expiry is not None:
            click.echo(f"Response cache expires after: {user.cache_expiry}")
        else:
            click.echo("Response cache expiration is turned off.")


@cache.command(name="where")
def cache_where() -> None:
    """Show where the cache database is located."""
    from ...database import engine_path

    click.echo(engine_path)
