"""Faction lookups across all enemy content sources (Undercity, The Pit)."""

from __future__ import annotations

from engine.encounters import load_encounters
from engine.pit import load_gladiators


def enemy_faction(name: str) -> str:
    for encounter in load_encounters():
        enemy = encounter.get("enemy")
        if enemy and enemy["name"] == name:
            return enemy.get("faction", "Unknown")
    for gladiator in load_gladiators():
        if gladiator["name"] == name:
            return gladiator.get("faction", "Unknown")
    return "Unknown"
