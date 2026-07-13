# Neon Dragon

**Alpha 2.0**

A single-player, terminal-based RPG set in a cyberpunk vaporwave city —
Neo Meridian. No server, no accounts, no web frontend. Just a Python
CLI you run in a terminal, with a local JSON save file per character.

## Requirements

- Python 3.11+
- [Rich](https://github.com/Textualize/rich) (terminal UI/formatting)

## Setup

```bash
git clone <repo-url> neon-dragon
cd neon-dragon
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python main.py
```

## Features

- Character creation — 2 classes (Street Samurai, Netrunner), each a
  different balance of the same stats (a third, charisma-focused class
  is pulled for now pending a redesign)
- A hub of 8 locations in Neo Meridian, each with real mechanics:
  Undercity (Jack In / Find a Fight / Scavenge), NetVault (banking),
  Hyphen8d's Hut (cyberware with a daily rotating stock and market
  events), Doc Wire's Clinic (healing, curing, and consumable
  supplies), RoboDOJO (drone sparring / stat training), The Pit
  (tiered gladiator fights), Fixer Board (reputation-gated contracts),
  Chrome Noodle Bar (free rest + charisma-gated contracts)
- Turn-based combat with a live two-panel HUD (HP bars, status badges,
  a real-time enemy sensor scan), directional »»»/««« narration tags,
  and gear- and damage-aware hit descriptions that change with your
  equipped cyberware, class, and how hard you actually hit
- Status effects (Bleeding, Stunned, Drunk) with colored glyph badges,
  per-enemy factions (Street Gang, Corp, Ronin, Feral, Gladiator), and
  a signature class special on a cooldown — Street Samurai's Samurai
  Slash, Netrunner's Override System
- A day/night cycle — leaving the hub (with confirmation) sends your
  merc home to sleep: full heal, status effects cleared, and a "Daily
  Data Feed" panel summarizing where you stand
- Faction Heat — rack up too many kills against Corp or Street Gang in
  one day and you risk a retaliatory ambush, mid-Scavenge or the
  moment you wake up
- A dynamic economy at Hyphen8d's Hut — a random daily price event
  (discount or surge) on one cyberware slot, on top of a Charisma
  discount that stacks with it
- A consumable-item inventory (Nanite Patches, EMP Grenades, and more)
  usable mid-combat without breaking your turn economy
- Charisma has real mechanical weight: shop discounts, cheaper trauma
  bills after a lost fight, and gates on higher-tier contracts
- A rare secondary currency and the black-market economy built around
  it, for players who go looking
- In-game character info (`[I]`) and help (`[?]`) screens, accessible
  mid-session without spending a turn
- Bracket-hotkey menus throughout — every screen shows a bold-bracketed
  letter, and on a real terminal you don't even need to press Enter
- A fixed 120-column layout so tables and panels render identically
  regardless of terminal width
- JSON save/load, one file per character, autosaved on returning to
  the main menu

## Docs

- [`GAME_DESIGN.md`](GAME_DESIGN.md) — world, hub locations, and
  mechanics design notes; the source of truth for what the game
  currently is and how it's meant to evolve
- [`PLAYER_GUIDE.md`](PLAYER_GUIDE.md) — how everything actually works
  right now, including an honest list of what's not built yet. Also
  readable in-game via the `?` command
- [`CLAUDE.md`](CLAUDE.md) — the technical/process contract this
  project is built under (this was built with
  [Claude Code](https://claude.com/claude-code))

## Content is data, not code

NPCs, contracts, encounter tables, cyberware, consumables, and the
Pit's gladiator roster all live under [`content/`](content/) as JSON.
Adding or tuning content is a data edit, not a code change.

## Status

Alpha 2.0. Every hub location has real mechanics; the current "end
game" is working through Fixer Board and Chrome Noodle Bar contracts,
with a day-cycle economy layered on top of it. See the "What's not
built yet" section of `PLAYER_GUIDE.md` for known gaps.

## Credits

Built by Matthew Arevalo ([Gial Ventures](mailto:matt@gial.co)) with
[Claude](https://claude.com) via [Claude Code](https://claude.com/claude-code).

## License

[MIT](LICENSE) — free to use, modify, and distribute. Keep the
copyright notice.
