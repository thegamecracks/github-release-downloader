def bucket_predicate(exc: Exception) -> bool:
    """The predicate function that should be used when creating a
    :py:class:`ResponseCache` to be used by the client.
    """
    import httpx

    if not isinstance(exc, httpx.HTTPStatusError):
        return False

    status = exc.response.status_code
    # NOTE: GitHub's API actually raises 403 instead of 429
    return status >= 500 or status in (401, 403, 429)
