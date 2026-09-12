# savetest.py - one-off probe for saving on the fx-CG100.
# Run it from the Python app and read the Shell (output survives the
# script ending). Four questions:
#   1. can a script write and read back a file?
#   2. can lowercase be typed at an input() prompt?
#   3. does print() disturb the casioplot screen?
#   4. does a "-" measure correctly now (it read 0.00 before)?

from casioplot import clear_screen, show_screen, get_pixel, draw_string, getkey

W = 384
BLACK = (0, 0, 0)
SIZE = "small"


def try_write(path):
    try:
        f = open(path, "w")
        f.write("DIETRY-SAVE-TEST")
        f.close()
    except Exception as e:
        return "write failed: " + repr(e)
    try:
        f = open(path)
        back = f.read()
        f.close()
    except Exception as e:
        return "wrote, read failed: " + repr(e)
    if back == "DIETRY-SAVE-TEST":
        return "OK - writes work"
    return "read back wrong: " + repr(back)


print("1. FILE WRITES")
print("   dtsave.txt : " + try_write("dtsave.txt"))
print("   /dtsave.txt: " + try_write("/dtsave.txt"))

print("2. TYPING - type this code back, exactly:  7kQ3-p9")
try:
    typed = input("   code: ")
    print("   got: " + repr(typed))
    print("   lowercase ok" if typed == "7kQ3-p9" else "   differs - check lowercase/symbols")
except Exception as e:
    print("   input() failed: " + repr(e))

# 3. print() while the drawing screen is up: does the drawing survive?
clear_screen()
draw_string(2, 2, "If you can read this box after the", BLACK, SIZE)
draw_string(2, 16, "Shell text appeared, print() is safe.", BLACK, SIZE)
draw_string(2, 40, "Press any key for the last test.", BLACK, SIZE)
show_screen()
print("3. PRINT TEST: this line was printed while the drawing was up.")
print("   Did the drawing stay on screen? (look now)")
while not getkey():
    pass

# 4. the dash width, with the every-row scan that fixed the 0.00 reading
clear_screen()
draw_string(0, 0, "-" * 20, BLACK, SIZE)
blank = get_pixel(W - 1, 30)
edge = 0
x = W - 1
while x >= 0 and not edge:
    y = 0
    while y < 24:
        if get_pixel(x, y) != blank:
            edge = x + 1
            break
        y += 1
    x -= 1
print("4. DASH WIDTH: %.2f  (0.00 means the scan still misses it)" % (edge / 20.0))
print("Done - report these four answers.")
