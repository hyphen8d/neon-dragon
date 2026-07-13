"""Shared bracket-hotkey menu helpers, used by main.py, hub.py, and combat.py."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt


def hotkey_bracket(key: str, label: str) -> str:
    """Bold-bracket the hotkey letter where it naturally occurs in label
    (e.g. "Deposit" + "D" -> "[D]eposit"). Falls back to a leading
    "[X] label" if the key isn't actually in the label text."""
    idx = label.upper().find(key.upper())
    if idx == -1:
        return f"[bold bright_magenta][{key.upper()}][/bold bright_magenta] {label}"
    return (
        f"{label[:idx]}[bold bright_magenta][{label[idx].upper()}]"
        f"[/bold bright_magenta]{label[idx + 1:]}"
    )


def hotkey_prompt(console: Console, options: list[tuple[str, str]], prompt: str = "") -> str:
    """Print bracket-hotkey-styled options inline and return the chosen key,
    uppercased. `options` is a list of (key, label) pairs."""
    text = "  ".join(hotkey_bracket(key, label) for key, label in options)
    if prompt:
        text = f"{prompt}\n{text}"
    keys = [key for key, _ in options]
    choice = Prompt.ask(text, choices=keys, show_choices=False, case_sensitive=False)
    return choice.upper()
