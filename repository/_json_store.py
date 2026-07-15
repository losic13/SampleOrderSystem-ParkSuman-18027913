import json
from pathlib import Path


def ensure_file(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        write_json(file_path, {})


def read_json(file_path: Path) -> dict:
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(file_path: Path, data: dict) -> None:
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
