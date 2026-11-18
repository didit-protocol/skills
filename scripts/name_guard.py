#!/usr/bin/env python3
"""Name guard: fail when a file holds a name that must never be published.

The names are NOT in this repository. It is public, and a list of them would
publish them. `tests/data/withheld-names.digests` holds one keyed digest
(HMAC-SHA256) per name, and the key is the secret DIDIT_NAME_GUARD_KEY, so
nobody can turn a digest back into a name by trying candidates.

Every run of one to four consecutive words is compared, as whole lower-case
words joined by one space. A name that is also two ordinary words written
together is therefore matched only when it is written together. What is
compared:

- the text of every file;
- the path of every file, because a file or folder name is published too;
- the raw bytes of images and fonts, where a caption or a comment can sit.

A file whose text the guard cannot read (a PDF, an archive, an office document,
any other binary) is refused, not skipped: what cannot be checked cannot be
published here.

The script reads the tree it is given as DATA. It never imports or runs anything
from it, never follows a symbolic link, and its report never contains a word it
found: it gives line numbers, and a path with the offending part replaced.

    python3 -I scripts/name_guard.py <tree> [--digests <file>]

Exit code: 0 nothing found, 1 a name was found or a file cannot be checked,
2 the check could not run (no key, or no usable digest file).
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
WITHHELD = "<withheld>"
# Binary files that hold no prose of their own. Their bytes are still compared.
IMAGE_AND_FONT_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2"}
# Containers: their text is compressed or encoded, so reading the bytes proves nothing.
CONTAINER_SUFFIXES = {
    ".pdf", ".zip", ".gz", ".tgz", ".tar", ".bz2", ".xz", ".7z", ".rar", ".jar", ".whl",
    ".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp", ".epub",
}  # fmt: skip
CONTAINER_MAGIC = (b"%PDF", b"PK\x03\x04", b"\x1f\x8b", b"BZh", b"\xfd7zXZ", b"7z\xbc\xaf", b"Rar!")


def load_digests(path):
    """The digests in `path`. Raises ValueError when the file is empty or holds anything else."""
    lines = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError("the digest file is empty")
    for line in lines:
        if not DIGEST_RE.match(line):
            raise ValueError("the digest file holds digests only, never a name")
    return frozenset(lines)


def tree_files(root):
    """Every regular file under `root`, sorted. No symbolic link is followed or read."""
    root = Path(root)
    found = []
    for folder, folders, names in os.walk(root, followlinks=False):
        folders[:] = sorted(name for name in folders if name != ".git" and not (Path(folder) / name).is_symlink())
        for name in sorted(names):
            path = Path(folder) / name
            if path.is_symlink() or not path.is_file():
                continue
            found.append(path)
    return found


def withheld_runs(words, key, digests, cache):
    """The (start, size) of every run of 1 to 4 words that is a withheld name."""
    runs = []
    for size in range(1, MAX_WORDS + 1):
        for start in range(len(words) - size + 1):
            joined = " ".join(words[start : start + size])
            hit = cache.get(joined)
            if hit is None:
                hit = hmac.new(key, joined.encode("utf-8"), hashlib.sha256).hexdigest() in digests
                cache[joined] = hit
            if hit:
                runs.append((start, size))
    return runs


def withheld_name_lines(text, key, digests, cache):
    """Line numbers where a withheld name starts. Never the words."""
    found = [(m.group(0), text.count("\n", 0, m.start()) + 1) for m in WORD_RE.finditer(text.lower())]
    runs = withheld_runs([word for word, _ in found], key, digests, cache)
    return sorted({found[start][1] for start, _ in runs})


def masked_path(parts, key, digests, cache):
    """(the path with every part that takes part in a withheld name replaced, whether any was)."""
    words, owners = [], []
    for index, part in enumerate(parts):
        for match in WORD_RE.finditer(part.lower()):
            words.append(match.group(0))
            owners.append(index)
    hit_parts = set()
    for start, size in withheld_runs(words, key, digests, cache):
        hit_parts.update(owners[start : start + size])
    shown = "/".join(WITHHELD if index in hit_parts else part for index, part in enumerate(parts))
    return shown, bool(hit_parts)


def cannot_be_read(path, data):
    """True for a file whose text the guard cannot read: a container, or a binary that is no image or font."""
    suffix = path.suffix.lower()
    if suffix in CONTAINER_SUFFIXES or data.startswith(CONTAINER_MAGIC):
        return True
    return b"\x00" in data and suffix not in IMAGE_AND_FONT_SUFFIXES


def scan(root, key, digests):
    """(files seen, [(shown path, where the name is)], [shown paths of files that cannot be checked]).

    A shown path never contains a withheld name: the part that holds one is replaced.
    """
    root = Path(root)
    cache = {}
    found, unreadable = [], []
    files = tree_files(root)
    for path in files:
        shown, in_path = masked_path(path.relative_to(root).parts, key, digests, cache)
        where = ["in its path"] if in_path else []
        data = path.read_bytes()
        if cannot_be_read(path, data):
            unreadable.append(shown)
        else:
            # Undecodable bytes become a replacement character, so one stray byte cannot hide a file.
            lines = withheld_name_lines(data.decode("utf-8", errors="replace"), key, digests, cache)
            if lines and path.suffix.lower() in IMAGE_AND_FONT_SUFFIXES:
                where.append("in its bytes")
            elif lines:
                where.append("line " + ", ".join(str(line) for line in lines))
        if where:
            found.append((shown, "; ".join(where)))
    return len(files), found, unreadable


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

    seen, found, unreadable = scan(args.tree, key.encode("utf-8"), digests)
    if not found and not unreadable:
        print(f"name guard: {seen} files checked, no withheld name")
        return 0
    if found:
        print(f"name guard: a withheld name is in {len(found)} of {seen} files (where it is, never what it is):")
        for shown, where in found:
            print(f"  {shown}: {where}")
    if unreadable:
        print(f"name guard: {len(unreadable)} of {seen} files cannot be read as text, so they cannot be checked.")
        print("  Publish them as text, or leave them out of this repository:")
        for shown in unreadable:
            print(f"  {shown}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
