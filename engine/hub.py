"""Hub menu / navigation between Neo Meridian locations."""

from __future__ import annotations

import random

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from engine.achievements import check_achievements, load_achievements
from engine.bestiary import TRAINING_DRONES, enemy_faction
from engine.character import CYBERWARE_SLOTS, Character, hp_style
from engine.city import roll_headline, roll_weather
from engine.combat import ABILITIES, run_combat
from engine.datashards import get_datashard, load_datashards, maybe_find_datashard
from engine.encounters import get_enemy_by_name, roll_combat_encounter, roll_scavenge_encounter
from engine.heat import AMBUSH_CHANCE, HEAT_FACTIONS, hot_factions, reset_daily_kills
from engine.help import show_help
from engine.inventory import buy_item, describe_effect, get_usable_item, load_usable_items
from engine.leveling import xp_for_next_level
from engine.npcs import get_npc, npc_at, random_line
from engine.pit import load_gladiators
from engine.quests import (
    accept_quest,
    advance_quest,
    available_quests,
    check_fetch_steps,
    current_step,
    get_quest,
    locked_quests,
    notify_step,
    pending_coerce_step,
    pending_deliver_step,
    pending_pay_step,
    print_quest_result,
)
from engine.shop import (
    buy_and_equip,
    buy_black_market_item,
    currency_of,
    describe_market_modifier,
    discounted_cost,
    format_credits,
    format_price,
    get_daily_catalog,
    get_item,
    give_away,
    load_black_market,
    load_street_modded,
    roll_daily_market,
    sell_back_value,
    street_modded_unlocked,
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
    DIVIDER_STATIC,
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
from engine.ui import (
    OPTION_SEPARATOR,
    glitch_rule,
    glitch_title_rule,
    hotkey_bracket,
    hotkey_prompt,
    make_hp_bar,
    press_any_key,
    read_choice,
)

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
        format_credits(character.credits),
        format_credits(character.banked_credits),
    )

    console.print(hud)
    return hud


def print_hub_menu(character: Character) -> None:
    glitch_title_rule(console, f"[{LABEL}]Neo Meridian[/{LABEL}]")
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
    shard_note = f"{len(character.datashards)}/{len(load_datashards())} recovered"
    actions.add_row(hotkey_bracket("A", "Archives"), f"Read recovered Datashard lore fragments ({shard_note}).")
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
    glitch_title_rule(console, f"[{TEXT_DIM}]{label}[/{TEXT_DIM}]", style=TEXT_DIM)


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
            f"open.[/{LABEL}] You skim a hot corporate credit-chip off the tray! +{format_credits(amount)}."
        )
        if random.random() < QUANTUM_CORE_DROP_CHANCE:
            character.quantum_cores += 1
            console.print(
                f"[{INFO}]The sub-grid crypto-seal completely ruptures, exposing the vault's "
                f"high-tier logic core.[/{INFO}] Tucked deep behind the primary cooling rails is "
                "something that shouldn't be there — a Quantum Core, humming at a frequency that "
                "gives you a migraine behind one eye. It doesn't look manufactured. It looks grown, "
                "veined like something that used to be alive, and for a second you'd swear it pulsed "
                "in time with your own heartbeat before you pocketed it. +1 Quantum Core."
            )
        maybe_find_datashard(character, console)
        return

    console.print(
        f"[{ALERT}]FEEDBACK ALERT: A heavy Black-ICE counter-intrusion sub-routine snaps back "
        f"through your deck, pinning your physical coordinates.[/{ALERT}] Overhead, an automated "
        "corporate containment team deploys to neutralize the breach!"
    )
    encounter = roll_combat_encounter(character, faction="Corp")
    console.print(f"[{TEXT_DIM}]{encounter['intro']}[/{TEXT_DIM}]")
    run_combat(character, encounter["enemy"])


def _find_a_fight(character: Character) -> None:
    encounter = roll_combat_encounter(character)
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
        encounter = roll_combat_encounter(character, faction=faction)
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
        encounter = roll_combat_encounter(character)
        console.print(f"[{TEXT_DIM}]{encounter['intro']}[/{TEXT_DIM}]")
        run_combat(character, encounter["enemy"])
        return

    encounter = roll_scavenge_encounter(character)
    console.print(f"[{TEXT_DIM}]{encounter['intro']}[/{TEXT_DIM}]")
    if encounter["type"] == "loot":
        low, high = encounter["credits"]
        amount = random.randint(low, high)
        character.credits += amount
        console.print(f"\n[{ACCENT}]Score![/{ACCENT}] +{format_credits(amount)}.")
    # "nothing" encounters just print their flavor line above.
    maybe_find_datashard(character, console)


