#!/usr/bin/env python3
"""Name guard: fail when a file holds a name that must never be published.

The names are NOT in this repository. It is public, and a list of them would
publish them. `tests/data/withheld-names.digests` holds one keyed digest
(HMAC-SHA256) per name, and the key is the secret DIDIT_NAME_GUARD_KEY, so
nobody can turn a digest back into a name by trying candidates.

Every run of one to four consecutive words of every text file is compared, as
whole lower-case words joined by one space. A name that is also two ordinary
words written together is therefore matched only when it is written together.

The script reads the tree it is given as DATA. It never imports or runs anything
from it, never follows a symbolic link, and prints file names and line numbers
only, never the words it found. That is what lets a workflow run it, with the
key, against the files of a pull request it does not trust.

    python3 -I scripts/name_guard.py <tree> [--digests <file>]

Exit code: 0 no name found, 1 a name was found, 2 the check could not run
(no key, or no usable digest file).
"""

import argparse
import hashlib
import hmac
import os
import re
import sys
from pathlib import Path

KEY_VARIABLE = "DIDIT_NAME_GUARD_KEY"
DEFAULT_DIGESTS = Path(__file__).resolve().parent.parent / "tests" / "data" / "withheld-names.digests"
WORD_RE = re.compile(r"[a-z0-9]+")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_WORDS = 4
# Images, fonts and archives hold no prose. Everything else is read as text.
SKIPPED_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".woff", ".woff2", ".zip"}


def load_digests(path):
    """The digests in `path`. Raises ValueError when the file is empty or holds anything else."""
    lines = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError("the digest file is empty")
    for line in lines:
        if not DIGEST_RE.match(line):
            raise ValueError("the digest file holds digests only, never a name")
    return frozenset(lines)


def text_files(root):
    """Every regular file under `root`, sorted. No symbolic link is followed or read."""
    root = Path(root)
    found = []
    for folder, folders, names in os.walk(root, followlinks=False):
        folders[:] = sorted(name for name in folders if name != ".git" and not (Path(folder) / name).is_symlink())
        for name in sorted(names):
            path = Path(folder) / name
            if path.is_symlink() or not path.is_file() or path.suffix.lower() in SKIPPED_SUFFIXES:
                continue
            found.append(path)
    return found


def withheld_name_lines(text, key, digests, cache):
    """Line numbers where a run of 1 to 4 words is a withheld name. Never the words."""
    words = [(m.group(0), text.count("\n", 0, m.start()) + 1) for m in WORD_RE.finditer(text.lower())]
    lines = []
    for size in range(1, MAX_WORDS + 1):
        for start in range(len(words) - size + 1):
            joined = " ".join(word for word, _ in words[start : start + size])
            hit = cache.get(joined)
            if hit is None:
                hit = hmac.new(key, joined.encode("utf-8"), hashlib.sha256).hexdigest() in digests
                cache[joined] = hit
            if hit:
                lines.append(words[start][1])
    return sorted(set(lines))


def scan(root, key, digests):
    """(files checked, [(path relative to root, [line numbers])] for every file that holds a withheld name)."""
    root = Path(root)
    cache = {}
    found = []
    files = text_files(root)
    for path in files:
        # Undecodable bytes become a replacement character, so one stray byte cannot hide a file.
        text = path.read_bytes().decode("utf-8", errors="replace")
        lines = withheld_name_lines(text, key, digests, cache)
        if lines:
            found.append((path.relative_to(root).as_posix(), lines))
    return len(files), found


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fail when a file holds a name that must never be published.")
    parser.add_argument("tree", help="the folder to check; it is read as data and nothing in it is run")
    parser.add_argument("--digests", default=str(DEFAULT_DIGESTS), help="the digest file to compare against")
    args = parser.parse_args(argv)

    key = os.environ.get(KEY_VARIABLE, "")
    if not key:
        print(f"name guard: {KEY_VARIABLE} is not set, so nothing was checked")
        return 2
    if not Path(args.tree).is_dir():
        print("name guard: the tree to check is not a folder")
        return 2
    try:
        digests = load_digests(args.digests)
    except (OSError, ValueError) as error:
        print(f"name guard: the digest file cannot be used ({error})")
        return 2

    checked, found = scan(args.tree, key.encode("utf-8"), digests)
    if not found:
        print(f"name guard: {checked} files checked, no withheld name")
        return 0
    print(f"name guard: a withheld name is in {len(found)} of {checked} files (file and lines only):")
    for name, lines in found:
        print(f"  {name}: line {', '.join(str(line) for line in lines)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
