# github-release-downloader

![A demonstration of the program in bash](/images/demo-2023-03-15.png)

A command-line program written in Python for downloading GitHub release assets.

## Notice

[github-release-downloader on PyPI](https://pypi.org/project/github-release-downloader/)
is a completely distinct project authored by MaxBQb.
Check out [their repository](https://github.com/MBQbUtils/GithubReleaseDownloader)
if you are interested in a library+CLI for the same purpose!

## Features

### Authenticated API requests

A [Personal Access Token] can be provided to the program using the `grd auth`
command. This allows for making authenticated API requests, which are not
limited to the usual [60 requests/hour] rate limit. This application only
requires read permission for whatever repositories you will be downloading
from (for classic tokens, they should have the `repo:public_repo` permission).

[Personal Access Token]: https://github.com/settings/tokens
[60 requests/hour]: https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting

### API response caching

API responses are cached in an [SQLite] database to reduce API requests that
would count against your current rate limit.

[SQLite]: https://sqlite.org/index.html

### Encryption-at-rest support

If the [SQLite] library used by your Python installation has encryption support
(for example [SEE], [SQLCipher], and [SQLiteMultipleCiphers]), the `grd encrypt`
command can be used to add a custom passphrase, protecting your access token from
being misused. Each time the database needs to be opened, you will be prompted
for your passphrase.

[SEE]: https://sqlite.org/see/doc/release/www/readme.wiki
[SQLCipher]: https://github.com/sqlcipher/sqlcipher
[SQLiteMultipleCiphers]: https://github.com/utelle/SQLite3MultipleCiphers/

## Dependencies

- [Python 3.11] or higher

[Python 3.11]: https://www.python.org/downloads/

## Usage

1. Install github-release-downloader.

   If you have Git installed, you can run the following command:

   ```sh
   pip install git+https://github.com/thegamecracks/github-release-downloader
   ```

   For users without Git, you can download the repository [as a zip], then
   extract it, open a terminal inside the directory, and run:

   ```sh
   pip install .
   ```

   Several dependencies are required by this project so installing in
   a [virtual environment] is recommended. If you prefer to not handle
   the virtual environment yourself, installing this through [pipx] is
   a good alternative:

   ```sh
   pip install pipx  # see their proper installation instructions on PyPI
   pipx install git+https://github.com/thegamecracks/github-release-downloader
   ```

2. (Optional) Create and add a [Personal Access Token](#authenticated-api-requests).

3. Run `grd download <owner> <repo>` to download an asset from that repository,
   or alternatively `python -m grd download <owner> <repo>`.

[as a zip]: https://github.com/thegamecracks/github-release-downloader/archive/refs/heads/main.zip
[virtual environment]: https://docs.python.org/3/library/venv.html
[pipx]: https://pypi.org/project/pipx/

## Development

### Project Structure

- src/
   - alembic/ - Contains the [alembic] database migration scripts.
   - cli/ - Implements the command-line interface with [Click].
   - client/ - Provides the API client and [Pydantic] models to interact with GitHub.
   - database/ - Defines the [SQLAlchemy] models and connections to the SQLite database.

[alembic]: https://alembic.sqlalchemy.org/
[Click]: https://click.palletsprojects.com/
[Pydantic]: https://docs.pydantic.dev/
[SQLAlchemy]: https://docs.sqlalchemy.org/en/20/

### Todo-list

- [ ] `list <owner> <repo>` - list available releases for a repository
- [ ] Allow downloading tar/zip archives

### Wishlist

- [ ] Terminal user interface (perhaps with [textual]?)

[textual]: https://github.com/Textualize/textual
