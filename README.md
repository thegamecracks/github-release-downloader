# github-release-downloader

![A demonstration of the program in bash](/images/demo-2023-03-15.png)

A command-line program written in Python for downloading GitHub release assets.

## TODO

- [ ] Data persistency

    - [X] Username and token
    - [ ] Response caching

        - [X] Time-based invalidation
        - [ ] Error-based invalidation
        - [X] Manual invalidation

    - [X] Encryption-at-rest support

- [ ] Command-line interface

    - [X] auth - Set or clear authentication
    - [ ] download [-r/--release <name>] <owner> <repo> <filename>
    - [ ] list [-r/--release <name>] <owner> <repo>

- [ ] Terminal user interface
