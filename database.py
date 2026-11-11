import json
import os
from typing import Any, Dict, Union

from config import CONFESS_FILE, FILTER_FILE


def load_json(file_path: Union[str, os.PathLike[str]]) -> Dict[str, Any]:
    path = os.fspath(file_path)
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_json(file_path: Union[str, os.PathLike[str]], data: Dict[str, Any]) -> None:
    path = os.fspath(file_path)
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


filters_db = load_json(FILTER_FILE)
confess_settings = load_json(CONFESS_FILE)
confess_cooldown: Dict[int, float] = {}
