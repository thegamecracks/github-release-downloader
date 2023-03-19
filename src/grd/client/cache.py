def bucket_predicate(exc: Exception) -> bool:
    """The predicate function that should be used when creating a
    :py:class:`ResponseCache` to be used by the client.
    """
    import httpx

    if not isinstance(exc, httpx.HTTPStatusError):
        return False

    status = exc.response.status_code
    return status >= 500 or status == 429
