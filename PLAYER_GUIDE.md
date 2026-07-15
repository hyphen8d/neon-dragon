# Neon Dragon — Player Guide

Welcome to Neo Meridian. This guide covers what everything actually
does in the game as it stands right now.

## Getting started

You play as a cyber mercenary — a merc — scraping by in Neo Meridian.
From the main menu: **New Merc** creates a character (pick a name and
a class), **Load Merc** resumes a saved one, **Quit** exits. There's
no daily turn limit — play as long as you like in one sitting.

## Classes

Two classes right now, each a different balance of the same stats (a
third, charisma-focused class is pulled pending a redesign):

- **Street Samurai** — high HP and Attack, low Tech. Built to punch
  through fights with raw damage.
- **Netrunner** — low HP and Attack, high Tech. Built around the
  Tech/Hack combat action instead of Attack.

## Stats

- **HP** — health. Hits zero and you're patched up at 1 HP with a
  medical bill (see Combat).
- **Attack** — damage on the Attack combat action.
- **Defense** — reduces incoming damage in combat.
- **Tech** — damage on the Tech/Hack combat action.
- **Charisma** — gates the two higher-tier contracts Endr3am offers at
  the Chrome Noodle Bar (see below), knocks the price down at
  Hyphen8d's Hut (2% off per point, capped at 40%), talks down
  your trauma bill if you go down in a fight (3% off per point,
  capped at 45% — see Combat), unlocks warmer/secret-revealing
  dialogue from several NPCs at 8+ (see Charisma and dialogue, below),
  and can talk your way past certain contract targets instead of
  fighting them outright (the **coerce** step type).
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
  +1 Tech, and a full heal — **plus you pick one of Attack/Defense/Tech
  to bump an extra point**, the one build-crafting choice you get
  outside of gear. A single big XP reward can trigger multiple
  level-ups at once, prompting you for a bonus point each time.
  Charisma doesn't grow on level-up — it comes from cyberware, not
  training (RoboDOJO doesn't offer it).

## The Hub — Neo Meridian

Every session loops through this menu. The Character Info line on the
main menu now shows how many contracts you've got active, so you don't
have to hunt for a reminder. NPCs also aren't purely random flavor —
a handful will start drawing from a different line pool once you've
actually earned it (a body count, a debt, a stash of Quantum Cores,
proven reliability) instead of repeating generic chatter forever. A
few even notice what's physically on you — walk into Doc Wire's
Clinic with the right piece of chrome bolted to your arm and he'll
have something to say about it, not just about your credit balance.
Locations:

### Chrome Noodle Bar
Static Rin, the bartender, has a pool of flavor lines, and it's a step
in several contracts. It's also a free rest stop: if you're below half
HP, you're topped up to half for free — doesn't do anything once
you're at or above that (Doc Wire's Clinic is still the only way to
heal further or clear status effects). Good for one free top-up a
day — if you've already used it and drop below half HP again before
you sleep, the bar won't heal you a second time; the free rest
resets when you sleep.

From there you pick one thing to do:

- **Buy a round** (25 credits) — not a flat dice roll, a little
  narrative each time. Something happens first — a Scav tries to
  pick your pocket, a jittery netrunner rambles about ghosts in the
  subnet, a ganger challenges you to synth-arm wrestling — and *then*
  the payoff lands: most of the time it's gossip (+2 reputation),
  sometimes a permanent +1 to Attack, Defense, or Tech, and sometimes
  you get thrown out **Drunk** — a status effect that weakens your
  next fight's Attack/Tech rolls until it wears off or you pay Doc
  Wire to cure it. (The arm-wrestling win has its own downside risk —
  read the flavor text before you celebrate.) Rin only pours you one
  round a day — the option resets when you sleep. Put in enough work
  against Corp targets and she starts comping it outright.
- **Check the shady booth in the back** — Endr3am, a tall merc, runs
  his own contract board here, separate from the Fixer Board and
  gated by **Charisma** instead of Reputation. Charisma only comes
  from Hyphen8d's Hut skin-slot cyberware (Synth-Derm +3, Mirrorskin
  +6) — RoboDOJO doesn't train it.

