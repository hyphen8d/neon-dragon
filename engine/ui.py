"""Shared bracket-hotkey menu helpers, used by main.py, hub.py, and combat.py.

Menu selections read a single keypress with no Enter required on a real
terminal (raw/cbreak mode via termios+tty on macOS/Linux, msvcrt on
Windows). When stdin isn't a terminal — piped input, as used by this
project's test scripts — reads fall back to line-buffered input so
scripted playthroughs keep working unchanged.
"""

from __future__ import annotations

import sys

from rich.console import Console

from engine.character import hp_style
from engine.theme import DANGER, DIVIDER, HOTKEY, NOTE, TEXT_DIM

HP_BAR_WIDTH = 10

# Vertical partition between options in a hotkey menu row, e.g.
# "[A]ttack │ [D]efend │ [L]eave" instead of a plain double space.
OPTION_SEPARATOR = f" [{TEXT_DIM}]{DIVIDER}[/{TEXT_DIM}] "


def make_hp_bar(hp: int, max_hp: int) -> str:
    """A 10-cell block-bar HP meter (█ filled, ░ empty), color-coded via
    hp_style's danger thresholds (red/yellow/white) — a compact visual
    companion to the numeric HP text."""
    style = hp_style(hp, max_hp)
    ratio = 0.0 if max_hp <= 0 else max(0.0, min(1.0, hp / max_hp))
    filled = round(ratio * HP_BAR_WIDTH)
    bar = "█" * filled + "░" * (HP_BAR_WIDTH - filled)
    return f"[{style}]{bar}[/{style}]"


def read_key() -> str:
    """Read a single character of input, case-preserved, no Enter required
    on an interactive terminal. Raises EOFError at end of piped input,
    same as Rich's Prompt.ask did."""
    if not sys.stdin.isatty():
        line = sys.stdin.readline()
        if line == "":
            raise EOFError("EOF when reading a line")
        return line.strip()[:1]

    if sys.platform == "win32":
        import msvcrt

        return msvcrt.getwch()

    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)  # keeps Ctrl+C/SIGINT working, unlike setraw
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def read_line() -> str:
    """Read a full line, Enter required -- no raw/cbreak juggling needed,
    since canonical (line-buffered) mode is the terminal's default state
    when we simply don't touch termios. Used by read_choice() whenever a
    choice can be more than one character long (a list with 10+ entries);
    read_key() only ever returns a single character, which silently
    discards the rest of a multi-digit line at a single-keystroke prompt."""
    line = sys.stdin.readline()
    if line == "":
        raise EOFError("EOF when reading a line")
    return line.strip()


def read_choice(console: Console, choices: list[str], prompt: str = "") -> str:
    """Read a validated choice (case-insensitive, auto-stripped) against
    `choices`, reprompting on anything else. Single hotkeys read as one
    keypress with no Enter required; a choice set with any entry longer
    than one character (a numbered list past 9 items) reads a full line
    instead, since a single keystroke can't represent a two-digit number."""
    valid = {c.upper() for c in choices}
    multi_char = any(len(c) > 1 for c in choices)
    while True:
        if prompt:
            console.print(prompt, end=" ")
        console.file.flush()
        key = read_line() if multi_char else read_key()
        if not key:
            continue
        key = key.strip().upper()
        if key in valid:
            console.print(key)
            return key
        console.print(f"{key}\n[{DANGER}]Not a valid option — try again.[/{DANGER}]")


def hotkey_bracket(key: str, label: str, affordable: bool = True, reason: str = "Insufficient Funds") -> str:
    """Bold-bracket the hotkey letter where it naturally occurs in label
    (e.g. "Deposit" + "D" -> "[D]eposit"). Falls back to a leading
    "[X] label" if the key isn't actually in the label text.

    When affordable is False, the whole option renders dimmed gray instead
    of the usual bright accent, with a bracketed note appended (defaults to
    "[Insufficient Funds]"; pass `reason` for a different blocker, e.g. a
    daily cap) so a player can visually scan a menu for what they can
    actually do right now."""
    idx = label.upper().find(key.upper())
    if not affordable:
        base = f"[{key.upper()}]{label}" if idx == -1 else f"{label[:idx]}[{label[idx].upper()}]{label[idx + 1:]}"
        return f"[{TEXT_DIM}]{base}[/{TEXT_DIM}] [{NOTE}][{reason}][/{NOTE}]"
    if idx == -1:
        return f"[{HOTKEY}][{key.upper()}][/{HOTKEY}] {label}"
    return (
        f"{label[:idx]}[{HOTKEY}][{label[idx].upper()}]"
        f"[/{HOTKEY}]{label[idx + 1:]}"
    )


def hotkey_prompt(console: Console, options: list[tuple[str, str]], prompt: str = "") -> str:
    """Print bracket-hotkey-styled options inline and return the chosen key,
    uppercased. `options` is a list of (key, label) pairs. No Enter required
    on a real terminal. The action deck is closed off with a dim bottom
    bar once a choice is made, anchoring it to the bottom of the frame."""
    text = OPTION_SEPARATOR.join(hotkey_bracket(key, label) for key, label in options)
    if prompt:
        text = f"{prompt}\n{text}"
    choice = read_choice(console, [key for key, _ in options], prompt=text)
    console.rule(style=TEXT_DIM)
    return choice


def press_any_key(console: Console, message: str = "Press any key to continue...") -> None:
    """Show a dim prompt and block on a single keypress before clearing the
    screen. Since menu input is unbuffered elsewhere, important narration
    (victory/defeat text, contract rewards, a combat round's outcome)
    needs an explicit pause like this or a player can blow straight past
    it with their next hotkey press. Pass a context-specific `message`
    when "continue" isn't accurate (e.g. actually returning to the hub)."""
    console.print(f"\n[{NOTE}][{message}][/{NOTE}]")
    console.file.flush()
    read_key()
    console.clear()
