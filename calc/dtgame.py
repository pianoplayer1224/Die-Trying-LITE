# dtgame.py - rules for dietry.py (Die Trying, fx-CG100 edition).
# No drawing in here, which keeps it testable and keeps dietry.py under
# the calculator's 300-line limit. Same rules as die_trying.py.

import random
from dtdata import *

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
ORANGE = (224, 152, 47)
RED = (200, 30, 30)
GREEN = (30, 130, 60)


def num(v):
    # Float -> short text: 2.0 -> "2", 2.6 -> "2.6", 1.25 -> "1.25".
    s = "%.2f" % v
    while s.endswith("0"):
        s = s[:-1]
    if s.endswith("."):
        s = s[:-1]
    return s


def gd_round(x):
    # GDScript round(): halves go up (2.5 -> 3). Values are never negative.
    return int(x + 0.5)


def wrap(text, n):
    lines = []
    cur = ""
    for word in text.split(" "):
        if cur and len(cur) + 1 + len(word) > n:
            lines.append(cur)
            cur = word
        elif cur:
            cur = cur + " " + word
        else:
            cur = word
    lines.append(cur)
    return lines


def build_delays(duration):
    # Roll animation delays, each up to SLOWDOWN times the first.
    weights = []
    for i in range(TICK_COUNT):
        t = 0.0 if TICK_COUNT <= 1 else i / (TICK_COUNT - 1)
        weights.append(1.0 + (SLOWDOWN - 1.0) * t)
    total = sum(weights)
    return [duration * w / total for w in weights]


# (menu key, shop title, menu label, Game attribute, [(display, cost), ...])
# A list, not a dict: MicroPython 1.9.4 dicts don't keep their order.
UPGRADES = [
    ("2", "Dice", "Upgrade Dice", "die_level",
     [(d[0], d[2]) for d in DICE_TIERS]),
    ("3", "Speed", "Upgrade Speed", "speed_level",
     [(num(v) + "s", c) for v, c in SPEED_LEVELS]),
    ("4", "Money Mult", "Upgrade Money Mult", "money_mult_level",
     [("x" + num(v), c) for v, c in MONEY_MULT_LEVELS]),
    ("5", "Match Bonus", "Upgrade Match Bonus", "match_mult_level",
     [("x" + num(v), c) for v, c in MATCH_MULT_LEVELS]),
]
UPGRADE_BY_KEY = {u[0]: u for u in UPGRADES}


class Splash:
    def __init__(self):
        self.recent = []
        self.pending = ""
        self.next_idx = {}
        self.thresholds = {}
        for c in MILESTONES:
            self.next_idx[c] = 0
            self.thresholds[c] = sorted(MILESTONES[c])

    def report(self, category, total):
        # Mark every newly crossed threshold, but queue only the highest.
        ts = self.thresholds[category]
        newest = ""
        while self.next_idx[category] < len(ts) and total >= ts[self.next_idx[category]]:
            newest = MILESTONES[category][ts[self.next_idx[category]]]
            self.next_idx[category] += 1
        if newest:
            self.pending = newest

    def next(self):
        # A pending milestone beats a random line; no repeats within 5.
        if self.pending:
            msg = self.pending
            self.pending = ""
            return msg
        window = min(NO_REPEAT_WINDOW, len(RANDOM_SPLASHES) - 1)
        choices = [i for i in range(len(RANDOM_SPLASHES)) if i not in self.recent]
        i = random.choice(choices)
        self.recent.append(i)
        while len(self.recent) > window:
            self.recent.pop(0)
        return RANDOM_SPLASHES[i]


