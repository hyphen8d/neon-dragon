"""Rook -- cautious first-timer, Street Samurai. Reads the help screen
before doing anything, plays conservatively, checks status often, banks
credits, doesn't gamble. Grinds well past the early game to see how the
loop holds up once fights stop being a threat."""
from driver import (
    Session, create_character, check_info, check_archives, grind_day, leave_and_sleep,
    resume_character, save_slug_index, visit_chrome_noodle_bar, visit_undercity, visit_netvault,
    visit_doc_wire, visit_hyphen8d, visit_robodojo, visit_the_pit, visit_fixer_board,
)

NAME = "0RookQA"
COMBAT = ["A", "A", "A", "D", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A"]


def run() -> bool:
    s = Session("rook")
    try:
        # Reads the rules before making a character -- main menu's [H]elp
        # dumps the player guide straight back to the main menu, no gate.
        s.expect_any([r"ew Merc"])
        s.send("H")
        s.expect_any([r"ew Merc"])

        create_character(s, NAME, "S")
        check_info(s)

        # Day 1: cautious exploration -- rest stop, bank some credits, one safe fight.
        visit_chrome_noodle_bar(s, "L", None)
        visit_netvault(s, "D", "10")
        visit_undercity(s, "F", COMBAT, "D")
        check_info(s)
        visit_doc_wire(s, "H", "5")
        leave_and_sleep(s, COMBAT, "D")

        # Day 2: try the trainer and the shop, cautiously.
        resume_character(s, save_slug_index(NAME))
        visit_robodojo(s, "A", COMBAT, "D", None)
        visit_hyphen8d(s, "B", "1")
        visit_fixer_board(s, "1")
        check_info(s)
        leave_and_sleep(s, COMBAT, "D")

        # Days 3-17: grind well past the early game -- cautious Rook still
        # picks Defense most of the time, but occasionally banks a
        # Charisma point too (a real player exploring the new level-up
        # option, not a min-maxer). Chrome Noodle Bar's contract board is
        # checked periodically, since Charisma creeping up can unlock the
        # "coerce"-type contract, which visit_undercity now knows how to
        # answer if one comes up pending.
        for day in range(15):
            resume_character(s, save_slug_index(NAME))
            pick = "C" if day % 4 == 3 else "D"
            if day % 5 == 0:
                visit_chrome_noodle_bar(s, "C", "1")
            grind_day(s, COMBAT, pick, fights=3)

        # Endgame check: where does a cautious player actually end up?
        resume_character(s, save_slug_index(NAME))
        check_info(s)
        check_archives(s)
        visit_fixer_board(s, "1")
        visit_the_pit(s, "1", COMBAT, "D")
        leave_and_sleep(s, COMBAT, "D")

        print("ROOK: completed OK")
        return True
    except Exception as e:
        print(f"ROOK: FAILED -- {e}")
        return False
    finally:
        s.close()


if __name__ == "__main__":
    run()
