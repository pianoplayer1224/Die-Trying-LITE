# dietry.py - Die Trying for the Casio fx-CG100 (MicroPython 1.9.4).
# Run from the Python app; dtdata.py, dtgame.py and dtsave.py must sit
# next to it (the 300-line limit splits it up). Keys 0-6; AC stops.

from casioplot import clear_screen, show_screen, set_pixel, get_pixel, draw_string, getkey
import random
from dtgame import *
from dtsave import *

# ---- Tuning: adjust these on the calculator ----------------------------
FONT = "small"             # draw_string size: "small", "medium" or "large"
AUTO_CALIBRATE = True      # measure the real font at startup
CHAR_W = 6.36              # average character width, measured on an fx-CG100
MAX_W = 8                  # widest glyph ("M"), used for bounds and line art
LINE_H = 11                # text row pitch (glyph height 10 + 1)
LOOPS_PER_SEC = 120000     # busy-wait loops per second (there is no clock)
TICK_OVERHEAD = 0.0        # seconds one animation tick costs on its own
HELP_EXIT_ONE_ROW = False  # True puts "6. Help" and "0. Exit" on one row

# Roll speed: a roll lasts SPEED_LEVELS[speed_level] seconds as in Godot.
# No clock, so it is a counting loop: time five base rolls, divide by 5
# -> T, multiply LOOPS_PER_SEC by 3.0 / T. Short rolls still slow? drawing
# is the floor: TICK_OVERHEAD = floor / 12.

KEYS = {91: "0", 81: "1", 82: "2", 83: "3", 71: "4", 72: "5", 73: "6"}

W, H, COLS = 384, 192, 53

# A line of ordinary text, for measuring the average character width.
SAMPLE = "The house always wins. Rolled a 6 on the d20! 0123456789"

# Screen layout, top to bottom (y in pixels); set by set_layout().
SPLASH_Y, RULE1_Y, CONTENT_Y, RULE2_Y, STATUS_Y, RULE3_Y, MENU_Y = 1, 0, 0, 0, 0, 0, 0

def set_layout():
    global COLS, RULE1_Y, CONTENT_Y, RULE2_Y, STATUS_Y, RULE3_Y, MENU_Y
    # Wrap between average and widest glyph: no overflow, no early wrap.
    COLS = int(W / ((CHAR_W + MAX_W) / 2.0))
    RULE1_Y = SPLASH_Y + 2 * LINE_H + 1
    CONTENT_Y = RULE1_Y + 3
    RULE2_Y = CONTENT_Y + 3 * LINE_H + 1
    STATUS_Y = RULE2_Y + 3
    RULE3_Y = STATUS_Y + LINE_H + 1
    MENU_Y = RULE3_Y + 5

set_layout()

# ---- Font measurement ------------------------------------------------------
# The font is proportional (fx-CG100: M 8.00, i 3.95, space 6.00, avg
# 6.36), so a character count is not a width. get_pixel reads the drawing
# buffer, so measuring needs no show_screen and never reaches the display.
_WIDTHS = {}

def right_edge(s, size=None):
    clear_screen()
    draw_string(0, 0, s, BLACK, size or FONT)
    blank = get_pixel(W - 1, H - 1)
    # MAX_W belongs to FONT, so it cannot bound a bigger size: scanning
    # from a too-small x would find ink inside the text and report it as
    # the right edge, which then centres the string off to the right.
    x = W - 1 if size else min(W - 1, len(s) * MAX_W + 4)
    while x >= 0:
        y = 0
        while y <= (LINE_H + 2) * (3 if size else 1):  # a bigger size is taller
            if get_pixel(x, y) != blank:
                return x + 1
            y += 1
        x -= 1
    return 0

def bottom_edge(s):
    clear_screen()
    draw_string(0, 0, s, BLACK, FONT)
    blank = get_pixel(W - 1, H - 1)
    y = 39
    while y >= 0:
        x = 0
        while x < 40:
            if get_pixel(x, y) != blank:
                return y + 1
            x += 1
        y -= 1
    return 0

