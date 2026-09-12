"""Desktop tests for calc/dietry.py using the stub casioplot."""
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests" / "stub"))
sys.path.insert(1, str(ROOT / "calc"))

import builtins
import os
import tempfile

import casioplot as cp


def _no_input(*_a):
    raise EOFError("no console in tests")


builtins.input = _no_input
cp.keys += [0, 91]      # dietry calls main() on import: press "0" so it exits
import dietry as dt
import dtsave

dtsave.SAVE_FILE = tempfile.gettempdir() + "/dt_test_save.txt"  # never the repo
if os.path.exists(dtsave.SAVE_FILE):
    os.remove(dtsave.SAVE_FILE)      # a leftover would load into later tests

CODE = {v: k for k, v in dt.KEYS.items()}


def press(*chars):
    for ch in chars:
        cp.keys.extend([0, CODE[ch]])   # release, then press


# 1. d2 match streak: 2,2,2 -> $2,$4,$6, match 1,2,3
g = dt.Game()
earn, match = [], []
for v in (2, 2, 2):
    g.on_roll_done(v)
    earn.append(g.last_earnings)
    match.append(g.match_length)
assert earn == [2, 4, 6], earn
assert match == [1, 2, 3], match

# 2. bust at x1.5 pays round(1.5)=2, wipes progress and streak
g.money_mult_level = 2
lines = g.on_roll_done(1)
assert g.last_earnings == 2 and g.progress == 0 and g.match_length == 0
assert ("BUST! Progress wiped (-6).", dt.RED) in lines, lines

# 3. GDScript rounding
assert dt.gd_round(2.5) == 3 and dt.gd_round(2.4) == 2
g = dt.Game()
g.money_mult_level = 1
assert g.calculate_earnings(2) == 3

# 4. match level 4, streak 3 -> 4 + 3*1 = 7
g.match_mult_level = 4
g.match_length = 3
assert g.match_multiplier() == 7.0

# 5. buying everything costs exactly $18,530
g = dt.Game()
g.money = 18530
for key, *_ in dt.UPGRADES:
    while "MAXED" not in g.buy(key)[0]:
        pass
assert g.money == 0 and g.total_spent == 18530
assert g.splash.next() == dt.MILESTONES["spent"][18530]
assert dt.Game().buy("2") == ("Need $25 for Dice (you have $0).", dt.RED)

# 6. milestones fire once, highest only
s = dt.Splash()
s.report("rolls", 9)
assert s.next() in dt.RANDOM_SPLASHES
s.report("rolls", 10)
assert s.next() == "Ten rolls. A promising start."
s.report("rolls", 10)
assert s.next() in dt.RANDOM_SPLASHES
s.report("rolls", 300)
assert s.next() == dt.MILESTONES["rolls"][250]
random.seed(1)
s = dt.Splash()
seq = [s.next() for _ in range(200)]
assert all(len(set(seq[i:i + 6])) == 6 for i in range(len(seq) - 5))

# 7. win at >= 500
g = dt.Game()
g.progress = 495
g.on_roll_done(6)
assert g.won and g.progress == 501

# 8. roll timing matches dice.gd exactly: 12 ticks, weights lerp(1, 6)
for duration in (3.0, 1.4, 0.6):
    weights = [1.0 + 5.0 * (i / 11.0) for i in range(12)]
    expect = [duration * w / sum(weights) for w in weights]
    got = dt.build_delays(duration)
    assert len(got) == 12 and all(abs(a - b) < 1e-12 for a, b in zip(got, expect))
    assert abs(sum(got) - duration) < 1e-9
    assert abs(got[-1] / got[0] - 6.0) < 1e-9

