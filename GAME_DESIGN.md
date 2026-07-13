# NEON DRAGON — Game Design Document

A single-player, terminal-based RPG set in a cyberpunk vaporwave world.
Local save file, hub-and-spoke structure, text-driven combat and dialogue.
No daily turn limit — see section 3.

## 1. Setting

**City name:** Neo Meridian (working title — change freely)
A sprawling, rain-slicked megacity run by corps, fixers, and street gangs.
Neon signage, synth pop bleeding out of noodle bars, chrome and static.
Tone: equal parts Blade Runner grime and Miami-vaporwave color palette —
magenta, cyan, deep purple, hot pink against black.

## 2. The Hub

A menu of locations the player travels between:

| Hub role               | Neon Dragon location   | Function                              |
|-----------------------|-------------------------|----------------------------------------|
| Rest stop               | **The Chrome Noodle Bar** | Rest, heal, hear rumors/gossip, flavor NPCs |
| Random encounters       | **The Undercity**         | Random encounters, fights, loot        |
| Bank                     | **NetVault**              | Deposit/withdraw credits (safe from death-loss) |
| Weapon/armor shop        | **Hyphen8d's Hut**        | Buy/sell gear and cyberware — 4-item daily rotating stock, Charisma haggles the price down, one slot has a daily price event |
| Healer                    | **Doc Wire's Clinic**     | Heal HP for credits, cure status effects |
| Trainer                  | **RoboDOJO**              | Spar with training drones to train stats, learn new abilities |
| Arena                     | **The Pit**               | PvE gladiator fights for reputation/credits |
| Romance NPC (Violet)    | **[NPC of your choosing]** | Flavor relationship subplot             |
| Leaderboard/contracts    | **Fixer Board**           | Leaderboard, contracts posted    |

## 3. Core Loop

1. Player logs in (loads save).
2. Player picks a hub location from the menu.
3. Combat/dialogue/contract resolves, stats and credits update.
4. Player keeps navigating the hub for as long as they want within a
   day — no limit on how many locations/actions they visit before
   leaving. (Decided during phase 5+6 review: cut a hard turn limit to
   keep sessions unconstrained.)