def text_w(s, size=None):
    # Exact width, measured once per string. Measuring clears the drawing
    # buffer, so call it before drawing a frame, never mid-frame.
    key = s if size is None else size + s
    w = _WIDTHS.get(key)
    if w is None:
        w = right_edge(s, size)
        if w < 1:
            w = int(len(s) * CHAR_W)
        if len(_WIDTHS) > 150:
            _WIDTHS.clear()
        _WIDTHS[key] = w
    return w

def measure_font():
    global CHAR_W, MAX_W, LINE_H, HELP_EXIT_ONE_ROW
    _WIDTHS.clear()
    wide = right_edge("M" * 20) / 20.0
    if 3.0 <= wide <= 20.0:
        MAX_W = int(wide + 0.999)
    avg = right_edge(SAMPLE) / float(len(SAMPLE))
    high = bottom_edge("Mgy")
    if 3.0 <= avg <= 20.0 and 6 <= high <= 30:
        CHAR_W = avg
        LINE_H = high + 1
        set_layout()
    if MENU_Y + 7 * LINE_H > H:  # no room for "6. Help" and "0. Exit"
        HELP_EXIT_ONE_ROW = True

# ---- Drawing ---------------------------------------------------------------
def text(x, y, s, color=BLACK, size=None):
    draw_string(int(x), y, s, color, size or FONT)