# 9. the font is measured, not guessed. The stub is proportional, with
# the real device's metrics: "M" 8px, "i" 4px, digits 8px, space 6px.
dt.CHAR_W, dt.MAX_W, dt.LINE_H = 99, 99, 99
dt._WIDTHS.clear()
dt.measure_font()
expect = cp.advance(dt.SAMPLE) / float(len(dt.SAMPLE))
assert abs(dt.CHAR_W - expect) < 0.05, (dt.CHAR_W, expect)
assert dt.MAX_W == 8 and dt.LINE_H == 13, (dt.MAX_W, dt.LINE_H)
assert dt.MENU_Y + 7 * dt.LINE_H <= dt.H

# 9b. exact per-string widths, including a thin "-" the old probe missed
for s in ("M" * 20, "Money: $99983692", "-------/    \\-------", "iiii"):
    assert dt.text_w(s) == cp.advance(s), (s, dt.text_w(s), cp.advance(s))
assert dt.text_w("M" * 20) == 160
dt._WIDTHS.clear()

# 10. menu labels, including "Upgrade" on 4 and 5
assert dt.menu_lines(dt.Game()) == [
    "1. Roll (d2)", "2. Upgrade Dice (d2 -> d4)  $25", "3. Upgrade Speed (3s -> 2.6s)  $50",
    "4. Upgrade Money Mult (x1 -> x1.25)  $40", "5. Upgrade Match Bonus (x2 -> x2.5)  $20",
    "6. Help", "0. Exit"]
assert all(len(l) <= dt.COLS for page in dt.HELP_PAGES for l in page)
assert all(len(l) <= dt.COLS for l in dt.menu_lines(dt.Game()))

# 11. the star: hand-tuned on the device, so no character-grid symmetry
# check here - the font is proportional, so equal character counts do not
# mean equal widths. Just guard the things that would break drawing.
assert all(row.isascii() and "_" not in row for row in dt.WIN_ART)
assert max(len(row) for row in dt.WIN_ART) <= 30
assert any("your did it" in row for row in dt.WIN_ART)

# 12. splash lines are centred on their measured width: equal margins
del cp.frames[:], cp.problems[:]
g = dt.Game()
for splash in ("seal", "The house always wins.", "You miss 100% of the rolls you don't take.",
               "'It is mathematically proven that on average your partner"):
    dt.render(splash, [], g)
    for x, _y, s in [c[:3] for c in cp.frames[-1] if c[2] in dt.wrap(splash, dt.COLS)]:
        left, right = x, dt.W - (x + cp.advance(s))
        assert abs(left - right) <= 1, (s, left, right)

# 12b. a huge pile of money must not run into the progress readout
# (it did on the real calculator at $99,983,692)
del cp.problems[:]
g = dt.Game()
g.money, g.progress = 99983692, 101
dt.render("seal", [("Rolled a 6 on the d20!  +6 progress, +$24", dt.BLACK)], g)
assert not cp.problems, cp.problems
money_x = [c[0] for c in cp.frames[-1] if c[2].startswith("Money:")][0]
prog_x = [c[0] for c in cp.frames[-1] if c[2].startswith("Progress:")][0]
assert prog_x >= money_x + cp.advance("Money: $99983692"), (money_x, prog_x)

# 13. scripted session: help (2 pages), failed buy, winning roll, play again, exit
del cp.frames[:], cp.frame_pixels[:], cp.problems[:]
g = dt.Game()
g.progress, g.die_level = 499, 6
real_randint = dt.random.randint
dt.random.randint = lambda a, b: b          # every roll shows the top face
press("6", "1", "1", "2", "1", "1", "0")
dt.main(g)
dt.random.randint = real_randint
assert not cp.keys, "unused keys: %r" % cp.keys
assert g.progress == 0 and not g.won and g.total_rolls == 0   # reset by play again
assert not cp.problems, cp.problems
# the startup font probe draws no frames: it never calls show_screen
assert len(cp.frames) == 21, len(cp.frames)


def find(needle, last=False):
    hits = [i for i, f in enumerate(cp.frames) if any(needle in c[2] for c in f)]
    assert hits, needle
    return hits[-1] if last else hits[0]


# the last frame is the exit screen, not a blank one
assert any("Press AC to exit" in c[2] for c in cp.frames[-1]), cp.as_text(cp.frames[-1])

