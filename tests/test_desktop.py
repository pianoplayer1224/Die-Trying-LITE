"""Tests for the terminal version, die_trying.py."""
import builtins
import os
import pathlib
import random
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / "calc"))
import die_trying as dt
import dtgame          # the calculator's rules, for the cross-load test
import dtsave          # the calculator's codec

dt.SAVE_FILE = tempfile.gettempdir() + "/dt_desktop_test.save"   # never the repo


def fresh():
    return dt.Game(dt.random.Random(0))


# 1. d2 match streak: 2,2,2 -> $2,$4,$6
g = fresh()
earn, match = [], []
for v in (2, 2, 2):
    g.on_roll_done(v)
    earn.append(g.state.last_earnings)
    match.append(g.state.match_length)
assert earn == [2, 4, 6], earn
assert match == [1, 2, 3], match

# 2. bust at x1.5 pays round(1.5)=2, wipes progress and streak
g.state.money_mult_level = 2
lines = g.on_roll_done(1)
assert g.state.last_earnings == 2 and g.state.progress == 0
assert g.state.match_length == 0 and g.state.best_run == 6
assert "BUST! Progress wiped (-6)." in lines, lines

# 3. GDScript rounding: 2 * 1.25 = 2.5 -> 3 (Python round would give 2)
g = fresh()
g.state.money_mult_level = 1
assert g.calculate_earnings(2) == 3
assert dt.gd_round(2.5) == 3 and dt.gd_round(2.4) == 2

# 4. match level 4, streak 3 -> 7
g.state.match_mult_level = 4
g.state.match_length = 3
assert g.match_multiplier() == 11.0

# 5. buying everything costs exactly $28,530
g = fresh()
g.state.money = 28530
for key in dt.UPGRADES:
    while "MAXED" not in g.buy(key):
        pass
assert g.state.money == 0 and g.state.total_spent == 28530
assert g.splash.next() == dt.MILESTONES["spent"][28530]
assert "Not enough money" in fresh().buy("2")

# 6. menu labels, including "Upgrade" on 4 and 5
assert dt.menu_lines(fresh()) == [
    "1. Roll (d2)", "2. Upgrade Dice (d2 -> d4)  $25", "3. Upgrade Speed (3s -> 2.6s)  $50",
    "4. Upgrade Money Mult (x1 -> x1.25)  $40", "5. Upgrade Match Bonus (x2 -> x3)  $20",
    "6. Help", "", "0. Exit"]

# 7. milestones fire once, highest only
s = dt.Splash()
s.report("rolls", 9)
assert s.next() not in dt.MILESTONES["rolls"].values()
s.report("rolls", 10)
assert s.next() == "Ten rolls. A promising start."
s.report("rolls", 10)
assert s.next() in dt.RANDOM_SPLASHES
s.report("rolls", 300)
assert s.next() == dt.MILESTONES["rolls"][250]

# 8. win stops the playtime clock; reset clears the game
g = fresh()
g.state.progress = 495
g.on_roll_done(6)
assert g.state.game_won and g.state.progress == 501
t = g.state.playtime
time.sleep(0.05)
assert g.state.playtime == t
g.state.reset()
assert g.state.progress == 0 and not g.state.game_won

# 9. roll delays match dice.gd
d = dt.build_delays(3.0)
assert len(d) == 12 and abs(sum(d) - 3.0) < 1e-9 and abs(d[-1] / d[0] - 6) < 1e-9

# 10. full win -> play again -> exit through main(), sleep/input patched
dt.time.sleep = lambda _s: None
g = fresh()
g.state.progress = 499
g.state.die_level = 6
answers = iter(["1", "y", "0"])
builtins.input = lambda _p="": next(answers)
dt.main(g)
assert g.state.progress == 0 and not g.state.game_won

# ---- saving ---------------------------------------------------------------
if os.path.exists(dt.SAVE_FILE):
    os.remove(dt.SAVE_FILE)

