import datetime
from typing import Any

from sqlalchemy import JSON
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    ...


class Response(Base, kw_only=True):
    """Stores a key-value mapping of cached responses."""

    __tablename__ = "response_cache"

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)


class User(Base, kw_only=True):
    """Stores various user settings."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    github_username: Mapped[str]
    github_token: Mapped[str]


if __name__ == "__main__":
    from sqlalchemy import create_mock_engine
    from sqlalchemy.sql.elements import CompilerElement

    def dump(sql: CompilerElement, *args, **kwargs):
        print(sql.compile(dialect=engine.dialect))

    engine = create_mock_engine("sqlite+pysqlite://", dump)  # type: ignore
    Base.metadata.create_all(engine)