# the win screen's star block is centred as a whole, clear of the stats
win = cp.frames[find("YOU WIN!")]
star_x = sorted({c[0] for c in win if c[2] in dt.WIN_ART})
assert len(star_x) == 1 and star_x[0] > 0, star_x

for name, i in (("start", find("Welcome to DIE TRYING.")),
                ("help p1", find("HOW TO PLAY")),
                ("after buy", find("Dice already MAXED")),
                ("last roll tick", find("Rolling", last=True)),
                ("win", find("YOU WIN!")),
                ("new game", find("New game started"))):
    print("---- %s (%d set_pixel calls) ----" % (name, cp.frame_pixels[i]))
    print(cp.as_text(cp.frames[i]))

# 14. a mid-game frame with a match and a bust
g = dt.Game()
g.money = 120
g.on_roll_done(2)
dt.render("Somewhere, a d20 is laughing at you.", g.on_roll_done(2), g)
print("---- match frame ----")
print(cp.as_text(cp.frames[-1]))
dt.render("The house always wins.", g.on_roll_done(1), g)
print("---- bust frame ----")
print(cp.as_text(cp.frames[-1]))
assert not cp.problems, cp.problems

# ---- saving ---------------------------------------------------------------
if os.path.exists(dtsave.SAVE_FILE):
    os.remove(dtsave.SAVE_FILE)

# 15. round trip: every stored field survives, and spent/earned are derived
rng = random.Random(7)
for _ in range(400):
    a = dt.Game()
    a.die_level = rng.randrange(7)
    a.speed_level = rng.randrange(8)
    a.money_mult_level = rng.randrange(6)
    a.match_mult_level = rng.randrange(5)
    # Realistic states only: a game cannot have more wipes than rolls, nor
    # money before its first roll - load_code rejects both as corruption.
    a.total_rolls = rng.randrange(8192)
    a.bust_count = rng.randrange(min(2048, a.total_rolls) + 1)
    a.progress = rng.randrange(512) if a.total_rolls else 0
    a.money = rng.randrange(65536) if a.total_rolls else 0
    code = dt.save_code(a)
    assert len(code) == 10 and all(c in dt.ALPHABET for c in code), code
    b = dt.Game()
    assert dt.load_code(b, code), code
    for f in ("die_level", "speed_level", "money_mult_level", "match_mult_level",
              "progress", "money", "total_rolls", "bust_count"):
        assert getattr(a, f) == getattr(b, f), (f, code, getattr(a, f), getattr(b, f))
    assert b.total_spent == dt.spent_from_levels(a)
    assert b.total_earned == b.money + b.total_spent

# 16. the grouped form shown on the exit screen loads the same
a = dt.Game()
a.die_level, a.progress, a.money, a.total_rolls = 5, 321, 4242, 99
code = dt.save_code(a)
assert dt.grouped(code) == code[:5] + " " + code[5:]
b = dt.Game()
assert dt.load_code(b, dt.grouped(code))
assert (b.die_level, b.progress, b.money, b.total_rolls) == (5, 321, 4242, 99)

# 17. clamping: too-big values saturate instead of corrupting other fields
a = dt.Game()
a.money, a.progress, a.total_rolls, a.bust_count = 99983692, 519, 70000, 5000
b = dt.Game()
assert dt.load_code(b, dt.save_code(a))
assert (b.money, b.progress, b.total_rolls, b.bust_count) == (65535, 511, 8191, 2047)

# 18. with no checksum, only range validation rejects typos. Measure the
# share caught so the trade-off stays documented, and make sure a rejected
# code never half-loads.
a = dt.Game()
a.die_level, a.money, a.progress, a.total_rolls = 4, 1234, 250, 77
code = dt.save_code(a)
tried = caught = 0
for i in range(len(code)):
    for repl in dt.ALPHABET:
        if repl == code[i]:
            continue
        tried += 1
        victim = dt.Game()
        victim.money, victim.die_level = 999, 2
        if not dt.load_code(victim, code[:i] + repl + code[i + 1:]):
            caught += 1
            assert (victim.money, victim.die_level) == (999, 2)   # untouched
