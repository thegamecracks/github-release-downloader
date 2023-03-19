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
    if verbose:
        import logging

        levels = {
            1: logging.WARNING,
            2: logging.INFO,
            3: logging.DEBUG,
        }

        logging.basicConfig(
            format="%(levelname)s:%(name)s:%(message)s",
            level=levels.get(verbose, logging.DEBUG),
        )
