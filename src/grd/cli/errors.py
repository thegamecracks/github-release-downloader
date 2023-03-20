from __future__ import annotations

import datetime
import functools
from typing import (
    TYPE_CHECKING,
    Callable,
    Concatenate,
    NoReturn,
    ParamSpec,
    TypeVar,
)

from ..client.dates import maybe_parse_http_date

if TYPE_CHECKING:
    import httpx

    from .state import CLIState


def _maybe_parse_retry_after(s: str | None) -> datetime.datetime | None:
    if s is None:
        return None

    try:
        delta = datetime.timedelta(seconds=int(s))
        return datetime.datetime.now(datetime.timezone.utc) + delta
    except ValueError:
        return maybe_parse_http_date(s)


def _transform_httpx_status_error(e: httpx.HTTPStatusError) -> NoReturn:
    def check_ratelimits() -> None:
        if int(headers.get("X-Ratelimit-Remaining")) > 0:
            return

        date = _maybe_parse_retry_after(headers.get("Retry-After"))
        date = date or maybe_parse_http_date(headers.get("X-Ratelimit-Reset"))
        if date is not None:
            e.add_note(
                "Please retry after: {} ({})".format(
                    date.astimezone().strftime("%c"),
                    datetime.datetime.now().astimezone() - date,
                )
            )

    status_code = e.response.status_code
    headers = e.response.headers

    e.add_note(e.response.text)

    if status_code == 401:
        data = e.response.json()

        message = data.get("message")
        if message == "Bad credentials":
            e.add_note(
                "The token used for authentication was invalid. "
                "Please use `grd auth` to correct your token. Note that too many "
                "invalid requests can result in a temporary ban from the API."
            )
    elif status_code in (403, 429):
        check_ratelimits()

    raise e


P = ParamSpec("P")
T = TypeVar("T")


def wrap_httpx_errors(
    func: Callable[Concatenate[CLIState, P], T]
) -> Callable[Concatenate[CLIState, P], T]:
    @functools.wraps(func)
    def wrapper(ctx: CLIState, *args: P.args, **kwargs: P.kwargs) -> T:
        import httpx

        try:
            return func(ctx, *args, **kwargs)
        except httpx.HTTPStatusError as e:
            _transform_httpx_status_error(e)

    return wrapper
