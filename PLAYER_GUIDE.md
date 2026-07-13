# Neon Dragon — Player Guide

Welcome to Neo Meridian. This guide covers what everything actually
does in the game as it stands right now.

## Getting started

From the main menu: **New Runner** creates a character (pick a name
and a class), **Load Runner** resumes a saved one, **Quit** exits.
There's no daily turn limit — play as long as you like in one sitting.

## Classes

Two classes right now, each a different balance of the same stats:

- **Street Samurai** — high HP and Attack, low Tech. Built to punch
  through fights with raw damage.
- **Netrunner** — low HP and Attack, high Tech. Built around the
  Tech/Hack combat action instead of Attack.

(A third class, Fixer, built around Charisma, is on hold until
Charisma actually does something mechanically — see below.)

## Stats

- **HP** — health. Hits zero and you're patched up at 1 HP with a
  medical bill (see Combat).
- **Attack** — damage on the Attack combat action.
- **Defense** — reduces incoming damage in combat.
- **Tech** — damage on the Tech/Hack combat action.
- **Charisma** — tracked on your sheet, but nothing in the game reads
  it yet. No dialogue checks, no discounts, no gated content. Purely
  cosmetic for now.
- **Credits** — cash on hand. Spent at the Chop Shop, the Clinic, and
  the Dojo; lost (partially) if you go down in a fight.
- **Banked Credits** — cash stored at NetVault. Never touched by
  combat defeat, no matter what.
- **Reputation** — earned from Pit fights and completed Fixer Board
  contracts. Gates higher-tier contracts (see Fixer Board below). Not
  used anywhere else yet.
- **XP / Level** — XP accumulates from combat and quests. Leveling
  itself isn't wired up to anything yet — no automatic stat growth or
  level-up rewards.

## The Hub — Neo Meridian

Every session loops through this menu. Locations:

### Chrome Noodle Bar
Static Rin, the bartender, has a pool of flavor lines and occasional
job rumors. No mechanical effect — a flavor stop, and a step in the
"Word on the Street" contract.

### Undercity
Random encounters, weighted: gang fights, a rogue drone, a corp
patrol, a scavenger stash (free credits, no fight), or nothing at all.
Combat encounters use the same fight system as everywhere else.

### NetVault
Deposit or withdraw credits with Ms. Kessler. Banked credits are safe
from the trauma bill you take when a fight goes badly — on-hand
credits aren't.

### Chop Shop
Buy cyberware from Jax across four slots: arm, eyes, spine, skin. Each
item gives a flat bonus to one stat (Attack, Tech, Defense, or
Charisma). Buying a second item for an occupied slot auto-sells the
old one for half its cost as trade-in credit. You can also sell
outright from the Sell menu.

### Doc Wire's Clinic
Heals HP for credits at a flat rate (2 credits per HP), capped to
whatever you can afford. No-op if you're already at full health.

### The Dojo
Permanently trains a stat (Attack, Defense, Tech, or Charisma) up by
1 for a flat 40 credits per point. No cap on how high you can train.

### The Pit
Choose a fight from a fixed roster of three gladiators, toughest
paying out the most. Wins grant credits, XP, and reputation — this is
one of the two ways to earn reputation (the other is Fixer Board
contracts).

### Fixer Board
Accept, track, and turn in contracts from The Fixer. Each contract is
a short chain of steps — talk to someone, kill something, then report
back here to collect the reward. **Some contracts require a minimum
reputation before The Fixer will offer them** — if you see a note
about locked contracts, go earn reputation at the Pit or by finishing
lower-tier contracts first.

## Combat

Turn-based. Each round you pick:

- **Attack** — damage based on your Attack stat.
- **Tech/Hack** — damage based on your Tech stat.
- **Defend** — halves incoming damage that round.
- **Flee** — coin-flip chance to escape with no reward either way.

Damage is roughly `stat + random(1-6) - enemy defense`, minimum 1.

If your HP hits zero, Doc Wire's trauma team patches you up to 1 HP
and bills you a flat 40 credits from whatever's on hand — this can put
you in debt (negative credits) if you don't have enough. Banked
credits at NetVault are never touched by this.

## Quests

Quests chain "talk" (visit a location) and "kill" (defeat a named
enemy) steps. All contracts are managed at the Fixer Board — accepted,
tracked, and turned in there, even if the steps in between happen
elsewhere. Completing a contract pays credits, XP, and reputation.

## Saving

One JSON save file per character, named after them. The game saves
automatically whenever you leave the hub back to the main menu.

## What's not built yet

A few things mentioned in the game's design notes but not implemented:

- Charisma has no mechanical effect.
- No status effects (poison, stun, etc.) — Doc Wire's "cure status
  effects" is flavor text only.
- No ability/skill system — the Dojo trains stats, not abilities.
- No fetch/deliver quests — only talk/kill steps exist so far.
