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


def read_choice(console: Console, choices: list[str], prompt: str = "") -> str:
    """Read a single validated keypress (case-insensitive, auto-stripped)
    against `choices`, reprompting on anything else. No Enter required."""
    valid = {c.upper() for c in choices}
    while True:
        if prompt:
            console.print(prompt, end=" ")
        console.file.flush()
        key = read_key()
        if not key:
            continue
        key = key.strip().upper()
        if key in valid:
            console.print(key)
            return key
        console.print(f"{key}\n[red]Not a valid option — try again.[/red]")


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
    uppercased. `options` is a list of (key, label) pairs. No Enter required
    on a real terminal."""
    text = "  ".join(hotkey_bracket(key, label) for key, label in options)
    if prompt:
        text = f"{prompt}\n{text}"
    return read_choice(console, [key for key, _ in options], prompt=text)