# Ambient, diegetic hints that a faction is closing in on Faction Heat's
# ambush threshold (HEAT_KILL_THRESHOLD in engine/heat.py) -- shown a kill
# or two before it actually triggers, so a kill spree telegraphs its own
# rising risk instead of an ambush just appearing out of nowhere.
HEAT_WARNING_FLAVOR: dict[str, dict[int, str]] = {
    "Corp": {
        2: "Corp drones have been circling the block more than once — you notice, even if they pretend not to.",
        3: "Corp drones are aggressively scanning the perimeter now. They're close to calling it in.",
    },
    "Street Gang": {
        2: "A couple of Street Gang lookouts keep clocking you as you pass.",
        3: "Street Gang lookouts are unusually tense today — word's gotten around about you.",
    },
}


def _heat_warnings(character: Character) -> list[str]:
    warnings = []
    for faction in HEAT_FACTIONS:
        count = character.daily_kills.get(faction, 0)
        line = HEAT_WARNING_FLAVOR.get(faction, {}).get(count)
        if line:
            warnings.append(line)
    return warnings


def visit_undercity(character: Character) -> None:
    print_arrival(character, "Undercity")
    for warning in _heat_warnings(character):
        console.print(f"[italic {WARNING}]{warning}[/italic {WARNING}]")
    _check_coerce_step(character, "Undercity")

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
    amount = IntPrompt.ask(f"Deposit how much? (0 to cancel, up to {format_credits(character.credits)})")
    if amount <= 0:
        return
    if amount > character.credits:
        console.print(f"[{DANGER}]You don't have that much on hand.[/{DANGER}]")
        return
    character.credits -= amount
    character.banked_credits += amount
    console.print(f"[{CREDITS}]{format_credits(amount)} deposited.[/{CREDITS}] Banked: {format_credits(character.banked_credits)}")


def _withdraw(character: Character) -> None:
    if character.banked_credits <= 0:
        console.print(f"[{TEXT_DIM}]Nothing banked to withdraw.[/{TEXT_DIM}]")
        return
    amount = IntPrompt.ask(f"Withdraw how much? (0 to cancel, up to {format_credits(character.banked_credits)})")
    if amount <= 0:
        return
    if amount > character.banked_credits:
        console.print(f"[{DANGER}]You don't have that much banked.[/{DANGER}]")
        return
    character.banked_credits -= amount
    character.credits += amount
    console.print(f"[{CREDITS}]{format_credits(amount)} withdrawn.[/{CREDITS}] On hand: {format_credits(character.credits)}")


def visit_netvault(character: Character) -> None:
    print_arrival(character, "NetVault")

    for result in notify_step(character, "talk", "NetVault"):
        print_quest_result(console, character, result)
    _check_deliver_and_pay(character, "NetVault")

    print_menu_divider("Banking")
    right_panel = _station_data_panel(
        "VAULT LEDGER",
        [
            ("On Hand", f"[{CREDITS}]{format_credits(character.credits)}[/{CREDITS}]"),
            ("Banked", f"[{CREDITS}]{format_credits(character.banked_credits)}[/{CREDITS}]"),
            ("Safety", f"[{TEXT_DIM}]Banked credits are safe from death-loss[/{TEXT_DIM}]"),
            ("Security", "Agent Parker + K9 unit on the floor"),
        ],
    )
    _interaction_deck(npc_at("NetVault"), right_panel, character)
    console.print(_npc_panel(get_npc("agent_parker"), character))
    glitch_rule(console, style=TEXT_DIM)

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
        f"HP {character.hp}/{character.max_hp}. -{format_credits(cost)}."
    )


def _buy_supplies(character: Character) -> None:
    catalog = load_usable_items()

    console.print(f"\n[{INFO}]Credits on hand:[/{INFO}] [{CREDITS}]{format_credits(character.credits)}[/{CREDITS}]")
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
    console.print(f"[{ACCENT}]Bought:[/{ACCENT}] {item['name']}. -{format_credits(item['cost'])}.")