### Undercity
No longer a single random roll — you pick your approach. The arrival
screen carries a LOCAL AREA NETSCAN readout laying out all three
options and their risk profile, so check that before you choose:

- **[S] Slice Drop Box** — crack a corporate hardware drop box bolted
  to a wall somewhere in the sublevels. Odds and payout scale with
  your Tech stat. Crack it clean and you skim a credit-chip off the
  tray; trip the seal's Black-ICE counter-intrusion and it pins your
  location, forcing a fight against a Corp-faction enemy (Rogue Drone,
  Corp Patrol Trooper, or Corp Strike Team) right then. This is Tech's
  main use outside combat. Rarely, a clean crack exposes the box's
  logic core and a **Quantum Core** clicks free — it doesn't hum right,
  and it doesn't look manufactured. Check your Character Info screen
  for a running count. What they're for isn't posted anywhere.
- **[F] Find a Fight** — guarantees a combat encounter (still random
  which enemy), for when you specifically want XP/credits without
  gambling on nothing happening.
- **[H] Hunt Cache** — a passive scanner sweep for forgotten
  black-market drop boxes: the old low-risk pool, a cache (free
  credits) or a dead sector (nothing at all). Low risk, not zero risk:
  even with no Faction Heat there's a flat 10% chance someone else is
  sweeping the same frequency and jumps you instead, so it's not a
  farm-forever loop. Running hot (see Faction Heat below) adds a
  separate, steeper 15% chance of a faction-specific ambush on top of
  that baseline.

Three tougher enemies only show up in the fight/drop-box pools once
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

Your Charisma haggles the sticker price down — 2% off per point,
capped at 40% off. The catalog shows your actual price next to the
listed one whenever you're getting a discount, and the affordability
check (including trade-in credit) always uses your discounted price,
not the sticker price.

Hyphen8d only stocks **4 items at a time**, re-rolled from the full
catalog whenever you sleep — so what's on the shelf changes daily,
and there's no guarantee the item you want is in stock today. Each
day also brings one random market event affecting a single slot
(arm/eyes/spine/skin): either a price break or a price surge, shown
both at the Hut and on your Daily Data Feed (see Sleeping below). It
stacks with your Charisma discount rather than replacing it.

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
Two things happen here: stat training and learning abilities.

**Training** a stat (Attack, Defense, or Tech — not Charisma, which
comes from cyberware instead) is a real fight against a themed
sparring drone now, not an instant purchase — losing (or fleeing)
costs you nothing beyond whatever the fight itself did (HP, a
trauma bill if you go down). Winning permanently trains the stat up
by 1 and *then* charges a credit fee, scaled to the stat's current
value — 40 credits base, +5 credits for every point you already
have (so Attack 8 costs 80 on a win, Attack 20 costs 140). No cap on
the cost itself, so grinding one stat sky-high gets progressively
more expensive rather than staying flat forever. That fee is
deducted even if it takes you into debt — same as a trauma bill.

You only get **3 sparring bouts a day**, shared across all three
stats (not 3 each) — a fourth attempt just gets you waved off the
mats until you sleep. An attempt costs you one of those 3 whether
you win or lose, so a loss still eats into the day's quota.

**Learning an ability** ([B]) is a one-time credit purchase,
independent of class and permanent once bought. A learned ability
shows up as an extra combat option in every future fight, right
alongside your class's special, each with its own cooldown:

- **Adrenal Surge** (120 credits) — heal 15 HP on demand mid-fight,
  4-round cooldown.
- **Kill Switch** (180 credits) — a guaranteed hit that ignores
  enemy dodge entirely, unlike a normal Attack. 4-round cooldown.

### The Pit
Choose a fight from a fixed roster of five gladiators (two evenly
matched at the bottom tier, then three tougher tiers above that),
toughest paying out the most. Wins grant credits, XP, and reputation
— this is one of the two ways to earn reputation (the other is Fixer
Board contracts). Beating the current toughest gladiator has the
same rare shot at a Quantum Core as a clean Slice Drop Box crack
does.

Beat **Kingpin Draxx**, the current top-tier gladiator, and it sticks:
the announcer greets you as reigning champion on every future visit.
It doesn't end there, either — he holds a grudge. Don't be surprised
if he (and a couple of his crew) show up out in the Undercity to try
to take the belt back the hard way.

