# NEON DRAGON — Game Design Document

A single-player, terminal-based RPG inspired by *Legend of the Red Dragon*,
reskinned into a cyberpunk vaporwave world. Local save file, daily turn
limit, hub-and-spoke structure, text-driven combat and dialogue.

## 1. Setting

**City name:** Neo Meridian (working title — change freely)
A sprawling, rain-slicked megacity run by corps, fixers, and street gangs.
Neon signage, synth pop bleeding out of noodle bars, chrome and static.
Tone: equal parts Blade Runner grime and Miami-vaporwave color palette —
magenta, cyan, deep purple, hot pink against black.

## 2. The Hub (LORD's inn/forest/tavern loop)

A menu of locations the player travels between each turn:

| LORD equivalent      | Neon Dragon location   | Function                              |
|-----------------------|-------------------------|----------------------------------------|
| The Inn                | **The Chrome Noodle Bar** | Rest, heal, hear rumors/gossip, flavor NPCs |
| The Forest              | **The Undercity**         | Random encounters, fights, loot        |
| The Bank                | **NetVault**              | Deposit/withdraw credits (safe from death-loss) |
| The Weapon/Armor Shop   | **Chop Shop**             | Buy/sell gear and cyberware             |
| The Healer               | **Doc Wire's Clinic**     | Heal HP for credits, cure status effects |
| The Master (training)  | **The Dojo / Ripper Doc** | Train stats, learn new abilities        |
| Daily Battles/Arena     | **The Pit**               | PvE gladiator fights for reputation/credits |
| Romance NPC (Violet)    | **[NPC of your choosing]** | Flavor relationship subplot             |
| Player list/rankings    | **Fixer Board**           | Leaderboard, contracts/quests posted    |

## 3. Core Loop

1. Player logs in (loads save), sees turns remaining for the day.
2. Player picks a hub location from the menu.
3. Each action (fight, quest step, training) consumes a turn.
4. Combat/dialogue/quest resolves, stats and credits update.
5. When turns hit 0, player can end the day (or wait for a daily reset).
6. Save file persists between sessions.

## 4. Character

- Core stats: HP, Attack (Chrome/Melee), Defense (Armor), Tech (hacking/
  ranged), Charisma (dialogue/quest checks), Credits, XP/Level.
- Optional class flavor at creation: **Street Samurai** (melee-focused),
  **Netrunner** (tech/hacking-focused), **Fixer** (charisma/quest-focused).
- Cyberware slots instead of traditional armor slots (arm, eyes, spine,
  skin) — each grants a stat bonus, sourced from the Chop Shop.

## 5. NPCs

Data-driven (see CLAUDE.md) — not hardcoded. Each NPC has:
- Name, location, a short bio/flavor text
- A pool of dialogue lines (randomized on visit)
- Optionally: a quest hook, a shop inventory, or a relationship-track flag

Starter NPC roster (flavor only — expand freely):
- **Doc Wire** — clinic owner, gruff, healer
- **Ms. Kessler** — NetVault teller, deadpan corp-speak
- **Jax** — Chop Shop dealer, sells cyberware, shady
- **Static Rin** — bartender at the Chrome Noodle Bar, hears everything
- **The Fixer** — posts contracts/quests on the Fixer Board

## 6. Quests

Simple multi-step quest objects: fetch/kill/talk-to/deliver chains with a
credit + XP + reputation reward. Some quests unlock new hub locations or
NPCs. Start with 3-5 short quests before scaling up.

## 7. Combat

Turn-based, text-narrated. Player picks an action each round (Attack,
Tech/Hack, Defend, Use Item, Flee). Simple damage formulas to start
(stat + weapon roll vs. defense), can add status effects (EMP-stun,
bleed/"glitch") later.

## 8. Random Encounters (Undercity)

Weighted random table: street gang fights, scavenger loot finds, rogue
drone ambushes, corp patrol shakedowns, nothing-happens flavor text.

## 9. Aesthetic Rules

- Color palette: magenta/cyan/purple on black, used for headers, NPC
  names, and important numbers — not every line (avoid visual noise).
- Terse, noir-flavored narration. Short punchy sentences.
- ASCII/box-drawn panels for the hub menu and stat sheet.

## 10. Build Phases (suggested order)

1. Character creation + save/load + main menu skeleton
2. Hub navigation between locations (no content yet, just movement)
3. Combat engine + Undercity random encounters
4. NPCs + dialogue system (data-driven)
5. Quests
6. Daily turn limit + day-end/reset cycle
7. Chop Shop economy + cyberware
8. Polish: color palette, ASCII panels, flavor text pass

## Notes

This doc is a starting skeleton, not a spec to follow rigidly. Change
names, mechanics, and scope as the game takes shape in play. The point is
to keep updating this file as decisions get made, so it stays the source
of truth for what the game currently is.
