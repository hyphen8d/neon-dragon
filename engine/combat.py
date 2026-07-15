"""Turn-based combat resolution."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from engine.character import Character, hp_style
from engine.heat import record_kill
from engine.inventory import describe_effect, get_usable_item, use_item
from engine.leveling import check_level_up
from engine.quests import notify_step, print_quest_result
from engine.shop import get_item
from engine.status_effects import (
    DRUNK_STAT_PENALTY,
    EFFECT_ADJECTIVES,
    EFFECT_LABELS,
    apply_effect,
    has_effect,
    process_round_start,
)
from engine.theme import (
    ACCENT,
    ACCENT_SOFT,
    ALERT,
    BORDER,
    CREDITS,
    DANGER,
    ENEMY_ARROW,
    INFO,
    LABEL,
    NAME,
    PLAYER_ARROW,
    RARE,
    TELEMETRY_ENEMY,
    TELEMETRY_PLAYER,
    TEXT,
    TEXT_DIM,
    TEXT_PLAIN,
    WARNING,
)
from engine.ui import hotkey_prompt, make_hp_bar, press_any_key, read_choice

console = Console(width=120, highlight=False)


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
    is_droid: bool = False  # no blood to bleed — immune to the Bleed effect
    scan_desc: str = "No scan data available."  # flavor text shown in the enemy HUD panel
    status_effects: dict = field(default_factory=dict)

    @property
    def alive(self) -> bool:
        return self.hp > 0


@dataclass
class Move:
    """An extra combat action beyond the core Attack/Tech/Defend/Flee four —
    either a class's built-in special or a RoboDOJO-learned ability. Each
    gets its own hotkey, label, and independent per-fight cooldown; `effect`
    is called as effect(character, enemy, drunk_penalty, console) regardless
    of which fields it actually uses, so run_combat can dispatch to any of
    them the same way."""

    key: str
    label: str
    cooldown: int
    effect: Callable[[Character, "Enemy", int, Console], None]


COMBAT_LOG_MAXLEN = 10

# The last few rounds' narration lines for the current fight, in order --
# cleared at the start of every run_combat() call. _player_line/_enemy_line
# populate this as a side effect of formatting a line, so every existing
# console.print(_player_line(...)) / console.print(_enemy_line(...)) call
# site logs for free; nothing else needs to change to keep this in sync.
# Fights don't nest or overlap (one CLI, one fight at a time), so a single
# module-level deque is safe.
_combat_log: deque[str] = deque(maxlen=COMBAT_LOG_MAXLEN)


def _player_line(text: str) -> str:
    """Tag a player-turn resolution line (attacks, hacks, items, defend,
    flee) with a bright directional prefix, so it reads at a glance
    without parsing the sentence."""
    line = f"[{TELEMETRY_PLAYER}]{PLAYER_ARROW}[/{TELEMETRY_PLAYER}] {text}"
    _combat_log.append(line)
    return line


def _enemy_line(text: str) -> str:
    """Tag an enemy-turn attack or status-effect hit with an indented,
    darker directional prefix — the mirror of _player_line."""
    line = f"  [{TELEMETRY_ENEMY}]{ENEMY_ARROW}[/{TELEMETRY_ENEMY}] {text}"
    _combat_log.append(line)
    return line


def _show_combat_log(console: Console) -> None:
    """A pure peek -- shown mid-fight without spending a round, see the
    'V' handling in run_combat's action loop."""
    body = "\n".join(_combat_log)
    console.print(Panel(body, title=f"[{LABEL}]Action Log[/{LABEL}]", border_style=BORDER, padding=(1, 2)))
    press_any_key(console, "[SYS] COMBAT LINK PAUSED // PRESS ANY KEY_")


CRIT_CHANCE = 0.2
CRIT_MULTIPLIER = 1.5

# The Overclock Injector's temporary Attack boost (see engine/inventory.py's
# "attack_buff" effect) -- crashes into Bleed on expiry, handled centrally
# in engine/status_effects.py's process_round_start.
OVERCLOCK_ATTACK_BONUS = 12