def _cure(character: Character) -> None:
    if not character.status_effects:
        console.print(f"[{TEXT_DIM}]No status effects to clear.[/{TEXT_DIM}]")
        return

    action = hotkey_prompt(
        console, [("Y", "Yes"), ("N", "No")], prompt=f"Clear those for {format_credits(CURE_COST)}?"
    )
    if action != "Y":
        return
    if character.credits < CURE_COST:
        console.print(f"[{DANGER}]Not enough credits for that.[/{DANGER}]")
        return

    character.credits -= CURE_COST
    cured = cure_all(character)
    console.print(f"[{ACCENT}]Cleared {cured} status effect(s).[/{ACCENT}] -{format_credits(CURE_COST)}.")


def visit_doc_wires_clinic(character: Character) -> None:
    print_arrival(character, "Doc Wire's Clinic")

    for result in notify_step(character, "talk", "Doc Wire's Clinic"):
        print_quest_result(console, character, result)
    _check_deliver_and_pay(character, "Doc Wire's Clinic")

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
            ("Patch-up Rate", f"{format_credits(HEAL_COST_PER_HP)}/HP"),
            ("Cure Cost", f"{format_credits(CURE_COST)} flat"),
            ("Active Effects", effects_text),
        ],
    )
    _interaction_deck(npc_at("Doc Wire's Clinic"), right_panel, character)
    glitch_rule(console, style=TEXT_DIM)

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
    glitch_rule(console, style=TEXT_DIM)
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
    _check_deliver_and_pay(character, "RoboDOJO")

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
            ("Credits", f"[{CREDITS}]{format_credits(character.credits)}[/{CREDITS}]"),
            ("Bouts left today", f"{max(0, attempts_left)}/{TRAINING_ATTEMPTS_PER_DAY}"),
        ],
        extra=table,
    )
    _interaction_deck(npc_at("RoboDOJO"), right_panel, character)
    glitch_rule(console, style=TEXT_DIM)
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
    choice = read_choice(console, [k for k, _, _ in options], prompt=f"[SYS] AWAITING INPUT>\n{menu_text}")
    glitch_rule(console, style=TEXT_DIM)
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
        f"-{format_credits(cost)}."
    )
    check_achievements(character, console)


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
    console.print(f"[{ACCENT}]Learned:[/{ACCENT}] {ability['name']}. -{format_credits(ability['cost'])}.")


def visit_the_pit(character: Character) -> None:
    print_arrival(character, "The Pit")
    if character.kills.get("Kingpin Draxx", 0) > 0:
        console.print(
            f"[{ACCENT}]The announcer still doesn't quite believe it, three fights later: "
            f"\"...the reigning champion of the Pit!\"[/{ACCENT}] Draxx's old corner is empty. "
            f"Nobody's claimed it since you took the belt off him."
        )
    else:
        console.print(f"[{TEXT_DIM}]The crowd wants blood. Pick your match.[/{TEXT_DIM}]")

    print_menu_divider("The Ring")
    gladiators = load_gladiators()
    table = Table(border_style=BORDER)
    table.add_column("#", justify="right", style=LABEL)
    table.add_column("Gladiator", style=TEXT)
    table.add_column("HP", justify="right")
    table.add_column("Reward", justify="right")
    for i, g in enumerate(gladiators, start=1):
        table.add_row(str(i), g["name"], str(g["hp"]), f"{format_credits(g['credits_reward'])} / {g['reputation_reward']}rep")
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
            f"a Quantum Core, still warm, still faintly humming.[/{INFO}] It doesn't look "
            "manufactured. It looks grown, and for a moment you'd swear the hum synced itself to "
            "your pulse before settling back into its own rhythm. Whatever it is, it wasn't built "
            "to be carried around by someone like you. +1 Quantum Core."
        )


REST_THRESHOLD = 0.5  # free rest tops you up to this fraction of max HP, no further


def visit_chrome_noodle_bar(character: Character) -> None:
    print_arrival(character, "Chrome Noodle Bar")

    for result in notify_step(character, "talk", "Chrome Noodle Bar"):
        print_quest_result(console, character, result)
    _check_deliver_and_pay(character, "Chrome Noodle Bar")

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
        f"[{TEXT_DIM}]Already had one today[/{TEXT_DIM}]" if character.bought_round_today else format_credits(BUY_ROUND_COST)
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
    glitch_rule(console, style=TEXT_DIM)

    choice = hotkey_prompt(
        console,
        [("B", "Buy a round"), ("C", "Contract Booth"), ("L", "Leave")],
    )
    if choice == "B":
        _buy_a_round(character)
    elif choice == "C":
        _visit_endr3am(character)


BUY_ROUND_COST = 25

