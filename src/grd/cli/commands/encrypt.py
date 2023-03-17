import click
from typing import Literal

from .main import main
from ..state import CLIState, pass_state


@main.command()
@click.option(
    "-l",
    "--lock",
    "mode",
    flag_value="lock",
    help="Lock the database with a new password",
)
@click.option(
    "-u",
    "--unlock",
    "mode",
    flag_value="unlock",
    help="Unlock and turn off database encryption",
)
@pass_state
def encrypt(ctx: CLIState, mode: Literal["lock", "unlock"] | None):
    """Configure database encryption.

    This requires the underlying SQLite library to support encryption.

    """
    from ...database.engine import sqlite_encrypter

    if mode is None:
        if ctx.is_database_encrypted():
            click.echo("Database appears to be encrypted")
        else:
            click.echo("Database is not encrypted")

    elif mode == "lock":
        ctx.setup_database()

        from InquirerPy import inquirer

        password = inquirer.secret("New password:").execute()
        with sqlite_encrypter.engine.connect() as conn:
            sqlite_encrypter.change_password(conn, password)

    elif mode == "unlock":
        if not ctx.is_database_encrypted():
            return click.echo("Database is already unencrypted")

        ctx.setup_database()

        with sqlite_encrypter.engine.connect() as conn:
            sqlite_encrypter.change_password(conn, "")

    else:
        raise RuntimeError(f"unexpected mode: {mode!r}")
