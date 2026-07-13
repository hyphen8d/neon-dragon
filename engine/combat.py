"""Turn-based combat resolution."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from rich.console import Console

from engine.character import Character, hp_style
from engine.leveling import check_level_up
from engine.quests import notify_step, print_quest_result
from engine.shop import get_item
from engine.status_effects import DRUNK_STAT_PENALTY, EFFECT_LABELS, apply_effect, has_effect, process_round_start
from engine.ui import hotkey_prompt

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
    dodge_chance: float = 0.0
    ignores_defend: bool = False
    status_effects: dict = field(default_factory=dict)

    @property
    def alive(self) -> bool:
        return self.hp > 0


CRIT_CHANCE = 0.2
CRIT_MULTIPLIER = 1.5


def roll_damage(attack: int, defense: int) -> tuple[int, bool]:
    """Returns (damage, was_critical)."""
    base = max(1, attack + random.randint(1, 6) - defense)
    if random.random() < CRIT_CHANCE:
        return max(base, int(base * CRIT_MULTIPLIER)), True
    return base, False


FINISHING_LINES = [
    "You finish it clean — {dmg} damage, lights out for {enemy}.",
    "One last hit and {enemy} folds.",
    "The killing blow lands hard. {enemy} doesn't get up.",
]


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


def _player_hit(enemy: Enemy, stat_value: int, verb: str, console: Console) -> bool:
    """Resolve one player attack against the enemy. Returns True if it connected
    (missed dodges don't trigger gear on-hit effects)."""
    if enemy.dodge_chance and random.random() < enemy.dodge_chance:
        console.print(f"[dim]{enemy.name} slips the hit — you swing through empty air.[/dim]")
        return False

    dmg, crit = roll_damage(stat_value, enemy.defense)
    enemy.hp -= dmg
    prefix = "[bold yellow]CRITICAL![/bold yellow] " if crit else ""

    if not enemy.alive:
        line = random.choice(FINISHING_LINES).format(enemy=enemy.name, dmg=dmg)
        console.print(f"{prefix}[bold bright_magenta]{line}[/bold bright_magenta]")
    else:
        console.print(f"{prefix}[white]You {verb} for {dmg} damage.[/white]")
    return True


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
            action = hotkey_prompt(
                console,
                [("A", "Attack"), ("T", "Tech/Hack"), ("D", "Defend"), ("F", "Flee")],
            )

            drunk_penalty = DRUNK_STAT_PENALTY if has_effect(character, "drunk") else 0

            if action == "A":
                stat_value = max(0, character.attack - drunk_penalty)
                if _player_hit(enemy, stat_value, "strike", console) and enemy.alive:
                    _gear_inflict(character, enemy, "arm", console)
            elif action == "T":
                stat_value = max(0, character.tech - drunk_penalty)
                if _player_hit(enemy, stat_value, "hack their systems", console) and enemy.alive:
                    _gear_inflict(character, enemy, "eyes", console)
            elif action == "D":
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
            dmg, crit = roll_damage(enemy.attack, character.defense)
            bypassed = defending and enemy.ignores_defend
            if defending and not enemy.ignores_defend:
                dmg = max(0, dmg // 2)
            character.hp = max(0, character.hp - dmg)
            prefix = "[bold yellow]CRITICAL![/bold yellow] " if crit else ""
            suffix = " Your guard didn't matter." if bypassed else ""
            console.print(f"{prefix}[red]{enemy.name} hits you for {dmg} damage.{suffix}[/red]")

            if enemy.inflict_effect and random.random() < enemy.inflict_chance:
                apply_effect(character, enemy.inflict_effect, enemy.inflict_duration)
                label = EFFECT_LABELS.get(enemy.inflict_effect, enemy.inflict_effect)
                console.print(f"[yellow]The hit leaves you {label.lower()}![/yellow]")

    if character.hp <= 0:
        _handle_defeat(character)
    else:
        _handle_victory(character, enemy)


BONUS_LOOT_CHANCE = 0.25


def _handle_victory(character: Character, enemy: Enemy) -> None:
    character.credits += enemy.credits_reward
    character.xp += enemy.xp_reward
    character.reputation += enemy.reputation_reward
    character.kills[enemy.name] = character.kills.get(enemy.name, 0) + 1
    reward_text = f"+{enemy.credits_reward} credits, +{enemy.xp_reward} XP"
    if enemy.reputation_reward:
        reward_text += f", +{enemy.reputation_reward} reputation"
    console.print(f"\n[bold bright_magenta]{enemy.name} goes down.[/bold bright_magenta] {reward_text}.")

    if random.random() < BONUS_LOOT_CHANCE:
        bonus = max(1, int(enemy.credits_reward * random.uniform(0.2, 0.5)))
        character.credits += bonus
        console.print(f"[bold yellow]Bonus salvage![/bold yellow] +{bonus} credits.")

    check_level_up(character, console)
    for result in notify_step(character, "kill", enemy.name):
        print_quest_result(console, character, result)


TRAUMA_BILL_BASE = 40
TRAUMA_BILL_PER_LEVEL = 15


def trauma_bill(level: int) -> int:
    """Doc Wire's rate rises with level, so a bad fight stays costly instead
    of becoming trivial once credit income outgrows a flat fee."""
    return TRAUMA_BILL_BASE + (level - 1) * TRAUMA_BILL_PER_LEVEL


def _handle_defeat(character: Character) -> None:
    bill = trauma_bill(character.level)
    character.credits -= bill
    character.hp = 1
    console.print(
        f"\n[bold red]You go down hard.[/bold red] Doc Wire's trauma team scrapes you "
        f"off the pavement and stabilizes you — {bill} credits, billed on the spot."
    )
    if character.credits < 0:
        console.print(f"[red]You're {-character.credits} in the hole now.[/red]")
