"""Wrench -- optimizer/completionist Street Samurai. Grinds RoboDOJO
training, chases contracts and Pit tiers, checks the shop's sell path,
plays multiple days to see the daily economy loop (market rotation,
training cap reset)."""
from driver import (
    Session, create_character, check_info, leave_and_sleep, resume_character, save_slug_index,
    visit_chrome_noodle_bar, visit_undercity, visit_netvault, visit_doc_wire, visit_hyphen8d,
    visit_robodojo, visit_the_pit, visit_fixer_board,
)

NAME = "0WrenchQA"
COMBAT = ["A", "A", "S", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A"]


def run() -> bool:
    s = Session("wrench")
    try:
        create_character(s, NAME, "S")

        # Day 1: train hard, bank credits, take a contract, one fight for XP.
        visit_robodojo(s, "A", COMBAT, "A", None)
        visit_robodojo(s, "D", COMBAT, "A", None)
        visit_netvault(s, "D", "20")
        visit_fixer_board(s, "1")
        visit_undercity(s, "F", COMBAT, "A")
        check_info(s)
        leave_and_sleep(s, COMBAT, "A")

        # Day 2: resume, hit the Pit, try the shop's sell path, train a third bout.
        resume_character(s, save_slug_index(NAME))
        visit_the_pit(s, "1", COMBAT, "A")
        visit_hyphen8d(s, "B", "1")
        visit_hyphen8d(s, "S", "1")
        visit_robodojo(s, "T", COMBAT, "A", None)
        check_info(s)
        leave_and_sleep(s, COMBAT, "A")

        # Day 3: quick contract-board check, then wrap.
        resume_character(s, save_slug_index(NAME))
        visit_fixer_board(s, "1")
        visit_chrome_noodle_bar(s, "B", None)
        check_info(s)
        leave_and_sleep(s, COMBAT, "A")

        print("WRENCH: completed OK")
        return True
    except Exception as e:
        print(f"WRENCH: FAILED -- {e}")
        return False
    finally:
        s.close()


if __name__ == "__main__":
    run()
