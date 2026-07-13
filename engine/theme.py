"""Centralized Rich style/color definitions for Neon Dragon.

Every console.print markup tag and every Table/Panel `style` /
`border_style` / `header_style` kwarg across the engine should reference
one of these named constants instead of a hardcoded string, so the whole
game's vaporwave palette (magenta/cyan/purple, per GAME_DESIGN.md's
Aesthetic Rules) can be retuned from a single place.

Usage:
    from engine.theme import BORDER, ALERT

    table = Table(border_style=BORDER)
    console.print(f"[{ALERT}]Something's wrong.[/{ALERT}]")

`THEME` collects the same constants in a dict, for anything that wants to
introspect or iterate the palette rather than importing names directly.
"""

from __future__ import annotations

# --- Structure: borders and section labels ---
BORDER = "bright_cyan"  # standard table/panel borders
BORDER_ACCENT = "bright_magenta"  # HUD border and other elements meant to stand out
BORDER_RARE = "magenta"  # Black Market border — rare/hidden content
LABEL = "bright_magenta"  # section labels and rule headers ("Active contracts:", "Neo Meridian")

# --- Interaction ---
HOTKEY = "bold bright_magenta"  # bracketed hotkey letters in menus (engine/ui.py)
ACCENT = "bold bright_magenta"  # positive narration and panel/table titles elsewhere

# --- Narrative tone ---
ALERT = "bold red"  # critical danger — enemy names, defeat headers
DANGER = "red"  # damage taken, failed rolls, blocked/locked actions
WARNING = "yellow"  # status effects, cautionary notes
CREDITS = "bold yellow"  # currency figures
RARE = "bold magenta"  # Black Market / rare-item highlights

# --- Text weight ---
NAME = "bright_cyan"  # character name inline in prose
NAME_BOLD = "bold bright_cyan"  # character name in a table cell (e.g. HUD)
INFO = "bold cyan"  # NPC names, informative highlights
ACCENT_SOFT = "cyan"  # secondary label accents (table columns like Slot, Stat)
TEXT = "bold white"  # primary emphasized text (table values, item names)
TEXT_PLAIN = "white"  # unemphasized body text
TEXT_DIM = "dim white"  # de-emphasized flavor/narration text
NOTE = "dim italic"  # small inline notes, e.g. "[Insufficient Funds]"
ITALIC = "italic"  # lore/flavor paragraphs
SUBTITLE = "dim cyan"  # small subtitle text (e.g. version tag under the banner)

# --- Combat telemetry ---
# Directional prefixes on combat narrative lines, so a player-turn line vs
# an enemy-turn line is distinguishable without reading the sentence.
PLAYER_ARROW = "»»»"  # prefixes player-turn resolutions (attacks, hacks, items)
ENEMY_ARROW = "«««"  # prefixes (indented) enemy-turn attacks and status hits
TELEMETRY_PLAYER = "bold bright_cyan"  # color for the »»» tag
TELEMETRY_ENEMY = "bold red"  # color for the indented ««« tag

# --- Menu structure ---
DIVIDER = "│"  # vertical partition between options in a hotkey menu row

THEME: dict[str, str] = {
    "BORDER": BORDER,
    "BORDER_ACCENT": BORDER_ACCENT,
    "BORDER_RARE": BORDER_RARE,
    "LABEL": LABEL,
    "HOTKEY": HOTKEY,
    "ACCENT": ACCENT,
    "ALERT": ALERT,
    "DANGER": DANGER,
    "WARNING": WARNING,
    "CREDITS": CREDITS,
    "RARE": RARE,
    "NAME": NAME,
    "NAME_BOLD": NAME_BOLD,
    "INFO": INFO,
    "ACCENT_SOFT": ACCENT_SOFT,
    "TEXT": TEXT,
    "TEXT_PLAIN": TEXT_PLAIN,
    "TEXT_DIM": TEXT_DIM,
    "NOTE": NOTE,
    "ITALIC": ITALIC,
    "SUBTITLE": SUBTITLE,
    "PLAYER_ARROW": PLAYER_ARROW,
    "ENEMY_ARROW": ENEMY_ARROW,
    "TELEMETRY_PLAYER": TELEMETRY_PLAYER,
    "TELEMETRY_ENEMY": TELEMETRY_ENEMY,
    "DIVIDER": DIVIDER,
}
