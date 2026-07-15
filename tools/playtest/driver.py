"""Drives Neon Dragon's main.py through a scripted-but-reactive playthrough
so a persona script can play a full session and dump a transcript for
review. Not part of the game itself -- a QA tool.

Uses a plain (non-pty) subprocess: main.py's own read_key() (engine/ui.py)
falls back to line-buffered stdin reads when stdin isn't a tty -- this
project's own comments call that out as the intended path for scripted
playthroughs -- and Rich disables all ANSI styling when stdout isn't a
terminal, so the output we capture is plain, unstyled text.

Two non-obvious gotchas baked into this file, so a future edit doesn't
reintroduce them:

1. Rich's bracket-hotkey rendering (hotkey_bracket in engine/ui.py) prints
   real bracket punctuation around the hotkey letter, e.g. "[N]ew Merc" --
   splitting "New" across a literal "]". Anchors below match the text
   *after* the bracket (e.g. "ew Merc"), or plain narration text that was
   never hotkey-bracketed in the first place (arrival flavor paragraphs,
   custom prompt strings), never the raw label. This isn't just for
   anchors matched via expect_any() -- a plain containment check (`"x" in
   buffer`) is just as vulnerable, and the bracket can land *inside* a
   label instead of at the front: "Intimidate"'s hotkey is "N", which
   sits at index 1, so the rendered text is "I[N]timidate" -- checking
   for the substring "Intimidate" (see _fight_or_intimidate below) always
   fails silently, no exception, it just never matches. Both this and the
   "Slice Drop Box" -> "[S]lice Drop Box" version of the same trap
   (visit_undercity's coerce handling) shipped broken once each before
   being caught, so don't assume a literal label string is safe to search
   for anywhere in this file without checking how it actually renders.

2. read_key() used to -- on a real terminal *and* in the piped fallback --
   only ever consume a single character of input, discarding the rest of
   a multi-digit line, so item/save #10+ couldn't actually be selected.
   Fixed in engine/ui.py (read_choice() now reads a full Enter-confirmed
   line whenever a choice set has any two-digit entry). save_slug_index()
   below predates that fix and is kept anyway -- it's a cheap, harmless
   way to guarantee a low-digit index regardless of how many saves exist.
"""

from __future__ import annotations

import re
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python3"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

LOG_DIR = Path(__file__).resolve().parent / "logs"

sys.path.insert(0, str(PROJECT_DIR))


def save_slug_index(name: str) -> str:
    """The saves/ directory tends to accumulate old dev-test characters, so
    the "Load Merc" menu's 1-based index for a given persona isn't reliably
    low -- compute it from the same sorted listing the game itself uses
    (engine.save.list_saves). Persona names are prefixed with "0" (see
    e.g. rook.py) specifically so this always lands in the single digits,
    sidestepping the multi-digit read_key() bug documented up top."""
    from engine.save import _save_path, list_saves

    target_slug = _save_path(name).stem
    slugs = list_saves()
    return str(slugs.index(target_slug) + 1)


ANCHOR_HUB_RETURN = r"UPLINK IDLE"
ANCHOR_NEXT_ROUND = r"NEXT ROUND QUEUED"
ANCHOR_LEVELUP = r"Put a bonus point somewhere"
ANCHOR_VICTORY = r"goes down\."
ANCHOR_DEFEAT = r"You go down hard"
ANCHOR_FLEE = r"(You slip into the shadows|You break line of sight|A sharp turn down an alley)"
ANCHOR_RECHARGE = r"is still recharging"
ANCHOR_WHERE_TO = r"SELECT ROUTING"
ANCHOR_NEW_MERC = r"ew Merc"  # "[N]ew Merc" -- the literal bracket breaks up "New"
ANCHOR_LEAVE_CONFIRM = r"Head back to the safehouse"
# Every press_any_key() call in the game (engine/ui.py) uses a message
# ending in this phrase, regardless of context -- a "talk"-type contract
# auto-completing/advancing on arrival (notify_step, called by nearly every
# non-Undercity/Pit location before its own menu) prints one of these gates
# an unpredictable number of times, so any visit_* helper that sends its
# real menu choice immediately after the arrival text -- without accounting
# for this -- risks that choice being silently swallowed as the answer to
# a notification gate instead of the intended menu selection.
ANCHOR_PRESS_ANY_KEY = r"PRESS ANY KEY"
ANCHOR_NAME_PROMPT = r"What do they call you on the street\?"
ANCHOR_CHOOSE_PATH = r"Choose your path"
# engine/prologue.py's four press_any_key beats plus its forced tutorial
# fight, run once for every new merc between class selection and the first
# hub screen. ANCHOR_PROLOGUE_STABILIZED only prints on a loss; the
# PROLOGUE COMPLETE gate always prints regardless of outcome.
ANCHOR_PROLOGUE_WAKE = r"REGAINING CONSCIOUSNESS"
ANCHOR_PROLOGUE_DEBT = r"DEBT LOGGED"
ANCHOR_PROLOGUE_CHROME = r"CHROME LINKED"
ANCHOR_PROLOGUE_THREAT = r"THREAT DETECTED"
ANCHOR_PROLOGUE_STABILIZED = r"STABILIZED"
ANCHOR_PROLOGUE_COMPLETE = r"PROLOGUE COMPLETE"
# Printed in the enemy panel of the combat HUD every round -- the earliest
# reliable sign combat has actually started, as opposed to a non-combat
# resolution (a clean Slice Drop Box crack, a Hunt Cache dead sector, a
# RoboDOJO daily-cap refusal) that goes straight to ANCHOR_HUB_RETURN.
ANCHOR_COMBAT_STARTED = r"Scan: "

