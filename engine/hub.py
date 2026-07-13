"""Hub menu / navigation between Neo Meridian locations."""

from __future__ import annotations

import random

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from engine.character import CYBERWARE_SLOTS, Character
from engine.combat import run_combat
from engine.encounters import roll_encounter
from engine.npcs import npc_at, random_line
from engine.quests import accept_quest, available_quests, current_step, get_quest, notify_step, print_quest_result
from engine.shop import buy_and_equip, get_item, load_cyberware, sell_back_value, unequip

console = Console()

# Location -> one-line flavor for the hub menu table. Real content (rest,
# shop, combat, etc.) is wired up location by location in later phases.
LOCATIONS: dict[str, str] = {
    "Chrome Noodle Bar": "Rest, heal, and hear rumors over synth-noodles and static pop.",
    "Undercity": "Random encounters — gang fights, scavenger loot, drone ambushes.",
    "NetVault": "Deposit and withdraw credits, safe from death-loss.",
    "Chop Shop": "Buy and sell gear and cyberware.",
    "Doc Wire's Clinic": "Heal HP for credits, cure status effects.",
    "The Dojo": "Train stats, learn new abilities.",
    "The Pit": "PvE gladiator fights for reputation and credits.",
    "Fixer Board": "Leaderboard and posted contracts/quests.",
}

# Location -> longer arrival description, shown when you actually step
# into the place (as opposed to the short blurb in the hub menu table).
LOCATION_DESCRIPTIONS: dict[str, str] = {
    "Chrome Noodle Bar": (
        "Steam curls off the noodle vats under a buzzing pink sign. Synth pop "
        "bleeds from a cracked speaker, and every stool's got a story nobody's "
        "telling straight."
    ),
    "Undercity": (
        "Sublevel streets, sodium light dying orange through the smog. Water "
        "drips from a hundred unseen pipes. Something always seems to be "
        "watching from the dark."
    ),
    "NetVault": (
        "Chrome and glass, cold as a server room because it is one. "
        "Biometric scanners hum behind a counter that's seen a thousand "
        "transactions and trusts none of them."
    ),
    "Chop Shop": (
        "Wires hang from the ceiling like vines. Half-built limbs sit in "
        "bins marked in a shorthand only the shop understands. Smells like "
        "solder and ozone."
    ),
    "Doc Wire's Clinic": (
        "A converted shipping container wired for surgery. Trauma gurneys, "
        "mismatched monitors, and a fridge that's definitely not for food."
    ),
    "The Dojo": (
        "Bare concrete, scorch marks on the walls, a ring of cracked "
        "mirrors. Somewhere a heavy bag swings on its own, still recovering "
        "from the last session."
    ),
    "The Pit": (
        "A sunken arena ringed by chain-link and floodlights, a chanting "
        "crowd lost in the dark beyond. The sand's stained in ways bleach "
        "won't fix."
    ),
    "Fixer Board": (
        "A cracked terminal bolted to a brick wall, scrolling contracts in "
        "glitchy green text. Torn paper flyers underneath it, decades out "
        "of date."
    ),
}


def print_status(character: Character) -> None:
    console.print(
        f"[bright_cyan]{character.name}[/bright_cyan] "
        f"[dim](Lvl {character.level} {character.char_class})[/dim]   "
        f"HP [bold]{character.hp}/{character.max_hp}[/bold]   "
        f"Credits [bold yellow]{character.credits}[/bold yellow]"
    )


def print_hub_menu(character: Character, location_names: list[str]) -> None:
    console.rule("[bright_magenta]Neo Meridian[/bright_magenta]")
    print_status(character)
    console.print()
    table = Table(border_style="bright_cyan", show_header=False)
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Location", style="bold white")
    table.add_column("Description", style="dim")
    for i, name in enumerate(location_names, start=1):
        table.add_row(str(i), name, LOCATIONS[name])
    table.add_row("0", "Leave", "Head home and save your progress.")
    console.print(table)


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


def visit_undercity(character: Character) -> None:
    print_arrival("Undercity")
    encounter = roll_encounter()
    console.print(f"[dim]{encounter['intro']}[/dim]")

    if encounter["type"] == "combat":
        run_combat(character, encounter["enemy"])
    elif encounter["type"] == "loot":
        low, high = encounter["credits"]
        amount = random.randint(low, high)
        character.credits += amount
        console.print(f"[bold yellow]+{amount} credits.[/bold yellow]")
    # "nothing" encounters just print their flavor line above.


def visit_location(character: Character, location: str) -> None:
    print_arrival(location)

    for result in notify_step(character, "talk", location):
        print_quest_result(console, result)

    npc = npc_at(location)
    if npc is None:
        console.print("[dim](nothing to do here yet — coming in a later phase)[/dim]")
        return

    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")


