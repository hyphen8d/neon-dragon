"""Hub menu / navigation between Neo Meridian locations."""

from __future__ import annotations

import random

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.rule import Rule
from rich.table import Table

from engine.bestiary import TRAINING_DRONES, enemy_faction
from engine.character import CYBERWARE_SLOTS, Character, hp_style
from engine.combat import ABILITIES, run_combat
from engine.encounters import roll_combat_encounter, roll_scavenge_encounter
from engine.heat import AMBUSH_CHANCE, hot_factions, reset_daily_kills
from engine.help import show_help
from engine.inventory import buy_item, describe_effect, get_usable_item, load_usable_items
from engine.leveling import xp_for_next_level
from engine.npcs import get_npc, npc_at, random_line
from engine.pit import load_gladiators
from engine.quests import (
    accept_quest,
    available_quests,
    current_step,
    get_quest,
    locked_quests,
    notify_step,
    print_quest_result,
)
from engine.shop import (
    buy_and_equip,
    buy_black_market_item,
    currency_of,
    describe_market_modifier,
    discounted_cost,
    format_price,
    get_daily_catalog,
    get_item,
    load_black_market,
    roll_daily_market,
    sell_back_value,
    unequip,
)
from engine.status_effects import EFFECT_LABELS, apply_effect, cure_all
from engine.theme import (
    ACCENT,
    ACCENT_SOFT,
    ALERT,
    BORDER,
    BORDER_ACCENT,
    BORDER_RARE,
    CREDITS,
    DANGER,
    INFO,
    LABEL,
    NAME_BOLD,
    NOTE,
    RARE,
    TEXT,
    TEXT_DIM,
    TEXT_PLAIN,
    WARNING,
)
from engine.ui import OPTION_SEPARATOR, hotkey_bracket, hotkey_prompt, make_hp_bar, press_any_key, read_choice

console = Console(width=120, highlight=False)

# Rare secondary currency drop — Jack In runs and top-tier Pit wins only
# (whichever tier is highest in content/pit.json; see visit_the_pit).
QUANTUM_CORE_DROP_CHANCE = 0.04

# Location -> hub hotkey letter. Kept as an explicit dict (rather than
# deriving from LOCATIONS' first letters) so the mapping is easy to scan
# and guaranteed collision-free with the Actions row below.
LOCATION_HOTKEYS: dict[str, str] = {
    "C": "Chrome Noodle Bar",
    "U": "Undercity",
    "N": "NetVault",
    "H": "Hyphen8d's Hut",
    "D": "Doc Wire's Clinic",
    "R": "RoboDOJO",
    "P": "The Pit",
    "F": "Fixer Board",
}

# Location -> one-line flavor for the hub menu table. Real content (rest,
# shop, combat, etc.) is wired up location by location in later phases.
LOCATIONS: dict[str, str] = {
    "Chrome Noodle Bar": "Rest, heal, and hear rumors over synth-noodles and static pop.",
    "Undercity": "Jack in, pick a fight, or scavenge — your call.",
    "NetVault": "Deposit and withdraw credits, safe from death-loss.",
    "Hyphen8d's Hut": "Buy and sell gear and cyberware.",
    "Doc Wire's Clinic": "Heal HP for credits, cure status effects.",
    "RoboDOJO": "Spar with training drones to sharpen your stats.",
    "The Pit": "PvE gladiator fights for reputation and credits.",
    "Fixer Board": "Leaderboard and posted contracts.",
}

# Location -> longer arrival description, shown when you actually step
# into the place (as opposed to the short blurb in the hub menu table).
LOCATION_DESCRIPTIONS: dict[str, str] = {
    "Chrome Noodle Bar": (
        "Steam curls off the noodle vats under a buzzing pink sign, "
        "condensation beading on cracked plastic booths. Synth pop bleeds "
        "from a speaker with one blown tweeter, looping the same three songs "
        "for years. Every stool's got a story nobody's telling straight. The "
        "noodles are cheap, the gossip is cheaper, and Static Rin keeps a "
        "mental ledger of every favor owed in three districts."
    ),
    "Undercity": (
        "Sublevel streets, sodium light dying orange through a smog that "
        "never quite clears. Water drips from a hundred unseen pipes, "
        "pooling in cracks where the pavement gave up years ago. Something "
        "always seems to be watching from the dark — a drone, a ganger, a "
        "rat the size of a housecat, hard to say which."
        "\n\n[bright_magenta]LOCAL AREA NETSCAN:[/bright_magenta]\n"
        "  » Slice Drop Box      — High-yield corporate node hack. Scaled by Tech. High risk of Trace & Corp Ambush.\n"
        "  » Find a Fight       — Guaranteed localized enemy intercept. Optimal for raw XP grinding.\n"
        "  » Hunt Cache         — Passive scanner sweep for forgotten underworld drops. Low risk, unless Heat is high."
    ),
    "NetVault": (
        "Chrome and glass, cold as a server room because it technically is "
        "one. Biometric scanners hum behind a counter that's processed a "
        "thousand transactions today and trusts none of them. Armed drones "
        "drift near the ceiling on quiet rotors, watching everyone equally. "
        "The vault door behind reception hasn't opened for a customer in "
        "years."
    ),
    "Hyphen8d's Hut": (
        "Wires hang from the ceiling like vines, tangled around fluorescent "
        "tubes that flicker on a schedule only Hyphen8d understands. "
        "Half-built limbs sit in bins marked in a shorthand only the shop "
        "understands, chrome fingers twitching when a stray current finds "
        "them. Smells like solder and ozone. Hyphen8d insists everything's "
        "legitimate. Hyphen8d is lying."
    ),
    "Doc Wire's Clinic": (
        "A converted shipping container wired for surgery, welded shut on "
        "three sides and propped open with a car battery nobody's bothered "
        "to remove. Trauma gurneys line one wall, a fridge in the corner "
        "that's definitely not for food. The smell of antiseptic fights "
        "synth-tobacco smoke. Doc Wire's hands shake until they pick up a "
        "scalpel."
    ),
    "RoboDOJO": (
        "Servo-limbed training drones circle a scorched practice ring, "
        "sparks catching the overhead floods every time a hit lands clean. A "
        "rack of practice blades sits worn smooth from years of grips, mats "
        "patched more than original. This is where you get better, one "
        "bruise at a time. The drones don't hold back, or get tired, or care "
        "what it costs."
    ),
    "The Pit": (
        "A sunken arena ringed by chain-link and floodlights, a chanting "
        "crowd lost in the dark beyond the light's reach. The sand's "
        "stained in ways bleach won't fix, and the house doesn't pretend "
        "otherwise. Betting runs the aisles in a currency that isn't quite "
        "credits and isn't quite favors. A scoreboard flickers names of "
        "gladiators who didn't walk out."
    ),
    "Fixer Board": (
        "A cracked terminal bolted to a brick wall, scrolling contracts in "
        "glitchy green text that occasionally drops a line and never "
        "notices. Torn paper flyers underneath are decades out of date, "
        "advertising jobs that paid out or got someone killed long ago. The "
        "terminal takes a cut before you even see the payout, quietly, "
        "automatically."
    ),
}