def center(y, s, color=BLACK, size=None):
    # Uses the measured width when the string has been measured already.
    w = _WIDTHS.get(s if size is None else size + s)
    if w is None:
        w = int(len(s) * CHAR_W)
    text(max(0, (W - w) // 2), y, s, color, size)

def hline(y, x0=0, x1=W - 1, color=BLACK):
    for x in range(int(x0), int(x1) + 1):
        set_pixel(x, y, color)

def bar(x, y, w, h, frac):
    hline(y, x, x + w)
    hline(y + h, x, x + w)
    fill = x + int((w - 1) * min(frac, 1.0))
    for yy in range(y + 1, y + h):
        set_pixel(x, yy, BLACK)
        set_pixel(x + w, yy, BLACK)
        hline(yy, x + 1, fill, GREEN)

def render(splash, content, g):
    # The whole frame: splash / content / money + progress / menu.
    parts = wrap(splash, COLS)
    money = "Money: $%d" % g.money
    prog = "Progress: %d/%d" % (g.progress, GOAL)
    for s in parts[:2]:        # measure before drawing: it clears the buffer
        text_w(s)
    money_w = text_w(money)
    prog_w = text_w(prog)
    clear_screen()
    for i in range(min(2, len(parts))):
        center(SPLASH_Y + i * LINE_H, parts[i], ORANGE)
    hline(RULE1_Y)
    rows = []
    for s, color in content:
        for part in wrap(s, COLS):
            rows.append((part, color))
    for i in range(min(3, len(rows))):
        text(2, CONTENT_Y + i * LINE_H, rows[i][0], rows[i][1])
    hline(RULE2_Y)
    # Everything after the money is placed from its real width, so a
    # jackpot cannot run into the progress readout.
    text(2, STATUS_Y, money, GREEN)
    px = 2 + money_w + MAX_W
    text(px, STATUS_Y, prog)
    bx = px + prog_w + MAX_W
    if W - 3 - bx >= 20:
        bar(bx, STATUS_Y + 2, W - 3 - bx, LINE_H - 4, g.progress / GOAL)
    hline(RULE3_Y)
    hline(RULE3_Y + 2)
    lines = menu_lines(g, HELP_EXIT_ONE_ROW)
    for i in range(len(lines)):
        text(2, MENU_Y + i * LINE_H, lines[i])
    show_screen()

# ---- Input -----------------------------------------------------------------
# getkey() reports the key held right now and never waits, so every read
# first waits for release - otherwise one press would act many times.
def wait_release():
    while getkey():
        pass

def read_key():
    wait_release()
    while True:
        k = getkey()
        if k in KEYS:
            return KEYS[k]

def wait_any():
    wait_release()
    while not getkey():
        pass

# ---- Roll animation (no time module: delays are busy-wait loops) ----------
def wait(sec):
    n = int(sec * LOOPS_PER_SEC)
    for _ in range(n):
        pass

def animate_roll(g, splash):
    # Flicker random faces, slowing down; the last one shown is the result.
    name, faces, _cost = DICE_TIERS[g.die_level]
    render(splash, [], g)
    shown = ""
    face = 1
    for d in build_delays(SPEED_LEVELS[g.speed_level][0]):
        face = random.randint(1, faces)
        if shown:
            text(2, CONTENT_Y, shown, WHITE)  # redraw in white = erase
        shown = "Rolling %s...  [ %d ]" % (name, face)
        text(2, CONTENT_Y, shown)
        show_screen()
        wait(d - TICK_OVERHEAD)  # drawing already used TICK_OVERHEAD seconds
    return face

# ---- Other screens ---------------------------------------------------------
def show_help():
    for i in range(len(HELP_PAGES)):
        clear_screen()
        for j in range(len(HELP_PAGES[i])):
            text(2, 1 + j * LINE_H, HELP_PAGES[i][j])
        last = i + 1 == len(HELP_PAGES)
        text(2, H - LINE_H - 1, "Any key: back to game" if last else "Any key: next page", ORANGE)
        show_screen()
        wait_any()

def win_screen(g, splash):
    # Star on the left, stats on the right, the pair centred together.
    # Returns True to play again, False to quit.
    stats = ["YOU WIN!", "Reached %d/%d" % (g.progress, GOAL),
             "Rolls:  %d" % g.total_rolls, "Wipes:  %d" % g.bust_count,
             "Earned: $%d" % g.total_earned, "Spent:  $%d" % g.total_spent]
    footer = "1 = Play again     0 = Quit"
    top_line = wrap(splash, COLS)[0]
    star_px = max([text_w(row) for row in WIN_ART])   # measure before drawing
    stat_px = max([text_w(s) for s in stats])
    text_w(footer)
    text_w(top_line)
    clear_screen()
    x0 = max(0, (W - star_px - 2 * MAX_W - stat_px) // 2)
    sx = x0 + star_px + 2 * MAX_W
    center(SPLASH_Y, top_line, ORANGE)
    top = LINE_H + 6
    for i in range(len(WIN_ART)):
        text(x0, top + i * LINE_H, WIN_ART[i], ORANGE)
    for i in range(len(stats)):
        text(sx, top + (i + 2) * LINE_H, stats[i], GREEN if i == 0 else BLACK)
    center(H - LINE_H - 1, footer)
    show_screen()
    while True:
        k = read_key()
        if k == "1":
            g.reset()
            return True
        if k == "0":
            return False

def main(g=None):
    if AUTO_CALIBRATE:
        try:
            measure_font()
        except Exception:
            pass  # get_pixel unusable: keep the measured-by-hand fallbacks
    g = g or Game()
    content = [(boot_load(g), ORANGE),
               ("Reach the goal (500) or... die trying.", BLACK),
               ("Press 1 to roll, 6 for help.", BLACK)]
    while True:
        splash = g.splash.next()
        render(splash, content, g)
        k = read_key()
        if k == "0":
            break
        elif k == "1":
            content = g.on_roll_done(animate_roll(g, splash))
            autosave(g)
            if g.won:
                if not win_screen(g, g.splash.next()):
                    break
                content = [("New game started. Good luck!", BLACK)]
        elif k == "6":
            show_help()
        else:
            content = [g.buy(k)]
            autosave(g)
    # Ending the script leaves the casioplot screen up until AC is pressed,
    # and there is no call to close it, so say so instead of going blank.
    shown = grouped(save_code(g))
    bye = ["Save code:", "Note it down to continue later.", "Press AC to exit"]
    for s in bye:
        text_w(s)
    text_w(shown, "large")     # the code itself gets the big font
    clear_screen()
    center(H // 2 - 3 * LINE_H, bye[0])
    center(H // 2 - 2 * LINE_H, shown, ORANGE, "large")
    center(H // 2 + LINE_H, bye[1])
    center(H // 2 + 2 * LINE_H, bye[2])
    show_screen()

# Called directly: it's not certain the Python app sets __name__ to "__main__".
main()
