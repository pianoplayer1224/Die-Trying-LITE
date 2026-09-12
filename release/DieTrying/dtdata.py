# dtdata.py - data for dietry.py (Die Trying, fx-CG100 edition).
# Tables and text only. ASCII only: the calculator can't show anything else.

DICE_TIERS = [
    # (display name, faces, cost)
    ("d2", 2, 0),
    ("d4", 4, 25),
    ("d6", 6, 75),
    ("d8", 8, 200),
    ("d10", 10, 500),
    ("d12", 12, 1200),
    ("d20", 20, 4000),
]

SPEED_LEVELS = [
    # (roll duration in seconds, cost)
    (3.0, 0),
    (2.6, 50),
    (2.2, 100),
    (1.8, 200),
    (1.4, 500),
    (1.0, 1000),
    (0.8, 2000),
    (0.6, 5000),
]

MONEY_MULT_LEVELS = [
    # (multiplier, cost)
    (1.0, 0),
    (1.25, 40),
    (1.5, 120),
    (2.0, 300),
    (3.0, 800),
    (4.0, 2000),
]

MATCH_MULT_LEVELS = [
    # (starting multiplier on a double, cost)
    (2.0, 0),
    (2.5, 20),
    (3.0, 50),
    (3.5, 100),
    (4.0, 250),
]

GOAL = 500
BUST_VALUE = 1

# Roll animation: TICK_COUNT faces, each delay up to SLOWDOWN times
# longer than the first, summing to the roll duration.
TICK_COUNT = 12
SLOWDOWN = 6.0

NO_REPEAT_WINDOW = 5

RANDOM_SPLASHES = [
    "Also try Unfair Flips!",
    "Now with twenty sides!",
    "Statistically, you'll be fine.",
    "Money is permanent. Dignity is not.",
    "A one in six chance of regret.",
    "100% organic, free-range pseudorandomness.",
    "The house always wins.",
    "Do not eat the dice.",
    "Snake eyes sold separately.",
    "Every roll is a coin flip if you squint.",
    "More time was spent making these messages than balancing the game.",
    "Though unlikely, this game may never end.",
    "In dice we trust.",
    "Upgrade your dice, not your life choices.",
    "Rolling a 1 builds character. Mostly negative character.",
    "Speed doesn't fix a bad roll. It just gets you there faster.",
    "Somewhere, a d20 is laughing at you.",
    "Play-tested by someone with a gambling addiction.",
    "No dice were harmed. Several were disappointed.",
    "Achievement unlocked: reading splash text instead of playing.",
    "Failure is just progress with extra steps.",
    "You miss 100% of the rolls you don't take.",
    "Optimism is not a valid strategy.",
    "Simulation for the Nation!",
    "Remember the 3-2-1 Rule for File Backups!",
    "seal",
    "Visit sealnet.xyz",
    "FILTERED.",
    "Mark 83 1,000 lb ballute-type retarded bomb",
    "Decisions, decisions...",
    "sudo rm -rf --no-preserve-root",
    "FROGE BOGEUS",
    "7EAM!",
    "1f986_duck",
    "Squawk 7700, Contact Guard on 121.5",
    "You are meant to be doing Maths, aren't you?",
    "Imagine having a Fancy Ass Calculator. I bet you don't even use it for Graphing.'",
    "Get the FX-CG100 Graphing Calculator from casio.com for only GBP139.99! Never mind, it's sold out.",
    "https://github.com/pianoplayer1224/Die-Trying-LITE",
    "'It is mathematically proven that on average your partner has more partners than you'",
    "'We are two parts of a song. He is the music, and i am the words' -From some book",
    "'If god would have wanted you to win he wouldn't have created me'",
]

# Milestones fire once each. No playtime milestones: the calculator has
# no clock (no time module).
MILESTONES = {
    "rolls": {
        10: "Ten rolls. A promising start.",
        50: "Fifty rolls now.",
        100: "One hundred rolls. Hope you're having fun!",
        250: "250 rolls. This is a lifestyle now.",
        500: "500 rolls. Seek help.",
        1000: "1000 rolls. Seek help, urgently.",
        5000: "5000 rolls. Please stop.",
    },
    "busts": {
        1: "Your first wipe. It won't be your last.",
        5: "Five wipes. The die is just being honest.",
        10: "Ten wipes. Have you considered not rolling ones?",
        25: "25 wipes. That's dedication. Or denial.",
        50: "50 wipes. The one is your most loyal face.",
        100: "100 wipes. Damn, you are unlucky.",
    },
    "earned": {
        100: "First $100 earned. Get yourself something nice.",
        500: "$500 lifetime earnings. The dice are paying rent.",
        1000: "$1,000 earned. The economy fears you.",
        5000: "$5,000 earned. Statistically inevitable, still impressive.",
        10000: "$10,000 earned. Consider diversifying into more dice.",
        20000: "$20,000 lifetime earnings. You Won Capitalism.",
    },
    "spent": {
        100: "$100 spent. Investing in yourself.",
        500: "$500 spent. The upgrade shop thanks you.",
        2000: "$2,000 spent. All purchases are final.",
        5000: "$5,000 spent. No refunds!",
        10000: "$10,000 spent. Money can, in fact, buy happiness.",
        18530: "You really just bought everything in the store, didn't you?",
    },
}

HELP_PAGES = [
    [
        "HOW TO PLAY",
        "Roll the die to progress towards the goal (500)",
        "and earn money equal to the number you roll.",
        "",
        "But, roll a 1 and your progress gets WIPED.",
        "",
        "Roll the same number twice in a row to start a",
        "MATCH STREAK. Each roll in the streak earns",
        "bonus money. The streak ends if you roll a 1,",
        "or roll a different number.",
        "",
        "Upgrade your dice, earn money, and get gambling!",
    ],
    [
        "UPGRADES",
        "Dice        - more faces: higher rolls, rarer 1s.",
        "Speed       - shorter roll animation.",
        "Money Mult  - multiplies all money earned.",
        "Match Bonus - raises the streak's starting",
        "              multiplier AND how much each",
        "              extra match adds.",
        "",
        "Keys: press 0-6 on the keypad. AC stops the game.",
    ],
]

# The "your did it" star from the Godot win sprite.
WIN_ART = [
    "           /\\",
    "          /  \\",
    "-------/    \\-------",
    "\\                      /",
    "  \\                  /",
    "    \\ your did it  /",
    "   /                \\",
    "  /        /\\        \\",
    " /       /    \\       \\",
    "/-----/       \\-----\\",
]