# Location -> Rich box style for the arrival Panel, so the frame itself
# reflects the setting: sterile corp square edges, brutal heavy-line dives,
# ornate double-line storefronts. Anywhere not listed gets the default
# soft ROUNDED look.
LOCATION_BOX_STYLES: dict[str, box.Box] = {
    "NetVault": box.SQUARE,
    "Undercity": box.HEAVY,
    "The Pit": box.HEAVY,
    "Hyphen8d's Hut": box.DOUBLE,
}


def print_status(character: Character) -> Table:
    """The persistent HUD — merc identity, level, core combat stats, and
    credits, as a single-row color-coded bar. Printed at the top of every
    hub location view (via print_arrival) and the hub menu itself, so it
    reads the same everywhere: a fixed instrument panel, not scrolling text."""
    hp_color = hp_style(character.hp, character.max_hp)

    hud = Table(border_style=BORDER_ACCENT, header_style=ACCENT, expand=True)
    hud.add_column("Merc", style=NAME_BOLD)
    hud.add_column("Class", style=TEXT_PLAIN)
    hud.add_column("Lvl", justify="center", style=TEXT)
    hud.add_column("Day", justify="center", style=TEXT_DIM)
    hud.add_column("HP", justify="center")
    hud.add_column("ATK", justify="center", style=INFO)
    hud.add_column("DEF", justify="center", style=INFO)
    hud.add_column("TECH", justify="center", style=INFO)
    hud.add_column("CHA", justify="center", style=RARE)
    hud.add_column("Credits", justify="right", style=CREDITS)
    hud.add_column("Banked", justify="right", style=CREDITS)

    hud.add_row(
        character.name,
        character.char_class,
        str(character.level),
        str(character.day),
        f"[{hp_color}]{character.hp}/{character.max_hp}[/{hp_color}] {make_hp_bar(character.hp, character.max_hp)}",
        str(character.attack),
        str(character.defense),
        str(character.tech),
        str(character.charisma),
        str(character.credits),
        str(character.banked_credits),
    )

    console.print(hud)
    return hud


def print_hub_menu(character: Character) -> None:
    console.rule(f"[{LABEL}]Neo Meridian[/{LABEL}]")
    print_status(character)
    console.print()

    locations = Table(
        title=f"[{ACCENT}]Locations[/{ACCENT}]",
        border_style=BORDER,
        show_header=False,
    )
    locations.add_column("Location", style=TEXT)
    locations.add_column("Description", style=TEXT_DIM)
    for key, name in LOCATION_HOTKEYS.items():
        locations.add_row(hotkey_bracket(key, name), LOCATIONS[name])
    console.print(locations)

    actions = Table(
        title=f"[{ACCENT}]Actions[/{ACCENT}]",
        border_style=BORDER,
        show_header=False,
    )
    actions.add_column("Action", style=TEXT)
    actions.add_column("Description", style=TEXT_DIM)
    contracts_note = f"{len(character.active_quests)} active" if character.active_quests else "none active"
    actions.add_row(
        hotkey_bracket("I", "Character Info"),
        f"View your full stats, gear, contracts ({contracts_note}), and kills.",
    )
    actions.add_row(f"[{ACCENT}][?][/{ACCENT}] Help", "Open the player guide.")
    actions.add_row(hotkey_bracket("L", "Leave"), "Head to the safehouse to sleep — advances the day, full heal.")
    console.print(actions)


def print_arrival(character: Character, location: str) -> None:
    console.clear()
    print_status(character)
    console.print()
    console.print(
        Panel(
            LOCATION_DESCRIPTIONS[location],
            title=f"[{ACCENT}]{location}[/{ACCENT}]",
            border_style=BORDER,
            padding=(0, 2),
            box=LOCATION_BOX_STYLES.get(location, box.ROUNDED),
        )
    )


def print_menu_divider(label: str) -> None:
    """Visually separate in-character scene/dialogue above from the
    out-of-character menu/mechanics below."""
    console.print()
    console.rule(f"[{TEXT_DIM}]{label}[/{TEXT_DIM}]", style=TEXT_DIM)


def _npc_panel(npc: dict, character: Character) -> Panel:
    """Left half of a location's Interaction Deck — an NPC's bio, a rule,
    and one line of dialogue, framed in its own bordered box. The line is
    character-aware — see random_line's conditional_lines handling — so
    an NPC can react to what this merc has actually done."""
    body = Table.grid(padding=(0, 0))
    body.add_column()
    body.add_row(f"[{TEXT_DIM} italic]{npc['bio']}[/{TEXT_DIM} italic]")
    body.add_row(Rule(style=TEXT_DIM))
    body.add_row(f"[italic]“{random_line(npc, character)}”[/italic]")
    return Panel(body, title=f"[{INFO}]{npc['name']}[/{INFO}]", border_style=BORDER, padding=(1, 2))


def _station_data_panel(title: str, rows: list[tuple[str, str]], extra: Table | None = None) -> Panel:
    """Right half of a location's Interaction Deck — borderless key/value
    rows of the room's operational rates, optionally followed by a
    fuller table (RoboDOJO's training costs, for instance)."""
    body = Table.grid(padding=(0, 2))
    body.add_column(style=TEXT_DIM, justify="right")
    body.add_column(style=TEXT)
    for label, value in rows:
        body.add_row(label, value)

    content = body
    if extra is not None:
        content = Table.grid()
        content.add_column()
        content.add_row(body)
        content.add_row(extra)

    return Panel(content, title=f"[{ACCENT}]{title}[/{ACCENT}]", border_style=BORDER_ACCENT, padding=(1, 2))


def _interaction_deck(npc: dict, right_panel: Panel, character: Character) -> None:
    """Print the location's dual-panel dashboard: NPC dialogue on the
    left, room diagnostics/operational rates on the right, side by side
    across the full 120-column layout."""
    grid = Table.grid(padding=(0, 4), expand=True)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_row(_npc_panel(npc, character), right_panel)
    console.print(grid)


JACK_IN_BASE_CHANCE = 0.30
JACK_IN_TECH_SCALING = 0.04
JACK_IN_MAX_CHANCE = 0.85
JACK_IN_CREDIT_RANGE = (15, 35)


def _jack_in(character: Character) -> None:
    console.print(
        f"[{TEXT_DIM}]You locate a matte-black corporate drop box bolted to a wet brick wall, its "
        f"security modules pulsing a cold amber. You slap your deck onto the link interface and "
        f"begin fracturing the cryptographic seals...[/{TEXT_DIM}]"
    )
    chance = min(JACK_IN_MAX_CHANCE, JACK_IN_BASE_CHANCE + character.tech * JACK_IN_TECH_SCALING)
    if random.random() < chance:
        low, high = JACK_IN_CREDIT_RANGE
        amount = random.randint(low, high) + character.tech // 2
        character.credits += amount
        console.print(
            f"[{LABEL}]Click. The internal magnetic latch fires and the reinforced hopper drops "
            f"open.[/{LABEL}] You skim a hot corporate credit-chip off the tray! +{amount} credits."
        )
        if random.random() < QUANTUM_CORE_DROP_CHANCE:
            character.quantum_cores += 1
            console.print(
                f"[{INFO}]The sub-grid crypto-seal completely ruptures, exposing the vault's "
                f"high-tier logic core.[/{INFO}] Tucked deep behind the primary cooling rails, a "
                "glowing Quantum Core clicks free. +1 Quantum Core."
            )
        return

    console.print(
        f"[{ALERT}]FEEDBACK ALERT: A heavy Black-ICE counter-intrusion sub-routine snaps back "
        f"through your deck, pinning your physical coordinates.[/{ALERT}] Overhead, an automated "
        "corporate containment team deploys to neutralize the breach!"
    )
    encounter = roll_combat_encounter(character.level, faction="Corp")
    console.print(f"[{TEXT_DIM}]{encounter['intro']}[/{TEXT_DIM}]")
    run_combat(character, encounter["enemy"])


