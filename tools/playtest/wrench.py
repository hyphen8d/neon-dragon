"""Wrench -- optimizer/completionist Street Samurai. Grinds RoboDOJO
training, chases contracts and Pit tiers, checks the shop's sell path,
plays multiple days to see the daily economy loop (market rotation,
training cap reset). Also the persona that most deliberately leans into
Charisma via the level-up bonus point, on the theory a completionist
eventually wants every door open -- an Attack-focused early game to be
strong enough for the Pit's top tier, then a Charisma-only finishing
stretch specifically to clear the Charisma 8+ threshold a few NPCs gate
their warmer dialogue behind (Static Rin, The Fixer, Hyphen8d) and to
get a real shot at Endr3am's Charisma-gated contracts, including the
"coerce"-type one succeeding cleanly instead of always failing the
check the way a low-Charisma run necessarily would."""
from driver import (
    Session, create_character, check_info, check_archives, grind_day, leave_and_sleep,
    resume_character, save_slug_index, visit_chrome_noodle_bar, visit_undercity, visit_netvault,
    visit_doc_wire, visit_hyphen8d, visit_robodojo, visit_the_pit, visit_fixer_board,
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

        # Days 4-13: Attack-focused completionist grind -- alternates
        # training, contract-board checks (both boards), and Undercity
        # actions, occasionally banking a Charisma point but mostly
        # building the combat power needed for a real shot at the Pit's
        # top tier later.
        for day in range(10):
            resume_character(s, save_slug_index(NAME))
            pick = "C" if day % 3 == 2 else "A"
            if day % 3 == 0:
                visit_robodojo(s, "A", COMBAT, pick, None)
            if day % 4 == 1:
                visit_chrome_noodle_bar(s, "C", "1")
            if day % 4 == 2:
                visit_fixer_board(s, "1")
            if day % 5 == 0:
                visit_the_pit(s, "2", COMBAT, pick)
            grind_day(s, COMBAT, pick, fights=2)

        # Days 14-23: Charisma-only finishing stretch -- every level-up
        # bonus point goes to Charisma, no exceptions, so it reliably
        # clears the 8+ threshold instead of trickling up by chance.
        # Keeps checking Endr3am's board along the way, since a rising
        # Charisma can unlock "Silver Tongue" (or a similar coerce
        # contract) mid-stretch and this gives it a real chance to fire
        # and, this time, potentially pass the check outright instead of
        # always failing into the fallback fight.
        for day in range(14):
            resume_character(s, save_slug_index(NAME))
            if day % 3 == 0:
                visit_chrome_noodle_bar(s, "C", "1")
            if day % 4 == 2:
                visit_chrome_noodle_bar(s, "B", None)  # a Buy a Round shot too
            # Guaranteed-combat days here, not the usual S/F/H rotation --
            # a clean Slice Drop Box crack or a quiet Hunt Cache sweep
            # earns no XP at all, and this stretch specifically needs
            # level-ups (each one a chance to bank another Charisma point)
            # on a bounded day budget. Datashard/economy variety already
            # gets covered by this persona's earlier days and by rook/ghost.
            grind_day(s, COMBAT, "C", fights=3, actions=["F"])

        # Endgame check: full completionist status sweep, including a
        # deliberate revisit of every NPC gated on Charisma 8+ (Static
        # Rin, The Fixer, Hyphen8d) so their warmer dialogue pool, if
        # unlocked, actually gets read out this run instead of just
        # inferred from the stat.
        resume_character(s, save_slug_index(NAME))
        check_info(s)
        check_archives(s)
        visit_chrome_noodle_bar(s, "L", None)
        visit_fixer_board(s, "0")
        visit_hyphen8d(s, "S", "1")
        visit_the_pit(s, "5", COMBAT, "A")  # go for the top tier now
        leave_and_sleep(s, COMBAT, "C")

        print("WRENCH: completed OK")
        return True
    except Exception as e:
        print(f"WRENCH: FAILED -- {e}")
        return False
    finally:
        s.close()


if __name__ == "__main__":
    run()
