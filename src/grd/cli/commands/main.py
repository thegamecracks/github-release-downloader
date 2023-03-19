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
    """github-release-downloader

    A user-friendly utility for downloading GitHub release assets.

    \b
    Examples:
        # Download an asset from username/repository
        grd download USERNAME REPOSITORY

    \b
        # Use maximum logging verbosity
        grd -vvv download USERNAME REPOSITORY

    \b
        # Update authentication credentials
        grd auth

    """
    if verbose:
        import logging

        levels = {
            1: logging.WARNING,
            2: logging.INFO,
            3: logging.DEBUG,
        }

        logging.basicConfig(
            format="%(levelname)s:%(name)s: %(message)s",
            level=levels.get(verbose, logging.DEBUG),
        )
