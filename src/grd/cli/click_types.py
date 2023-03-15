import datetime
import re

import click


class TimedeltaType(click.ParamType):
    """A click parameter type for :py:class:`datetime.timedelta`.

    Supported formats are:

        * 120s
        * 3h0m
        * 3d 23h 59m 59s (any separator allowed)

    """

    name = "duration"

    _unit_mapping = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    _unit_regex = re.compile(r"(\d+)([a-z])")

    def convert(
        self,
        value: str,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> datetime.timedelta:
        value = value.lower()
        delta = datetime.timedelta()

        m: re.Match | None = None
        for m in self._unit_regex.finditer(value):
            n_str, unit = m.groups()
            scale = self._unit_mapping.get(unit)
            if scale is None:
                valid_units = "|".join(self._unit_mapping)
                self.fail(f"duration unit must be {valid_units}, not {unit!r}")

            delta += datetime.timedelta(seconds=int(n_str) * scale)

        if m is None:
            self.fail("invalid duration (format: 1d:2h:3m:4s)")

        return delta
