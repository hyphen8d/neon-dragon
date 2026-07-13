# Neon Dragon — Player Guide

Welcome to Neo Meridian. This guide covers what everything actually
does in the game as it stands right now.

## Getting started

You play as a cyber mercenary — a merc — scraping by in Neo Meridian.
From the main menu: **New Merc** creates a character (pick a name and
a class), **Load Merc** resumes a saved one, **Quit** exits. There's
no daily turn limit — play as long as you like in one sitting.

## Classes

Two classes right now, each a different balance of the same stats:

- **Street Samurai** — high HP and Attack, low Tech. Built to punch
  through fights with raw damage.
- **Netrunner** — low HP and Attack, high Tech. Built around the
  Tech/Hack combat action instead of Attack.

(A third class, Fixer, built around Charisma, is on hold until
Charisma has more mechanical weight behind it — see below.)

## Stats

- **HP** — health. Hits zero and you're patched up at 1 HP with a
  medical bill (see Combat).
- **Attack** — damage on the Attack combat action.
- **Defense** — reduces incoming damage in combat.
- **Tech** — damage on the Tech/Hack combat action.
- **Charisma** — gates the two higher-tier contracts Endr3am offers at
  the Chrome Noodle Bar (see below). No effect on combat, dialogue, or
  shop prices yet.
- **Credits** — cash on hand. Spent at Hyphen8d's Hut, the Clinic, and
  RoboDOJO; lost (partially) if you go down in a fight.
- **Banked Credits** — cash stored at NetVault. Never touched by
  combat defeat, no matter what.
- **Reputation** — earned from Pit fights and completed contracts.
  Gates higher-tier Fixer Board contracts (see below).
- **XP / Level** — XP comes from combat kills and completed contracts.
  Each level costs more than the last (level 2 needs 50 total XP,
  level 3 needs 150, level 4 needs 300 — 50 more per level than the
  one before). Every level grants +3 Max HP, +1 Attack, +1 Defense,
  +1 Tech, and a full heal. A single big XP reward can trigger
  multiple level-ups at once. Charisma doesn't grow on level-up since it has no
  effect in combat.

## The Hub — Neo Meridian

Every session loops through this menu. Locations:

### Chrome Noodle Bar
Static Rin, the bartender, has a pool of flavor lines, and it's a step
in several contracts. It's also a free rest stop: if you're below half
HP, you're topped up to half for free — doesn't do anything once
you're at or above that (Doc Wire's Clinic is still the only way to
heal further or clear status effects).

From there you pick one thing to do:

- **Buy a round** (25 credits) — a gamble. Small chance (12%) of a
  permanent +1 to Attack, Defense, or Tech. Most of the time (58%) just
  a bit of gossip (+2 reputation). The rest of the time (30%) you get
  thrown out **Drunk** — a status effect that weakens your next fight's
  Attack/Tech rolls until it wears off or you pay Doc Wire to cure it.
- **Check the shady booth in the back** — Endr3am, a tall merc, runs
  his own contract board here, separate from the Fixer Board and
  gated by **Charisma** instead of Reputation. Charisma only comes
  from Hyphen8d's Hut skin-slot cyberware (Synth-Derm +3, Mirrorskin
  +6) — RoboDOJO doesn't train it.

### Undercity
No longer a single random roll — you pick your approach:

- **Jack in** — attempt to steal credits. Odds and payout scale with
  your Tech stat. Fail and you're traced: it forces a fight against a
  Corp-faction enemy (Rogue Drone, Corp Patrol Trooper, or Corp Strike
  Team) right then. This is Tech's main use outside combat.
- **Find a fight** — guarantees a combat encounter (still random which
  enemy), for when you specifically want XP/credits without gambling
  on nothing happening.
- **Scavenge** — the old low-risk pool: a scavenger stash (free
  credits) or nothing at all. No combat risk.

Three tougher enemies only show up in the fight/jack-in pools once
you're leveled enough to meet them: a **Ronin Netrunner** (level 3+,
dodges some hits), a **Corp Strike Team** (level 5+, ignores your
Defend), and a **Chrome Beast** (level 7+, heavy Bleed). The Undercity
keeps getting more dangerous instead of staying exactly as easy as it
was at level 1.

### NetVault
Deposit or withdraw credits with Ms. Kessler. Banked credits are safe
from the trauma bill you take when a fight goes badly — on-hand
credits aren't.

### Hyphen8d's Hut
Buy cyberware from Hyphen8d across four slots: arm, eyes, spine, skin.
Each item gives a flat bonus to one stat (Attack, Tech, Defense, or
Charisma). Buying a second item for an occupied slot auto-sells the
old one for half its cost as trade-in credit. You can also sell
outright from the Sell menu.

The higher-cost arm and eyes items also let you inflict status effects
on enemies, not just deal more damage: **Razor Claws** (arm) has a
chance to cause Bleeding on Attack, **Target-Lock Eyes** (eyes) has a
chance to cause Stunned on Tech/Hack. The cheaper tier of each slot
(Chrome Arm Mk.I, Optic Scanner) doesn't — that capability is what the
higher price actually buys. Both the shop catalog and your loadout
screen (Character Info, and the Hut itself) show a "Special" column
calling out exactly which effect an item causes, so it's not buried in
this guide alone.

