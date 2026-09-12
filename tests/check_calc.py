"""Static fx-CG100 / MicroPython 1.9.4 compatibility checker for calc/*.py."""
import ast
import io
import pathlib
import sys
import tokenize

ROOT = pathlib.Path(__file__).resolve().parent.parent
CALC = ROOT / "calc"
ALLOWED_IMPORTS = {"random", "casioplot", "dtdata", "dtgame", "dtsave", "math"}
# str methods that MicroPython 1.9.4 builds commonly lack
RISKY_METHODS = {"center", "ljust", "rjust", "zfill", "casefold", "format_map",
                 "isascii", "removeprefix", "removesuffix", "expandtabs", "title"}

errors = []


def err(path, msg):
    errors.append("%s: %s" % (path.name, msg))


for path in sorted(CALC.glob("*.py")):
    raw = path.read_bytes()
    if len(path.stem) > 8:
        err(path, "file name longer than 8 characters")
    if not raw.isascii():
        err(path, "non-ASCII bytes")
    if b"\t" in raw:
        err(path, "tab characters")
    if raw.count(b"\n") != raw.count(b"\r\n"):
        err(path, "not CR+LF line endings")
    src = raw.decode("ascii", "replace")
    lines = src.splitlines()
    if len(lines) > 300:
        err(path, "%d lines (max 300)" % len(lines))
    longest = max(len(l) for l in lines)
    if longest > 255:
        err(path, "line of %d chars (max 255)" % longest)

    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        name = tokenize.tok_name[tok.type]
        if name == "FSTRING_START" or (name == "STRING" and "f" in tok.string.split("'")[0].split('"')[0].lower()):
            err(path, "f-string at line %d" % tok.start[0])

    tree = ast.parse(src)
    for node in ast.walk(tree):
        line = getattr(node, "lineno", "?")
        if isinstance(node, (ast.NamedExpr, ast.AnnAssign, ast.AsyncFunctionDef,
                             ast.Await, ast.YieldFrom, ast.JoinedStr)):
            err(path, "%s at line %s" % (type(node).__name__, line))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns or any(a.annotation for a in node.args.args + node.args.kwonlyargs):
                err(path, "annotation at line %s" % line)
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    err(path, "import %s at line %s" % (a.name, line))
        if isinstance(node, ast.ImportFrom) and node.module.split(".")[0] not in ALLOWED_IMPORTS:
            err(path, "from %s import at line %s" % (node.module, line))
        if isinstance(node, ast.Attribute) and node.attr in RISKY_METHODS:
            err(path, "risky str method .%s at line %s" % (node.attr, line))
    print("%-10s %3d lines, longest %3d chars" % (path.name, len(lines), longest))

if errors:
    print("PROBLEMS:")
    for e in errors:
        print("  " + e)
    sys.exit(1)
print("COMPATIBILITY CHECK PASSED")
