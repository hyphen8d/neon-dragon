"""Load Datashard lore collectibles and grant them as rare Undercity loot.

Datashards are pure worldbuilding — no stat payoff — dropped as a small
bonus on top of a clean Slice Drop Box crack or a successful Hunt Cache
sweep (see engine/hub.py's _jack_in/_scavenge), and readable afterward
from the hub's Archives screen."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

from engine.character import Character
from engine.theme import ACCENT, BORDER_RARE, RARE, TEXT_DIM

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "datashards.json"

# Deliberately modest — a bonus on top of the credit/Quantum Core payoff,
# not a competing reward, so it never feels like the "real" prize was missed.
DATASHARD_DROP_CHANCE = 0.12


def load_datashards() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["datashards"]


def get_datashard(shard_id: str) -> dict[str, Any]:
    for shard in load_datashards():
        if shard["id"] == shard_id:
            return shard
    raise KeyError(shard_id)


def maybe_find_datashard(character: Character, console: Console) -> None:
    """Roll for a Datashard find. Silent no-op on a miss, or if every
    shard in the pool is already unlocked -- called from both Jack In
    (on a clean crack) and Hunt Cache (on a successful sweep), so nothing
    here needs to know which one triggered it."""
    if random.random() >= DATASHARD_DROP_CHANCE:
        return
    unseen = [s for s in load_datashards() if s["id"] not in character.datashards]
    if not unseen:
        return

    shard = random.choice(unseen)
    character.datashards.append(shard["id"])
    console.print(
        Panel(
            f"[{TEXT_DIM}]Corrupted fragment recovered — added to your Archive.[/{TEXT_DIM}]\n"
            f"[{ACCENT}]{shard['title']}[/{ACCENT}]",
            title=f"[{RARE}]DATASHARD FOUND[/{RARE}]",
            border_style=BORDER_RARE,
            padding=(1, 2),
        )
    )