def _effective_attack(character: Character, drunk_penalty: int) -> int:
    """Attack stat as it actually applies this round -- drunk knocks it
    down, an active Overclock Injector buff (see OVERCLOCK_ATTACK_BONUS)
    bumps it up. Shared by the plain Attack action, Samurai Slash, and
    Kill Switch so the buff can't be missed in one of them by accident."""
    bonus = OVERCLOCK_ATTACK_BONUS if has_effect(character, "overclock") else 0
    return max(0, character.attack - drunk_penalty + bonus)


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
    "{enemy} goes down in a shower of sparks and static.",
    "You put {enemy} down for good, {dmg} damage and done.",
]

# Randomized per-hit narration so no two rounds read identically. Each
# pool is picked from with random.choice() and formatted with whatever
# of {enemy}/{dmg} it uses — see _player_hit, _samurai_slash, and
# run_combat's enemy-turn section.

# Impact verbs, chosen by the magnitude of the damage roll rather than
# randomly — a graze reads as a graze regardless of what dealt it. Every
# flavor template below takes a {verb} slot filled by _impact_verb().
IMPACT_VERBS_LOW = ["grazes", "pings off", "scratches"]  # 1-3 damage
IMPACT_VERBS_STANDARD = ["strikes", "hits", "breaches"]  # 4-8 damage
IMPACT_VERBS_HIGH = ["shatters", "melts down", "ruptures", "eviscerates"]  # 9+ damage


def _impact_verb(dmg: int) -> str:
    if dmg <= 3:
        return random.choice(IMPACT_VERBS_LOW)
    if dmg <= 8:
        return random.choice(IMPACT_VERBS_STANDARD)
    return random.choice(IMPACT_VERBS_HIGH)


# Attack/Tech hit flavor is gear-aware: which cyberware (if any) sits in
# the relevant slot decides the flavor, not just the action type. Keyed
# by item id from content/items.json and content/black_market.json.
ARM_HIT_FLAVOR: dict[str, str] = {
    "chrome_arm_mk1": "Your servo-driven hydraulic Chrome Arm {verb} {enemy} for {dmg} damage.",
    "razor_claws": "Your monofilament Razor Claws {verb} {enemy} for {dmg} damage.",
    "singularity_fist": "Your Singularity Fist's graviton emitter {verb} {enemy} for {dmg} damage.",
}

EYES_HIT_FLAVOR: dict[str, str] = {
    "optic_scanner": "Your Optic Scanner calculates defensive trajectories — a buffer overflow "
    "{verb} {enemy} for {dmg} damage.",
    "target_lock_eyes": "Your military surplus Target-Lock arrays calibrate on vital circuits as "
    "a terminal exploit {verb} {enemy} for {dmg} damage.",
    "oracle_retinas": "Your Oracle Retinas read three seconds ahead — the routed exploit "
    "{verb} {enemy} for {dmg} damage.",
}

EMPTY_ARM_FLAVOR = [
    "Your desperate street-brawler punch {verb} {enemy} for {dmg} damage.",
]
EMPTY_TECH_FLAVOR = [
    "Your flood of basic ping spam {verb} {enemy}'s network ports for {dmg} damage.",
]

DODGE_FLAVOR = [
    "{enemy} slips the hit — you swing through empty air.",
    "{enemy} reads the attack and steps clear.",
    "Your strike goes wide as {enemy} ducks away.",
    "{enemy} weaves out of range just in time.",
]

ENEMY_ATTACK_FLAVOR = [
    "{enemy} {verb} you for {dmg} damage.",
    "{enemy} lands a solid hit and {verb} you for {dmg} damage.",
    "Pain flares as {enemy} {verb} you for {dmg} damage.",
    "{enemy} doesn't hold back — it {verb} you for {dmg} damage.",
    "A vicious strike from {enemy} {verb} you for {dmg} damage.",
    "{enemy} finds a gap in your guard and {verb} you for {dmg} damage.",
]