# Corp body count that gets you treated like a local hero at the Noodle Bar —
# same threshold Static Rin's conditional_lines use in content/npcs.json.
CORP_HERO_KILL_THRESHOLD = 15


def _buy_a_round(character: Character) -> None:
    if character.bought_round_today:
        console.print(f"\n[{TEXT_DIM}]Rin cuts you off. \"One's your limit tonight, choom. Come back tomorrow.\"[/{TEXT_DIM}]")
        return

    corp_kills = sum(count for name, count in character.kills.items() if enemy_faction(name) == "Corp")
    is_corp_hero = corp_kills >= CORP_HERO_KILL_THRESHOLD

    if not is_corp_hero and character.credits < BUY_ROUND_COST:
        console.print(f"\n[{DANGER}]Can't even afford to buy yourself a drink right now.[/{DANGER}]")
        return

    character.bought_round_today = True
    if is_corp_hero:
        console.print(
            f"\n[{ACCENT}]Rin waves off your credits. \"This one's on the house — anybody putting that many "
            f"corp badges in the ground drinks free here.\"[/{ACCENT}]"
        )
    else:
        character.credits -= BUY_ROUND_COST
        console.print(f"\n[{TEXT_DIM}]You slap {format_credits(BUY_ROUND_COST)} on the bar. Rin pours.[/{TEXT_DIM}]")

    _resolve_round_encounter(character)


# Micro-narratives for "Buy a Round" — each fires before its mechanical
# payoff so the bar feels like a place things happen, not a slot machine.
# Weights keep the overall odds close to the old flat 12% stat / 58% rep /
# 30% drunk split, just spread across flavor instead of one line per tier.
ROUND_ENCOUNTERS: list[dict] = [
    {
        "weight": 4,
        "kind": "stat",
        "stat": "attack",
        "intro": "A ganger at the next stool challenges you to synth-arm wrestling for bragging rights. You win, "
        "but something in your forearm pops on the last push.",
        "outcome": "+1 Attack, permanently.",
    },
    {
        "weight": 4,
        "kind": "stat",
        "stat": "tech",
        "intro": "A jittery netrunner two seats down rambles about ghosts haunting the local subnet, then face-plants "
        "into the bar. You slide his untouched synth-beer over and actually listen this time.",
        "outcome": "+1 Tech, permanently.",
    },
    {
        "weight": 4,
        "kind": "stat",
        "stat": "defense",
        "intro": "A grizzled old merc corners you about a firefight gone wrong twenty years back — where to plant your "
        "feet, when to actually block instead of hoping. Free lesson, no charge.",
        "outcome": "+1 Defense, permanently.",
    },
    {
        "weight": 4,
        "kind": "rep_scav",
        "intro": "A Scav's fingers brush your pocket mid-toast. You catch his wrist before the credits move an inch. "
        "He goes pale, then buys the whole bar a round to make it disappear.",
        "outcome": "+2 reputation.",
    },
    {
        "weight": 28,
        "kind": "rep",
        "intro": "Rin slides you a drink and leans in with the good stuff — who's hiring, who's hiding, who's already "
        "dead and doesn't know it yet.",
        "outcome": "+2 reputation.",
    },
    {
        "weight": 28,
        "kind": "rep",
        "intro": "You buy a round for a table of off-duty mercs. Turns out one of them owed you a favor from a job "
        "you don't even remember taking. Word gets around that you collect.",
        "outcome": "+2 reputation.",
    },
    {
        "weight": 14,
        "kind": "drunk",
        "intro": "You get loud, then sloppy, then horizontal on the noodle counter. Rin has you tossed out before "
        "you can order another.",
    },
    {
        "weight": 14,
        "kind": "drunk",
        "intro": "You challenge the jukebox to a staring contest and lose badly. Somewhere around round three you "
        "started singing. Rin is not letting you forget it.",
    },
]


