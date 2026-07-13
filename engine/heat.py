"""Faction Heat: racking up kills against one faction in a single day
raises the odds of that faction sending an ambush your way. Heat is
tracked per day and wiped clean whenever the player sleeps it off at
the safehouse (see hub.py's _sleep_and_advance_day)."""

from __future__ import annotations

from engine.character import Character

# Factions with enough street presence in Neo Meridian to retaliate.
# Ronin, Feral, and Gladiator kills don't build heat — no organization
# behind them to come looking for you.
HEAT_FACTIONS = ("Corp", "Street Gang")

HEAT_KILL_THRESHOLD = 3
AMBUSH_CHANCE = 0.15


def record_kill(character: Character, faction: str) -> None:
    character.daily_kills[faction] = character.daily_kills.get(faction, 0) + 1


def has_heat(character: Character, faction: str) -> bool:
    return character.daily_kills.get(faction, 0) > HEAT_KILL_THRESHOLD


def hot_factions(character: Character) -> list[str]:
    """Which heat-tracked factions are currently running hot on this
    character, in HEAT_FACTIONS order."""
    return [faction for faction in HEAT_FACTIONS if has_heat(character, faction)]


def reset_daily_kills(character: Character) -> None:
    character.daily_kills = {}
