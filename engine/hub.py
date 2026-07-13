"""Hub menu / navigation. Real location menu arrives in phase 2."""

from __future__ import annotations

from rich.console import Console

from engine.character import Character

console = Console()


def enter_hub(character: Character) -> None:
    """Placeholder hub loop — location navigation is built in phase 2."""
    console.print(
        f"\n[bright_cyan]{character.name}[/bright_cyan] steps out into Neo Meridian. "
        "[dim](hub navigation coming in phase 2...)[/dim]\n"
    )