DEFEND_FLAVOR = [
    "You raise your guard, bracing for impact.",
    "You plant your feet and prepare to absorb the hit.",
    "You tighten your stance, ready to weather the blow.",
]

FLEE_SUCCESS_FLAVOR = [
    "You slip into the shadows and get away.",
    "You break line of sight and vanish into the crowd.",
    "A sharp turn down an alley loses your pursuer.",
]

FLEE_FAIL_FLAVOR = [
    "You can't shake them — they block your escape.",
    "No clean angle — you're boxed in.",
    "They anticipate the move and cut you off.",
]

# Class -> (hotkey, label) for each class's signature combat move.
# Classes with no entry here just don't get a fifth menu option.
CLASS_SPECIALS: dict[str, tuple[str, str]] = {
    "Street Samurai": ("S", "Samurai Slash"),
    "Netrunner": ("O", "Override System"),
}

SPECIAL_COOLDOWN = 3
SAMURAI_SLASH_MULTIPLIER = 1.5
SAMURAI_SLASH_BLEED_DURATION = 2
OVERRIDE_STUN_DURATION = 2


def _samurai_slash(character: Character, enemy: Enemy, drunk_penalty: int, console: Console) -> None:
    """Guaranteed 1.5x-damage strike that always leaves the enemy bleeding.
    A dodge still evades it entirely, same as a normal Attack."""
    if enemy.dodge_chance and random.random() < enemy.dodge_chance:
        miss = random.choice(DODGE_FLAVOR).format(enemy=enemy.name)
        console.print(_player_line(f"[{TEXT_DIM}]{miss}[/{TEXT_DIM}]"))
        return

    old_hp = enemy.hp
    stat_value = _effective_attack(character, drunk_penalty)
    dmg, crit = roll_damage(stat_value, enemy.defense)
    dmg = max(1, int(dmg * SAMURAI_SLASH_MULTIPLIER))
    enemy.hp -= dmg
    new_hp = max(0, enemy.hp)
    prefix = f"[{CREDITS}]CRITICAL![/{CREDITS}] " if crit else ""

    if not enemy.alive:
        line = random.choice(FINISHING_LINES).format(enemy=enemy.name, dmg=dmg)
        console.print(_player_line(f"{prefix}[{ACCENT}]{line}[/{ACCENT}] [{TEXT_DIM}]({enemy.name} HP: {old_hp} -> 0)[/{TEXT_DIM}]"))
        return

    console.print(_player_line(
        f"{prefix}[{RARE}]Samurai Slash![/{RARE}] You carve {enemy.name} for {dmg} damage. "
        f"[{TEXT_DIM}]({enemy.name} HP: {old_hp} -> {new_hp})[/{TEXT_DIM}]"
    ))
    if apply_effect(enemy, "bleed", SAMURAI_SLASH_BLEED_DURATION):
        console.print(_player_line(f"[{WARNING}]{enemy.name} is left bleeding.[/{WARNING}]"))
    else:
        console.print(_player_line(f"[{TEXT_DIM}]No blood to spill — {enemy.name}'s chassis shrugs it off.[/{TEXT_DIM}]"))


def _override_system(character: Character, enemy: Enemy, drunk_penalty: int, console: Console) -> None:
    """Deals no damage but forces a guaranteed multi-round stun — a hack,
    not a physical hit, so it isn't subject to dodge_chance. Ignores
    character/drunk_penalty; kept in the signature so every Move's effect
    can be called the same way (see run_combat)."""
    apply_effect(enemy, "stunned", OVERRIDE_STUN_DURATION)
    console.print(_player_line(
        f"[{INFO}]Override System![/{INFO}] You lock {enemy.name}'s systems — "
        f"stunned for {OVERRIDE_STUN_DURATION} rounds."
    ))


ADRENAL_SURGE_HEAL = 15
KILL_SWITCH_BONUS = 3