# Picked from the very start of each location's arrival flavor paragraph --
# panel text wraps at ~114 cols and long/late phrases can straddle a wrap
# boundary (border char + newline land mid-phrase), so keep these short and
# near the opening line where wrapping hasn't kicked in yet.
ARRIVE_CHROME_BAR = r"Steam curls off the noodle vats"
ARRIVE_NETVAULT = r"Chrome and glass, cold as a server room"
ARRIVE_HYPHEN8D = r"Wires hang from the ceiling like vines"
ARRIVE_DOC_WIRE = r"A converted shipping container wired for surgery"

DEFAULT_TIMEOUT = 12


class Session:
    def __init__(self, logname: str):
        LOG_DIR.mkdir(exist_ok=True)
        self.log = open(LOG_DIR / f"{logname}.log", "w")
        self.proc = subprocess.Popen(
            [PYTHON, "main.py"],
            cwd=PROJECT_DIR,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.buffer = ""
        self.pos = 0  # cursor: only text at/after this offset is "unseen"
        self.lock = threading.Lock()
        self.reader = threading.Thread(target=self._pump, daemon=True)
        self.reader.start()

    def _pump(self) -> None:
        while True:
            ch = self.proc.stdout.read(1)
            if ch == "":
                break
            with self.lock:
                self.buffer += ch
            self.log.write(ch)
            self.log.flush()

    def send(self, text: str) -> None:
        self.log.write(f"\n>>> SEND: {text!r}\n")
        self.log.flush()
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def expect_any(self, patterns: list[str], timeout: int = DEFAULT_TIMEOUT) -> int:
        """Blocks until one of `patterns` appears in *unseen* output (i.e.
        at or after self.pos), then advances the cursor past that match so
        a later call can't re-match the same old occurrence -- otherwise a
        generic anchor seen once (e.g. the hub-return prompt) would satisfy
        every future wait for it instantly, regardless of actual game state."""
        deadline = time.time() + timeout
        compiled = [re.compile(p) for p in patterns]
        while time.time() < deadline:
            with self.lock:
                unseen = self.buffer[self.pos :]
            best = None  # (match_start, match_end, pattern_index)
            for i, pat in enumerate(compiled):
                m = pat.search(unseen)
                if m and (best is None or m.start() < best[0]):
                    best = (m.start(), m.end(), i)
            if best is not None:
                self.pos += best[1]
                return best[2]
            if self.proc.poll() is not None:
                self.log.write(f"\n!!! DRIVER: process exited while waiting for {patterns}\n")
                raise RuntimeError(f"process exited while waiting for one of: {patterns}")
            time.sleep(0.05)
        self.log.write(f"\n!!! DRIVER: TIMEOUT waiting for {patterns}\n")
        raise RuntimeError(f"TIMEOUT waiting for one of: {patterns}")

    def ack(self) -> None:
        """Send a blank line to satisfy a pending press_any_key() read.
        Every ANCHOR_HUB_RETURN / ANCHOR_NEXT_ROUND match leaves the game
        blocked on exactly one more line of input -- forgetting this call
        after detecting one of those anchors hangs the whole session."""
        self.send("")

    def close(self) -> None:
        try:
            self.send("Q")
            self.proc.wait(timeout=5)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        self.log.close()


def run_combat_loop(
    s: Session, action_cycle: list[str], level_up_pick: str, final_anchor: str = ANCHOR_HUB_RETURN, ack_final: bool = True
) -> str:
    """Sends combat actions until the fight resolves. Returns 'won', 'lost',
    or 'fled'. Call this once combat is confirmed underway (its first round's
    HUD/action-menu is already on screen) -- it sends the first action itself.
    `final_anchor` is whatever text follows combat resolution -- normally the
    hub-return prompt, but the sleep/ambush path goes straight to the main
    menu instead with no press_any_key gate (ack_final=False)."""
    idx_cycle = 0
    round_guard = 0
    while True:
        round_guard += 1
        if round_guard > 40:
            raise RuntimeError("combat loop exceeded round guard -- likely stuck")
        action = action_cycle[idx_cycle % len(action_cycle)]
        idx_cycle += 1
        s.send(action)
        idx = s.expect_any(
            [ANCHOR_RECHARGE, ANCHOR_LEVELUP, ANCHOR_NEXT_ROUND, ANCHOR_VICTORY, ANCHOR_DEFEAT, ANCHOR_FLEE],
            timeout=DEFAULT_TIMEOUT,
        )
        if idx == 0:  # recharging -- resend a safe fallback this same round
            s.send("A")
            idx2 = s.expect_any(
                [ANCHOR_LEVELUP, ANCHOR_NEXT_ROUND, ANCHOR_VICTORY, ANCHOR_DEFEAT, ANCHOR_FLEE],
                timeout=DEFAULT_TIMEOUT,
            )
            idx = idx2 + 1
        if idx in (1, 3):
            # Victory. "{enemy} goes down." always prints *before* any
            # "LEVEL UP!"/bonus-point prompt in the same burst of output,
            # so matching whichever text comes first (ANCHOR_VICTORY, since
            # it's textually earlier) does NOT mean no level-up is coming --
            # it may still be sitting unread just past this match. Always
            # check for a pending level-up prompt before treating the fight
            # as fully resolved, regardless of which anchor fired first.
            if idx == 1:
                # This match *was* the bonus-point prompt -- answer it
                # before checking what comes next (another level, or done).
                s.send(level_up_pick)
            while True:
                nxt = s.expect_any([ANCHOR_LEVELUP, final_anchor], timeout=DEFAULT_TIMEOUT)
                if nxt == 1:
                    if ack_final:
                        s.ack()
                    return "won"
                s.send(level_up_pick)
        if idx == 2:  # next round -- consume the pause, then pick the next action
            s.ack()
            continue
        if idx == 4:  # defeat
            s.expect_any([final_anchor], timeout=DEFAULT_TIMEOUT)
            if ack_final:
                s.ack()
            return "lost"
        if idx == 5:  # fled
            s.expect_any([final_anchor], timeout=DEFAULT_TIMEOUT)
            if ack_final:
                s.ack()
            return "fled"


def _run_prologue(s: Session) -> None:
    """Walks the new-merc prologue (engine/prologue.py): four press_any_key
    beats, then a forced tutorial fight against a fixed, 0 credit/0 XP
    "Malfunctioning Med-Drone" -- weak enough, and reward-less enough, that
    a flat "always Attack" script is fine regardless of which persona is
    being created. Only called from create_character(); personas don't
    need to know this scene exists."""
    s.expect_any([ANCHOR_PROLOGUE_WAKE])
    s.ack()
    s.expect_any([ANCHOR_PROLOGUE_DEBT])
    s.ack()
    s.expect_any([ANCHOR_PROLOGUE_CHROME])
    s.ack()
    s.expect_any([ANCHOR_PROLOGUE_THREAT])
    s.ack()
    s.expect_any([ANCHOR_COMBAT_STARTED])
    result = run_combat_loop(
        s,
        ["A"],
        "A",
        final_anchor=rf"({ANCHOR_PROLOGUE_STABILIZED}|{ANCHOR_PROLOGUE_COMPLETE})",
        ack_final=False,
    )
    s.ack()  # answers whichever gate run_combat_loop stopped at
    if result == "lost":
        # STABILIZED fires first on a loss -- PROLOGUE COMPLETE always
        # follows it, and still needs its own ack.
        s.expect_any([ANCHOR_PROLOGUE_COMPLETE])
        s.ack()


def create_character(s: Session, name: str, class_key: str) -> None:
    """A leftover save from a *previous, failed* run under this persona's
    name (e.g. this driver's own subprocess got killed mid-session) makes
    "New Merc" reject the name as a duplicate and silently re-prompt --
    every subsequent send() in this function would then land on the wrong
    prompt, desyncing the whole session in a way that's very confusing to
    debug from a transcript alone. Deleting any pre-existing save for this
    exact name first makes every run self-cleaning regardless of how the
    last one ended."""
    from engine.save import _save_path, delete_save, list_saves

    slug = _save_path(name).stem
    if slug in list_saves():
        delete_save(slug)

    s.expect_any([ANCHOR_NEW_MERC])
    s.send("N")
    s.expect_any([ANCHOR_NAME_PROMPT])
    s.send(name)
    s.expect_any([ANCHOR_CHOOSE_PATH])
    s.send(class_key)
    _run_prologue(s)
    s.expect_any([ANCHOR_WHERE_TO])


def leave_and_sleep(s: Session, combat_actions: list[str], level_up_pick: str) -> None:
    s.send("L")
    s.expect_any([ANCHOR_LEAVE_CONFIRM])
    s.send("Y")
    # Sleeping may trigger a Faction Heat ambush (a full combat) before the
    # Daily Data Feed prints and we're dumped back at the main menu -- that
    # path has no press_any_key gate at all, unlike every other combat site.
    idx = s.expect_any([ANCHOR_COMBAT_STARTED, ANCHOR_NEW_MERC], timeout=DEFAULT_TIMEOUT)
    if idx == 1:
        return
    run_combat_loop(s, combat_actions, level_up_pick, final_anchor=ANCHOR_NEW_MERC, ack_final=False)


def resume_character(s: Session, slug_index: str) -> None:
    s.send("L")
    s.expect_any([r"Load which merc"])
    s.send(slug_index)
    s.expect_any([ANCHOR_WHERE_TO])


def visit_undercity(s: Session, choice: str, combat_actions: list[str], level_up_pick: str) -> str | None:
    """A "coerce" quest step pending against this location (see
    engine/hub.py's _check_coerce_step) prints a Y/N prompt *before* the
    normal arrival text's "Slice Drop Box" menu -- speculatively check for
    it with a short timeout first (most visits won't have one pending, so
    this is a fast no-op almost every time) and resolve it (always saying
    Y) before falling through to the normal menu wait."""
    s.send("U")
    reached_menu = False
    try:
        s.expect_any([r"Attempt to coerce the target"], timeout=0.5)
        s.send("Y")
        # Past this point we're waiting for the real hotkey menu, not the
        # arrival flavor text's plain mention of "Slice Drop Box" (already
        # behind us) -- the rendered menu option is hotkey-bracketed as
        # "[S]lice Drop Box", so the matchable substring is "lice Drop Box"
        # (same convention as ANCHOR_NEW_MERC's "ew Merc" for "[N]ew Merc").
        idx = s.expect_any([ANCHOR_COMBAT_STARTED, r"lice Drop Box"], timeout=DEFAULT_TIMEOUT)
        if idx == 0:
            run_combat_loop(s, combat_actions, level_up_pick, final_anchor=r"lice Drop Box", ack_final=False)
        reached_menu = True
    except RuntimeError:
        pass
    if not reached_menu:
        s.expect_any([r"Slice Drop Box"])
    s.send(choice)
    if choice == "L":
        s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return None
    idx = s.expect_any([ANCHOR_COMBAT_STARTED, ANCHOR_HUB_RETURN], timeout=DEFAULT_TIMEOUT)
    if idx == 1:
        s.ack()
        return None
    return _fight_or_intimidate(s, combat_actions, level_up_pick)


ANCHOR_ATTACK_OPTION = r"\[A\]ttack"


def _fight_or_intimidate(s: Session, combat_actions: list[str], level_up_pick: str) -> str:
    """Call right after ANCHOR_COMBAT_STARTED matches for a fight that
    *could* offer Intimidate (i.e. a random Undercity encounter -- Pit/
    RoboDOJO fights never do, see Enemy.min_level in engine/combat.py).
    "[A]ttack" and "I[N]timidate" are both printed as part of the *same*
    single options line (run_combat's `OPTION_SEPARATOR.join(...)`), with
    Attack always first -- so racing the two against each other via
    expect_any() (an earlier version of this helper's mistake) is wrong,
    not just imprecise: Attack, being first in reading order, always
    "wins" the race regardless of whether Intimidate is also present
    later on the very same line. What's actually needed is a containment
    check, not a race. expect_any([ANCHOR_ATTACK_OPTION]) first
    guarantees the whole options line has landed in the buffer (it's one
    atomic console.print() call, so if "[A]ttack" is visible the rest of
    the same line already is too) -- only then is peeking the remaining
    buffer for Intimidate reliable, no sleep/timing guess involved.

    The containment check itself has to look for "timidate", not
    "Intimidate" -- hotkey_bracket() splits the label around its hotkey
    letter, and "N" sits at index 1 of "Intimidate", so the rendered text
    is literally "I[N]timidate". The contiguous substring "Intimidate"
    never actually appears (a second version of this helper's mistake,
    the same bracket-splitting trap as ANCHOR_NEW_MERC's "ew Merc")."""
    s.expect_any([ANCHOR_ATTACK_OPTION], timeout=DEFAULT_TIMEOUT)
    with s.lock:
        unseen = s.buffer[s.pos :]
    if "timidate" in unseen:
        s.send("N")
        s.expect_any([ANCHOR_HUB_RETURN], timeout=DEFAULT_TIMEOUT)
        s.ack()
        return "intimidated"
    return run_combat_loop(s, combat_actions, level_up_pick)


def _settle_notifications(s: Session, ready_anchor: str) -> None:
    """After a location's arrival text, an unpredictable number of "talk"
    contract notifications (Contract updated/complete) can each print
    their own press_any_key gate before the location's real menu appears
    -- and a completing contract can itself push the character over a
    level threshold, which prints its own "Put a bonus point somewhere"
    prompt (engine/leveling.py's check_level_up, called *before*
    print_quest_result's own press_any_key) that needs a real letter
    answer, not a blank ack. Always answers "A" (Attack) for one of these
    -- always a valid choice for every class -- rather than threading each
    persona's preferred pick through every location helper for what's a
    rare, incidental level-up outside of combat. Loops until `ready_anchor`
    -- text that only appears once the real per-location menu/Interaction
    Deck is on screen -- shows up, so the caller's next s.send(choice)
    always lands on the intended prompt instead of an interstitial one."""
    while True:
        idx = s.expect_any([ANCHOR_PRESS_ANY_KEY, ANCHOR_LEVELUP, ready_anchor], timeout=DEFAULT_TIMEOUT)
        if idx == 2:
            return
        if idx == 1:
            s.send("A")
        else:
            s.ack()


def visit_chrome_noodle_bar(s: Session, choice: str, contract_index: str | None) -> None:
    s.send("C")
    s.expect_any([ARRIVE_CHROME_BAR])
    _settle_notifications(s, r"uy a round")
    s.send(choice)
    if choice in ("L", "B"):
        s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return
    if choice == "C":
        idx = s.expect_any([r"Take a contract\? \(0 to cancel\)", ANCHOR_HUB_RETURN])
        if idx == 0:
            s.send(contract_index or "0")
            s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()


def visit_netvault(s: Session, choice: str, amount: str | None) -> None:
    s.send("N")
    s.expect_any([ARRIVE_NETVAULT])
    _settle_notifications(s, r"Banking")
    s.send(choice)
    if choice == "L":
        s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return
    idx = s.expect_any([r"Deposit how much", r"Withdraw how much", ANCHOR_HUB_RETURN])
    if idx in (0, 1):
        s.send(amount or "0")
        s.expect_any([ANCHOR_HUB_RETURN])
    s.ack()


def visit_hyphen8d(s: Session, choice: str, item_index: str | None) -> None:
    s.send("H")
    s.expect_any([ARRIVE_HYPHEN8D])
    _settle_notifications(s, r"Shop Menu")
    s.send(choice)
    if choice == "L":
        s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return
    if choice == "B":
        s.expect_any([r"Buy which item\? \(0 to cancel\)"])
        s.send(item_index or "0")
        s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return
    if choice == "S":
        idx = s.expect_any([r"Sell which item\? \(0 to cancel\)", ANCHOR_HUB_RETURN])
        if idx == 0:
            s.send(item_index or "0")
            s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return
    if choice == "M":
        s.expect_any([r"Buy which prototype\? \(0 to cancel\)"])
        s.send(item_index or "0")
        s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()


def visit_doc_wire(s: Session, choice: str, amount: str | None) -> None:
    s.send("D")
    s.expect_any([ARRIVE_DOC_WIRE])
    _settle_notifications(s, r"Clinic Menu")
    s.send(choice)
    if choice == "L":
        s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return
    if choice == "H":
        idx = s.expect_any([r"Heal how much HP", ANCHOR_HUB_RETURN])
        if idx == 0:
            s.send(amount or "0")
            s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return
    if choice == "C":
        idx = s.expect_any([r"Clear those for", ANCHOR_HUB_RETURN])
        if idx == 0:
            s.send("Y")
            s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return
    if choice == "B":
        s.expect_any([r"Buy which item\? \(0 to cancel\)"])
        s.send(amount or "0")
        s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()


def visit_robodojo(
    s: Session, choice: str, combat_actions: list[str], level_up_pick: str, ability_index: str | None
) -> str | None:
    s.send("R")
    _settle_notifications(s, r"AWAITING INPUT")
    s.send(choice)
    if choice == "L":
        s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return None
    if choice == "B":
        idx = s.expect_any([r"Learn which ability\? \(0 to cancel\)", ANCHOR_HUB_RETURN])
        if idx == 0:
            s.send(ability_index or "0")
            s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return None
    # A/D/T -- either a sparring bout starts, or the daily cap message fires.
    idx = s.expect_any([ANCHOR_COMBAT_STARTED, ANCHOR_HUB_RETURN], timeout=DEFAULT_TIMEOUT)
    if idx == 1:
        s.ack()
        return None
    return run_combat_loop(s, combat_actions, level_up_pick)


def visit_the_pit(s: Session, gladiator_index: str, combat_actions: list[str], level_up_pick: str) -> str | None:
    s.send("P")
    s.expect_any([r"Step into the ring\? \(0 to cancel\)"])
    s.send(gladiator_index)
    if gladiator_index == "0":
        s.expect_any([ANCHOR_HUB_RETURN])
        s.ack()
        return None
    s.expect_any([ANCHOR_COMBAT_STARTED], timeout=DEFAULT_TIMEOUT)
    return run_combat_loop(s, combat_actions, level_up_pick)


def visit_fixer_board(s: Session, contract_index: str | None) -> None:
    s.send("F")
    _settle_notifications(s, r"Contract Board")
    idx = s.expect_any([r"Take a contract\? \(0 to cancel\)", ANCHOR_HUB_RETURN])
    if idx == 0:
        s.send(contract_index or "0")
        s.expect_any([ANCHOR_HUB_RETURN])
    s.ack()


def check_info(s: Session) -> None:
    s.send("I")
    s.expect_any([ANCHOR_HUB_RETURN])
    s.ack()


def check_help(s: Session) -> None:
    s.send("?")
    s.expect_any([ANCHOR_HUB_RETURN])
    s.ack()


def check_archives(s: Session) -> None:
    """Visits the [A]rchives Datashard screen and immediately backs out
    (0 to cancel) regardless of how many shards have been found."""
    s.send("A")
    idx = s.expect_any([r"Read which fragment\? \(0 to cancel\)", ANCHOR_HUB_RETURN])
    if idx == 0:
        s.send("0")
        s.expect_any([ANCHOR_HUB_RETURN])
    s.ack()


# Cycled across Undercity actions inside grind_day rather than always
# "F" (Find a Fight) -- Slice Drop Box and Hunt Cache are the only two
# ways a Datashard can turn up (engine/datashards.py's
# maybe_find_datashard), so a grind that never visits them will never
# find one no matter how many fights it plays.
_UNDERCITY_ACTION_CYCLE = ["S", "F", "H"]


def grind_day(
    s: Session,
    combat_actions: list[str],
    level_up_pick: str,
    fights: int = 3,
    actions: list[str] | None = None,
) -> None:
    """One day of repeatable, level-agnostic play: a fixed number of
    Undercity actions (by default cycling Slice Drop Box / Find a Fight /
    Hunt Cache, so a coerce prompt pending on a Chrome Noodle Bar contract
    also gets a chance to fire, since visit_undercity's ARRIVE text prints
    every visit, and Datashards get a real shot at turning up), then
    sleep. Pass `actions=["F"]` for guaranteed-combat days instead -- the
    default rotation trades some XP volume for Slice Drop Box/Hunt Cache
    coverage, since only Find a Fight guarantees a fight (a clean Slice
    Drop Box crack or a quiet Hunt Cache sweep earns no XP at all), which
    matters if a persona specifically needs to level up quickly (e.g. to
    reliably clear a stat threshold within a bounded number of days).
    Used to grind a persona from early-game into a genuinely advanced
    state without hand-writing dozens of unique days."""
    cycle = actions or _UNDERCITY_ACTION_CYCLE
    for i in range(fights):
        action = cycle[i % len(cycle)]
        visit_undercity(s, action, combat_actions, level_up_pick)
    leave_and_sleep(s, combat_actions, level_up_pick)
