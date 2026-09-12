"""Desktop stand-in for the fx-CG100 casioplot module (tests only).

The real font is proportional, so this stub is too: "M" is the widest
glyph, everything else is narrower. That is what makes the centring
tests meaningful.
"""
W, H = 384, 192
WIDE_W, NARROW_W, LINE_H = 8, 6, 13
WHITE = (255, 255, 255)
# Widths measured on a real fx-CG100 (size "small"), rounded to pixels.
ADV = {"M": 8, "W": 8, "m": 8, "i": 4, "l": 4, "j": 4, "t": 5,
       "1": 8, "2": 8, "3": 8, "4": 8, "5": 8, "6": 8, "7": 8, "8": 8,
       "9": 8, "0": 8, "-": 7, "/": 6, "\\": 6, " ": 6, ".": 4, ",": 4}
INK_ROWS = {"-": (5, 6)}   # a dash is a pixel or two tall, mid-cell

calls = []          # draw_string calls since the last clear_screen()
frames = []         # snapshot of calls at each show_screen()
frame_pixels = []   # set_pixel count at each show_screen()
problems = []
keys = []           # scripted getkey() results, consumed front to back
_pixels = [0]


SCALE = {"large": 2, "medium": 1, "small": 1}


def char_w(ch, size="small"):
    return ADV.get(ch, NARROW_W) * SCALE.get(size, 1)


def advance(s, size="small"):
    return sum(char_w(c, size) for c in s)


def clear_screen():
    del calls[:]
    _pixels[0] = 0


def show_screen():
    frames.append(list(calls))
    frame_pixels.append(_pixels[0])


def set_pixel(x, y, color=(0, 0, 0)):
    _pixels[0] += 1
    if not (0 <= x < W and 0 <= y < H):
        problems.append("set_pixel out of range: %r" % ((x, y),))


def get_pixel(x, y):
    # Enough emulation for measure_font(): ink inside a drawn non-space
    # character cell, white everywhere else.
    for x0, y0, s, color, size in calls:
        scale = SCALE.get(size, 1)
        if color == WHITE or not (y0 <= y < y0 + LINE_H * scale - 1) or x < x0:
            continue
        pos = x0
        for ch in s:
            if pos <= x < pos + char_w(ch, size):
                lo, hi = INK_ROWS.get(ch, (0, LINE_H - 2))
                if ch == " " or not (y0 + lo * scale <= y <= y0 + hi * scale):
                    return WHITE
                return (0, 0, 0)
            pos += char_w(ch, size)
    return WHITE


def draw_string(x, y, s, color=(0, 0, 0), size="medium"):
    if not isinstance(x, int):
        problems.append("non-int x: %r" % ((x, y, s),))
    if not isinstance(s, str) or not s.isascii():
        problems.append("non-ASCII or non-str text: %r" % (s,))
    if not (0 <= x < W and 0 <= y < H):
        problems.append("draw_string origin out of range: %r" % ((x, y, s),))
    if x + advance(s, size) > W or y + LINE_H * SCALE.get(size, 1) > H + 1:
        problems.append("text may overflow the screen: %r" % ((x, y, s),))
    for x0, y0, s0, c0, sz in calls:      # text drawn over other text
        if y0 == y and c0 != WHITE and color != WHITE and s.strip() and s0.strip():
            if x < x0 + advance(s0, sz) and x0 < x + advance(s, size):
                problems.append("overlapping text: %r over %r" % (s, s0))
    if color == WHITE:  # drawing in white erases earlier identical text
        for c in calls:
            if c[:3] == [x, y, s]:
                calls.remove(c)
                return
    calls.append([x, y, s, color, size])


def getkey():
    if not keys:
        raise RuntimeError("test ran out of scripted keys")
    return keys.pop(0)


def as_text(frame):
    """Render a frame's text calls as a y-labelled text grid."""
    rows = {}
    for x, y, s, _color, _size in frame:
        rows.setdefault(y, []).append((x, s))
    out = []
    for y in sorted(rows):
        line = ""
        for x, s in sorted(rows[y]):
            line = line.ljust(int(x / NARROW_W)) + s
        out.append("%3d| %s" % (y, line))
    return "\n".join(out)
