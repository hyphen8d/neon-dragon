"""Hub menu / navigation between Neo Meridian locations."""

from __future__ import annotations

import random

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from engine.character import Character
from engine.combat import run_combat
from engine.encounters import roll_encounter
from engine.npcs import npc_at, random_line

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

    npc = npc_at(location)
    if npc is None:
        console.print("[dim](nothing to do here yet — coming in a later phase)[/dim]")
        return

    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")


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
        else:
            visit_location(character, chosen)
