import datetime
from typing import Any

from sqlalchemy import DateTime, JSON, TypeDecorator
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)


# https://docs.sqlalchemy.org/en/20/core/custom_types.html#store-timezone-aware-timestamps-as-timezone-naive-utc
class TZDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif not value.tzinfo:
            # Interpret as local time
            value = value.astimezone()

        return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        return value


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    ...


class Response(Base, kw_only=True):
    """Stores a key-value mapping of cached responses."""

    __tablename__ = "response_cache"

    created_at: Mapped[datetime.datetime] = mapped_column(
        TZDateTime,
        default=datetime.datetime.now,
    )
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)


class User(Base, kw_only=True):
    """Stores various user settings."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    github_username: Mapped[str | None] = mapped_column(default=None)
    github_token: Mapped[str | None] = mapped_column(default=None)


if __name__ == "__main__":
    from sqlalchemy import create_mock_engine
    from sqlalchemy.sql.elements import CompilerElement

    def dump(sql: CompilerElement, *args, **kwargs):
        print(sql.compile(dialect=engine.dialect))

    engine = create_mock_engine("sqlite+pysqlite://", dump)  # type: ignore
    Base.metadata.create_all(engine)
