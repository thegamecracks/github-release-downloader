import click

__all__ = ("main",)


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity of the program.",
)
def main(verbose: int):
    from ...database import setup_database

    if verbose:
        import logging

        logging.basicConfig(
            format="%(levelname)s:%(name)s:%(message)s",
            level=logging.DEBUG,
        )

    setup_database()
