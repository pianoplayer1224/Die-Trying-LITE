"""Tests for the terminal version, die_trying.py."""
import builtins
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import die_trying as dt


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
assert g.match_multiplier() == 7.0

# 5. buying everything costs exactly $18,530
g = fresh()
g.state.money = 18530
for key in dt.UPGRADES:
    while "MAXED" not in g.buy(key):
        pass
assert g.state.money == 0 and g.state.total_spent == 18530
assert g.splash.next() == dt.MILESTONES["spent"][18530]
assert "Not enough money" in fresh().buy("2")

# 6. menu labels, including "Upgrade" on 4 and 5
assert dt.menu_lines(fresh()) == [
    "1. Roll (d2)", "2. Upgrade Dice (d2 -> d4)  $25", "3. Upgrade Speed (3s -> 2.6s)  $50",
    "4. Upgrade Money Mult (x1 -> x1.25)  $40", "5. Upgrade Match Bonus (x2 -> x2.5)  $20",
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

print("ALL DESKTOP TESTS PASSED")
