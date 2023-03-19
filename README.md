# github-release-downloader

![A demonstration of the program in bash](/images/demo-2023-03-15.png)

A command-line program written in Python for downloading GitHub release assets.

## Dependencies

This package requires Python 3.11 to be installed.

## Usage

1. Generate a [Personal Access Token] for your GitHub account.

   This is used to make authenticated requests, avoiding the [60 requests/hour]
   rate limit. The token should only be given read permission for whatever
   repositories you will be downloading from (`repo:public_repo` for classic tokens).

   As of now, this application does not support making unauthenticated requests.

2. Install github-release-downloader.

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

3. Run `grd download <owner> <repo>` to download an asset from that repository,
   or alternatively `python -m grd download <owner> <repo>`.

[Personal Access Token]: https://github.com/settings/tokens
[60 requests/hour]: https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting
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

    - [X] auth - Set or clear authentication
    - [X] download [-r/--release <name>] [-f/--file <name>] <owner> <repo>

        - [ ] Downloading tar/zip archives

    - [ ] list [-r/--release <name>] <owner> <repo>

- [ ] Explicit handling of API error status codes

    - [ ] 429 Ratelimited
    - [ ] 404 Removed releases/assets
    - [ ] Cache invalidation

- [ ] Improved logging

### Wishlist

- [ ] Terminal user interface (perhaps with [textual]?)

[textual]: https://github.com/Textualize/textual
