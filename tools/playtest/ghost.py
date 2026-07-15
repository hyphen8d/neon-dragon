"""Ghost -- reckless glass-cannon Netrunner. Dives into Undercity
repeatedly, spends down to zero, pokes at hidden/edge-case stuff (the
undocumented Black Market hotkey, cancel paths, insufficient-funds paths)
without reading anything first. Then just keeps diving, well past the
point it should still be a real fight, to see how the game handles a
player who never slows down."""
from driver import (
    Session, create_character, check_info, check_archives, grind_day, leave_and_sleep,
    resume_character, save_slug_index, visit_chrome_noodle_bar, visit_undercity, visit_netvault,
    visit_doc_wire, visit_hyphen8d, visit_robodojo, visit_the_pit, visit_fixer_board,
)

NAME = "0GhostQA"
COMBAT = ["T", "T", "T", "T", "T", "T", "T", "T", "T", "T", "T", "T", "T", "T", "T", "T", "T", "T", "T", "T"]


def run() -> bool:
    s = Session("ghost")
    try:
        create_character(s, NAME, "N")

        # Straight into the Undercity, no exploring the safe stuff first.
        visit_undercity(s, "S", COMBAT, "T")
        visit_undercity(s, "S", COMBAT, "T")
        visit_undercity(s, "F", COMBAT, "T")

        # Curiosity: try the hidden Black Market hotkey with zero Quantum Cores.
        visit_hyphen8d(s, "M", "1")
        # Edge case: withdraw with (likely) nothing banked.
        visit_netvault(s, "W", "9999")
        # Edge case: try to buy supplies with whatever's left.
        visit_doc_wire(s, "B", "1")
        visit_chrome_noodle_bar(s, "C", "1")
        check_info(s)
        leave_and_sleep(s, COMBAT, "T")

        resume_character(s, save_slug_index(NAME))
        visit_robodojo(s, "B", COMBAT, "T", "1")
        visit_undercity(s, "H", COMBAT, "T")
        visit_undercity(s, "H", COMBAT, "T")
        visit_the_pit(s, "4", COMBAT, "T")  # aim high, see what a mismatched fight looks like
        check_info(s)
        leave_and_sleep(s, COMBAT, "T")

        # Keep diving, no restraint, for as long as it takes to stop being
        # dangerous -- an occasional Charisma pick thrown in on level-up
        # rather than pure Tech-stacking, since that's what a real reckless
        # player might do on a whim rather than optimizing every point.
        for day in range(18):
            resume_character(s, save_slug_index(NAME))
            pick = "C" if day % 5 == 4 else "T"
            if day % 6 == 2:
                visit_chrome_noodle_bar(s, "C", "1")
            grind_day(s, COMBAT, pick, fights=4)

        resume_character(s, save_slug_index(NAME))
        check_info(s)
        check_archives(s)
        visit_the_pit(s, "4", COMBAT, "T")
        leave_and_sleep(s, COMBAT, "T")

        print("GHOST: completed OK")
        return True
    except Exception as e:
        print(f"GHOST: FAILED -- {e}")
        return False
    finally:
        s.close()


if __name__ == "__main__":
    run()