### Fixer Board
Accept, track, and turn in contracts from The Fixer. Each contract is
a short chain of steps — talk to someone, kill something, then report
back here to collect the reward. **Some contracts require a minimum
reputation before The Fixer will offer them** — if you see a note
about locked contracts, go earn reputation at the Pit or by finishing
lower-tier contracts first.

## Combat

Turn-based. The screen redraws fresh at the start of every round: your
status on the left, the enemy's on the right, both with a block-bar HP
meter alongside the numbers. Below that HUD, only that round's action
text streams in — your move, then the enemy's — tagged with a bright
`»»»` if it's something you did or a dim, indented `«««` if it's the
enemy's turn, so you can tell at a glance who did what without reading
every line. You'll be asked to press a key before the next round clears
the screen, so nothing flashes past unread.

The enemy's panel also runs a live sensor scan: a fixed description of
what you're looking at, plus a readout line that shifts as their HP
drops — "Systems Nominal" above 75%, "Structural Degradation Detected"
between 30-75%, "Catastrophic Hardware Failure Imminent" below 30%.

Each round you pick:

- **Attack** — damage based on your Attack stat.
- **Tech/Hack** — damage based on your Tech stat.
- **Defend** — halves incoming damage that round.
- **Flee** — coin-flip chance to escape with no reward either way.

Attack and Tech/Hack narration is gear-aware — a bare fist reads
nothing like a Chrome Arm punch or Razor Claws. The verb itself also
scales with how hard you hit: a 2-damage tap "grazes," an 8-damage hit
"strikes," and anything 9+ "shatters" or worse. Same system applies to
enemy hits against you.

Each class also gets a signature move, on a 3-round cooldown (usable
turn 1, then locked out for 3 rounds after each use):

- **Street Samurai — [S]amurai Slash** — 1.5x damage and guarantees
  Bleeding on the enemy (a normal Attack's Bleed only comes from
  Razor Claws cyberware, and even then only by chance). Still dodgeable
  like a normal Attack.
- **Netrunner — [O]verride System** — no damage, but guarantees 2
  rounds of Stun. Not a physical hit, so enemy dodge doesn't apply.

Abilities learned at RoboDOJO (see below) stack on top of your class
special as more of these extra combat options, each with its own
independent cooldown — a Street Samurai who's bought both abilities
fights with three extra options beyond the core four.

While a move is on cooldown, the combat menu shows rounds remaining
next to its name; picking it early just tells you it's still
recharging without costing your turn.

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
income outgrows a flat fee. Your Charisma talks the trauma team down
— 3% off the bill per point, capped at 45% off — applied after the
level scaling. Banked credits at NetVault are never touched by this.

### Status effects

Status effects show up everywhere as a colored hazard-tag badge —
`[ /// BLEED ]`, `[ !!! STUN ]`, `[ ERR: DRUNK ]` — in the combat HUD,
your Character Info screen, and anywhere else they're listed, so
they're easy to spot at a glance. Status effects go both ways:

- **Bleeding** — 3 damage at the start of the affected side's turn,
  for the effect's duration. Droids (Rogue Drone) have no blood to
  spill — Bleed never lands on them, whether from an enemy ability,
  Razor Claws, or Samurai Slash's guaranteed proc.
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

Currently: Street Gangers, Sewer Hounds, Ganger Bosses, Chrome
Beasts, and Scrap Dog Vex/The Widow (Pit) can inflict Bleeding;
Rogue Drones, Corp Patrol Troopers, Corp Blacksite Enforcers, and
Volt Jockey (Pit) can inflict Stunned. Ironclad Marta and Kingpin
Draxx (Pit) don't inflict anything. On your side, Razor Claws causes
Bleeding and Target-Lock Eyes causes Stunned.

## Contracts

