"""Hub menu / navigation between Neo Meridian locations."""

from __future__ import annotations

import random

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.table import Table

from engine.bestiary import enemy_faction
from engine.character import CYBERWARE_SLOTS, Character, hp_style
from engine.combat import run_combat
from engine.encounters import roll_combat_encounter, roll_scavenge_encounter
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
from engine.shop import buy_and_equip, discounted_cost, get_item, load_cyberware, sell_back_value, unequip
from engine.status_effects import EFFECT_LABELS, apply_effect, cure_all
from engine.ui import hotkey_bracket, hotkey_prompt, read_choice

console = Console(highlight=False)

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


def print_status(character: Character) -> None:
    style = hp_style(character.hp, character.max_hp)
    console.print(
        f"[bright_cyan]{character.name}[/bright_cyan] "
        f"[dim](Lvl {character.level} {character.char_class})[/dim]   "
        f"HP [{style}]{character.hp}/{character.max_hp}[/{style}]   "
        f"Credits [bold yellow]{character.credits}[/bold yellow]   "
        f"Banked [bold yellow]{character.banked_credits}[/bold yellow]"
    )


def print_hub_menu(character: Character) -> None:
    console.rule("[bright_magenta]Neo Meridian[/bright_magenta]")
    print_status(character)
    console.print()

    locations = Table(
        title="[bold bright_magenta]Locations[/bold bright_magenta]",
        border_style="bright_cyan",
        show_header=False,
    )
    locations.add_column("Location", style="bold white")
    locations.add_column("Description", style="dim")
    for key, name in LOCATION_HOTKEYS.items():
        locations.add_row(hotkey_bracket(key, name), LOCATIONS[name])
    console.print(locations)

    actions = Table(
        title="[bold bright_magenta]Actions[/bold bright_magenta]",
        border_style="bright_cyan",
        show_header=False,
    )
    actions.add_column("Action", style="bold white")
    actions.add_column("Description", style="dim")
    actions.add_row(hotkey_bracket("I", "Character Info"), "View your full stats, gear, contracts, and kills.")
    actions.add_row("[bold bright_magenta][?][/bold bright_magenta] Help", "Open the player guide.")
    actions.add_row(hotkey_bracket("L", "Leave"), "Head home and save your progress.")
    console.print(actions)


def print_arrival(location: str) -> None:
    console.print()
    console.print(
        Panel(
            LOCATION_DESCRIPTIONS[location],
            title=f"[bold bright_magenta]{location}[/bold bright_magenta]",
            border_style="bright_cyan",
            padding=(0, 2),
        )
    )


def print_menu_divider(label: str) -> None:
    """Visually separate in-character scene/dialogue above from the
    out-of-character menu/mechanics below."""
    console.print()
    console.rule(f"[dim]{label}[/dim]", style="dim")


JACK_IN_BASE_CHANCE = 0.30
JACK_IN_TECH_SCALING = 0.04
JACK_IN_MAX_CHANCE = 0.85
JACK_IN_CREDIT_RANGE = (15, 35)


def _jack_in(character: Character) -> None:
    console.print("[dim]You slot in, feel the local net grid light up around you.[/dim]")
    chance = min(JACK_IN_MAX_CHANCE, JACK_IN_BASE_CHANCE + character.tech * JACK_IN_TECH_SCALING)
    if random.random() < chance:
        low, high = JACK_IN_CREDIT_RANGE
        amount = random.randint(low, high) + character.tech // 2
        character.credits += amount
        console.print(f"[bold bright_magenta]Clean in, clean out.[/bold bright_magenta] +{amount} credits.")
        return

    console.print("[red]Something pings back. You've been traced.[/red]")
    encounter = roll_combat_encounter(character.level, faction="Corp")
    console.print(f"[dim]{encounter['intro']}[/dim]")
    run_combat(character, encounter["enemy"])


def _find_a_fight(character: Character) -> None:
    encounter = roll_combat_encounter(character.level)
    console.print(f"[dim]{encounter['intro']}[/dim]")
    run_combat(character, encounter["enemy"])


