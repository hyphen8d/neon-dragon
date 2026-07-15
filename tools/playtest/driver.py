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
   custom prompt strings), never the raw label.

2. read_key() -- on a real terminal *and* in the piped fallback -- only
   ever consumes a single character of input, discarding the rest of a
   multi-digit line. This means multi-digit menu choices (item #10+,
   save #10+) cannot actually be selected in the shipped game today; see
   save_slug_index() below for how this driver works around it for its
   own purposes, and flag it to whoever's reading this if it's still true.
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


ANCHOR_HUB_RETURN = r"Press any key to return to the central hub"
ANCHOR_NEXT_ROUND = r"Press any key for the next round"
ANCHOR_LEVELUP = r"Put a bonus point somewhere"
ANCHOR_VICTORY = r"goes down\."
ANCHOR_DEFEAT = r"You go down hard"
ANCHOR_FLEE = r"(You slip into the shadows|You break line of sight|A sharp turn down an alley)"
ANCHOR_RECHARGE = r"is still recharging"
ANCHOR_WHERE_TO = r"Where to\?"
ANCHOR_NEW_MERC = r"ew Merc"  # "[N]ew Merc" -- the literal bracket breaks up "New"
ANCHOR_LEAVE_CONFIRM = r"Head back to the safehouse"
ANCHOR_NAME_PROMPT = r"What do they call you on the street\?"
ANCHOR_CHOOSE_PATH = r"Choose your path"
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


def create_character(s: Session, name: str, class_key: str) -> None:
    s.expect_any([ANCHOR_NEW_MERC])
    s.send("N")
    s.expect_any([ANCHOR_NAME_PROMPT])
    s.send(name)
    s.expect_any([ANCHOR_CHOOSE_PATH])
    s.send(class_key)
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
    s.send("U")
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
    return run_combat_loop(s, combat_actions, level_up_pick)


def visit_chrome_noodle_bar(s: Session, choice: str, contract_index: str | None) -> None:
    s.send("C")
    s.expect_any([ARRIVE_CHROME_BAR])
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
    s.expect_any([r"What'll it be\?"])
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
