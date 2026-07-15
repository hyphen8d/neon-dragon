"""Render the player guide inside the game, straight from PLAYER_GUIDE.md."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown

from engine.theme import ACCENT, BORDER
from engine.ui import glitch_rule, glitch_title_rule

GUIDE_PATH = Path(__file__).resolve().parent.parent / "PLAYER_GUIDE.md"


def show_help(console: Console) -> None:
    console.print()
    glitch_title_rule(console, f"[{ACCENT}]Player Guide[/{ACCENT}]")
    console.print(Markdown(GUIDE_PATH.read_text()))
    glitch_rule(console, style=BORDER)
