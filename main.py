"""Neon Dragon — entry point and main menu loop."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from engine.character import CLASSES, Character
from engine.help import show_help
from engine.hub import enter_hub
from engine.save import list_saves, load_character, save_character, save_exists

console = Console()

TITLE = """[bold bright_magenta]N E O N   D R A G O N[/bold bright_magenta]
[cyan]// neo meridian, after dark //[/cyan]
[dim purple]rain on chrome, neon on wet asphalt[/dim purple]"""


def print_title() -> None:
    console.print(Panel.fit(TITLE, border_style="bright_cyan", padding=(1, 6)))


def print_main_menu() -> None:
    table = Table(border_style="bright_cyan", show_header=False)
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Action", style="bold white")
    table.add_row("1", "New Runner")
    table.add_row("2", "Load Runner")
    table.add_row("3", "Help")
    table.add_row("4", "Quit")
    console.print(table)


def print_character_sheet(character: Character) -> None:
    console.rule(f"[bold bright_magenta]{character.name}[/bold bright_magenta] [dim]— {character.char_class}[/dim]")
    table = Table(border_style="bright_magenta")
    table.add_column("Stat", style="cyan")
    table.add_column("Value", style="bold white")
    table.add_row("Level", str(character.level))
    table.add_row("XP", str(character.xp))
    table.add_row("HP", f"{character.hp}/{character.max_hp}")
    table.add_row("Attack", str(character.attack))
    table.add_row("Defense", str(character.defense))
    table.add_row("Tech", str(character.tech))
    table.add_row("Charisma", str(character.charisma))
    table.add_row("Credits", str(character.credits))
    table.add_row("Banked", str(character.banked_credits))
    table.add_row("Reputation", str(character.reputation))
    console.print(table)


def choose_class() -> str:
    class_names = list(CLASSES.keys())

    table = Table(border_style="bright_cyan")
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Class", style="bold magenta")
    table.add_column("Flavor")
    table.add_column("HP", justify="right")
    table.add_column("ATK", justify="right")
    table.add_column("DEF", justify="right")
    table.add_column("TECH", justify="right")
    table.add_column("CHA", justify="right")
    for i, name in enumerate(class_names, start=1):
        stats = CLASSES[name]
        table.add_row(
            str(i),
            name,
            stats["flavor"],
            str(stats["hp"]),
            str(stats["attack"]),
            str(stats["defense"]),
            str(stats["tech"]),
            str(stats["charisma"]),
        )
    console.print(table)

    choice = IntPrompt.ask("Choose your path", choices=[str(i) for i in range(1, len(class_names) + 1)])
    return class_names[choice - 1]


def create_character() -> Character:
    console.rule("[bright_magenta]New Runner[/bright_magenta]")
    while True:
        name = Prompt.ask("What do they call you on the street?").strip()
        if not name:
            console.print("[red]Need a name, choom.[/red]")
            continue
        if save_exists(name):
            console.print(f"[red]A runner named '{name}' already exists.[/red]")
            continue
        break

    char_class = choose_class()
    character = Character.new(name=name, char_class=char_class)
    save_character(character)
    console.print(f"\n[bright_cyan]{character.name}[/bright_cyan] hits the streets of Neo Meridian.\n")
    print_character_sheet(character)
    return character


def choose_existing_save() -> str | None:
    slugs = list_saves()
    if not slugs:
        console.print("[dim]No runners found on file.[/dim]")
        return None

    table = Table(border_style="bright_cyan")
    table.add_column("#", justify="right")
    table.add_column("Name")
    for i, slug in enumerate(slugs, start=1):
        table.add_row(str(i), slug.replace("_", " "))
    console.print(table)

    choice = IntPrompt.ask(
        "Load which runner? (0 to cancel)",
        choices=[str(i) for i in range(len(slugs) + 1)],
        show_choices=False,
    )
    if choice == 0:
        return None
    return slugs[choice - 1]


def main() -> None:
    print_title()
    while True:
        console.print()
        print_main_menu()
        choice = Prompt.ask("Choose", choices=["1", "2", "3", "4"], show_choices=False)

        if choice == "1":
            character = create_character()
        elif choice == "2":
            slug = choose_existing_save()
            if slug is None:
                continue
            character = load_character(slug)
            console.print()
            print_character_sheet(character)
        elif choice == "3":
            show_help(console)
            continue
        else:
            console.print("[dim]Stay chrome.[/dim]")
            break

        enter_hub(character)
        save_character(character)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Connection terminated.[/dim]")