def _adrenal_surge(character: Character, enemy: Enemy, drunk_penalty: int, console: Console) -> None:
    """Combat stims — heals a flat amount on the spot. Class-independent
    (RoboDOJO ability); ignores the enemy entirely."""
    missing = character.max_hp - character.hp
    healed = min(missing, ADRENAL_SURGE_HEAL)
    old_hp = character.hp
    character.hp += healed
    if healed > 0:
        console.print(_player_line(
            f"[{ACCENT}]Adrenal Surge![/{ACCENT}] Combat stims flood your system. +{healed} HP. "
            f"[{TEXT_DIM}](Your HP: {old_hp} -> {character.hp})[/{TEXT_DIM}]"
        ))
    else:
        console.print(_player_line(f"[{TEXT_DIM}]Adrenal Surge fires, but you're already at full health.[/{TEXT_DIM}]"))


def _kill_switch(character: Character, enemy: Enemy, drunk_penalty: int, console: Console) -> None:
    """A guaranteed opening — ignores enemy dodge_chance entirely, unlike a
    normal Attack. Class-independent (RoboDOJO ability)."""
    stat_value = _effective_attack(character, drunk_penalty) + KILL_SWITCH_BONUS
    old_hp = enemy.hp
    dmg, crit = roll_damage(stat_value, enemy.defense)
    enemy.hp -= dmg
    new_hp = max(0, enemy.hp)
    prefix = f"[{CREDITS}]CRITICAL![/{CREDITS}] " if crit else ""

    if not enemy.alive:
        line = random.choice(FINISHING_LINES).format(enemy=enemy.name, dmg=dmg)
        console.print(_player_line(f"{prefix}[{ACCENT}]{line}[/{ACCENT}] [{TEXT_DIM}]({enemy.name} HP: {old_hp} -> 0)[/{TEXT_DIM}]"))
        return

    console.print(_player_line(
        f"{prefix}[{RARE}]Kill Switch![/{RARE}] No dodge, no mercy — your opening strike {_impact_verb(dmg)} "
        f"{enemy.name} for {dmg} damage. [{TEXT_DIM}]({enemy.name} HP: {old_hp} -> {new_hp})[/{TEXT_DIM}]"
    ))


# Purchasable at RoboDOJO, independent of class — see engine/hub.py's
# _learn_ability. Once learned, an ability is permanent on the Character
# (learned_abilities) and shows up as an extra Move in every future fight,
# alongside any class special.
ABILITY_COOLDOWN = 4

ABILITIES: dict[str, dict] = {
    "adrenal_surge": {
        "name": "Adrenal Surge",
        "hotkey": "H",
        "cost": 120,
        "cooldown": ABILITY_COOLDOWN,
        "flavor": f"Combat stims — heal {ADRENAL_SURGE_HEAL} HP mid-fight.",
        "effect": _adrenal_surge,
    },
    "kill_switch": {
        "name": "Kill Switch",
        "hotkey": "K",
        "cost": 180,
        "cooldown": ABILITY_COOLDOWN,
        "flavor": "A guaranteed opening strike — always connects, dodge or no dodge.",
        "effect": _kill_switch,
    },
}


def _character_moves(character: Character) -> list[Move]:
    """Every extra combat action available this fight beyond the core
    Attack/Tech/Defend/Flee four: the class's built-in special (if any),
    plus any abilities learned at RoboDOJO, each as its own Move with an
    independent cooldown. Order is class special first, then abilities in
    the order they were learned."""
    moves: list[Move] = []
    special = CLASS_SPECIALS.get(character.char_class)
    if special:
        key, label = special
        effect = _samurai_slash if key == "S" else _override_system
        moves.append(Move(key=key, label=label, cooldown=SPECIAL_COOLDOWN, effect=effect))
    for ability_id in character.learned_abilities:
        ability = ABILITIES[ability_id]
        moves.append(Move(key=ability["hotkey"], label=ability["name"], cooldown=ability["cooldown"], effect=ability["effect"]))
    return moves


