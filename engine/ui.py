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

from engine.theme import DANGER, HOTKEY, NOTE, TEXT_DIM


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
        console.print(f"{key}\n[{DANGER}]Not a valid option — try again.[/{DANGER}]")


def hotkey_bracket(key: str, label: str, affordable: bool = True) -> str:
    """Bold-bracket the hotkey letter where it naturally occurs in label
    (e.g. "Deposit" + "D" -> "[D]eposit"). Falls back to a leading
    "[X] label" if the key isn't actually in the label text.

    When affordable is False, the whole option renders dimmed gray instead
    of the usual bright accent, with an "[Insufficient Funds]" note
    appended, so a player can visually scan a menu for what they can
    actually pay for."""
    idx = label.upper().find(key.upper())
    if not affordable:
        base = f"[{key.upper()}]{label}" if idx == -1 else f"{label[:idx]}[{label[idx].upper()}]{label[idx + 1:]}"
        return f"[{TEXT_DIM}]{base}[/{TEXT_DIM}] [{NOTE}][Insufficient Funds][/{NOTE}]"
    if idx == -1:
        return f"[{HOTKEY}][{key.upper()}][/{HOTKEY}] {label}"
    return (
        f"{label[:idx]}[{HOTKEY}][{label[idx].upper()}]"
        f"[/{HOTKEY}]{label[idx + 1:]}"
    )


def hotkey_prompt(console: Console, options: list[tuple[str, str]], prompt: str = "") -> str:
    """Print bracket-hotkey-styled options inline and return the chosen key,
    uppercased. `options` is a list of (key, label) pairs. No Enter required
    on a real terminal."""
    text = "  ".join(hotkey_bracket(key, label) for key, label in options)
    if prompt:
        text = f"{prompt}\n{text}"
    return read_choice(console, [key for key, _ in options], prompt=text)


def press_any_key(console: Console) -> None:
    """Show a dim 'press any key' prompt and block on a single keypress
    before clearing the screen. Since menu input is unbuffered elsewhere,
    important narration (victory/defeat text, contract rewards) needs an
    explicit pause like this or a player can blow straight past it with
    their next hotkey press."""
    console.print(f"\n[{NOTE}][Press any key to return to the central hub...][/{NOTE}]")
    console.file.flush()
    read_key()
    console.clear()