def _resolve_round_encounter(character: Character) -> None:
    encounter = random.choices(ROUND_ENCOUNTERS, weights=[e["weight"] for e in ROUND_ENCOUNTERS], k=1)[0]
    console.print(f"\n[{TEXT_DIM}]{encounter['intro']}[/{TEXT_DIM}]")

    if encounter["kind"] == "stat":
        stat_key = encounter["stat"]
        setattr(character, stat_key, getattr(character, stat_key) + 1)
        message = f"[{ACCENT}]{encounter['outcome']}[/{ACCENT}]"
        if stat_key == "attack" and random.random() < 0.10:
            character.hp = max(1, character.hp - 5)
            message += f" [{DANGER}]The wire you pulled doesn't stop stinging — 5 damage.[/{DANGER}]"
        console.print(message)
    elif encounter["kind"] in ("rep", "rep_scav"):
        character.reputation += 2
        console.print(f"[{CREDITS}]{encounter['outcome']}[/{CREDITS}]")
    else:
        apply_effect(character, "drunk", 3)
        console.print(f"[{DANGER}]Drunk for the next few rounds.[/{DANGER}]")


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
    glitch_rule(console, style=TEXT_DIM)
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
            line = f"  [bold]{quest['title']}[/bold] — {step['description']}"
            if step["type"] == "coerce":
                line += (
                    f" [{WARNING}](Requires Charisma {step['min_charisma']}, have {character.charisma} — "
                    f"failing means a fight with {step['fail_enemy']})[/{WARNING}]"
                )
            console.print(line)

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
    table.add_column("Risk", style=WARNING)
    for i, quest in enumerate(open_quests, start=1):
        coerce_step = next((s for s in quest["steps"] if s["type"] == "coerce"), None)
        risk = (
            f"Coerce check: Charisma {coerce_step['min_charisma']}+, "
            f"or fight {coerce_step['fail_enemy']}"
            if coerce_step
            else ""
        )
        table.add_row(str(i), quest["title"], quest["hook"], risk)
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

    # A quest that opens on a "fetch" step might already be satisfied —
    # a player who bought the target item before ever taking the contract
    # shouldn't have to sell it and buy it back to make it "count."
    for result in check_fetch_steps(character):
        print_quest_result(console, character, result)


def _check_deliver_and_pay(character: Character, location: str) -> None:
    """Check for an active "deliver" or "pay" step targeting this location
    and, if the player can actually satisfy it right now, confirm before
    acting on it — unlike "talk"/"kill", both hand over something real
    (an equipped item, a chunk of credits), so this doesn't silently
    auto-advance the way notify_step does. Called from the same location
    visits that already call notify_step(character, "talk", location)."""
    deliver = pending_deliver_step(character, location)
    if deliver is not None:
        quest_id, step = deliver
        quest = get_quest(quest_id)
        item_id = step["item"]
        if item_id not in character.cyberware.values():
            item = get_item(item_id)
            console.print(
                f"\n[{TEXT_DIM}]{quest['title']}: you don't have a {item['name']} on you yet — "
                f"buy one from Hyphen8d's Hut first.[/{TEXT_DIM}]"
            )
        else:
            item = get_item(item_id)
            confirm = hotkey_prompt(
                console,
                [("Y", "Yes"), ("N", "No")],
                prompt=f"Hand over your {item['name']} to complete '{quest['title']}'?",
            )
            if confirm == "Y":
                give_away(character, item["slot"])
                completed_quest = advance_quest(character, quest_id)
                if completed_quest is not None:
                    print_quest_result(console, character, {"quest": completed_quest, "completed": True})
                else:
                    print_quest_result(
                        console,
                        character,
                        {"quest": quest, "completed": False, "next_step": current_step(character, quest_id)},
                    )

    pay = pending_pay_step(character, location)
    if pay is not None:
        quest_id, step = pay
        quest = get_quest(quest_id)
        amount = step["amount"]
        if character.credits < amount:
            shortfall = amount - character.credits
            console.print(
                f"\n[{TEXT_DIM}]{quest['title']}: you need {format_credits(shortfall)} more to pay this off "
                f"({amount} total).[/{TEXT_DIM}]"
            )
        else:
            confirm = hotkey_prompt(
                console,
                [("Y", "Yes"), ("N", "No")],
                prompt=f"Pay off {format_credits(amount)} to complete '{quest['title']}'?",
            )
            if confirm == "Y":
                character.credits -= amount
                completed_quest = advance_quest(character, quest_id)
                if completed_quest is not None:
                    print_quest_result(console, character, {"quest": completed_quest, "completed": True})
                else:
                    print_quest_result(
                        console,
                        character,
                        {"quest": quest, "completed": False, "next_step": current_step(character, quest_id)},
                    )