def _choose_inventory_item(character: Character, console: Console) -> str | None:
    """Show the player's carried items and return the chosen item_id, or
    None if they cancel. Doesn't consume anything itself."""
    counts: dict[str, int] = {}
    order: list[str] = []
    for item_id in character.inventory:
        if item_id not in counts:
            order.append(item_id)
        counts[item_id] = counts.get(item_id, 0) + 1

    table = Table(border_style=BORDER, show_header=False)
    table.add_column("#", justify="right", style=LABEL)
    table.add_column("Item", style=TEXT)
    table.add_column("Qty", justify="right")
    table.add_column("Effect", style=TEXT_DIM)
    for i, item_id in enumerate(order, start=1):
        item = get_usable_item(item_id)
        table.add_row(str(i), item["name"], f"x{counts[item_id]}", describe_effect(item))
    console.print(table)

    choice = read_choice(
        console,
        [str(i) for i in range(len(order) + 1)],
        prompt="Use which item? (0 to cancel)",
    )
    if choice == "0":
        return None
    return order[int(choice) - 1]


def _effects_text(combatant) -> str:
    if not combatant.status_effects:
        return f"[{TEXT_DIM}]None[/{TEXT_DIM}]"
    parts = [f"{EFFECT_LABELS.get(e, e)} ({r})" for e, r in combatant.status_effects.items()]
    return ", ".join(parts)


def _scan_readout(hp: int, max_hp: int) -> str:
    """A live behavioral readout that shifts with the enemy's HP, so the
    scan panel reads as an active sensor feed rather than static flavor."""
    ratio = 0.0 if max_hp <= 0 else max(hp, 0) / max_hp
    if ratio > 0.75:
        return f"[{ACCENT_SOFT}]Scan: Systems Nominal[/{ACCENT_SOFT}]"
    if ratio >= 0.30:
        return f"[{WARNING}]Scan: Structural Degradation Detected[/{WARNING}]"
    return f"[{ALERT}]Scan: Catastrophic Hardware Failure Imminent[/{ALERT}]"


def _combatant_panel(
    name: str,
    hp: int,
    max_hp: int,
    rows: list[tuple[str, str]],
    border_style: str,
    title_style: str,
) -> Panel:
    hp_color = hp_style(hp, max_hp)
    body = Table.grid(padding=(0, 1))
    body.add_column(style=TEXT_DIM, justify="right")
    body.add_column(style=TEXT)
    body.add_row("HP", f"[{hp_color}]{max(hp, 0)}/{max_hp}[/{hp_color}] {make_hp_bar(hp, max_hp)}")
    for label, value in rows:
        body.add_row(label, value)
    return Panel(body, title=f"[{title_style}]{name}[/{title_style}]", border_style=border_style, padding=(0, 1))


def _print_combat_hud(
    character: Character,
    enemy: Enemy,
    enemy_max_hp: int,
    moves: list[Move],
    cooldowns: dict[str, int],
) -> None:
    """The persistent combat dashboard — player status on the left, enemy
    vitals on the right — redrawn fresh at the top of every round."""
    player_rows = [
        ("Class", character.char_class),
        ("Attack", str(character.attack)),
        ("Defense", str(character.defense)),
        ("Tech", str(character.tech)),
        ("Status", _effects_text(character)),
    ]
    for move in moves:
        cd = cooldowns[move.key]
        cd_text = f"[{ACCENT}]Ready[/{ACCENT}]" if cd <= 0 else f"[{TEXT_DIM}]{cd} round(s)[/{TEXT_DIM}]"
        player_rows.append((move.label, cd_text))
    player_panel = _combatant_panel(character.name, character.hp, character.max_hp, player_rows, BORDER, NAME)

    enemy_rows = [
        ("Faction", enemy.faction),
        ("Status", _effects_text(enemy)),
        ("Scan", f"[{TEXT_DIM}]{enemy.scan_desc}[/{TEXT_DIM}]"),
        ("Readout", _scan_readout(enemy.hp, enemy_max_hp)),
    ]
    enemy_panel = _combatant_panel(enemy.name, enemy.hp, enemy_max_hp, enemy_rows, ALERT, ALERT)

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_row(player_panel, enemy_panel)
    console.print(grid)
    console.rule(style=BORDER)