def _find_a_fight(character: Character) -> None:
    encounter = roll_combat_encounter(character.level)
    console.print(f"[{TEXT_DIM}]{encounter['intro']}[/{TEXT_DIM}]")
    run_combat(character, encounter["enemy"])


CACHE_BASE_RISK_CHANCE = 0.10  # flat per-attempt risk, independent of Faction Heat


def _scavenge(character: Character) -> None:
    hot = hot_factions(character)
    if hot and random.random() < AMBUSH_CHANCE:
        faction = random.choice(hot)
        console.print(
            f"[{DANGER}]{faction} muscle jumps you while you're focused on sweeping the sector "
            f"for low-frequency cache signals, looking for payback.[/{DANGER}]"
        )
        encounter = roll_combat_encounter(character.level, faction=faction)
        console.print(f"[{TEXT_DIM}]{encounter['intro']}[/{TEXT_DIM}]")
        run_combat(character, encounter["enemy"])
        return

    # Even at zero Heat, sweeping for caches isn't risk-free — otherwise
    # it's an infinite farm loop. A flat baseline chance of getting caught
    # applies to every attempt, on top of the Heat-triggered ambush above.
    if random.random() < CACHE_BASE_RISK_CHANCE:
        console.print(
            f"[{DANGER}]Bad luck — you're not the only one sweeping this frequency tonight.[/{DANGER}]"
        )
        encounter = roll_combat_encounter(character.level)
        console.print(f"[{TEXT_DIM}]{encounter['intro']}[/{TEXT_DIM}]")
        run_combat(character, encounter["enemy"])
        return

    encounter = roll_scavenge_encounter(character.level)
    console.print(f"[{TEXT_DIM}]{encounter['intro']}[/{TEXT_DIM}]")
    if encounter["type"] == "loot":
        low, high = encounter["credits"]
        amount = random.randint(low, high)
        character.credits += amount
        console.print(f"\n[{ACCENT}]Score![/{ACCENT}] +{amount} credits.")
    # "nothing" encounters just print their flavor line above.


def visit_undercity(character: Character) -> None:
    print_arrival(character, "Undercity")

    print_menu_divider("The Streets")
    choice = hotkey_prompt(
        console,
        [
            ("S", "Slice Drop Box"),
            ("F", "Find a Fight"),
            ("H", "Hunt Cache"),
            ("L", "Leave"),
        ],
    )
    if choice == "S":
        _jack_in(character)
    elif choice == "F":
        _find_a_fight(character)
    elif choice == "H":
        _scavenge(character)


def _deposit(character: Character) -> None:
    if character.credits <= 0:
        console.print(f"[{TEXT_DIM}]Nothing on hand to deposit.[/{TEXT_DIM}]")
        return
    amount = IntPrompt.ask(f"Deposit how much? (0 to cancel, up to {character.credits})")
    if amount <= 0:
        return
    if amount > character.credits:
        console.print(f"[{DANGER}]You don't have that much on hand.[/{DANGER}]")
        return
    character.credits -= amount
    character.banked_credits += amount
    console.print(f"[{CREDITS}]{amount} credits deposited.[/{CREDITS}] Banked: {character.banked_credits}")


def _withdraw(character: Character) -> None:
    if character.banked_credits <= 0:
        console.print(f"[{TEXT_DIM}]Nothing banked to withdraw.[/{TEXT_DIM}]")
        return
    amount = IntPrompt.ask(f"Withdraw how much? (0 to cancel, up to {character.banked_credits})")
    if amount <= 0:
        return
    if amount > character.banked_credits:
        console.print(f"[{DANGER}]You don't have that much banked.[/{DANGER}]")
        return
    character.banked_credits -= amount
    character.credits += amount
    console.print(f"[{CREDITS}]{amount} credits withdrawn.[/{CREDITS}] On hand: {character.credits}")


def visit_netvault(character: Character) -> None:
    print_arrival(character, "NetVault")

    for result in notify_step(character, "talk", "NetVault"):
        print_quest_result(console, character, result)

    print_menu_divider("Banking")
    right_panel = _station_data_panel(
        "VAULT LEDGER",
        [
            ("On Hand", f"[{CREDITS}]{character.credits}[/{CREDITS}]"),
            ("Banked", f"[{CREDITS}]{character.banked_credits}[/{CREDITS}]"),
            ("Safety", f"[{TEXT_DIM}]Banked credits are safe from death-loss[/{TEXT_DIM}]"),
            ("Security", "Agent Parker + K9 unit on the floor"),
        ],
    )
    _interaction_deck(npc_at("NetVault"), right_panel, character)
    console.print(_npc_panel(get_npc("agent_parker"), character))

    action = hotkey_prompt(console, [("D", "Deposit"), ("W", "Withdraw"), ("L", "Leave")])
    if action == "D":
        _deposit(character)
    elif action == "W":
        _withdraw(character)


HEAL_COST_PER_HP = 2


CURE_COST = 15


