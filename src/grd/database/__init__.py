from pathlib import Path

# For faster loading, don't import database submodules here
from ..dirs import dirs

engine_path = Path(f"{dirs.user_data_dir}/data.db")