def _gear_inflict(character: Character, enemy: Enemy, slot: str, console: Console) -> None:
    """Higher-tier arm/eyes cyberware can inflict a status effect on the enemy."""
    item_id = character.cyberware.get(slot)
    if not item_id:
        return
    item = get_item(item_id)
    effect = item.get("inflict_effect")
    if not effect or random.random() >= item.get("inflict_chance", 0):
        return
    if not apply_effect(enemy, effect, item.get("inflict_duration", 1)):
        return
    adjective = EFFECT_ADJECTIVES.get(effect, effect)
    console.print(_player_line(f"[{WARNING}]{item['name']} leaves {enemy.name} {adjective}![/{WARNING}]"))


def _hit_flavor(character: Character, action_type: str, enemy_name: str, dmg: int) -> str:
    """Pick a hit description tailored to whatever's (or isn't) equipped in
    the slot this action uses — a Chrome Arm punch reads nothing like a
    bare-knuckle brawl."""
    if action_type == "attack":
        slot, gear_flavor, empty_flavor = "arm", ARM_HIT_FLAVOR, EMPTY_ARM_FLAVOR
    else:
        slot, gear_flavor, empty_flavor = "eyes", EYES_HIT_FLAVOR, EMPTY_TECH_FLAVOR

    item_id = character.cyberware.get(slot)
    if item_id and item_id in gear_flavor:
        template = gear_flavor[item_id]
    elif item_id:
        # Unlisted gear in this slot (future content) — still gear-aware,
        # just without hand-written flavor for it yet.
        template = f"Your {get_item(item_id)['name']} {{verb}} {{enemy}} for {{dmg}} damage."
    else:
        template = random.choice(empty_flavor)

    return template.format(enemy=enemy_name, dmg=dmg, verb=_impact_verb(dmg))


def _player_hit(character: Character, enemy: Enemy, stat_value: int, action_type: str, console: Console) -> bool:
    """Resolve one player attack against the enemy. Returns True if it connected
    (missed dodges don't trigger gear on-hit effects)."""
    if enemy.dodge_chance and random.random() < enemy.dodge_chance:
        miss = random.choice(DODGE_FLAVOR).format(enemy=enemy.name)
        console.print(_player_line(f"[{TEXT_DIM}]{miss}[/{TEXT_DIM}]"))
        return False

    old_hp = enemy.hp
    dmg, crit = roll_damage(stat_value, enemy.defense)
    enemy.hp -= dmg
    new_hp = max(0, enemy.hp)
    prefix = f"[{CREDITS}]CRITICAL![/{CREDITS}] " if crit else ""

    if not enemy.alive:
        line = random.choice(FINISHING_LINES).format(enemy=enemy.name, dmg=dmg)
        console.print(_player_line(f"{prefix}[{ACCENT}]{line}[/{ACCENT}] [{TEXT_DIM}]({enemy.name} HP: {old_hp} -> 0)[/{TEXT_DIM}]"))
    else:
        line = _hit_flavor(character, action_type, enemy.name, dmg)
        console.print(_player_line(
            f"{prefix}[{TEXT_PLAIN}]{line}[/{TEXT_PLAIN}] "
            f"[{TEXT_DIM}]({enemy.name} HP: {old_hp} -> {new_hp})[/{TEXT_DIM}]"
        ))
    return True


