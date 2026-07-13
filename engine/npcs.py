"""Load NPC definitions and pick dialogue lines."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "npcs.json"


def load_npcs() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["npcs"]


def npc_at(location: str) -> dict[str, Any] | None:
    for npc in load_npcs():
        if npc["location"] == location:
            return npc
    return None


def get_npc(npc_id: str) -> dict[str, Any]:
    for npc in load_npcs():
        if npc["id"] == npc_id:
            return npc
    raise KeyError(npc_id)


def random_line(npc: dict[str, Any]) -> str:
    return random.choice(npc["lines"])
