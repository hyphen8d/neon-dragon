"""Load Doc Wire's usable-item catalog and handle buying/using consumables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console

from engine.character import Character
from engine.status_effects import apply_effect

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "usable_items.json"


def load_usable_items() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["usable_items"]


def get_usable_item(item_id: str) -> dict[str, Any]:
    for item in load_usable_items():
        if item["id"] == item_id:
            return item
    raise KeyError(item_id)


def describe_effect(item: dict[str, Any]) -> str:
    """One-line summary of what an item does, for shop and combat menus."""
    if item["effect"] == "heal":
        return f"Heals {item['amount']} HP"
    if item["effect"] == "stun":
        return f"Stuns {item['faction']} enemies for {item['duration']} round(s)"
    return item["effect"]


def buy_item(character: Character, item_id: str) -> dict[str, Any]:
    """Buy one copy of an item and add it to the character's inventory."""
    item = get_usable_item(item_id)
    character.credits -= item["cost"]
    character.inventory.append(item_id)
    return item


def use_item(character: Character, item_id: str, console: Console, enemy: Any = None) -> None:
    """Consume one copy of an item from inventory and apply its effect.
    `enemy` is required for enemy-targeted effects (e.g. stun); heal-type
    effects ignore it."""
    item = get_usable_item(item_id)
    character.inventory.remove(item_id)

    if item["effect"] == "heal":
        missing = character.max_hp - character.hp
        healed = min(missing, item["amount"])
        character.hp += healed
        if healed > 0:
            console.print(f"[bold bright_magenta]{item['name']} used.[/bold bright_magenta] +{healed} HP.")
        else:
            console.print(f"[dim]{item['name']} used, but you're already at full health.[/dim]")
        return

    if item["effect"] == "stun":
        if enemy is None:
            console.print(f"[dim]Nothing to use {item['name']} on right now.[/dim]")
            return
        target_faction = item.get("faction")
        if target_faction and enemy.faction != target_faction:
            console.print(
                f"[dim]{item['name']} fizzles — {enemy.name} isn't running the systems "
                f"it's built for.[/dim]"
            )
            return
        apply_effect(enemy, "stunned", item["duration"])
        console.print(
            f"[bold cyan]{item['name']}![/bold cyan] {enemy.name}'s systems lock up — "
            f"stunned for {item['duration']} round(s)."
        )
        return

    raise ValueError(f"Unknown usable item effect: {item['effect']!r}")