def run_combat(character: Character, enemy_data: dict) -> bool:
    """Resolve a fight round by round. Mutates character HP/credits/XP in
    place. Returns True on a win, False on a loss or a successful flee."""
    enemy = Enemy(**enemy_data)
    enemy_max_hp = enemy.hp
    _combat_log.clear()

    moves = _character_moves(character)
    moves_by_key = {move.key: move for move in moves}
    cooldowns: dict[str, int] = {move.key: 0 for move in moves}

    while character.hp > 0 and enemy.alive:
        console.clear()
        # Decrement before drawing anything this round, so the HUD panel
        # and the action menu's cooldown label always agree — previously
        # the HUD showed the pre-decrement value and the menu showed the
        # post-decrement one, disagreeing by one round every fight.
        for key in cooldowns:
            if cooldowns[key] > 0:
                cooldowns[key] -= 1
        _print_combat_hud(character, enemy, enemy_max_hp, moves, cooldowns)
        console.print()

        stunned = process_round_start(character, console, is_player=True)
        if character.hp <= 0:
            break

        defending = False
        if stunned:
            console.print(_player_line(f"[{WARNING}]You're stunned — you can't act this round![/{WARNING}]"))
        else:
            options = [("A", "Attack"), ("T", "Tech/Hack"), ("D", "Defend"), ("F", "Flee")]
            for move in moves:
                cd = cooldowns[move.key]
                label = move.label if cd <= 0 else f"{move.label} ({cd})"
                options.append((move.key, label))
            if character.inventory:
                options.append(("I", "Items"))
            if _combat_log:
                options.append(("V", "View Log"))

            while True:
                action = hotkey_prompt(console, options)
                if action in moves_by_key and cooldowns[action] > 0:
                    move = moves_by_key[action]
                    console.print(f"[{TEXT_DIM}]{move.label} is still recharging ({cooldowns[action]} more round(s)).[/{TEXT_DIM}]")
                    continue
                if action == "V":
                    # A pure peek — doesn't spend the round, so redraw the
                    # HUD (press_any_key already cleared the screen) and
                    # loop back to the same action prompt.
                    _show_combat_log(console)
                    _print_combat_hud(character, enemy, enemy_max_hp, moves, cooldowns)
                    console.print()
                    continue
                if action == "I":
                    item_id = _choose_inventory_item(character, console)
                    if item_id is None:
                        continue
                    if use_item(character, item_id, console, enemy=enemy):
                        # A guaranteed-flee item (Scrambler Flare) ends the
                        # fight on the spot -- same as a successful Flee,
                        # no enemy turn.
                        return False
                break

            drunk_penalty = DRUNK_STAT_PENALTY if has_effect(character, "drunk") else 0

            if action == "A":
                stat_value = _effective_attack(character, drunk_penalty)
                if _player_hit(character, enemy, stat_value, "attack", console) and enemy.alive:
                    _gear_inflict(character, enemy, "arm", console)
            elif action == "T":
                stat_value = max(0, character.tech - drunk_penalty)
                if _player_hit(character, enemy, stat_value, "tech", console) and enemy.alive:
                    _gear_inflict(character, enemy, "eyes", console)
            elif action == "D":
                defending = True
                brace = random.choice(DEFEND_FLAVOR)
                console.print(_player_line(f"[{TEXT_DIM}]{brace}[/{TEXT_DIM}]"))
            elif action in moves_by_key:
                move = moves_by_key[action]
                move.effect(character, enemy, drunk_penalty, console)
                cooldowns[action] = move.cooldown
            elif action == "I":
                pass  # item effect already resolved in the selection loop above
            else:
                if random.random() < 0.5:
                    line = random.choice(FLEE_SUCCESS_FLAVOR)
                    console.print(_player_line(f"[{TEXT_DIM}]{line}[/{TEXT_DIM}]"))
                    return False
                line = random.choice(FLEE_FAIL_FLAVOR)
                console.print(_player_line(f"[{TEXT_DIM}]{line}[/{TEXT_DIM}]"))

        if not enemy.alive:
            break

        enemy_stunned = process_round_start(enemy, console)
        if not enemy.alive:
            break

        if enemy_stunned:
            console.print(_enemy_line(f"[{WARNING}]{enemy.name} is stunned and can't act![/{WARNING}]"))
        else:
            old_hp = character.hp
            dmg, crit = roll_damage(enemy.attack, character.defense)
            bypassed = defending and enemy.ignores_defend
            if defending and not enemy.ignores_defend:
                dmg = max(0, dmg // 2)
            character.hp = max(0, character.hp - dmg)
            new_hp = character.hp
            prefix = f"[{CREDITS}]CRITICAL![/{CREDITS}] " if crit else ""
            suffix = " Your guard didn't matter." if bypassed else ""
            line = random.choice(ENEMY_ATTACK_FLAVOR).format(enemy=enemy.name, dmg=dmg, verb=_impact_verb(dmg))
            console.print(_enemy_line(
                f"{prefix}[{DANGER}]{line}{suffix}[/{DANGER}] "
                f"[{TEXT_DIM}](Your HP: {old_hp} -> {new_hp})[/{TEXT_DIM}]"
            ))

            if enemy.inflict_effect and random.random() < enemy.inflict_chance:
                apply_effect(character, enemy.inflict_effect, enemy.inflict_duration)
                adjective = EFFECT_ADJECTIVES.get(enemy.inflict_effect, enemy.inflict_effect)
                console.print(_enemy_line(f"[{WARNING}]The hit leaves you {adjective}![/{WARNING}]"))

        # The round's over but the fight isn't — pause here so the player
        # actually gets to read what just happened before the next round's
        # clear() wipes it. Without this, narration flashes and vanishes.
        if character.hp > 0 and enemy.alive:
            press_any_key(console, "[SYS] NEXT ROUND QUEUED // PRESS ANY KEY_")

    if character.hp <= 0:
        _handle_defeat(character)
        return False
    _handle_victory(character, enemy)
    return True


BONUS_LOOT_CHANCE = 0.25


def _handle_victory(character: Character, enemy: Enemy) -> None:
    character.credits += enemy.credits_reward
    character.xp += enemy.xp_reward
    character.reputation += enemy.reputation_reward
    character.kills[enemy.name] = character.kills.get(enemy.name, 0) + 1
    character.total_fights_won += 1
    character.total_credits_earned += enemy.credits_reward
    record_kill(character, enemy.faction)
    reward_text = f"+{enemy.credits_reward} credits, +{enemy.xp_reward} XP"
    if enemy.reputation_reward:
        reward_text += f", +{enemy.reputation_reward} reputation"
    console.print(f"\n[{ACCENT}]{enemy.name} goes down.[/{ACCENT}] {reward_text}.")

    if random.random() < BONUS_LOOT_CHANCE:
        bonus = max(1, int(enemy.credits_reward * random.uniform(0.2, 0.5)))
        character.credits += bonus
        character.total_credits_earned += bonus
        console.print(f"[{CREDITS}]Bonus salvage![/{CREDITS}] +{bonus} credits.")

    check_level_up(character, console)
    for result in notify_step(character, "kill", enemy.name):
        print_quest_result(console, character, result)


TRAUMA_BILL_BASE = 40
TRAUMA_BILL_PER_LEVEL = 15

# Every point of Charisma talks the trauma team down 3%, capped at 45% —
# a high-Charisma build can smooth-talk their way out of most of the bill.
CHARISMA_BILL_DISCOUNT_PER_POINT = 0.03
CHARISMA_BILL_DISCOUNT_CAP = 0.45


def trauma_bill(level: int) -> int:
    """Doc Wire's rate rises with level, so a bad fight stays costly instead
    of becoming trivial once credit income outgrows a flat fee."""
    return TRAUMA_BILL_BASE + (level - 1) * TRAUMA_BILL_PER_LEVEL


def _handle_defeat(character: Character) -> None:
    bill = trauma_bill(character.level)
    discount = min(CHARISMA_BILL_DISCOUNT_CAP, character.charisma * CHARISMA_BILL_DISCOUNT_PER_POINT)
    bill = int(bill * (1 - discount))
    character.credits -= bill
    character.hp = 1
    console.print(
        f"\n[{ALERT}]You go down hard.[/{ALERT}] Doc Wire's trauma team scrapes you "
        f"off the pavement and stabilizes you — {bill} credits, billed on the spot."
    )
    if character.credits < 0:
        console.print(f"[{DANGER}]You're {-character.credits} in the hole now.[/{DANGER}]")