# 11. round trip through a 10-character code
rng = random.Random(11)
for _ in range(200):
    a = fresh()
    s = a.state
    s.die_level = rng.randrange(7)
    s.speed_level = rng.randrange(9)
    s.money_mult_level = rng.randrange(6)
    s.match_mult_level = rng.randrange(5)
    s.total_rolls = rng.randrange(8192)
    s.bust_count = rng.randrange(min(2048, s.total_rolls) + 1)
    s.progress = rng.randrange(512) if s.total_rolls else 0
    s.money = rng.randrange(65536) if s.total_rolls else 0
    code = dt.save_code(s)
    assert len(code) == 10 and all(c in dt.ALPHABET for c in code), code
    b = fresh()
    assert dt.load_code(b, code), code
    for f in ("die_level", "speed_level", "money_mult_level", "match_mult_level",
              "progress", "money", "total_rolls", "bust_count"):
        assert getattr(s, f) == getattr(b.state, f), (f, code)
    assert b.state.total_spent == dt.spent_from_levels(s)
    assert b.state.total_earned == b.state.money + b.state.total_spent

# 12. codes are interchangeable with the calculator edition, both ways
calc = dtgame.Game()
calc.die_level, calc.speed_level, calc.money_mult_level = 6, 5, 4
calc.match_mult_level, calc.progress, calc.money = 3, 101, 18636
calc.total_rolls, calc.bust_count = 792, 78
calc_code = dtsave.save_code(calc)
here = fresh()
assert dt.load_code(here, calc_code), calc_code
assert (here.state.money, here.state.progress, here.state.die_level,
        here.state.total_rolls, here.state.bust_count) == (18636, 101, 6, 792, 78)
assert dt.save_code(here.state) == calc_code          # and identical going back
back = dtgame.Game()
assert dtsave.load_code(back, dt.save_code(here.state))
assert (back.money, back.total_rolls, back.bust_count) == (18636, 792, 78)

# 13. rejection: bad codes leave the game untouched
victim = fresh()
victim.state.money, victim.state.die_level = 999, 2
for bad in ("", "toolongcode12", "!!!!!!!!!!", "0000000001"):  # last: money, no rolls
    assert not dt.load_code(victim, bad), bad
    assert (victim.state.money, victim.state.die_level) == (999, 2)
assert dt.load_code(fresh(), dt.grouped(calc_code))    # grouped form still loads

# 14. the file carries playtime and best run, which the code cannot
g = fresh()
g.state.money, g.state.progress, g.state.total_rolls = 4242, 300, 400
g.state.bust_count, g.state.best_run = 40, 480
g.state.start_time = time.monotonic() - 125.0
assert dt.save_file(g)
b = fresh()
assert dt.load_file(b)
assert (b.state.money, b.state.progress, b.state.total_rolls) == (4242, 300, 400)
assert b.state.best_run == 480
assert 120 < b.state.playtime < 135, b.state.playtime

# 15. boot_load prefers the file; then a typed code; then a new game
b = fresh()
assert dt.boot_load(b) == "Save loaded." and b.state.money == 4242
os.remove(dt.SAVE_FILE)
builtins.input = lambda _p="": calc_code
b = fresh()
assert dt.boot_load(b) == "Save code loaded." and b.state.money == 18636
assert os.path.exists(dt.SAVE_FILE)     # a typed code is written straight out
os.remove(dt.SAVE_FILE)
builtins.input = lambda _p="": "NOTACODE"
b = fresh()
assert dt.boot_load(b) == "Code not recognised - starting a new game."
assert b.state.money == 0
builtins.input = lambda _p="": ""
assert dt.boot_load(fresh()) == "Welcome to DIE TRYING."

# 16. playing writes the save, and Help shows the transferable code
if os.path.exists(dt.SAVE_FILE):
    os.remove(dt.SAVE_FILE)
dt.time.sleep = lambda _s: None
g = fresh()
answers = iter(["1", "6", "0"])
builtins.input = lambda _p="": next(answers)
dt.main(g)                       # a supplied game must not prompt for a code
assert os.path.exists(dt.SAVE_FILE)
saved = open(dt.SAVE_FILE).read().split()
assert len(saved[0]) == 10 and len(saved) == 3, saved
b = fresh()
assert dt.load_code(b, saved[0]) and b.state.total_rolls == 1
os.remove(dt.SAVE_FILE)

print("ALL DESKTOP TESTS PASSED")