def _heal(character: Character) -> None:
    missing = character.max_hp - character.hp
    if missing <= 0:
        console.print(f"[{TEXT_DIM}]You're already at full health.[/{TEXT_DIM}]")
        return

    max_affordable = min(missing, character.credits // HEAL_COST_PER_HP)
    if max_affordable <= 0:
        console.print(f"[{DANGER}]You can't afford so much as a bandage right now.[/{DANGER}]")
        return

    amount = IntPrompt.ask(f"Heal how much HP? (0 to cancel, up to {max_affordable})")
    if amount <= 0:
        return
    if amount > max_affordable:
        console.print(f"[{DANGER}]You can't afford that much healing.[/{DANGER}]")
        return

    cost = amount * HEAL_COST_PER_HP
    character.hp += amount
    character.credits -= cost
    console.print(
        f"[{ACCENT}]Patched up.[/{ACCENT}] "
        f"HP {character.hp}/{character.max_hp}. -{cost} credits."
    )


def _buy_supplies(character: Character) -> None:
    catalog = load_usable_items()

    console.print(f"\n[{INFO}]Credits on hand:[/{INFO}] [{CREDITS}]{character.credits}[/{CREDITS}]")
    table = Table(border_style=BORDER)
    table.add_column("#", justify="right", style=LABEL)
    table.add_column("Item", style=TEXT)
    table.add_column("Effect")
    table.add_column("Cost", justify="right")
    table.add_column("Description", style=TEXT_DIM)
    for i, item in enumerate(catalog, start=1):
        table.add_row(str(i), item["name"], describe_effect(item), str(item["cost"]), item["flavor"])
    console.print(table)

    choice = read_choice(
        console,
        [str(i) for i in range(len(catalog) + 1)],
        prompt="Buy which item? (0 to cancel)",
    )
    if choice == "0":
        return

    item = catalog[int(choice) - 1]
    if character.credits < item["cost"]:
        console.print(f"[{DANGER}]Not enough credits for that.[/{DANGER}]")
        return

    buy_item(character, item["id"])
    console.print(f"[{ACCENT}]Bought:[/{ACCENT}] {item['name']}. -{item['cost']} credits.")


def _cure(character: Character) -> None:
    if not character.status_effects:
        console.print(f"[{TEXT_DIM}]No status effects to clear.[/{TEXT_DIM}]")
        return

    action = hotkey_prompt(
        console, [("Y", "Yes"), ("N", "No")], prompt=f"Clear those for {CURE_COST} credits?"
    )
    if action != "Y":
        return
    if character.credits < CURE_COST:
        console.print(f"[{DANGER}]Not enough credits for that.[/{DANGER}]")
        return

    character.credits -= CURE_COST
    cured = cure_all(character)
    console.print(f"[{ACCENT}]Cleared {cured} status effect(s).[/{ACCENT}] -{CURE_COST} credits.")


def visit_doc_wires_clinic(character: Character) -> None:
    print_arrival(character, "Doc Wire's Clinic")

    for result in notify_step(character, "talk", "Doc Wire's Clinic"):
        print_quest_result(console, character, result)

    print_menu_divider("Clinic Menu")
    hp_color = hp_style(character.hp, character.max_hp)
    effects_text = (
        ", ".join(EFFECT_LABELS.get(e, e) for e in character.status_effects)
        if character.status_effects
        else f"[{TEXT_DIM}]None[/{TEXT_DIM}]"
    )
    right_panel = _station_data_panel(
        "MEDBAY STATUS",
        [
            ("HP", f"[{hp_color}]{character.hp}/{character.max_hp}[/{hp_color}]"),
            ("Patch-up Rate", f"{HEAL_COST_PER_HP} credits/HP"),
            ("Cure Cost", f"{CURE_COST} credits flat"),
            ("Active Effects", effects_text),
        ],
    )
    _interaction_deck(npc_at("Doc Wire's Clinic"), right_panel, character)

    can_afford_heal = character.credits >= HEAL_COST_PER_HP
    can_afford_cure = character.credits >= CURE_COST
    options = [
        ("H", "Heal", can_afford_heal),
        ("C", "Cure Effects", can_afford_cure),
        ("B", "Buy Supplies", True),
        ("L", "Leave", True),
    ]
    menu_text = OPTION_SEPARATOR.join(hotkey_bracket(key, label, affordable) for key, label, affordable in options)
    action = read_choice(console, [key for key, _, _ in options], prompt=menu_text)
    console.rule(style=TEXT_DIM)
    if action == "H":
        _heal(character)
    elif action == "C":
        _cure(character)
    elif action == "B":
        _buy_supplies(character)


TRAIN_BASE_COST = 40
TRAIN_SURCHARGE_PER_POINT = 5

# Shared across all three stats, not per-stat — three sparring bouts total
# per day, however you split them. Resets on sleep (_sleep_and_advance_day),
# same pattern as Chrome Noodle Bar's Buy a Round.
TRAINING_ATTEMPTS_PER_DAY = 3

TRAINABLE_STATS: dict[str, tuple[str, str]] = {
    "A": ("attack", "Attack"),
    "D": ("defense", "Defense"),
    "T": ("tech", "Tech"),
}

SPARRING_FLAVOR: dict[str, str] = {
    "attack": "The melee drone comes in fast. You trade blows until it flags a clean hit and powers down.",
    "defense": "A heavy-frame drone leans into you again and again. You learn to read the wind-up.",
    "tech": "You jack into a sparring ICE routine and duel it through three simulated firewalls.",
}


def _train_cost(current_value: int) -> int:
    """Training cost rises with the stat's current value, so grinding one
    stat sky-high gets progressively more expensive instead of staying flat."""
    return TRAIN_BASE_COST + current_value * TRAIN_SURCHARGE_PER_POINT


def visit_robodojo(character: Character) -> None:
    print_arrival(character, "RoboDOJO")

    for result in notify_step(character, "talk", "RoboDOJO"):
        print_quest_result(console, character, result)

    print_menu_divider("Training")
    attempts_left = TRAINING_ATTEMPTS_PER_DAY - character.training_attempts_today
    can_train = attempts_left > 0
    table = Table(border_style=BORDER, show_header=False)
    table.add_column("Stat", style=TEXT)
    table.add_column("Current", justify="right")
    table.add_column("Fee on win", justify="right")
    for key, (attr, label) in TRAINABLE_STATS.items():
        current = getattr(character, attr)
        table.add_row(hotkey_bracket(key, label, can_train, reason="Capped Today"), str(current), str(_train_cost(current)))

    right_panel = _station_data_panel(
        "TRAINING LOG",
        [
            ("Credits", f"[{CREDITS}]{character.credits}[/{CREDITS}]"),
            ("Bouts left today", f"{max(0, attempts_left)}/{TRAINING_ATTEMPTS_PER_DAY}"),
        ],
        extra=table,
    )
    _interaction_deck(npc_at("RoboDOJO"), right_panel, character)
    if can_train:
        console.print(
            f"[{TEXT_DIM}]A training drone powers up, servos whirring, waiting for you to pick a discipline. "
            f"Spar it for real — win and the stat gain sticks, but the fee's only charged on a win.[/{TEXT_DIM}]"
        )
    else:
        console.print(
            f"[{TEXT_DIM}]Daryl waves you off the mats. \"You're done sparring for today, choom. "
            f"Body needs to recover. Come back tomorrow.\"[/{TEXT_DIM}]"
        )

    ability_table = Table(title=f"[{LABEL}]Abilities[/{LABEL}]", border_style=BORDER, show_header=False)
    ability_table.add_column("Ability", style=TEXT)
    ability_table.add_column("Status")
    ability_table.add_column("Cost", justify="right")
    ability_table.add_column("Effect", style=TEXT_DIM)
    for ability_id, ability in ABILITIES.items():
        learned = ability_id in character.learned_abilities
        status = f"[{ACCENT}]Learned[/{ACCENT}]" if learned else f"[{TEXT_DIM}]Available[/{TEXT_DIM}]"
        cost_text = f"[{TEXT_DIM}]—[/{TEXT_DIM}]" if learned else str(ability["cost"])
        ability_table.add_row(ability["name"], status, cost_text, ability["flavor"])
    console.print(ability_table)

    options = [(k, label, can_train) for k, (_, label) in TRAINABLE_STATS.items()] + [
        ("B", "Learn Ability", True),
        ("L", "Leave", True),
    ]
    menu_text = OPTION_SEPARATOR.join(
        hotkey_bracket(key, label, affordable, reason="Capped Today") for key, label, affordable in options
    )
    choice = read_choice(console, [k for k, _, _ in options], prompt=f"What'll it be?\n{menu_text}")
    console.rule(style=TEXT_DIM)
    if choice == "L":
        return
    if choice == "B":
        _learn_ability(character)
        return

    _spar(character, choice)


def _spar(character: Character, choice: str) -> None:
    """Train a stat by actually fighting a themed sparring drone (see
    TRAINING_DRONES) instead of an instant guaranteed purchase — winning
    grants +1 to the stat and only then charges the credit fee; losing (or
    fleeing) costs nothing extra beyond whatever the fight itself did.
    Capped at TRAINING_ATTEMPTS_PER_DAY bouts, shared across all three
    stats, spent on the attempt regardless of outcome."""
    if character.training_attempts_today >= TRAINING_ATTEMPTS_PER_DAY:
        console.print(f"[{DANGER}]You're tapped out for today — Daryl won't let you back on the mats.[/{DANGER}]")
        return

    attr, label = TRAINABLE_STATS[choice]
    character.training_attempts_today += 1
    console.print(f"[{TEXT_DIM}]{SPARRING_FLAVOR[attr]}[/{TEXT_DIM}]")
    won = run_combat(character, dict(TRAINING_DRONES[attr]))

    if not won:
        console.print(f"\n[{TEXT_DIM}]No stat gain this time — the drone resets for another round tomorrow.[/{TEXT_DIM}]")
        return

    cost = _train_cost(getattr(character, attr))
    character.credits -= cost
    setattr(character, attr, getattr(character, attr) + 1)
    console.print(
        f"\n[{ACCENT}]Training paid off.[/{ACCENT}] {label} increased to {getattr(character, attr)}. "
        f"-{cost} credits."
    )


def _learn_ability(character: Character) -> None:
    available = [aid for aid in ABILITIES if aid not in character.learned_abilities]
    if not available:
        console.print(f"\n[{TEXT_DIM}]You've learned everything Daryl's cleared to teach.[/{TEXT_DIM}]")
        return

    table = Table(border_style=BORDER, show_header=False)
    table.add_column("#", justify="right", style=LABEL)
    table.add_column("Ability", style=TEXT)
    table.add_column("Cost", justify="right")
    table.add_column("Effect", style=TEXT_DIM)
    for i, ability_id in enumerate(available, start=1):
        ability = ABILITIES[ability_id]
        table.add_row(str(i), ability["name"], str(ability["cost"]), ability["flavor"])
    console.print(table)

    choice = read_choice(
        console,
        [str(i) for i in range(len(available) + 1)],
        prompt="Learn which ability? (0 to cancel)",
    )
    if choice == "0":
        return

    ability_id = available[int(choice) - 1]
    ability = ABILITIES[ability_id]
    if character.credits < ability["cost"]:
        console.print(f"[{DANGER}]Not enough credits for that.[/{DANGER}]")
        return

    character.credits -= ability["cost"]
    character.learned_abilities.append(ability_id)
    console.print(f"[{ACCENT}]Learned:[/{ACCENT}] {ability['name']}. -{ability['cost']} credits.")


def visit_the_pit(character: Character) -> None:
    print_arrival(character, "The Pit")
    console.print(f"[{TEXT_DIM}]The crowd wants blood. Pick your match.[/{TEXT_DIM}]")

    print_menu_divider("The Ring")
    gladiators = load_gladiators()
    table = Table(border_style=BORDER)
    table.add_column("#", justify="right", style=LABEL)
    table.add_column("Gladiator", style=TEXT)
    table.add_column("HP", justify="right")
    table.add_column("Reward", justify="right")
    for i, g in enumerate(gladiators, start=1):
        table.add_row(str(i), g["name"], str(g["hp"]), f"{g['credits_reward']}cr / {g['reputation_reward']}rep")
    console.print(table)

    choice = read_choice(
        console,
        [str(i) for i in range(len(gladiators) + 1)],
        prompt="Step into the ring? (0 to cancel)",
    )
    if choice == "0":
        return

    gladiator = gladiators[int(choice) - 1]
    console.print(f"\n[{TEXT_DIM}]{gladiator['intro']}[/{TEXT_DIM}]")
    tier = gladiator.get("tier")
    top_tier = max(g.get("tier", 0) for g in gladiators)
    enemy_data = {k: v for k, v in gladiator.items() if k not in ("id", "intro", "tier")}
    won = run_combat(character, enemy_data)

    if won and tier == top_tier and random.random() < QUANTUM_CORE_DROP_CHANCE:
        character.quantum_cores += 1
        console.print(
            f"\n[{INFO}]Tucked in the gladiator's rig, something that isn't scrap — "
            f"a Quantum Core, still warm.[/{INFO}] +1 Quantum Core."
        )


REST_THRESHOLD = 0.5  # free rest tops you up to this fraction of max HP, no further


def visit_chrome_noodle_bar(character: Character) -> None:
    print_arrival(character, "Chrome Noodle Bar")

    for result in notify_step(character, "talk", "Chrome Noodle Bar"):
        print_quest_result(console, character, result)

    rest_floor = int(character.max_hp * REST_THRESHOLD)
    if character.hp >= rest_floor:
        rest_text = f"[{TEXT_DIM}]Already rested — no free heal available[/{TEXT_DIM}]"
    elif character.rested_today:
        rest_text = f"[{TEXT_DIM}]Already used today's free rest[/{TEXT_DIM}]"
    else:
        healed = rest_floor - character.hp
        character.hp = rest_floor
        character.rested_today = True
        rest_text = f"[{ACCENT}]+{healed} HP, on the house[/{ACCENT}]"

    board_active = [
        quest_id for quest_id in character.active_quests if get_quest(quest_id).get("board", "Fixer Board") == "Chrome Noodle Bar"
    ]
    round_status = (
        f"[{TEXT_DIM}]Already had one today[/{TEXT_DIM}]" if character.bought_round_today else f"{BUY_ROUND_COST} credits"
    )
    right_panel = _station_data_panel(
        "BAR TAB",
        [
            ("Free Rest", rest_text),
            ("Buy a Round", round_status),
            ("Active Contracts", str(len(board_active))),
        ],
    )
    _interaction_deck(npc_at("Chrome Noodle Bar"), right_panel, character)

    choice = hotkey_prompt(
        console,
        [("B", "Buy a round"), ("C", "Contract Booth"), ("L", "Leave")],
    )
    if choice == "B":
        _buy_a_round(character)
    elif choice == "C":
        _visit_endr3am(character)


BUY_ROUND_COST = 25


def _buy_a_round(character: Character) -> None:
    if character.bought_round_today:
        console.print(f"\n[{TEXT_DIM}]Rin cuts you off. \"One's your limit tonight, choom. Come back tomorrow.\"[/{TEXT_DIM}]")
        return
    if character.credits < BUY_ROUND_COST:
        console.print(f"\n[{DANGER}]Can't even afford to buy yourself a drink right now.[/{DANGER}]")
        return

    character.bought_round_today = True
    character.credits -= BUY_ROUND_COST
    console.print(f"\n[{TEXT_DIM}]You slap {BUY_ROUND_COST} credits on the bar. Rin pours.[/{TEXT_DIM}]")

    roll = random.random()
    if roll < 0.12:
        stat_key = random.choice(["attack", "defense", "tech"])
        setattr(character, stat_key, getattr(character, stat_key) + 1)
        console.print(
            f"[{ACCENT}]Rin tells a story that actually sticks with you.[/{ACCENT}] "
            f"+1 {stat_key.capitalize()}, permanently."
        )
    elif roll < 0.70:
        character.reputation += 2
        console.print(f"[{CREDITS}]Decent gossip tonight.[/{CREDITS}] +2 reputation.")
    else:
        apply_effect(character, "drunk", 3)
        console.print(
            f"[{DANGER}]You get loud, then sloppy, then horizontal. Rin has you tossed out "
            f"before you can order another.[/{DANGER}]"
        )


def _visit_endr3am(character: Character) -> None:
    print_menu_divider("Contract Booth")
    board_active = [
        quest_id for quest_id in character.active_quests if get_quest(quest_id).get("board", "Fixer Board") == "Chrome Noodle Bar"
    ]
    board_completed = [
        quest_id for quest_id in character.completed_quests if get_quest(quest_id).get("board", "Fixer Board") == "Chrome Noodle Bar"
    ]
    right_panel = _station_data_panel(
        "BOOTH LEDGER",
        [
            ("Charisma", str(character.charisma)),
            ("Contracts Active", str(len(board_active))),
            ("Contracts Completed", str(len(board_completed))),
        ],
    )
    _interaction_deck(get_npc("endr3am"), right_panel, character)
    _browse_contract_board(character, "Chrome Noodle Bar")


def _browse_contract_board(character: Character, board: str) -> None:
    active_ids = [
        quest_id for quest_id in character.active_quests if get_quest(quest_id).get("board", "Fixer Board") == board
    ]
    if active_ids:
        console.print(f"\n[{LABEL}]Active contracts:[/{LABEL}]")
        for quest_id in active_ids:
            quest = get_quest(quest_id)
            step = current_step(character, quest_id)
            console.print(f"  [bold]{quest['title']}[/bold] — {step['description']}")

    locked = locked_quests(character, board)
    if locked:
        console.print(f"\n[{TEXT_DIM}]Locked contracts:[/{TEXT_DIM}]")
        for quest in locked:
            gaps = []
            min_rep = quest.get("min_reputation", 0)
            if character.reputation < min_rep:
                gaps.append(f"Reputation {min_rep} (have {character.reputation})")
            min_cha = quest.get("min_charisma", 0)
            if character.charisma < min_cha:
                gaps.append(f"Charisma {min_cha} (have {character.charisma})")
            min_lvl = quest.get("min_level", 1)
            if character.level < min_lvl:
                gaps.append(f"Level {min_lvl} (have {character.level})")
            console.print(f"  [{TEXT_DIM}]{quest['title']} — needs {', '.join(gaps)}[/{TEXT_DIM}]")

    open_quests = available_quests(character, board)
    if not open_quests:
        console.print(f"\n[{TEXT_DIM}]No new contracts posted right now.[/{TEXT_DIM}]")
        return

    console.print(f"\n[{LABEL}]Open contracts:[/{LABEL}]")
    table = Table(border_style=BORDER, show_header=False)
    table.add_column("#", justify="right", style=LABEL)
    table.add_column("Title", style=TEXT)
    table.add_column("Hook", style=TEXT_DIM)
    for i, quest in enumerate(open_quests, start=1):
        table.add_row(str(i), quest["title"], quest["hook"])
    console.print(table)

    choice = read_choice(
        console,
        [str(i) for i in range(len(open_quests) + 1)],
        prompt="Take a contract? (0 to cancel)",
    )
    if choice == "0":
        return

    chosen_quest = open_quests[int(choice) - 1]
    accept_quest(character, chosen_quest["id"])
    console.print(f"\n[{ACCENT}]Contract accepted:[/{ACCENT}] {chosen_quest['title']}")
    console.print(f"  {chosen_quest['steps'][0]['description']}")


def visit_fixer_board(character: Character) -> None:
    print_arrival(character, "Fixer Board")

    for result in notify_step(character, "talk", "Fixer Board"):
        print_quest_result(console, character, result)

    print_menu_divider("Contract Board")
    board_active = [
        quest_id for quest_id in character.active_quests if get_quest(quest_id).get("board", "Fixer Board") == "Fixer Board"
    ]
    board_completed = [
        quest_id for quest_id in character.completed_quests if get_quest(quest_id).get("board", "Fixer Board") == "Fixer Board"
    ]
    right_panel = _station_data_panel(
        "BOARD STATUS",
        [
            ("Reputation", str(character.reputation)),
            ("Contracts Active", str(len(board_active))),
            ("Contracts Completed", str(len(board_completed))),
        ],
    )
    _interaction_deck(npc_at("Fixer Board"), right_panel, character)
    _browse_contract_board(character, "Fixer Board")


def build_loadout_table(character: Character, title: str | None = None) -> Table:
    table = Table(title=title, border_style=BORDER, show_header=False)
    table.add_column("Slot", style=ACCENT_SOFT)
    table.add_column("Installed", style=TEXT)
    table.add_column("Special", style=WARNING)
    for slot in CYBERWARE_SLOTS:
        item_id = character.cyberware[slot]
        installed = "empty"
        special = ""
        if item_id:
            item = get_item(item_id)
            installed = item["name"]
            if item.get("inflict_effect"):
                label = EFFECT_LABELS.get(item["inflict_effect"], item["inflict_effect"])
                special = f"Causes {label}"
        table.add_row(slot.capitalize(), installed, special)
    return table


def build_catalog_table(catalog: list[dict], character: Character) -> Table:
    table = Table(title=f"[{LABEL}]Today's Stock[/{LABEL}]", border_style=BORDER)
    table.add_column("#", justify="right", style=LABEL)
    table.add_column("Item", style=TEXT)
    table.add_column("Slot")
    table.add_column("Bonus")
    table.add_column("Special", style=WARNING)
    table.add_column("Cost", justify="right", no_wrap=True)
    for i, item in enumerate(catalog, start=1):
        special = ""
        if item.get("inflict_effect"):
            special = EFFECT_LABELS.get(item["inflict_effect"], item["inflict_effect"])
        price = discounted_cost(character, item)
        affordable = character.credits >= price
        cost_text = str(price) if price == item["cost"] else f"[{CREDITS}]{price}[/{CREDITS}] [{TEXT_DIM}]({item['cost']})[/{TEXT_DIM}]"
        if not affordable:
            cost_text = f"[{TEXT_DIM}]{cost_text}[/{TEXT_DIM}] [{NOTE}]✗[/{NOTE}]"
        index_text = str(i) if affordable else f"[{TEXT_DIM}]{i}[/{TEXT_DIM}]"
        name_text = item["name"] if affordable else f"[{TEXT_DIM}]{item['name']}[/{TEXT_DIM}]"

        bonus_text = f"+{item['bonus']} {item['stat']}"
        equipped_id = character.cyberware.get(item["slot"])
        if equipped_id:
            equipped_item = get_item(equipped_id)
            if equipped_item["stat"] == item["stat"]:
                delta = item["bonus"] - equipped_item["bonus"]
                if delta > 0:
                    bonus_text += f"\n[{ACCENT}][Upgrade: +{delta}][/{ACCENT}]"
                elif delta < 0:
                    bonus_text += f"\n[{DANGER}][Downgrade: {delta}][/{DANGER}]"
                else:
                    bonus_text += f"\n[{TEXT_DIM}][Same: +0][/{TEXT_DIM}]"

        table.add_row(
            index_text,
            name_text,
            item["slot"].capitalize(),
            bonus_text,
            special,
            cost_text,
        )
    return table


def _print_shop_dashboard(character: Character, catalog: list[dict]) -> None:
    """Side-by-side gear-deck view — what's equipped next to what's for
    sale — so a player can compare without scrolling between two screens."""
    console.print(f"\n[{INFO}]Credits on hand:[/{INFO}] [{CREDITS}]{character.credits}[/{CREDITS}]")
    loadout_table = build_loadout_table(character, title=f"[{LABEL}]Your Chrome[/{LABEL}]")
    catalog_table = build_catalog_table(catalog, character)

    grid = Table.grid(padding=(0, 4))
    grid.add_column()
    grid.add_column()
    grid.add_row(loadout_table, catalog_table)
    console.print(grid)


def _buy_cyberware(character: Character, catalog: list[dict]) -> None:
    choice = read_choice(
        console,
        [str(i) for i in range(len(catalog) + 1)],
        prompt="Buy which item? (0 to cancel)",
    )
    if choice == "0":
        return

    item = catalog[int(choice) - 1]
    old_id = character.cyberware[item["slot"]]
    old_item = get_item(old_id) if old_id else None
    # Only count the trade-in toward affordability if it refunds credits —
    # a Black Market prototype in that slot refunds Quantum Cores instead.
    trade_in = sell_back_value(old_item) if old_item and currency_of(old_item) == "credits" else 0
    price = discounted_cost(character, item)
    if character.credits + trade_in < price:
        console.print(f"[{DANGER}]Not enough credits for that, even with a trade-in.[/{DANGER}]")
        return

    buy_and_equip(character, item["id"])
    if old_id:
        console.print(f"[{TEXT_DIM}]{get_item(old_id)['name']} pulled and sold back for parts.[/{TEXT_DIM}]")
    console.print(
        f"[{ACCENT}]Installed:[/{ACCENT}] {item['name']} "
        f"(+{item['bonus']} {item['stat']}) for {price} credits."
    )


def _sell_cyberware(character: Character) -> None:
    equipped_slots = [slot for slot in CYBERWARE_SLOTS if character.cyberware[slot]]
    if not equipped_slots:
        console.print(f"[{TEXT_DIM}]Nothing installed to sell.[/{TEXT_DIM}]")
        return

    table = Table(border_style=BORDER, show_header=False)
    table.add_column("#", justify="right", style=LABEL)
    table.add_column("Slot", style=TEXT)
    table.add_column("Installed", style=TEXT_DIM)
    for i, slot in enumerate(equipped_slots, start=1):
        item = get_item(character.cyberware[slot])
        table.add_row(str(i), slot.capitalize(), f"{item['name']} (sells for {format_price(item, sell_back_value(item))})")
    console.print(table)

    choice = read_choice(
        console,
        [str(i) for i in range(len(equipped_slots) + 1)],
        prompt="Sell which item? (0 to cancel)",
    )
    if choice == "0":
        return

    slot = equipped_slots[int(choice) - 1]
    item = unequip(character, slot)
    console.print(f"[{CREDITS}]{item['name']} sold for {format_price(item, sell_back_value(item))}.[/{CREDITS}]")


def _visit_black_market(character: Character) -> None:
    catalog = load_black_market()

    console.rule(f"[{RARE}]Black Market[/{RARE}]")
    console.print(
        f"[{TEXT_DIM}]Hyphen8d pulls a panel out of the wall. \"Didn't think you had these on you. "
        f"This stuff doesn't officially exist, choom.\"[/{TEXT_DIM}]\n"
    )
    console.print(f"[{INFO}]Quantum Cores:[/{INFO}] {character.quantum_cores}\n")

    table = Table(border_style=BORDER_RARE, box=box.DOUBLE)
    table.add_column("#", justify="right", style=LABEL)
    table.add_column("Item", style=TEXT)
    table.add_column("Slot")
    table.add_column("Bonus")
    table.add_column("Special", style=WARNING)
    table.add_column("Cost", justify="right")
    table.add_column("Description", style=TEXT_DIM)
    for i, item in enumerate(catalog, start=1):
        special = ""
        if item.get("inflict_effect"):
            label = EFFECT_LABELS.get(item["inflict_effect"], item["inflict_effect"])
            special = f"Causes {label}"
        table.add_row(
            str(i),
            item["name"],
            item["slot"].capitalize(),
            f"+{item['bonus']} {item['stat']}",
            special,
            format_price(item, item["cost"]),
            item["flavor"],
        )
    console.print(table)

    choice = read_choice(
        console,
        [str(i) for i in range(len(catalog) + 1)],
        prompt="Buy which prototype? (0 to cancel)",
    )
    if choice == "0":
        return

    item = catalog[int(choice) - 1]
    old_id = character.cyberware[item["slot"]]
    old_item = get_item(old_id) if old_id else None
    trade_in = sell_back_value(old_item) if old_item and currency_of(old_item) == "quantum_core" else 0
    if character.quantum_cores + trade_in < item["cost"]:
        console.print(
            f"[{DANGER}]Not enough Quantum Cores for that, even with a trade-in — "
            f"you need {format_price(item, item['cost'])}.[/{DANGER}]"
        )
        return

    buy_black_market_item(character, item["id"])
    console.print(
        f"[{RARE}]Installed:[/{RARE}] {item['name']} "
        f"(+{item['bonus']} {item['stat']}) for {format_price(item, item['cost'])}."
    )


def visit_hyphen8ds_hut(character: Character) -> None:
    print_arrival(character, "Hyphen8d's Hut")

    for result in notify_step(character, "talk", "Hyphen8d's Hut"):
        print_quest_result(console, character, result)

    print_menu_divider("Shop Menu")
    if not character.market_stock:
        roll_daily_market(character)

    right_panel = _station_data_panel(
        "SHOP STATUS",
        [("Today's Event", describe_market_modifier(character))],
    )
    _interaction_deck(npc_at("Hyphen8d's Hut"), right_panel, character)

    catalog = get_daily_catalog(character)
    _print_shop_dashboard(character, catalog)

    # The Black Market ([M]) is a hidden option — deliberately left off the
    # printed menu text. It's only worth anything once a player has found a
    # Quantum Core, so there's nothing to advertise for most of a playthrough.
    visible = [("B", "Buy"), ("S", "Sell"), ("L", "Leave")]
    menu_text = OPTION_SEPARATOR.join(hotkey_bracket(key, label) for key, label in visible)
    action = read_choice(console, [key for key, _ in visible] + ["M"], prompt=menu_text)
    console.rule(style=TEXT_DIM)
    if action == "B":
        _buy_cyberware(character, catalog)
    elif action == "S":
        _sell_cyberware(character)
    elif action == "M":
        _visit_black_market(character)


def _themed_table(title: str) -> Table:
    table = Table(title=f"[{ACCENT}]{title}[/{ACCENT}]", border_style=BORDER, show_header=False)
    table.add_column("Label", style=ACCENT_SOFT)
    table.add_column("Value", style=TEXT)
    return table


def show_character_info(character: Character) -> None:
    console.print()
    console.rule(f"[{ACCENT}]{character.name}[/{ACCENT}] [{TEXT_DIM}]— {character.char_class}[/{TEXT_DIM}]")
    console.print()

    attributes = _themed_table("Attributes")
    attributes.add_row("Level", str(character.level))
    attributes.add_row("Day", str(character.day))
    attributes.add_row("XP", f"{character.xp}/{xp_for_next_level(character)}")
    hp_row_style = hp_style(character.hp, character.max_hp)
    attributes.add_row("HP", f"[{hp_row_style}]{character.hp}/{character.max_hp}[/{hp_row_style}]")
    attributes.add_row("Attack", str(character.attack))
    attributes.add_row("Defense", str(character.defense))
    attributes.add_row("Tech", str(character.tech))
    attributes.add_row("Charisma", str(character.charisma))

    economy = _themed_table("Economy")
    economy.add_row("Credits", str(character.credits))
    economy.add_row("Banked", str(character.banked_credits))
    economy.add_row("Quantum Cores", str(character.quantum_cores))

    contracts = _themed_table("Reputation & Contracts")
    contracts.add_row("Reputation", str(character.reputation))
    contracts.add_row("Contracts active", str(len(character.active_quests)))
    contracts.add_row("Contracts completed", str(len(character.completed_quests)))

    loadout = build_loadout_table(character, title=f"[{ACCENT}]Chrome[/{ACCENT}]")

    effects = _themed_table("Status Effects")
    if character.status_effects:
        for effect, remaining in character.status_effects.items():
            effects.add_row(EFFECT_LABELS.get(effect, effect), f"{remaining} round(s)")
    else:
        effects.add_row("No active effects", "")

    inventory = _themed_table("Inventory")
    if character.inventory:
        counts: dict[str, int] = {}
        for item_id in character.inventory:
            counts[item_id] = counts.get(item_id, 0) + 1
        for item_id, count in counts.items():
            item = get_usable_item(item_id)
            inventory.add_row(item["name"], f"x{count}")
    else:
        inventory.add_row("Nothing carried", "")

    abilities = _themed_table("RoboDOJO Abilities")
    if character.learned_abilities:
        for ability_id in character.learned_abilities:
            abilities.add_row(ABILITIES[ability_id]["name"], "Learned")
    else:
        abilities.add_row("None learned yet", "")

    grid = Table.grid(padding=(0, 2))
    grid.add_column()
    grid.add_column()
    grid.add_row(attributes, economy)
    grid.add_row(contracts, loadout)
    grid.add_row(effects, inventory)
    grid.add_row(abilities)
    console.print(grid)

    kills = _themed_table("Kills by Faction")
    if character.kills:
        by_faction: dict[str, list[tuple[str, int]]] = {}
        for name, count in character.kills.items():
            by_faction.setdefault(enemy_faction(name), []).append((name, count))
        for faction in sorted(by_faction):
            entries = sorted(by_faction[faction])
            total = sum(count for _, count in entries)
            kills.add_row(f"[bold]{faction}[/bold]", f"[bold]{total}[/bold]")
            for name, count in entries:
                kills.add_row(f"  {name}", str(count))
    else:
        kills.add_row("No kills yet", "")
    console.print(kills)


def _sleep_and_advance_day(character: Character) -> None:
    """Leaving the hub means heading back to the safehouse to sleep it off —
    advances the game day, fully heals, and clears any lingering status
    effects, then prints a summary panel of where things stand."""
    console.print(
        f"\n[{TEXT_DIM}]You head back to the safehouse, credits and gear safe... for now. "
        f"Sleep hits like a wall.[/{TEXT_DIM}]"
    )

    character.day += 1
    hot = hot_factions(character)
    reset_daily_kills(character)
    roll_daily_market(character)
    character.bought_round_today = False
    character.rested_today = False
    character.training_attempts_today = 0

    healed = character.max_hp - character.hp
    character.hp = character.max_hp
    cured = cure_all(character)

    ambushed = False
    if hot and random.random() < AMBUSH_CHANCE:
        ambushed = True
        faction = random.choice(hot)
        console.print(
            f"\n[{DANGER}]You're barely through the door when {faction} muscle kicks it back "
            f"open — they tracked you home.[/{DANGER}]"
        )
        encounter = roll_combat_encounter(character.level, faction=faction)
        console.print(f"[{TEXT_DIM}]{encounter['intro']}[/{TEXT_DIM}]")
        run_combat(character, encounter["enemy"])

    faction_totals: dict[str, int] = {}
    for name, count in character.kills.items():
        kill_faction = enemy_faction(name)
        faction_totals[kill_faction] = faction_totals.get(kill_faction, 0) + count
    if faction_totals:
        kills_text = ", ".join(f"{faction}: {count}" for faction, count in sorted(faction_totals.items()))
    else:
        kills_text = "No kills yet"

    heat_text = ", ".join(hot) if hot else "None"
    if ambushed:
        heat_text += f" [{TEXT_DIM}](ambushed on waking)[/{TEXT_DIM}]"

    body = Table.grid(padding=(0, 2))
    body.add_column(style=ACCENT_SOFT)
    body.add_column(style=TEXT)
    body.add_row("Level", str(character.level))
    body.add_row("Credits", f"{character.credits} ({character.banked_credits} banked)")
    body.add_row("Reputation", str(character.reputation))
    body.add_row("HP", f"Fully restored (+{healed})" if healed > 0 else "Already full")
    if ambushed:
        body.add_row("HP now", f"{character.hp}/{character.max_hp}")
    body.add_row("Status effects cleared", str(cured))
    body.add_row("Heat yesterday", heat_text)
    body.add_row("Kills by faction", kills_text)
    body.add_row("Hyphen8d's Hut", describe_market_modifier(character))

    console.print(
        Panel(
            body,
            title=f"[{ACCENT}]Daily Data Feed[/{ACCENT}]",
            subtitle=f"[{TEXT_DIM}]{character.name} — Day {character.day}[/{TEXT_DIM}]",
            border_style=BORDER,
            padding=(1, 2),
        )
    )


def enter_hub(character: Character) -> None:
    while True:
        console.clear()
        console.print()
        print_hub_menu(character)
        choice = read_choice(console, [*LOCATION_HOTKEYS.keys(), "I", "L", "?"], prompt="Where to?")
        if choice == "L":
            confirm = hotkey_prompt(
                console,
                [("Y", "Yes"), ("N", "No")],
                prompt="Head back to the safehouse and call it a day?",
            )
            if confirm != "Y":
                continue
            _sleep_and_advance_day(character)
            return
        if choice == "?":
            show_help(console)
            press_any_key(console, "Press any key to return to the central hub...")
            continue
        if choice == "I":
            show_character_info(character)
            press_any_key(console, "Press any key to return to the central hub...")
            continue

        chosen = LOCATION_HOTKEYS[choice]

        if chosen == "Undercity":
            visit_undercity(character)
        elif chosen == "Chrome Noodle Bar":
            visit_chrome_noodle_bar(character)
        elif chosen == "Fixer Board":
            visit_fixer_board(character)
        elif chosen == "Hyphen8d's Hut":
            visit_hyphen8ds_hut(character)
        elif chosen == "NetVault":
            visit_netvault(character)
        elif chosen == "Doc Wire's Clinic":
            visit_doc_wires_clinic(character)
        elif chosen == "RoboDOJO":
            visit_robodojo(character)
        elif chosen == "The Pit":
            visit_the_pit(character)
        else:
            raise ValueError(f"No hub handler wired up for location: {chosen!r}")

        press_any_key(console, "Press any key to return to the central hub...")