def _check_coerce_step(character: Character, location: str) -> None:
    """Check for an active "coerce" step targeting this location and, if
    found, offer the Charisma-gated attempt — modeled on
    _check_deliver_and_pay: a real, consequential choice needs a
    confirmation, not a silent auto-advance from notify_step. Meeting the
    Charisma requirement advances the quest outright; falling short drops
    the target's guard and triggers a fight against the step's fail_enemy
    instead — winning that fight gets the job done the hard way and still
    advances the quest, losing just costs the usual trauma bill and leaves
    the step pending for another attempt."""
    coerce = pending_coerce_step(character, location)
    if coerce is None:
        return
    quest_id, step = coerce
    quest = get_quest(quest_id)
    min_charisma = step["min_charisma"]

    confirm = hotkey_prompt(
        console,
        [("Y", "Yes"), ("N", "No")],
        prompt=f"Attempt to coerce the target? (Requires Charisma {min_charisma}) — '{quest['title']}'",
    )
    if confirm != "Y":
        return

    if character.charisma >= min_charisma:
        console.print(f"\n[{ACCENT}]Your words land clean.[/{ACCENT}] They hand it over without another word.")
        completed_quest = advance_quest(character, quest_id)
        if completed_quest is not None:
            print_quest_result(console, character, {"quest": completed_quest, "completed": True})
        else:
            print_quest_result(
                console,
                character,
                {"quest": quest, "completed": False, "next_step": current_step(character, quest_id)},
            )
        return

    console.print(
        f"\n[{DANGER}]Your charm falls flat.[/{DANGER}] The words come out wrong, and things turn violent fast."
    )
    enemy = get_enemy_by_name(step["fail_enemy"])
    won = run_combat(character, dict(enemy))
    if won:
        console.print(f"[{TEXT_DIM}]Not the smooth way, but the job's done — you walk away with it regardless.[/{TEXT_DIM}]")
        completed_quest = advance_quest(character, quest_id)
        if completed_quest is not None:
            print_quest_result(console, character, {"quest": completed_quest, "completed": True})
        else:
            print_quest_result(
                console,
                character,
                {"quest": quest, "completed": False, "next_step": current_step(character, quest_id)},
            )
    else:
        console.print(f"[{TEXT_DIM}]No dice this time — the contract's still open if you want another shot.[/{TEXT_DIM}]")


def visit_fixer_board(character: Character) -> None:
    print_arrival(character, "Fixer Board")

    for result in notify_step(character, "talk", "Fixer Board"):
        print_quest_result(console, character, result)
    _check_deliver_and_pay(character, "Fixer Board")

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
    glitch_rule(console, style=TEXT_DIM)
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
        cost_text = (
            format_credits(price)
            if price == item["cost"]
            else f"[{CREDITS}]{format_credits(price)}[/{CREDITS}] [{TEXT_DIM}]({format_credits(item['cost'])})[/{TEXT_DIM}]"
        )
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
    console.print(f"\n[{INFO}]Credits on hand:[/{INFO}] [{CREDITS}]{format_credits(character.credits)}[/{CREDITS}]")
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
        f"(+{item['bonus']} {item['stat']}) for {format_credits(price)}."
    )

    for result in check_fetch_steps(character):
        print_quest_result(console, character, result)
    check_achievements(character, console)


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

    glitch_title_rule(console, f"[{RARE}]Black Market[/{RARE}]")
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
    check_achievements(character, console)


def _visit_street_stash(character: Character) -> None:
    if not street_modded_unlocked(character):
        console.print(
            f"\n[{TEXT_DIM}]Hyphen8d shrugs. \"Got some Street-Modded gear under the counter, "
            f"but that's earned, not bought. Put in the work against the gangs first.\"[/{TEXT_DIM}]"
        )
        return

    catalog = load_street_modded()

    glitch_title_rule(console, f"[{ACCENT}]Hyphen8d's Stash[/{ACCENT}]")
    console.print(
        f"[{TEXT_DIM}]Hyphen8d reaches under the counter without being asked. \"You've earned this, choom. "
        f"Gang crews stopped sending people my way after what you did to their guys.\"[/{TEXT_DIM}]\n"
    )

    table = Table(border_style=BORDER_ACCENT, box=box.DOUBLE)
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
        prompt="Buy which piece? (0 to cancel)",
    )
    if choice == "0":
        return

    item = catalog[int(choice) - 1]
    old_id = character.cyberware[item["slot"]]
    old_item = get_item(old_id) if old_id else None
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
        f"(+{item['bonus']} {item['stat']}) for {format_credits(price)}."
    )


