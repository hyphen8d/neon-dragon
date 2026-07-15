"""Rook -- cautious first-timer, Street Samurai. Reads the help screen
before doing anything, plays conservatively, checks status often, banks
credits, doesn't gamble."""
from driver import (
    Session, create_character, check_info, leave_and_sleep, resume_character, save_slug_index,
    visit_chrome_noodle_bar, visit_undercity, visit_netvault, visit_doc_wire, visit_hyphen8d,
    visit_robodojo, visit_the_pit, visit_fixer_board,
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

        print("ROOK: completed OK")
        return True
    except Exception as e:
        print(f"ROOK: FAILED -- {e}")
        return False
    finally:
        s.close()


if __name__ == "__main__":
    run()
