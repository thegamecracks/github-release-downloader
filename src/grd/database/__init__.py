from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..appdirs import dirs


def setup_schema():
    from .models import Base

    Base.metadata.create_all(data_engine)


data_engine = create_engine(f"sqlite+pysqlite:///{dirs.user_data_dir}/data.db")
data_session = sessionmaker(data_engine)
