# github-release-downloader

![A demonstration of the program in bash](/images/demo-2023-03-15.png)

A command-line program written in Python for downloading GitHub release assets.

## Features

### Authenticated API requests

A [Personal Access Token] can be provided to the program to make authenticated
API requests, which are not limited to the usual [60 requests/hour] rate limit.
The token should only be given read permission for whatever repositories you
will be downloading from (classic tokens should receive `repo:public_repo`).

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

This package requires [Python 3.11] or higher to be installed.

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

   The above commands will install multiple dependencies
   so a [virtual environment] is recommended.

2. (Optional) Create and add a [Personal Access Token] to the program.

3. Run `grd download <owner> <repo>` to download an asset from that repository,
   or alternatively `python -m grd download <owner> <repo>`.

[as a zip]: https://github.com/thegamecracks/github-release-downloader/archive/refs/heads/main.zip
[virtual environment]: https://docs.python.org/3/library/venv.html

## Development

### Todo-list

- [X] Data persistency

    - [X] Username and token
    - [X] Response caching

        - [X] Time-based invalidation
        - [X] Manual invalidation

    - [X] Encryption-at-rest support

- [ ] Command-line interface

    - [X] `auth` - Set or clear authentication
    - [X] `download [-r/--release <name>] [-f/--file <name>] <owner> <repo>`

        - [ ] Downloading tar/zip archives

    - [ ] `list [-r/--release <name>] <owner> <repo>`

- [ ] Explicit handling of API error status codes

    - [ ] 429 Ratelimited
    - [ ] 404 Removed releases/assets
    - [X] Cache invalidation

- [X] Implement [ETag caching](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#conditional-requests)

### Wishlist

- [ ] Terminal user interface (perhaps with [textual]?)

[textual]: https://github.com/Textualize/textual