def visit_fixer_board(character: Character) -> None:
    print_arrival("Fixer Board")

    for result in notify_step(character, "talk", "Fixer Board"):
        print_quest_result(console, result)

    npc = npc_at("Fixer Board")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    active_ids = list(character.active_quests.keys())
    if active_ids:
        console.print("\n[bright_magenta]Active contracts:[/bright_magenta]")
        for quest_id in active_ids:
            quest = get_quest(quest_id)
            step = current_step(character, quest_id)
            console.print(f"  [bold]{quest['title']}[/bold] — {step['description']}")

    open_quests = available_quests(character)
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

    choice = Prompt.ask(
        "Take a contract? (0 to skip)",
        choices=[str(i) for i in range(len(open_quests) + 1)],
        show_choices=False,
    )
    if choice == "0":
        return

    chosen_quest = open_quests[int(choice) - 1]
    accept_quest(character, chosen_quest["id"])
    console.print(f"\n[bold bright_magenta]Contract accepted:[/bold bright_magenta] {chosen_quest['title']}")
    console.print(f"  {chosen_quest['steps'][0]['description']}")


def print_loadout(character: Character) -> None:
    console.print("\n[bright_magenta]Your chrome:[/bright_magenta]")
    table = Table(border_style="bright_cyan", show_header=False)
    table.add_column("Slot", style="bold white")
    table.add_column("Installed", style="dim")
    for slot in CYBERWARE_SLOTS:
        item_id = character.cyberware[slot]
        installed = get_item(item_id)["name"] if item_id else "-- empty --"
        table.add_row(slot.capitalize(), installed)
    console.print(table)


def print_catalog(catalog: list[dict]) -> None:
    console.print("\n[bright_magenta]For sale:[/bright_magenta]")
    table = Table(border_style="bright_cyan")
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Item", style="bold white")
    table.add_column("Slot")
    table.add_column("Bonus")
    table.add_column("Cost", justify="right")
    table.add_column("Flavor", style="dim")
    for i, item in enumerate(catalog, start=1):
        table.add_row(
            str(i),
            item["name"],
            item["slot"].capitalize(),
            f"+{item['bonus']} {item['stat']}",
            str(item["cost"]),
            item["flavor"],
        )
    console.print(table)


def _buy_cyberware(character: Character) -> None:
    catalog = load_cyberware()
    print_catalog(catalog)

    choice = Prompt.ask(
        "Buy which item? (0 to cancel)",
        choices=[str(i) for i in range(len(catalog) + 1)],
        show_choices=False,
    )
    if choice == "0":
        return

    item = catalog[int(choice) - 1]
    old_id = character.cyberware[item["slot"]]
    trade_in = sell_back_value(get_item(old_id)) if old_id else 0
    if character.credits + trade_in < item["cost"]:
        console.print("[red]Not enough credits for that, even with a trade-in.[/red]")
        return

    buy_and_equip(character, item["id"])
    if old_id:
        console.print(f"[dim]{get_item(old_id)['name']} pulled and sold back for parts.[/dim]")
    console.print(
        f"[bold bright_magenta]Installed:[/bold bright_magenta] {item['name']} "
        f"(+{item['bonus']} {item['stat']})"
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

    choice = Prompt.ask(
        "Sell which item? (0 to cancel)",
        choices=[str(i) for i in range(len(equipped_slots) + 1)],
        show_choices=False,
    )
    if choice == "0":
        return

    slot = equipped_slots[int(choice) - 1]
    item = unequip(character, slot)
    console.print(f"[bold yellow]{item['name']} sold for {sell_back_value(item)} credits.[/bold yellow]")


def visit_chop_shop(character: Character) -> None:
    print_arrival("Chop Shop")

    npc = npc_at("Chop Shop")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    print_loadout(character)

    action = Prompt.ask("[1] Buy  [2] Sell  [0] Leave", choices=["0", "1", "2"], show_choices=False)
    if action == "1":
        _buy_cyberware(character)
    elif action == "2":
        _sell_cyberware(character)


def enter_hub(character: Character) -> None:
    location_names = list(LOCATIONS.keys())
    while True:
        console.print()
        print_hub_menu(character, location_names)
        choice = Prompt.ask(
            "Where to?",
            choices=[str(i) for i in range(len(location_names) + 1)],
            show_choices=False,
        )
        if choice == "0":
            console.print("[dim]You head back, credits and gear safe... for now.[/dim]")
            return

        chosen = location_names[int(choice) - 1]

        if chosen == "Undercity":
            visit_undercity(character)
        elif chosen == "Fixer Board":
            visit_fixer_board(character)
        elif chosen == "Chop Shop":
            visit_chop_shop(character)
        else:
            visit_location(character, chosen)