### Doc Wire's Clinic
Always offers a menu: **Heal** (2 credits per HP, capped to whatever
you can afford — a no-op if you're already at full health) or **Cure
Effects** (a flat 15 credits clears everything you're carrying,
regardless of how many effects or how severe — a no-op if you're not
carrying any).

### RoboDOJO
Permanently trains a stat (Attack, Defense, or Tech — not Charisma,
which comes from cyberware instead) up by 1. Cost scales with the
stat's current value — 40 credits base, +5
credits for every point you already have (so Attack 8 costs 80 for
the next point, Attack 20 costs 140). No hard cap, but grinding one
stat sky-high gets progressively more expensive rather than staying
flat forever. Each stat's sparring bout has its own short flavor
line, but the underlying training mechanic is unchanged.

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
Every hit — yours or theirs — has a 20% chance to be a **critical hit**
for 1.5x damage, called out with a CRITICAL! tag.

Some enemies have a gimmick beyond raw stats:

- **Dodge** — a chance to evade your attack entirely (Ronin Netrunner).
  A miss deals no damage and can't trigger a gear effect.
- **Ignores Defend** — some enemies punch through your guard regardless
  of whether you Defend that round (Corp Strike Team). You'll see
  "Your guard didn't matter" when it happens.

Killing blows get their own flavor line instead of the normal hit
text, so finishing a fight reads a little more dramatic than a
regular round.

Beating an enemy has a 25% chance of dropping bonus credits on top of
the normal reward ("Bonus salvage!") — rewards aren't always the same
amount even against the same enemy.

If your HP hits zero, Doc Wire's trauma team patches you up to 1 HP
and bills you from whatever's on hand — this can put you in debt
(negative credits) if you don't have enough. The bill scales with
level (40 credits base, +15 per level above 1), so losing a fight
stays costly as you progress instead of becoming trivial once your
income outgrows a flat fee. Banked credits at NetVault are never
touched by this.

### Status effects

Status effects go both ways:

- **Bleeding** — 3 damage at the start of the affected side's turn,
  for the effect's duration.
- **Stunned** — the affected side loses their action for that round
  entirely.
- **Drunk** — player-only, from a bad night at the Chrome Noodle Bar.
  Reduces your Attack/Tech roll for as long as it lasts.

Enemies inflict effects on hit if they have the ability; you inflict
them via certain cyberware when you Attack (arm slot) or Tech/Hack
(eyes slot) — see Hyphen8d's Hut above. Both sides' active effects show up
in the combat status line.

Effects tick down once per round and expire on their own, but they
don't clear just by leaving combat — if you win a fight while still
bleeding or stunned, you'll carry it into whatever you do next
(including your next fight) until it wears off or you pay to clear it
at Doc Wire's Clinic. Enemy status effects don't carry over — they
reset with each new fight.

Currently: Street Gangers, Chrome Beasts, and Scrap Dog Vex/The Widow
(Pit) can inflict Bleeding; Rogue Drones and Corp Patrol Troopers can
inflict Stunned. Ironclad Marta (Pit) doesn't inflict anything. On
your side, Razor Claws causes Bleeding and Target-Lock Eyes causes
Stunned.

## Contracts

12 contracts total across two boards — the Fixer Board and Endr3am's
board at the Chrome Noodle Bar. Contracts chain "talk" (visit a
location) and "kill" (defeat a named enemy) steps, accepted, tracked,
and turned in at their own board even if the steps happen elsewhere.
Completing one pays credits, XP, and reputation.

Three gates control what's on offer: **Reputation** (Fixer Board),
**Charisma** (Endr3am's board), and **Level** (both boards, tied to
the same tiers that unlock tougher Undercity enemies — several
higher-tier contracts specifically ask you to take down a Ronin
Netrunner, Corp Strike Team, or Chrome Beast). Some contracts stack
two gates at once for the harder jobs. A locked contract always shows
exactly what you're short on.

## Checking your status

From inside the hub, press **[I]** at the "Where to?" prompt to pull up
your full character info: attributes, credits/banked, reputation and
contract counts, cyberware loadout, active status effects, and a kill
tally grouped by faction. This doesn't cost a turn.

Enemies belong to a faction: **Street Gang** (Street Gangers), **Corp**
(Rogue Drones, Corp Patrol Troopers, Corp Strike Teams), **Ronin**
(Ronin Netrunners), **Feral** (Chrome Beasts), and **Gladiator** (the
Pit roster). The kill tally groups by faction first, then breaks down
by individual enemy underneath.

Press **[?]** the same way to reopen this guide mid-session.

## Saving

One JSON save file per character, named after them. The game saves
automatically whenever you leave the hub back to the main menu.

## What's not built yet

A few things mentioned in the game's design notes but not implemented:

- Charisma only gates two contracts — no effect on combat, dialogue,
  or shop prices.
- No ability/skill system — RoboDOJO trains stats, not abilities.
- No fetch/deliver contracts — only talk/kill steps exist so far.