def _scavenge(character: Character) -> None:
    encounter = roll_scavenge_encounter(character.level)
    console.print(f"[dim]{encounter['intro']}[/dim]")
    if encounter["type"] == "loot":
        low, high = encounter["credits"]
        amount = random.randint(low, high)
        character.credits += amount
        console.print(f"\n[bold bright_magenta]Score![/bold bright_magenta] +{amount} credits.")
    # "nothing" encounters just print their flavor line above.


def visit_undercity(character: Character) -> None:
    print_arrival("Undercity")

    print_menu_divider("The Streets")
    choice = hotkey_prompt(
        console,
        [
            ("J", "Jack in (steal credits, risk a trace)"),
            ("F", "Find a fight"),
            ("S", "Scavenge"),
            ("L", "Leave"),
        ],
    )
    if choice == "J":
        _jack_in(character)
    elif choice == "F":
        _find_a_fight(character)
    elif choice == "S":
        _scavenge(character)


def _deposit(character: Character) -> None:
    if character.credits <= 0:
        console.print("[dim]Nothing on hand to deposit.[/dim]")
        return
    amount = IntPrompt.ask(f"Deposit how much? (0 to cancel, up to {character.credits})")
    if amount <= 0:
        return
    if amount > character.credits:
        console.print("[red]You don't have that much on hand.[/red]")
        return
    character.credits -= amount
    character.banked_credits += amount
    console.print(f"[bold yellow]{amount} credits deposited.[/bold yellow] Banked: {character.banked_credits}")


def _withdraw(character: Character) -> None:
    if character.banked_credits <= 0:
        console.print("[dim]Nothing banked to withdraw.[/dim]")
        return
    amount = IntPrompt.ask(f"Withdraw how much? (0 to cancel, up to {character.banked_credits})")
    if amount <= 0:
        return
    if amount > character.banked_credits:
        console.print("[red]You don't have that much banked.[/red]")
        return
    character.banked_credits -= amount
    character.credits += amount
    console.print(f"[bold yellow]{amount} credits withdrawn.[/bold yellow] On hand: {character.credits}")


