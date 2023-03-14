from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, Response, User
from ..appdirs import dirs


Path(dirs.user_data_dir).mkdir(parents=True, exist_ok=True)
data_engine = create_engine(f"sqlite+pysqlite:///{dirs.user_data_dir}/data.db")
data_session = sessionmaker(data_engine)
Base.metadata.create_all(data_engine)
