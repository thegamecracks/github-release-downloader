import click


class CLIState:
    def __init__(self) -> None:
        self.has_setup_database = False

    def setup_database(self) -> None:
        """Sets up the database for the first time.

        This method is idempotent.

        """
        if self.has_setup_database:
            return

        from ..database import setup_database

        setup_database()


pass_state = click.make_pass_decorator(CLIState, ensure=True)