def visit_hyphen8ds_hut(character: Character) -> None:
    print_arrival(character, "Hyphen8d's Hut")

    for result in notify_step(character, "talk", "Hyphen8d's Hut"):
        print_quest_result(console, character, result)
    _check_deliver_and_pay(character, "Hyphen8d's Hut")

    print_menu_divider("Shop Menu")
    if not character.market_stock:
        roll_daily_market(character)

    right_panel = _station_data_panel(
        "SHOP STATUS",
        [("Today's Event", describe_market_modifier(character))],
    )
    _interaction_deck(npc_at("Hyphen8d's Hut"), right_panel, character)
    glitch_rule(console, style=TEXT_DIM)

    catalog = get_daily_catalog(character)
    _print_shop_dashboard(character, catalog)

    # The Black Market ([M]) and Hyphen8d's Street-Modded stash ([K]) are
    # hidden options — deliberately left off the printed menu text. The
    # Black Market is only worth anything once a player has found a
    # Quantum Core; the stash only opens once Hyphen8d respects your body
    # count against the Street Gangs (see street_modded_unlocked).
    visible = [("B", "Buy"), ("S", "Sell"), ("L", "Leave")]
    menu_text = OPTION_SEPARATOR.join(hotkey_bracket(key, label) for key, label in visible)
    action = read_choice(console, [key for key, _ in visible] + ["M", "K"], prompt=menu_text)
    glitch_rule(console, style=TEXT_DIM)
    if action == "B":
        _buy_cyberware(character, catalog)
    elif action == "S":
        _sell_cyberware(character)
    elif action == "M":
        _visit_black_market(character)
    elif action == "K":
        _visit_street_stash(character)


def _print_datashard(shard: dict) -> None:
    """Render one Datashard as a corrupted terminal readout — a noise band
    of DIVIDER_STATIC glyphs, a fake signal-diagnostics line, and the lore
    text itself, framed in a jagged HEAVY box instead of the game's usual
    soft ROUNDED panels so it visually reads as recovered data, not a
    normal UI screen."""
    noise = DIVIDER_STATIC * 12
    integrity = random.randint(22, 68)
    body = Group(
        Text.from_markup(f"[{WARNING}]{noise}[/{WARNING}]"),
        Text.from_markup(
            f"[{TEXT_DIM}]SIGNAL INTEGRITY: {integrity}%  //  RECOVERY: PARTIAL  //  SOURCE: UNKNOWN[/{TEXT_DIM}]"
        ),
        Text.from_markup(f"[{WARNING}]{noise}[/{WARNING}]"),
        Text(""),
        Text.from_markup(f"[italic {TEXT_PLAIN}]{shard['text']}[/italic {TEXT_PLAIN}]"),
    )
    console.print(
        Panel(
            body,
            title=f"[{RARE}]:: DATASHARD // {shard['title']} ::[/{RARE}]",
            border_style=ALERT,
            box=box.HEAVY,
            padding=(1, 3),
        )
    )
    press_any_key(console, "[SYS] DECRYPTION BUFFER FLUSHED // PRESS ANY KEY_")


def visit_archives(character: Character) -> None:
    print_menu_divider("Data Archive")
    all_shards = load_datashards()
    console.print(
        f"[{TEXT_DIM}]Fragments recovered: {len(character.datashards)}/{len(all_shards)}[/{TEXT_DIM}]\n"
    )

    if not character.datashards:
        console.print(
            f"[{TEXT_DIM}]No Datashards recovered yet. They turn up as rare finds on a clean Slice "
            f"Drop Box crack or a successful Hunt Cache sweep in the Undercity.[/{TEXT_DIM}]"
        )
        return

    shards = [get_datashard(shard_id) for shard_id in character.datashards]
    table = Table(border_style=BORDER_RARE, show_header=False, box=box.DOUBLE)
    table.add_column("#", justify="right", style=LABEL)
    table.add_column("Title", style=RARE)
    for i, shard in enumerate(shards, start=1):
        table.add_row(str(i), shard["title"])
    console.print(table)

    choice = read_choice(
        console,
        [str(i) for i in range(len(shards) + 1)],
        prompt="Read which fragment? (0 to cancel)",
    )
    if choice == "0":
        return
    _print_datashard(shards[int(choice) - 1])


def _themed_table(title: str) -> Table:
    # min_width keeps the title from wrapping onto two lines when the row
    # content is narrower than the title itself (e.g. a "Kills by Faction"
    # table with one short faction/count row).
    table = Table(
        title=f"[{ACCENT}]{title}[/{ACCENT}]",
        border_style=BORDER,
        show_header=False,
        min_width=len(title) + 2,
    )
    table.add_column("Label", style=ACCENT_SOFT)
    table.add_column("Value", style=TEXT)
    return table


