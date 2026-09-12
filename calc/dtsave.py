# dtsave.py - saving for dietry.py (Die Trying, fx-CG100 edition).
# Separate file because dtgame.py and dietry.py are both near the
# calculator's 300-line-per-file limit.

from dtgame import UPGRADES

# The save code is the real mechanism: this calculator does not let a
# script write files (open(path, "w") returns None instead of a file, and
# was confirmed to fail on an fx-CG100). The file path is still tried
# first, for builds that do allow it.
#
# Ten base64 characters, six bits each, packed as a bit stream - fields do
# not line up with characters, so one character carries the tail of one
# field and the head of the next:
#   levels 11 | progress 9 | money 16 | rolls 13 | wipes 11 = 60 bits
# total_spent is the sum of the costs of the levels owned, and
# total_earned = money + total_spent, so neither is stored - which is what
# makes ten characters enough.
#
# There is no room left for a checksum. Mistyped codes are caught only by
# what the data cannot be (levels out of range, more wipes than rolls,
# money without rolls) - see the measured rate in tests/test_calc.py. A
# typo that gets through loads a wrong but harmless game: the money reads
# wrong immediately and the real code is still sitting in the Shell.
#
# Nothing wider than ~22 bits is ever held in an int, so this works even
# without big-integer support.
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-."
SAVE_FILE = "dtsave.txt"
PRINT_SAVE = True   # print the code each roll, so quitting with AC is safe
WIDTHS = [11, 9, 16, 13, 11]
LIMITS = [1889, 511, 65535, 8191, 2047]
CODE_LEN = 10


def _emit(vals, widths):
    out = ""
    acc = 0
    n = 0
    for i in range(len(vals)):
        acc = (acc << widths[i]) | vals[i]
        n += widths[i]
        while n >= 6:
            n -= 6
            out += ALPHABET[(acc >> n) & 63]
            acc &= (1 << n) - 1
    if n:
        out += ALPHABET[(acc << (6 - n)) & 63]
    return out


def _read(s, widths):
    # Returns the field values, or None if a character is not in the alphabet.
    vals = []
    acc = 0
    n = 0
    pos = 0
    for w in widths:
        while n < w:
            if pos >= len(s):
                return None
            i = ALPHABET.find(s[pos])
            if i < 0:
                return None
            pos += 1
            acc = (acc << 6) | i
            n += 6
        n -= w
        vals.append((acc >> n) & ((1 << w) - 1))
        acc &= (1 << n) - 1
    return vals


def _clamp(v, hi):
    return 0 if v < 0 else (hi if v > hi else v)


def grouped(code):
    # Shown as two blocks of five: easier to read off the screen.
    return code[:5] + " " + code[5:]


def spent_from_levels(g):
    # Every purchase is recorded in the levels, so spending is derivable.
    total = 0
    for _key, _title, _label, attr, rows in UPGRADES:
        for i in range(getattr(g, attr) + 1):
            total += rows[i][1]
    return total


def save_code(g):
    levels = ((g.die_level * 9 + g.speed_level) * 6 + g.money_mult_level) * 5 \
        + g.match_mult_level
    vals = [levels, g.progress, g.money, g.total_rolls, g.bust_count]
    for i in range(len(vals)):
        vals[i] = _clamp(vals[i], LIMITS[i])
    return _emit(vals, WIDTHS)


def load_code(g, s):
    # Everything is validated before anything is written, so a bad code
    # leaves the game untouched instead of half-loaded.
    s = s.strip().replace(" ", "")   # tolerates the grouped form
    if len(s) != CODE_LEN:
        return False
    vals = _read(s, WIDTHS)
    if vals is None or vals[0] > LIMITS[0]:
        return False
    # No checksum fits, so lean on what the data cannot be: more wipes
    # than rolls, or money and progress in a game that never rolled.
    if vals[4] > vals[3]:
        return False
    if vals[3] == 0 and (vals[1] or vals[2]):
        return False
    levels = vals[0]
    g.reset()
    g.match_mult_level = levels % 5
    levels //= 5
    g.money_mult_level = levels % 6
    levels //= 6
    g.speed_level = levels % 9
    g.die_level = levels // 9
    g.progress = vals[1]
    g.money = vals[2]
    g.total_rolls = vals[3]
    g.bust_count = vals[4]
    g.best_run = g.progress          # not stored: no room, not displayed
    g.total_spent = spent_from_levels(g)
    g.total_earned = g.money + g.total_spent
    for name, total in (("rolls", g.total_rolls), ("busts", g.bust_count),
                        ("earned", g.total_earned), ("spent", g.total_spent)):
        g.splash.report(name, total)   # mark milestones seen...
    g.splash.pending = ""              # ...without showing them again
    return True


_FILE_OK = True   # cleared the first time a write fails, so we stop trying


def save_file(g):
    # open() returns None here rather than raising, so check both.
    global _FILE_OK
    if not _FILE_OK:
        return False
    try:
        f = open(SAVE_FILE, "w")
        if f is None:
            _FILE_OK = False
            return False
        f.write(save_code(g))
        f.close()
        return True
    except Exception:
        _FILE_OK = False
        return False


def load_file(g):
    try:
        f = open(SAVE_FILE)
        if f is None:
            return False
        code = f.read()
        f.close()
    except Exception:
        return False
    return load_code(g, code)


def autosave(g):
    # The Shell keeps its last 200 lines, so a printed code survives AC.
    if not save_file(g) and PRINT_SAVE:
        print(save_code(g))


def boot_load(g):
    # Returns the line to show as the first message.
    if load_file(g):
        return "Save file loaded."
    try:
        code = input("Save code (EXE for new game): ")
    except Exception:
        return "Welcome to DIE TRYING."
    if not code.strip():
        return "Welcome to DIE TRYING."
    if load_code(g, code):
        return "Save code loaded."
    return "Code not recognised - new game."
