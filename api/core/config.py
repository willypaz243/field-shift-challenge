import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return Path(os.getenv("DATA_DIR", ROOT / "data"))