20 contracts total across two boards — the Fixer Board and Endr3am's
board at the Chrome Noodle Bar. Contracts chain steps — "talk" (visit a
location), "kill" (defeat a named enemy), "fetch" (buy a specific
cyberware item from Hyphen8d's Hut), "deliver" (hand a fetched item over
to whoever asked for it — no trade-in refund, it's a gift, not a sale),
"pay" (pay a flat credit amount at a location), and "coerce" (talk your
way past a target instead of fighting them — see Charisma and dialogue,
below) — accepted, tracked, and turned in at their own board even if the
steps happen elsewhere. Completing one pays credits, XP, and reputation.

Talk and kill steps advance the moment you visit the right place or land
the killing blow. Deliver, pay, and coerce don't — all three take
something real from you (an item, credits, or a shot at avoiding a
fight), so all three ask you to confirm (Yes/No) before it happens, and
tell you exactly what you're still short on if you can't complete them
yet (how much more you need to pay, that you haven't bought the item
yet, or the Charisma a coerce attempt needs).

Three gates control what's on offer: **Reputation** (Fixer Board),
**Charisma** (Endr3am's board), and **Level** (both boards, tied to
the same tiers that unlock tougher Undercity enemies — several
higher-tier contracts specifically ask you to take down a Ganger
Boss, Ronin Netrunner, Corp Strike Team, Chrome Beast, or Corp
Blacksite Enforcer). Some contracts stack
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

## Faction Heat

Kill more than 3 enemies of the same faction in a single day and you
build heat with them — currently only **Corp** and **Street Gang**
track heat, since they're the two factions organized enough to send
someone looking for you. While hot with a faction, there's a 15%
chance of a high-risk ambush from that faction: either interrupting a
Hunt Cache sweep in the Undercity, or catching you the moment you wake up
at the safehouse the next day. Heat resets every time you sleep (see
below), so it's a same-day consequence of a killing spree, not a
permanent grudge.

## Sleeping (Leaving the hub)

Pressing **[L]eave** at the hub asks you to confirm — it's a bigger
deal than a normal menu back-out, since it costs your daily Buy a
round, your Chrome Noodle Bar free rest, and your RoboDOJO sparring
bouts, and resets Faction Heat, Hyphen8d's stock, and today's market.
Confirm and your merc heads home to sleep, not straight back to the
main menu. That advances the day counter, fully
heals you, clears every status effect you're carrying, resolves
Faction Heat (above), rolls a new day at Hyphen8d's Hut (fresh stock
and market event), and prints a "Daily Data Feed" panel summarizing
where you stand — level, credits, reputation, kills by faction, and
today's Hyphen8d's Hut pricing. The feed leads with a bit of city
color first: a weather line and a fake news headline, different every
morning. Purely cosmetic — Neo Meridian keeps existing while you're
asleep, none of it changes your stats. Your day only advances when you
choose to leave; there's still no limit on how much you do at the hub
before then.

## Saving

One JSON save file per character, named after them. The game saves
automatically whenever you leave the hub, and also on exit — even an
unexpected one — so nothing since your last visit is lost.

## Achievements & Milestones

Certain milestones — beating specific enemies, hitting kill-count
thresholds, equipping enough cyberware at once, or training a stat high
enough — unlock a permanent Achievement, announced with a styled panel
the moment you earn it. Unlocked achievements are listed on your
Character Info (`[I]`) screen.

**RoboDOJO belt ranks** are part of this system: train Attack or
Defense up to 10 through RoboDOJO sparring (or any other means) and you
unlock "Black Belt (Attack)" / "Black Belt (Defense)", each of which
grants a small permanent bonus in combat on top of the stat itself —
it doesn't go away even if the stat changes later.

## Charisma and dialogue

High Charisma doesn't just gate contracts and discount gear — several
NPCs (Static Rin, The Fixer, Hyphen8d) open up entirely different lines
at Charisma 8+, more respectful in tone and occasionally letting slip
something they wouldn't tell just anyone.

Some Chrome Noodle Bar contracts include a **coerce** step: talk your
way past a target instead of fighting them outright. You'll be asked to
attempt it, with the Charisma requirement shown up front. Meet it, and
the job's done clean. Fall short and say yes anyway, and the attempt
goes sideways into a fight — win that fight and the job still gets
done, just the hard way.

## What's not built yet

A few things mentioned in the game's design notes but not implemented:

- A third, charisma-focused class is pulled pending a redesign.
