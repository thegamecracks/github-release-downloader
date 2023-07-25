import datetime
from typing import overload

http_date_format = "%a, %d %b %Y %H:%M:%S %Z"


def format_http_date(dt: datetime.datetime) -> str:
    """Formats a datetime into an HTTP date.

    Reference:
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Date

    """
    s = dt.astimezone(datetime.timezone.utc).strftime(http_date_format)
    return s[: s.rindex("UTC")] + "GMT"


@overload
def maybe_parse_http_date(s: str) -> datetime.datetime:
    ...


@overload
def maybe_parse_http_date(s: None) -> None:
    ...


def maybe_parse_http_date(s: str | None) -> datetime.datetime | None:
    """Maybe parses an HTTP date into a datetime."""
    if s is not None:
        dt = datetime.datetime.strptime(s, http_date_format)
        return dt.replace(tzinfo=datetime.timezone.utc)
