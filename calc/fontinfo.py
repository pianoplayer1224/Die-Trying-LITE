# fontinfo.py - one-off probe: how wide is the fx-CG100 casioplot font?
# Run it from the Python app, then read the numbers (they are printed to
# the Shell as well as drawn, so they survive after the script ends).
# Tells us: is the font monospace, what is the average advance, the
# widest glyph, the line height, and whether get_pixel needs show_screen.

from casioplot import clear_screen, show_screen, get_pixel, draw_string, getkey

W = 384
BLACK = (0, 0, 0)
SIZE = "small"   # match dietry.py's FONT
SAMPLE = "The house always wins. Rolled a 6 on the d20! 0123456789"


def right_edge(s, refresh):
    # Rightmost column holding ink, comparing against a known blank pixel
    # so it works whatever get_pixel returns (tuple or packed int).
    clear_screen()
    draw_string(0, 0, s, BLACK, SIZE)
    if refresh:
        show_screen()
    blank = get_pixel(W - 1, 30)
    x = min(W - 1, len(s) * 12 + 4)
    while x >= 0:
        y = 0
        while y < 24:
            if get_pixel(x, y) != blank:
                return x + 1
            y += 1      # step 1: a "-" is only a pixel or two tall
        x -= 1
    return 0


def bottom_edge(s):
    clear_screen()
    draw_string(0, 0, s, BLACK, SIZE)
    show_screen()
    blank = get_pixel(W - 1, 30)
    y = 39
    while y >= 0:
        x = 0
        while x < 40:
            if get_pixel(x, y) != blank:
                return y + 1
            x += 1
        y -= 1
    return 0


out = []
for ch in ("M", "i", "1", "/", "-", " "):
    if ch == " ":
        # space has no ink: measure it between two Ms
        pair = right_edge("MM", True)
        gap = right_edge("M" + " " * 20 + "M", True)
        out.append("space  = %.2f" % ((gap - pair) / 20.0))
    else:
        out.append("%s      = %.2f" % (ch, right_edge(ch * 20, True) / 20.0))
out.append("avg    = %.2f" % (right_edge(SAMPLE, True) / float(len(SAMPLE))))
out.append("height = %d" % bottom_edge("Mgy"))
out.append("no show_screen: %.2f" % (right_edge("M" * 20, False) / 20.0))

for line in out:
    print(line)

clear_screen()
draw_string(2, 2, "casioplot font, size " + SIZE, BLACK, SIZE)
for i in range(len(out)):
    draw_string(2, 18 + i * 14, out[i], BLACK, SIZE)
draw_string(2, 18 + len(out) * 14, "(all equal = monospace)", BLACK, SIZE)
show_screen()
while not getkey():
    pass