class Game:
    def __init__(self):
        self.splash = Splash()  # kept on play-again: milestones fire once ever
        self.reset()

    def reset(self):
        self.money = 0
        self.progress = 0
        self.best_run = 0
        self.die_level = 0
        self.speed_level = 0
        self.money_mult_level = 0
        self.match_mult_level = 0
        self.last_roll = 0  # 0 = "no previous roll"
        self.match_length = 0
        self.last_earnings = 0
        self.won = False
        self.total_rolls = 0
        self.bust_count = 0
        self.total_earned = 0
        self.total_spent = 0

    def match_multiplier(self):
        if self.match_length < 2:
            return 1.0
        start = 2.0 + 1.0 * self.match_mult_level
        step = 1.0 + 1.0 * self.match_mult_level
        return start + step * (self.match_length - 2)

    def calculate_earnings(self, value):
        mult = MONEY_MULT_LEVELS[self.money_mult_level][0]
        return gd_round(value * mult * self.match_multiplier())

    def apply_roll(self, value):
        # ORDER MATTERS: match_length is updated BEFORE earnings are
        # calculated (and reset before earnings on a bust), which is what
        # makes a bust pay out at 1x match multiplier. Returns True on win.
        if value == BUST_VALUE:
            self.best_run = max(self.best_run, self.progress)
            self.progress = 0
            self.match_length = 0
            self.last_roll = 0
            self.last_earnings = self.calculate_earnings(value)
            self.money += self.last_earnings
            return False
        if self.last_roll == value:
            self.match_length += 1
        else:
            self.match_length = 1
        self.last_roll = value
        self.last_earnings = self.calculate_earnings(value)
        self.money += self.last_earnings
        self.progress += value
        self.best_run = max(self.best_run, self.progress)
        return self.progress >= GOAL

    def on_roll_done(self, value):
        # Apply the roll, update stats/milestones, return content lines.
        before = self.progress
        self.won = self.apply_roll(value)
        self.total_rolls += 1
        self.total_earned += self.last_earnings
        if value == BUST_VALUE:
            self.bust_count += 1
        self.splash.report("rolls", self.total_rolls)
        self.splash.report("earned", self.total_earned)
        self.splash.report("busts", self.bust_count)
        name = DICE_TIERS[self.die_level][0]
        if value == BUST_VALUE:
            lines = [("Rolled a 1 on the %s.  +$%d" % (name, self.last_earnings), BLACK)]
            if before > 0:
                lines.append(("BUST! Progress wiped (-%d)." % before, RED))
            else:
                lines.append(("BUST! ...luckily there was nothing to lose.", RED))
            return lines
        lines = [("Rolled a %d on the %s!  +%d progress, +$%d"
                  % (value, name, value, self.last_earnings), BLACK)]
        if self.match_length >= 2:
            lines.append(("MATCH x%d (x%s $)"
                          % (self.match_length, num(self.match_multiplier())), ORANGE))
        return lines

    def buy(self, key):
        # One buy for all four upgrades. Returns (message, color).
        _key, title, _label, attr, rows = UPGRADE_BY_KEY[key]
        level = getattr(self, attr)
        if level + 1 >= len(rows):
            return ("%s already MAXED (%s)." % (title, rows[level][0]), RED)
        new, cost = rows[level + 1]
        if self.money < cost:
            return ("Need $%d for %s (you have $%d)." % (cost, title, self.money), RED)
        self.money -= cost
        setattr(self, attr, level + 1)
        self.total_spent += cost
        self.splash.report("spent", self.total_spent)
        return ("%s upgraded: %s -> %s  (-$%d)" % (title, rows[level][0], new, cost), GREEN)


def menu_lines(g, one_row=False):
    # Lives here, not in dietry.py, which is at the 300-line file limit.
    lines = ["1. Roll (%s)" % DICE_TIERS[g.die_level][0]]
    for key, _title, label, attr, rows in UPGRADES:
        level = getattr(g, attr)
        if level + 1 >= len(rows):
            lines.append("%s. %s (%s) MAXED" % (key, label, rows[level][0]))
        else:
            lines.append("%s. %s (%s -> %s)  $%d" % (
                key, label, rows[level][0], rows[level + 1][0], rows[level + 1][1]))
    lines += ["6. Help          0. Exit"] if one_row else ["6. Help", "0. Exit"]
    return lines
