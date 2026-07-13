"""Load quest definitions and track a character's progress through them."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console

from engine.character import Character
from engine.leveling import check_level_up

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "quests.json"


def load_quests() -> list[dict[str, Any]]:
    data = json.loads(CONTENT_PATH.read_text())
    return data["quests"]


def get_quest(quest_id: str) -> dict[str, Any]:
    for quest in load_quests():
        if quest["id"] == quest_id:
            return quest
    raise KeyError(quest_id)


def _not_taken(character: Character, quest: dict[str, Any]) -> bool:
    return quest["id"] not in character.active_quests and quest["id"] not in character.completed_quests


def _meets_requirements(character: Character, quest: dict[str, Any]) -> bool:
    return (
        character.reputation >= quest.get("min_reputation", 0)
        and character.charisma >= quest.get("min_charisma", 0)
        and character.level >= quest.get("min_level", 1)
    )


def available_quests(character: Character, board: str = "Fixer Board") -> list[dict[str, Any]]:
    """Contracts on this board not yet taken/completed whose requirements are met."""
    return [
        q
        for q in load_quests()
        if q.get("board", "Fixer Board") == board and _not_taken(character, q) and _meets_requirements(character, q)
    ]


def locked_quests(character: Character, board: str = "Fixer Board") -> list[dict[str, Any]]:
    """Contracts on this board not yet taken/completed but still below requirements."""
    return [
        q
        for q in load_quests()
        if q.get("board", "Fixer Board") == board
        and _not_taken(character, q)
        and not _meets_requirements(character, q)
    ]


def accept_quest(character: Character, quest_id: str) -> None:
    character.active_quests[quest_id] = 0


def current_step(character: Character, quest_id: str) -> dict[str, Any]:
    quest = get_quest(quest_id)
    return quest["steps"][character.active_quests[quest_id]]


def advance_quest(character: Character, quest_id: str) -> dict[str, Any] | None:
    """Move a quest to its next step, granting the reward and returning the
    quest dict if that was the last step. Returns None otherwise."""
    quest = get_quest(quest_id)
    next_index = character.active_quests[quest_id] + 1
    if next_index < len(quest["steps"]):
        character.active_quests[quest_id] = next_index
        return None

    del character.active_quests[quest_id]
    character.completed_quests.append(quest_id)
    reward = quest["reward"]
    character.credits += reward["credits"]
    character.xp += reward["xp"]
    character.reputation += reward["reputation"]
    return quest


def notify_step(character: Character, step_type: str, target: str) -> list[dict[str, Any]]:
    """Check active quests for a step matching (step_type, target) and advance
    any that match. Returns one result dict per matching quest, each either
    {"quest": ..., "completed": True} or {"quest": ..., "completed": False,
    "next_step": ...}, for the caller to narrate."""
    results = []
    for quest_id in list(character.active_quests.keys()):
        step = current_step(character, quest_id)
        if step["type"] != step_type or step["target"] != target:
            continue
        quest = get_quest(quest_id)
        completed_quest = advance_quest(character, quest_id)
        if completed_quest is not None:
            results.append({"quest": completed_quest, "completed": True})
        else:
            results.append({"quest": quest, "completed": False, "next_step": current_step(character, quest_id)})
    return results


def print_quest_result(console: Console, character: Character, result: dict[str, Any]) -> None:
    quest = result["quest"]
    if result["completed"]:
        reward = quest["reward"]
        console.print(f"\n[bold bright_magenta]Contract complete:[/bold bright_magenta] {quest['title']}")
        console.print(f"  {quest['complete_text']}")
        console.print(
            f"  +{reward['credits']} credits, +{reward['xp']} XP, +{reward['reputation']} reputation."
        )
        check_level_up(character, console)
    else:
        console.print(
            f"\n[bright_magenta]Contract updated:[/bright_magenta] {quest['title']} — "
            f"{result['next_step']['description']}"
        )
