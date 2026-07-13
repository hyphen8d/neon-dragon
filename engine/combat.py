"""Turn-based combat resolution."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from rich.console import Console
from rich.prompt import Prompt

from engine.character import Character, hp_style
from engine.leveling import check_level_up
from engine.quests import notify_step, print_quest_result
from engine.shop import get_item
from engine.status_effects import EFFECT_LABELS, apply_effect, process_round_start

console = Console(highlight=False)


@dataclass
class Enemy:
    name: str
    hp: int
    attack: int
    defense: int
    credits_reward: int
    xp_reward: int
    reputation_reward: int = 0
    inflict_effect: str | None = None
    inflict_chance: float = 0.0
    inflict_duration: int = 0
    faction: str = "Unknown"
    status_effects: dict = field(default_factory=dict)

    @property
    def alive(self) -> bool:
        return self.hp > 0


def roll_damage(attack: int, defense: int) -> int:
    return max(1, attack + random.randint(1, 6) - defense)


def _status_text(combatant) -> str:
    if not combatant.status_effects:
        return ""
    parts = [f"{EFFECT_LABELS.get(e, e)} ({r})" for e, r in combatant.status_effects.items()]
    return f"   [yellow]{', '.join(parts)}[/yellow]"


def _gear_inflict(character: Character, enemy: Enemy, slot: str, console: Console) -> None:
    """Higher-tier arm/eyes cyberware can inflict a status effect on the enemy."""
    item_id = character.cyberware.get(slot)
    if not item_id:
        return
    item = get_item(item_id)
    effect = item.get("inflict_effect")
    if not effect or random.random() >= item.get("inflict_chance", 0):
        return
    apply_effect(enemy, effect, item.get("inflict_duration", 1))
    label = EFFECT_LABELS.get(effect, effect)
    console.print(f"[yellow]{item['name']} leaves {enemy.name} {label.lower()}![/yellow]")


def run_combat(character: Character, enemy_data: dict) -> None:
    """Resolve a fight round by round. Mutates character HP/credits/XP in place."""
    enemy = Enemy(**enemy_data)
    console.print(f"\n[bold red]{enemy.name}[/bold red] (HP {enemy.hp}) blocks your path.")

    while character.hp > 0 and enemy.alive:
        stunned = process_round_start(character, console, is_player=True)
        if character.hp <= 0:
            break

        style = hp_style(character.hp, character.max_hp)
        console.print(
            f"\n[bright_cyan]{character.name}[/bright_cyan] HP [{style}]{character.hp}/{character.max_hp}[/{style}]"
            f"{_status_text(character)}   [red]{enemy.name}[/red] HP {max(enemy.hp, 0)}{_status_text(enemy)}"
        )

        defending = False
        if stunned:
            console.print("[yellow]You're stunned — you can't act this round![/yellow]")
        else:
            action = Prompt.ask(
                "[bright_magenta]1[/bright_magenta] Attack  [bright_magenta]2[/bright_magenta] Tech/Hack  "
                "[bright_magenta]3[/bright_magenta] Defend  [bright_magenta]4[/bright_magenta] Flee",
                choices=["1", "2", "3", "4"],
                show_choices=False,
            )

            if action == "1":
                dmg = roll_damage(character.attack, enemy.defense)
                enemy.hp -= dmg
                console.print(f"[white]You strike for {dmg} damage.[/white]")
                if enemy.alive:
                    _gear_inflict(character, enemy, "arm", console)
            elif action == "2":
                dmg = roll_damage(character.tech, enemy.defense)
                enemy.hp -= dmg
                console.print(f"[white]You hack their systems for {dmg} damage.[/white]")
                if enemy.alive:
                    _gear_inflict(character, enemy, "eyes", console)
            elif action == "3":
                defending = True
                console.print("[dim]You brace for the hit.[/dim]")
            else:
                if random.random() < 0.5:
                    console.print("[dim]You slip into the shadows and get away.[/dim]")
                    return
                console.print("[dim]You can't shake them — they block your escape.[/dim]")

        if not enemy.alive:
            break

        enemy_stunned = process_round_start(enemy, console)
        if not enemy.alive:
            break

        if enemy_stunned:
            console.print(f"[yellow]{enemy.name} is stunned and can't act![/yellow]")
        else:
            dmg = roll_damage(enemy.attack, character.defense)
            if defending:
                dmg = max(0, dmg // 2)
            character.hp = max(0, character.hp - dmg)
            console.print(f"[red]{enemy.name} hits you for {dmg} damage.[/red]")

            if enemy.inflict_effect and random.random() < enemy.inflict_chance:
                apply_effect(character, enemy.inflict_effect, enemy.inflict_duration)
                label = EFFECT_LABELS.get(enemy.inflict_effect, enemy.inflict_effect)
                console.print(f"[yellow]The hit leaves you {label.lower()}![/yellow]")

    if character.hp <= 0:
        _handle_defeat(character)
    else:
        _handle_victory(character, enemy)


def _handle_victory(character: Character, enemy: Enemy) -> None:
    character.credits += enemy.credits_reward
    character.xp += enemy.xp_reward
    character.reputation += enemy.reputation_reward
    character.kills[enemy.name] = character.kills.get(enemy.name, 0) + 1
    reward_text = f"+{enemy.credits_reward} credits, +{enemy.xp_reward} XP"
    if enemy.reputation_reward:
        reward_text += f", +{enemy.reputation_reward} reputation"
    console.print(f"\n[bold bright_magenta]{enemy.name} goes down.[/bold bright_magenta] {reward_text}.")
    check_level_up(character, console)
    for result in notify_step(character, "kill", enemy.name):
        print_quest_result(console, character, result)


TRAUMA_BILL = 40


def _handle_defeat(character: Character) -> None:
    character.credits -= TRAUMA_BILL
    character.hp = 1
    console.print(
        f"\n[bold red]You go down hard.[/bold red] Doc Wire's trauma team scrapes you "
        f"off the pavement and stabilizes you — {TRAUMA_BILL} credits, billed on the spot."
    )
    if character.credits < 0:
        console.print(f"[red]You're {-character.credits} in the hole now.[/red]")
