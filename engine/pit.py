"""Load The Pit's gladiator roster."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "pit.json"


def load_gladiators() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["gladiators"]