rate = 100.0 * caught / tried
# Sanity checks only, no checksum: levels range, wipes <= rolls, and
# money/progress requiring a nonzero roll count.
assert rate > 8.0, rate    # measured ~11%; no checksum fits in 60 bits
print("single-char typos rejected by sanity checks: %.0f%%" % rate)
assert dt.load_code(dt.Game(), code)          # a good code still loads
assert not dt.load_code(dt.Game(), code + "xx")   # wrong length
assert not dt.load_code(dt.Game(), "")
assert not dt.load_code(dt.Game(), "!!!!!!!!!!")  # not in the alphabet

# 19. file round trip, and boot_load prefers the file over typing
a = dt.Game()
a.money, a.progress, a.die_level, a.total_rolls = 5000, 400, 3, 123
assert dtsave.save_file(a)
b = dt.Game()
assert dtsave.boot_load(b) == "Save file loaded."
assert (b.money, b.progress, b.die_level, b.total_rolls) == (5000, 400, 3, 123)
os.remove(dtsave.SAVE_FILE)

# 19b. on the real fx-CG100 open() returns None instead of raising, and
# writes are blocked: save_file must give up and stop retrying, and
# autosave must fall back to printing the code to the Shell.
real_open = builtins.open
real_print = builtins.print
printed = []
builtins.open = lambda *_a, **_k: None
builtins.print = lambda *a: printed.append(" ".join(str(x) for x in a))
dtsave._FILE_OK = True
a = dt.Game()
a.money, a.die_level, a.total_rolls = 4321, 2, 60
assert not dtsave.save_file(a)
assert dtsave._FILE_OK is False          # stops retrying every roll
assert not dtsave.load_file(dt.Game())
dtsave.autosave(a)
builtins.open, builtins.print = real_open, real_print
assert printed == [dt.save_code(a)], printed
b = dt.Game()
assert dt.load_code(b, printed[0]) and b.money == 4321
dtsave._FILE_OK = True

# 20. with no file, boot_load takes a typed code; a bad one starts a new game
builtins.input = lambda *_a: code
b = dt.Game()
assert dtsave.boot_load(b) == "Save code loaded."
assert b.die_level == 4 and b.money == 1234
builtins.input = lambda *_a: "NOTACODE"
b = dt.Game()
assert dtsave.boot_load(b) == "Code not recognised - new game."
assert b.money == 0 and b.progress == 0
builtins.input = lambda *_a: ""
assert dtsave.boot_load(dt.Game()) == "Welcome to DIE TRYING."
builtins.input = _no_input

# 21. loading does not re-fire milestones already earned
b = dt.Game()
b.money, b.total_rolls = 20000, 600
assert dt.load_code(b, dt.save_code(b))
assert b.splash.next() in dt.RANDOM_SPLASHES     # no milestone queued

# 22. the exit screen shows a loadable code, grouped and in the big font
del cp.frames[:]
g = dt.Game()
g.money, g.progress, g.die_level, g.total_rolls = 777, 42, 2, 55
press("0")
dt.main(g)
label = [c for c in cp.frames[-1] if c[2] == "Save code:"]
big = [c for c in cp.frames[-1] if c[4] == "large"]
assert len(label) == 1 and len(big) == 1, cp.as_text(cp.frames[-1])
assert " " in big[0][2] and len(big[0][2]) == 11, big[0][2]
# the big code must be centred on its own width, not the small font's
bx, _by, bs = big[0][0], big[0][1], big[0][2]
left, right = bx, dt.W - (bx + cp.advance(bs, "large"))
assert abs(left - right) <= 2, ("save code off-centre", left, right)
b = dt.Game()
assert dt.load_code(b, big[0][2])
assert (b.money, b.progress, b.die_level) == (777, 42, 2)

print("ALL CALC TESTS PASSED")