5. Choosing Leave asks for a Yes/No confirmation first — it's a
   consequential action (resets Faction Heat, the daily drink limit,
   and Hyphen8d's stock/market), not a plain menu back-out. Confirming
   sends the merc home to sleep: the day counter increments, HP fully
   restores, status effects clear, and a "Daily Data Feed" panel
   summarizes standing. This is also when Faction Heat (section 8)
   resolves and daily kill counts reset.
6. Save file persists between sessions.

## 4. Character

The player is a cyber mercenary (**merc**) working Neo Meridian's edges.

- Core stats: HP, Attack (Chrome/Melee), Defense (Armor), Tech (hacking/
  ranged), Charisma (contract-gating, shop discounts, trauma bill
  reduction), Credits, XP/Level.
- Class flavor at creation: **Street Samurai** (melee-focused), **Netrunner**
  (tech/hacking-focused), **Grifter** (charisma-focused — talks fast,
  moves smoothly, survives on street-smarts; bypasses problems steel or
  code can't touch). Charisma now carries real mechanical weight instead
  of only gating two Chrome Noodle Bar contracts — see section 6 and
  section 7 for the shop discount and trauma bill reduction it grants.
- Cyberware slots instead of traditional armor slots (arm, eyes, spine,
  skin) — each grants a stat bonus, sourced from Hyphen8d's Hut.

## 5. NPCs

Data-driven (see CLAUDE.md) — not hardcoded. Each NPC has:
- Name, location, a short bio/flavor text
- A pool of dialogue lines (randomized on visit)
- Optionally: a contract hook, a shop inventory, or a relationship-track flag

Starter NPC roster (flavor only — expand freely):
- **Doc Wire** — clinic owner, gruff, healer
- **Ms. Kessler** — NetVault teller, deadpan corp-speak
- **Hyphen8d** — Hyphen8d's Hut dealer, sells cyberware, shady
- **Static Rin** — bartender at the Chrome Noodle Bar, hears everything
- **The Fixer** — posts contracts on the Fixer Board
- **Endr3am** — tall merc who works the Chrome Noodle Bar's back booth,
  brokers merc-to-merc contracts there (charisma-gated, see section 6)

## 6. Contracts

Multi-step contract objects: talk/kill chains (fetch/deliver not yet built)
with a credit + XP + reputation reward. Two contract boards: the **Fixer
Board** (gated by Reputation, run by The Fixer) and **Endr3am's board** at
the Chrome Noodle Bar (gated by Charisma). A third gate, **Level**, applies
to contracts on either board and is tied to the same tiers that unlock
Undercity's tougher enemies (`min_reputation`, `min_charisma`, `min_level`
in the schema). 12 contracts total as of this pass. Beyond gating
Endr3am's board, Charisma also gets Hyphen8d's Hut prices down (2%
off per point, capped at 40%) — the Grifter's build strength shows up
there rather than in raw combat stats. Some contracts unlock
new hub locations or NPCs — not used yet, but the hook exists.

**Dynamic economy** (`engine/shop.py`, rolled by `roll_daily_market` in
`_sleep_and_advance_day`): each day, Hyphen8d's Hut restocks to a
random 4 items out of the full catalog, and one cyberware slot gets a
random price event — a 10-30% discount or surge — that stacks with the
Charisma discount rather than replacing it. Both are stored on
`Character` (`market_stock`, `market_modifier`) and re-roll on sleep;
`get_daily_catalog`/`discounted_cost` are the read paths the shop UI
uses, so nothing else needs to know the roll happened.

**Quantum Cores** (`Character.quantum_cores`): a rare secondary
currency, LORD-gem-style. 4% drop chance (`QUANTUM_CORE_DROP_CHANCE`
in `hub.py`) on a successful Jack In and on a Tier 3 Pit win only
(gladiators now carry a `tier` field in `content/pit.json`; Tiers 1-2
never drop). Spent at a hidden **Black Market** inside Hyphen8d's Hut
— reachable via an `[M]` hotkey deliberately left off the visible
Buy/Sell/Leave menu text, so it's undiscoverable without either
digging through the code or trying keys — selling four elite
prototype cyberware pieces (`content/black_market.json`, one per
slot, roughly double the top normal-tier bonus) priced only in Cores,
no Charisma discount or market event. `engine/shop.py`'s `get_item`
resolves ids across both catalogs so equipped Black Market gear works
everywhere normal gear does (loadout, sell menu); `unequip` refunds
whichever currency the item was actually priced in.

## 7. Combat

Turn-based, text-narrated. Player picks an action each round (Attack,
Tech/Hack, Defend, Flee, plus Items whenever inventory is non-empty —
see `content/usable_items.json`). Simple damage formulas (stat + roll
vs. defense). Status effects are implemented: Stunned (skip your
action) and Bleeding (damage over time), inflicted by specific
enemies. Droid enemies (`is_droid: true` in encounter data — currently
just Rogue Drone) are immune to Bleed from any source, enforced
centrally in `status_effects.apply_effect`.

Each class also has a signature special move on a 3-round cooldown:
Street Samurai's **Samurai Slash** (1.5x damage, guaranteed Bleed,
still dodgeable) and Netrunner's **Override System** (no damage,
guaranteed 2-round Stun, bypasses dodge). Cooldown state lives in
`run_combat`'s local loop, not on the saved Character — it resets
every fight. The Grifter doesn't have a combat special (yet) — its
build strength shows up in the economy instead (below).

Charisma talks down the trauma bill from a lost fight: 3% off per
point, capped at 45%. A high-Charisma build still goes down in a
fight the same as anyone else, but pays less to get patched up.

## 8. The Undercity

Not a single random roll — the player picks an approach: **Jack In**
(steal credits, odds/payout scaled by Tech, failure forces a Corp-faction
fight), **Find a Fight** (guaranteed combat, random enemy), or **Scavenge**
(the old low-risk loot/nothing pool). Combat pool includes three
level-gated tiers (Ronin Netrunner L3+, Corp Strike Team L5+, Chrome
Beast L7+) so difficulty rises with the player instead of staying flat.

**Faction Heat** (`engine/heat.py`): killing more than 3 enemies of the
same faction in a single day builds heat with that faction — currently
Corp and Street Gang only, the two with organized street presence to
retaliate. While hot, there's a 15% chance per Scavenge roll of an
ambush interrupting it instead of the normal loot/nothing outcome, and
the same 15% roll happens once on waking at the safehouse. Heat is
tracked on `Character.daily_kills` and wiped every time the player
sleeps (leaves the hub) — see section 3 on the day cycle.

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
5. Contracts
6. ~~Daily turn limit + day-end/reset cycle~~ — cut, see section 3
7. Hyphen8d's Hut economy + cyberware
8. Polish: color palette, ASCII panels, flavor text pass

## Notes

This doc is a starting skeleton, not a spec to follow rigidly. Change
names, mechanics, and scope as the game takes shape in play. The point is
to keep updating this file as decisions get made, so it stays the source
of truth for what the game currently is.