def show_character_info(character: Character) -> None:
    console.print()
    glitch_title_rule(console, f"[{ACCENT}]{character.name}[/{ACCENT}] [{TEXT_DIM}]— {character.char_class}[/{TEXT_DIM}]")
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
    economy.add_row("Credits", format_credits(character.credits))
    economy.add_row("Banked", format_credits(character.banked_credits))
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

    lifetime = _themed_table("Lifetime Record")
    lifetime.add_row("Total Days", str(character.total_days))
    lifetime.add_row("Total Credits Earned", format_credits(character.total_credits_earned))
    lifetime.add_row("Total Fights Won", str(character.total_fights_won))

    achievements = _themed_table("Achievements")
    all_achievements = {a["id"]: a for a in load_achievements()}
    if character.achievements:
        for achievement_id in character.achievements:
            achievement = all_achievements.get(achievement_id)
            if achievement is None:
                continue
            achievements.add_row(f"[{RARE}]{achievement['name']}[/{RARE}]", achievement["description"])
    else:
        achievements.add_row("None unlocked yet", "")

    grid = Table.grid(padding=(0, 2))
    grid.add_column()
    grid.add_column()
    grid.add_row(attributes, economy)
    grid.add_row(contracts, loadout)
    grid.add_row(effects, inventory)
    grid.add_row(abilities, lifetime)
    grid.add_row(achievements, Table.grid())
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
    character.total_days += 1
    hot = hot_factions(character)
    reset_daily_kills(character)
    # Roll and store today's City Conditions before the market roll, so a
    # market_surge/market_discount headline can actually steer
    # roll_daily_market's event instead of the two rolling independently.
    character.current_weather = roll_weather()
    character.current_headline = roll_headline()
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
        encounter = roll_combat_encounter(character, faction=faction)
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

    # City Conditions read as an ambient news ticker, not a stat row — kept
    # visually separate from the character stats below instead of sharing
    # the same label/value table (previously every row, flavor and stats
    # alike, rendered in the same cyan-label style and blurred together).
    conditions = Text.from_markup(
        f"[{TEXT_DIM} italic]{character.current_weather['text']}[/{TEXT_DIM} italic]\n"
        f"[{TEXT_DIM} italic]{character.current_headline['text']}[/{TEXT_DIM} italic]"
    )

    standing = _themed_table("Standing")
    standing.add_row("Level", str(character.level))
    standing.add_row("Credits", format_credits(character.credits))
    standing.add_row("Banked", format_credits(character.banked_credits))
    standing.add_row("Reputation", str(character.reputation))

    overnight = _themed_table("Overnight Report")
    overnight.add_row("HP", f"Fully restored (+{healed})" if healed > 0 else "Already full")
    if ambushed:
        overnight.add_row("HP now", f"{character.hp}/{character.max_hp}")
    overnight.add_row("Effects cleared", str(cured))
    overnight.add_row("Heat", heat_text)

    kills = _themed_table("Kills by Faction")
    if faction_totals:
        for faction, count in sorted(faction_totals.items()):
            kills.add_row(faction, str(count))
    else:
        kills.add_row("No kills yet", "")

    grid = Table.grid(padding=(0, 2))
    grid.add_column()
    grid.add_column()
    grid.add_column()
    grid.add_row(standing, overnight, kills)

    market_note = Text.from_markup(f"[{ACCENT_SOFT}]Hyphen8d's Hut:[/{ACCENT_SOFT}] [{TEXT_DIM}]{describe_market_modifier(character)}[/{TEXT_DIM}]")

    body = Group(conditions, Text(""), grid, Text(""), market_note)

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
        choice = read_choice(
            console, [*LOCATION_HOTKEYS.keys(), "I", "A", "L", "?"], prompt="meridianOS v2.5 // SELECT ROUTING:"
        )
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
            press_any_key(console, "[SYS] UPLINK IDLE // PRESS ANY KEY TO RETURN_")
            continue
        if choice == "I":
            show_character_info(character)
            press_any_key(console, "[SYS] UPLINK IDLE // PRESS ANY KEY TO RETURN_")
            continue
        if choice == "A":
            visit_archives(character)
            press_any_key(console, "[SYS] UPLINK IDLE // PRESS ANY KEY TO RETURN_")
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

        press_any_key(console, "[SYS] UPLINK IDLE // PRESS ANY KEY TO RETURN_")
