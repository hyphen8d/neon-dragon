"""Neon Dragon — entry point and main menu loop."""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from engine.character import CLASSES, Character, hp_style
from engine.help import show_help
from engine.hub import enter_hub
from engine.leveling import xp_for_next_level
from engine.save import delete_save, list_saves, load_character, save_character, save_exists
from engine.ui import hotkey_bracket, hotkey_prompt, read_choice

console = Console(width=120, highlight=False)

VERSION = "Alpha 1.5"

LORE = (
    "Neo Meridian never sleeps and never forgives. Corp towers own the sky, "
    "fixers and gangs own the streets underneath, and the rain never stops — "
    "it just changes color under the neon. Chrome is cheap. Everything else "
    "costs more than you think."
)

# Hand-built 5-row block font. Every letter is 5 rows tall; row widths within
# a word are kept equal so per-line Rich coloring/centering stays aligned.
_BLOCK_FONT: dict[str, list[str]] = {
    "N": ["█   █", "██  █", "█ █ █", "█  ██", "█   █"],
    "E": ["█████", "█    ", "████ ", "█    ", "█████"],
    "O": [" ███ ", "█   █", "█   █", "█   █", " ███ "],
    "D": ["████ ", "█   █", "█   █", "█   █", "████ "],
    "R": ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
    "A": [" ███ ", "█   █", "█████", "█   █", "█   █"],
    "G": [" ████", "█    ", "█  ██", "█   █", " ████"],
}

# Magenta -> cyan gradient, one shade per banner row (NEON's 5 rows, then
# DRAGON's 5 rows), for a vaporwave sunset feel down the block-letter title.
_BANNER_GRADIENT = [
    "#ff00c8", "#e31ace", "#c633d4", "#aa4dda", "#8e66e0",
    "#7180e7", "#5599ed", "#39b3f3", "#1cccf9", "#00e6ff",
]


def _block_word(word: str) -> list[str]:
    rows = ["" for _ in range(5)]
    for i, letter in enumerate(word):
        glyph = _BLOCK_FONT[letter]
        for r in range(5):
            rows[r] += glyph[r]
            if i != len(word) - 1:
                rows[r] += " "
    return rows


def _banner() -> Group:
    neon_rows = _block_word("NEON")
    dragon_rows = _block_word("DRAGON")
    pad = (len(dragon_rows[0]) - len(neon_rows[0])) // 2
    neon_rows = [" " * pad + row for row in neon_rows]

    lines = [*neon_rows, *dragon_rows]
    renderables = [
        Text(line, style=f"bold {color}", justify="center")
        for line, color in zip(lines, _BANNER_GRADIENT)
    ]
    return Group(*renderables)


def print_title() -> None:
    banner = _banner()
    version = Text(VERSION, style="dim cyan", justify="center")
    lore = Text(LORE, style="italic", justify="left")
    body = Group(banner, Text(""), version, Text(""), lore)
    console.print(Panel(body, border_style="bright_cyan", padding=(1, 4)))


MAIN_MENU_OPTIONS: list[tuple[str, str]] = [
    ("N", "New Merc"),
    ("L", "Load Merc"),
    ("D", "Delete Merc"),
    ("H", "Help"),
    ("Q", "Quit"),
]


def print_main_menu() -> None:
    table = Table(border_style="bright_cyan", show_header=False)
    table.add_column("Action", style="bold white")
    for key, label in MAIN_MENU_OPTIONS:
        table.add_row(hotkey_bracket(key, label))
    console.print(table)


def print_character_sheet(character: Character) -> None:
    console.rule(f"[bold bright_magenta]{character.name}[/bold bright_magenta] [dim]— {character.char_class}[/dim]")
    table = Table(border_style="bright_magenta")
    table.add_column("Stat", style="cyan")
    table.add_column("Value", style="bold white")
    table.add_row("Level", str(character.level))
    table.add_row("Day", str(character.day))
    table.add_row("XP", f"{character.xp}/{xp_for_next_level(character)}")
    style = hp_style(character.hp, character.max_hp)
    table.add_row("HP", f"[{style}]{character.hp}/{character.max_hp}[/{style}]")
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
    # First letter of each class name is unique among current classes
    # (Street Samurai / Netrunner); revisit if a future class collides.
    hotkeys = {name[0].upper(): name for name in class_names}

    table = Table(border_style="bright_cyan")
    table.add_column("Class", style="bold magenta")
    table.add_column("Flavor")
    table.add_column("HP", justify="right")
    table.add_column("ATK", justify="right")
    table.add_column("DEF", justify="right")
    table.add_column("TECH", justify="right")
    table.add_column("CHA", justify="right")
    for key, name in hotkeys.items():
        stats = CLASSES[name]
        table.add_row(
            hotkey_bracket(key, name),
            stats["flavor"],
            str(stats["hp"]),
            str(stats["attack"]),
            str(stats["defense"]),
            str(stats["tech"]),
            str(stats["charisma"]),
        )
    console.print(table)

    choice = hotkey_prompt(console, list(hotkeys.items()), prompt="Choose your path")
    return hotkeys[choice]


def create_character() -> Character:
    console.rule("[bright_magenta]New Merc[/bright_magenta]")
    while True:
        name = Prompt.ask("What do they call you on the street?").strip()
        if not name:
            console.print("[red]Need a name, choom.[/red]")
            continue
        if save_exists(name):
            console.print(f"[red]A merc named '{name}' already exists.[/red]")
            continue
        break

    char_class = choose_class()
    character = Character.new(name=name, char_class=char_class)
    save_character(character)
    console.print(f"\n[bright_cyan]{character.name}[/bright_cyan] hits the streets of Neo Meridian.\n")
    print_character_sheet(character)
    return character


def choose_existing_save(verb: str = "Load") -> str | None:
    slugs = list_saves()
    if not slugs:
        console.print("[dim]No mercs found on file.[/dim]")
        return None

    table = Table(border_style="bright_cyan")
    table.add_column("#", justify="right")
    table.add_column("Name")
    for i, slug in enumerate(slugs, start=1):
        table.add_row(str(i), slug.replace("_", " "))
    console.print(table)

    choice = read_choice(
        console,
        [str(i) for i in range(len(slugs) + 1)],
        prompt=f"{verb} which merc? (0 to cancel)",
    )
    if choice == "0":
        return None
    return slugs[int(choice) - 1]


def delete_character() -> None:
    slug = choose_existing_save(verb="Delete")
    if slug is None:
        return

    name = slug.replace("_", " ")
    confirm = hotkey_prompt(
        console,
        [("Y", "Yes"), ("N", "No")],
        prompt=f"Really delete '{name}'? This can't be undone.",
    )
    if confirm == "Y":
        delete_save(slug)
        console.print(f"[red]{name} deleted.[/red]")


def main() -> None:
    print_title()
    while True:
        console.print()
        print_main_menu()
        choice = hotkey_prompt(console, MAIN_MENU_OPTIONS)

        if choice == "N":
            character = create_character()
        elif choice == "L":
            slug = choose_existing_save()
            if slug is None:
                continue
            character = load_character(slug)
            console.print()
            print_character_sheet(character)
        elif choice == "D":
            delete_character()
            continue
        elif choice == "H":
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