def visit_netvault(character: Character) -> None:
    print_arrival("NetVault")

    npc = npc_at("NetVault")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    print_menu_divider("Banking")
    for result in notify_step(character, "talk", "NetVault"):
        print_quest_result(console, character, result)

    console.print(
        f"On hand: [bold yellow]{character.credits}[/bold yellow]   "
        f"Banked: [bold yellow]{character.banked_credits}[/bold yellow] [dim](safe from death-loss)[/dim]"
    )

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
        console.print("[dim]You're already at full health.[/dim]")
        return

    max_affordable = min(missing, character.credits // HEAL_COST_PER_HP)
    if max_affordable <= 0:
        console.print("[red]You can't afford so much as a bandage right now.[/red]")
        return

    amount = IntPrompt.ask(f"Heal how much HP? (0 to cancel, up to {max_affordable})")
    if amount <= 0:
        return
    if amount > max_affordable:
        console.print("[red]You can't afford that much healing.[/red]")
        return

    cost = amount * HEAL_COST_PER_HP
    character.hp += amount
    character.credits -= cost
    console.print(
        f"[bold bright_magenta]Patched up.[/bold bright_magenta] "
        f"HP {character.hp}/{character.max_hp}. -{cost} credits."
    )


def _buy_supplies(character: Character) -> None:
    catalog = load_usable_items()

    table = Table(border_style="bright_cyan")
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Item", style="bold white")
    table.add_column("Effect")
    table.add_column("Cost", justify="right")
    table.add_column("Description", style="dim")
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
        console.print("[red]Not enough credits for that.[/red]")
        return

    buy_item(character, item["id"])
    console.print(f"[bold bright_magenta]Bought:[/bold bright_magenta] {item['name']}. -{item['cost']} credits.")


def _cure(character: Character) -> None:
    if not character.status_effects:
        console.print("[dim]No status effects to clear.[/dim]")
        return

    action = hotkey_prompt(
        console, [("Y", "Yes"), ("N", "No")], prompt=f"Clear those for {CURE_COST} credits?"
    )
    if action != "Y":
        return
    if character.credits < CURE_COST:
        console.print("[red]Not enough credits for that.[/red]")
        return

    character.credits -= CURE_COST
    cured = cure_all(character)
    console.print(f"[bold bright_magenta]Cleared {cured} status effect(s).[/bold bright_magenta] -{CURE_COST} credits.")


def visit_doc_wires_clinic(character: Character) -> None:
    print_arrival("Doc Wire's Clinic")

    npc = npc_at("Doc Wire's Clinic")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    print_menu_divider("Clinic Menu")
    for result in notify_step(character, "talk", "Doc Wire's Clinic"):
        print_quest_result(console, character, result)

    console.print(
        f"HP: [bold]{character.hp}/{character.max_hp}[/bold]   "
        f"Patch-up rate: {HEAL_COST_PER_HP} credits/HP   "
        f"Cure rate: {CURE_COST} credits flat"
    )
    if character.status_effects:
        labels = ", ".join(EFFECT_LABELS.get(e, e) for e in character.status_effects)
        console.print(f"[yellow]Active effects:[/yellow] {labels}")

    action = hotkey_prompt(
        console,
        [("H", "Heal"), ("C", "Cure Effects"), ("B", "Buy Supplies"), ("L", "Leave")],
    )
    if action == "H":
        _heal(character)
    elif action == "C":
        _cure(character)
    elif action == "B":
        _buy_supplies(character)


TRAIN_BASE_COST = 40
TRAIN_SURCHARGE_PER_POINT = 5

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
    print_arrival("RoboDOJO")
    console.print("[dim]A training drone powers up, servos whirring, waiting for you to pick a discipline.[/dim]")

    print_menu_divider("Training")
    table = Table(border_style="bright_cyan", show_header=False)
    table.add_column("Stat", style="bold white")
    table.add_column("Current", justify="right")
    table.add_column("Next +1 costs", justify="right")
    for key, (attr, label) in TRAINABLE_STATS.items():
        current = getattr(character, attr)
        table.add_row(hotkey_bracket(key, label), str(current), str(_train_cost(current)))
    console.print(table)

    choice = hotkey_prompt(
        console,
        [(k, label) for k, (_, label) in TRAINABLE_STATS.items()] + [("L", "Leave")],
        prompt="Train which stat?",
    )
    if choice == "L":
        return

    attr, label = TRAINABLE_STATS[choice]
    cost = _train_cost(getattr(character, attr))
    if character.credits < cost:
        console.print("[red]Not enough credits to train right now.[/red]")
        return

    console.print(f"[dim]{SPARRING_FLAVOR[attr]}[/dim]")
    character.credits -= cost
    setattr(character, attr, getattr(character, attr) + 1)
    console.print(
        f"[bold bright_magenta]{label} increased to {getattr(character, attr)}.[/bold bright_magenta] "
        f"-{cost} credits."
    )


def visit_the_pit(character: Character) -> None:
    print_arrival("The Pit")
    console.print("[dim]The crowd wants blood. Pick your match.[/dim]")

    print_menu_divider("The Ring")
    gladiators = load_gladiators()
    table = Table(border_style="bright_cyan")
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Gladiator", style="bold white")
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
    console.print(f"\n[dim]{gladiator['intro']}[/dim]")
    enemy_data = {k: v for k, v in gladiator.items() if k not in ("id", "intro")}
    run_combat(character, enemy_data)


REST_THRESHOLD = 0.5  # free rest tops you up to this fraction of max HP, no further


def visit_chrome_noodle_bar(character: Character) -> None:
    print_arrival("Chrome Noodle Bar")

    npc = npc_at("Chrome Noodle Bar")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    for result in notify_step(character, "talk", "Chrome Noodle Bar"):
        print_quest_result(console, character, result)

    rest_floor = int(character.max_hp * REST_THRESHOLD)
    if character.hp >= rest_floor:
        console.print("\n[dim]You're rested enough already. No need to linger.[/dim]")
    else:
        healed = rest_floor - character.hp
        character.hp = rest_floor
        console.print(
            f"\n[bold bright_magenta]You crash in a booth for a while, noodles going cold.[/bold bright_magenta] "
            f"+{healed} HP, on the house."
        )

    console.print()
    choice = hotkey_prompt(
        console,
        [("B", "Buy a round"), ("C", "Check the shady booth in the back"), ("L", "Leave")],
    )
    if choice == "B":
        _buy_a_round(character)
    elif choice == "C":
        _visit_endr3am(character)


BUY_ROUND_COST = 25


def _buy_a_round(character: Character) -> None:
    if character.credits < BUY_ROUND_COST:
        console.print("\n[red]Can't even afford to buy yourself a drink right now.[/red]")
        return

    character.credits -= BUY_ROUND_COST
    console.print(f"\n[dim]You slap {BUY_ROUND_COST} credits on the bar. Rin pours.[/dim]")

    roll = random.random()
    if roll < 0.12:
        stat_key = random.choice(["attack", "defense", "tech"])
        setattr(character, stat_key, getattr(character, stat_key) + 1)
        console.print(
            f"[bold bright_magenta]Rin tells a story that actually sticks with you.[/bold bright_magenta] "
            f"+1 {stat_key.capitalize()}, permanently."
        )
    elif roll < 0.70:
        character.reputation += 2
        console.print("[bold yellow]Decent gossip tonight.[/bold yellow] +2 reputation.")
    else:
        apply_effect(character, "drunk", 3)
        console.print(
            "[red]You get loud, then sloppy, then horizontal. Rin has you tossed out "
            "before you can order another.[/red]"
        )


def _visit_endr3am(character: Character) -> None:
    print_menu_divider("Contract Board")
    broker = get_npc("endr3am")
    console.print(f"[bold cyan]{broker['name']}[/bold cyan] [dim]— {broker['bio']}[/dim]")
    console.print(f"  {random_line(broker)}")
    _browse_contract_board(character, "Chrome Noodle Bar")


def _browse_contract_board(character: Character, board: str) -> None:
    active_ids = [
        quest_id for quest_id in character.active_quests if get_quest(quest_id).get("board", "Fixer Board") == board
    ]
    if active_ids:
        console.print("\n[bright_magenta]Active contracts:[/bright_magenta]")
        for quest_id in active_ids:
            quest = get_quest(quest_id)
            step = current_step(character, quest_id)
            console.print(f"  [bold]{quest['title']}[/bold] — {step['description']}")

    locked = locked_quests(character, board)
    if locked:
        console.print("\n[dim]Locked contracts:[/dim]")
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
            console.print(f"  [dim]{quest['title']} — needs {', '.join(gaps)}[/dim]")

    open_quests = available_quests(character, board)
    if not open_quests:
        console.print("\n[dim]No new contracts posted right now.[/dim]")
        return

    console.print("\n[bright_magenta]Open contracts:[/bright_magenta]")
    table = Table(border_style="bright_cyan", show_header=False)
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Title", style="bold white")
    table.add_column("Hook", style="dim")
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
    console.print(f"\n[bold bright_magenta]Contract accepted:[/bold bright_magenta] {chosen_quest['title']}")
    console.print(f"  {chosen_quest['steps'][0]['description']}")


def visit_fixer_board(character: Character) -> None:
    print_arrival("Fixer Board")

    npc = npc_at("Fixer Board")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    print_menu_divider("Contract Board")
    for result in notify_step(character, "talk", "Fixer Board"):
        print_quest_result(console, character, result)
    _browse_contract_board(character, "Fixer Board")


def build_loadout_table(character: Character, title: str | None = None) -> Table:
    table = Table(title=title, border_style="bright_cyan", show_header=False)
    table.add_column("Slot", style="cyan")
    table.add_column("Installed", style="bold white")
    table.add_column("Special", style="yellow")
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


def print_loadout(character: Character) -> None:
    console.print("\n[bright_magenta]Your chrome:[/bright_magenta]")
    console.print(build_loadout_table(character))


def print_catalog(catalog: list[dict], character: Character) -> None:
    console.print("\n[bright_magenta]For sale:[/bright_magenta]")
    table = Table(border_style="bright_cyan")
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Item", style="bold white")
    table.add_column("Slot")
    table.add_column("Bonus")
    table.add_column("Special", style="yellow")
    table.add_column("Cost", justify="right")
    table.add_column("Description", style="dim")
    for i, item in enumerate(catalog, start=1):
        special = ""
        if item.get("inflict_effect"):
            label = EFFECT_LABELS.get(item["inflict_effect"], item["inflict_effect"])
            special = f"Causes {label}"
        price = discounted_cost(character, item)
        cost_text = str(price) if price == item["cost"] else f"[bold yellow]{price}[/bold yellow] [dim]({item['cost']})[/dim]"
        table.add_row(
            str(i),
            item["name"],
            item["slot"].capitalize(),
            f"+{item['bonus']} {item['stat']}",
            special,
            cost_text,
            item["flavor"],
        )
    console.print(table)


def _buy_cyberware(character: Character) -> None:
    catalog = load_cyberware()
    print_catalog(catalog, character)

    choice = read_choice(
        console,
        [str(i) for i in range(len(catalog) + 1)],
        prompt="Buy which item? (0 to cancel)",
    )
    if choice == "0":
        return

    item = catalog[int(choice) - 1]
    old_id = character.cyberware[item["slot"]]
    trade_in = sell_back_value(get_item(old_id)) if old_id else 0
    price = discounted_cost(character, item)
    if character.credits + trade_in < price:
        console.print("[red]Not enough credits for that, even with a trade-in.[/red]")
        return

    buy_and_equip(character, item["id"])
    if old_id:
        console.print(f"[dim]{get_item(old_id)['name']} pulled and sold back for parts.[/dim]")
    console.print(
        f"[bold bright_magenta]Installed:[/bold bright_magenta] {item['name']} "
        f"(+{item['bonus']} {item['stat']}) for {price} credits."
    )


def _sell_cyberware(character: Character) -> None:
    equipped_slots = [slot for slot in CYBERWARE_SLOTS if character.cyberware[slot]]
    if not equipped_slots:
        console.print("[dim]Nothing installed to sell.[/dim]")
        return

    table = Table(border_style="bright_cyan", show_header=False)
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Slot", style="bold white")
    table.add_column("Installed", style="dim")
    for i, slot in enumerate(equipped_slots, start=1):
        item = get_item(character.cyberware[slot])
        table.add_row(str(i), slot.capitalize(), f"{item['name']} (sells for {sell_back_value(item)})")
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
    console.print(f"[bold yellow]{item['name']} sold for {sell_back_value(item)} credits.[/bold yellow]")


def visit_hyphen8ds_hut(character: Character) -> None:
    print_arrival("Hyphen8d's Hut")

    npc = npc_at("Hyphen8d's Hut")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    print_menu_divider("Shop Menu")
    for result in notify_step(character, "talk", "Hyphen8d's Hut"):
        print_quest_result(console, character, result)

    print_loadout(character)

    action = hotkey_prompt(console, [("B", "Buy"), ("S", "Sell"), ("L", "Leave")])
    if action == "B":
        _buy_cyberware(character)
    elif action == "S":
        _sell_cyberware(character)


def _themed_table(title: str) -> Table:
    table = Table(title=f"[bold bright_magenta]{title}[/bold bright_magenta]", border_style="bright_cyan", show_header=False)
    table.add_column("Label", style="cyan")
    table.add_column("Value", style="bold white")
    return table


def show_character_info(character: Character) -> None:
    console.print()
    console.rule(f"[bold bright_magenta]{character.name}[/bold bright_magenta] [dim]— {character.char_class}[/dim]")
    console.print()

    attributes = _themed_table("Attributes")
    attributes.add_row("Level", str(character.level))
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

    contracts = _themed_table("Reputation & Contracts")
    contracts.add_row("Reputation", str(character.reputation))
    contracts.add_row("Contracts active", str(len(character.active_quests)))
    contracts.add_row("Contracts completed", str(len(character.completed_quests)))

    loadout = build_loadout_table(character, title="[bold bright_magenta]Chrome[/bold bright_magenta]")

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

    grid = Table.grid(padding=(0, 2))
    grid.add_column()
    grid.add_column()
    grid.add_row(attributes, economy)
    grid.add_row(contracts, loadout)
    grid.add_row(effects, inventory)
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


def enter_hub(character: Character) -> None:
    while True:
        console.print()
        print_hub_menu(character)
        choice = read_choice(console, [*LOCATION_HOTKEYS.keys(), "I", "L", "?"], prompt="Where to?")
        if choice == "L":
            console.print("[dim]You head back, credits and gear safe... for now.[/dim]")
            return
        if choice == "?":
            show_help(console)
            continue
        if choice == "I":
            show_character_info(character)
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
