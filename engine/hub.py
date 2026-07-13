"""Hub menu / navigation between Neo Meridian locations."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from engine.character import Character

console = Console()

# Location -> one-line flavor. Real content (rest, shop, combat, etc.)
# is wired up location by location in later phases.
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
        console.print(f"\n[bright_magenta]{chosen}[/bright_magenta] — [dim]{LOCATIONS[chosen]}[/dim]")
        console.print("[dim](nothing to do here yet — coming in a later phase)[/dim]")
