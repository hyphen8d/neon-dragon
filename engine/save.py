"""Load/save character data to JSON files under saves/."""

from __future__ import annotations

import json
from pathlib import Path

from engine.character import Character

SAVES_DIR = Path(__file__).resolve().parent.parent / "saves"


def _save_path(name: str) -> Path:
    slug = name.strip().lower().replace(" ", "_")
    return SAVES_DIR / f"{slug}.json"


def list_saves() -> list[str]:
    SAVES_DIR.mkdir(exist_ok=True)
    return sorted(p.stem for p in SAVES_DIR.glob("*.json"))


def save_exists(name: str) -> bool:
    return _save_path(name).exists()


def save_character(character: Character) -> None:
    SAVES_DIR.mkdir(exist_ok=True)
    _save_path(character.name).write_text(json.dumps(character.to_dict(), indent=2))


def load_character(slug: str) -> Character:
    data = json.loads(_save_path(slug).read_text())
    return Character.from_dict(data)


def delete_save(slug: str) -> None:
    path = _save_path(slug)
    if path.exists():
        path.unlink()
