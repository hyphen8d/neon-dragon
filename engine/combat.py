"""Turn-based combat resolution."""

from __future__ import annotations

import random
from dataclasses import dataclass

from rich.console import Console
from rich.prompt import Prompt

from engine.character import Character

console = Console()


@dataclass
class Enemy:
    name: str
    hp: int
    attack: int
    defense: int
    credits_reward: int
    xp_reward: int

    @property
    def alive(self) -> bool:
        return self.hp > 0


def roll_damage(attack: int, defense: int) -> int:
    return max(1, attack + random.randint(1, 6) - defense)


def run_combat(character: Character, enemy_data: dict) -> None:
    """Resolve a fight round by round. Mutates character HP/credits/XP in place."""
    enemy = Enemy(**enemy_data)
    console.print(f"\n[bold red]{enemy.name}[/bold red] (HP {enemy.hp}) blocks your path.")

    while character.hp > 0 and enemy.alive:
        console.print(
            f"\n[bright_cyan]{character.name}[/bright_cyan] HP {character.hp}/{character.max_hp}   "
            f"[red]{enemy.name}[/red] HP {max(enemy.hp, 0)}"
        )
        action = Prompt.ask(
            "[1] Attack  [2] Tech/Hack  [3] Defend  [4] Flee",
            choices=["1", "2", "3", "4"],
            show_choices=False,
        )
        defending = False

        if action == "1":
            dmg = roll_damage(character.attack, enemy.defense)
            enemy.hp -= dmg
            console.print(f"[white]You strike for {dmg} damage.[/white]")
        elif action == "2":
            dmg = roll_damage(character.tech, enemy.defense)
            enemy.hp -= dmg
            console.print(f"[white]You hack their systems for {dmg} damage.[/white]")
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

        dmg = roll_damage(enemy.attack, character.defense)
        if defending:
            dmg = max(0, dmg // 2)
        character.hp = max(0, character.hp - dmg)
        console.print(f"[red]{enemy.name} hits you for {dmg} damage.[/red]")

    if character.hp <= 0:
        _handle_defeat(character)
    else:
        _handle_victory(character, enemy)


def _handle_victory(character: Character, enemy: Enemy) -> None:
    character.credits += enemy.credits_reward
    character.xp += enemy.xp_reward
    console.print(
        f"\n[bold bright_magenta]{enemy.name} goes down.[/bold bright_magenta] "
        f"+{enemy.credits_reward} credits, +{enemy.xp_reward} XP."
    )


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
