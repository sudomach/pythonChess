import os
import sys
from pathlib import Path

MIN_WINDOW_SIZE = (640, 480)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return PROJECT_ROOT


def get_resource_path(*relative_parts: str) -> Path:
    return get_base_dir().joinpath(*relative_parts)


def get_user_data_dir() -> Path:
    if os.name == "nt":
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / "PythonChess"
    return PROJECT_ROOT / "data"
