#!/usr/bin/env python3
"""Name guard: fail when a file holds a name that must never be published.

The names are NOT in this repository. It is public, and a list of them would
publish them. `tests/data/withheld-names.digests` holds one keyed digest
(HMAC-SHA256) per name, and the key is the secret DIDIT_NAME_GUARD_KEY, so
nobody can turn a digest back into a name by trying candidates.

Every run of one to four consecutive words is compared, as whole lower-case
words joined by one space. A name that is also two ordinary words written
together is therefore matched only when it is written together. Before the
comparison the text is folded the way a reader sees it: wide and other
compatibility letters become plain ones, accents are dropped, and characters
that show nothing (a zero-width space, a soft hyphen, a variation selector) are
removed, so none of them can split or disguise a name. What is compared:

- the text of every text file;
- the path of every file and of every empty folder, because a name is published too;
- the name and the stored target of every symbolic link (the link is never followed).

A text file is a file that is valid UTF-8 from its first byte to its last. Every
other file is a binary, and a binary is never inspected. Its bytes can carry a
name in more ways than a check can enumerate (metadata, compressed chunks, a
colour profile, another text encoding, bytes a format lets a writer leave
anywhere), so the guard does not try. A binary is any file that is not valid
UTF-8 or has a zero byte in it, and also a PDF, an archive, an office document,
a font and an image of any kind, by its suffix or its first bytes. Such a file
is published only when a maintainer has looked at those exact bytes and listed
their SHA-256 in `tests/data/approved-binaries.sha256`. Any other binary is
refused, and so is an approved one after a single byte changes. Its path is
compared like every other path.

The script reads the tree it is given as DATA. It never imports or runs anything
from it, never follows a symbolic link, and its report never contains a word it
found: it gives line numbers, and a path with the offending part replaced. Both
lists default to the copies that sit next to THIS script, not to anything in the
tree it checks. Run from the default branch against a pull request's files (the
name-guard workflow), that means a pull request cannot approve its own binary or
change the digests it is judged by: the approval is a change a maintainer merges
first.

What it does not see, so nobody relies on it for that: what an approved binary
holds (a maintainer answered for it), a name written inside a longer word, with a
look-alike letter from another alphabet, or encoded (base64, escapes), and anything
outside the tree (commit messages, branch names, the text of a pull request).

    python3 -I scripts/name_guard.py <tree> [--digests <file>] [--approved <file>]

Exit code: 0 nothing found, 1 a name was found or a binary is not approved,
2 the check could not run (no key, or a list that cannot be used).
"""

import argparse
import hashlib
import hmac
import os
import re
import sys
import unicodedata
from pathlib import Path

KEY_VARIABLE = "DIDIT_NAME_GUARD_KEY"
DATA = Path(__file__).resolve().parent.parent / "tests" / "data"
DEFAULT_DIGESTS = DATA / "withheld-names.digests"
DEFAULT_APPROVED = DATA / "approved-binaries.sha256"
WORD_RE = re.compile(r"[a-z0-9]+")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_WORDS = 4
WITHHELD = "<withheld>"
# Unicode categories that show nothing or only decorate a letter: combining marks (accents,
# variation selectors) and format characters (zero-width spaces and joiners, the soft hyphen).
UNSEEN = {"Mn", "Me", "Cf"}
# Containers, which can be valid UTF-8 from end to end (a PDF with text filters) and still hold
# their text compressed or encoded.
CONTAINER_SUFFIXES = {
    ".pdf", ".zip", ".gz", ".tgz", ".tar", ".bz2", ".xz", ".7z", ".rar", ".jar", ".whl",
    ".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp", ".epub",
}  # fmt: skip
# First bytes of containers, images and fonts, whatever the file is called. Nearly all of them
# fail the UTF-8 rule anyway; this names them without relying on that.
BINARY_MAGIC = (
    b"%PDF", b"PK\x03\x04", b"\x1f\x8b", b"BZh", b"\xfd7zXZ", b"7z\xbc\xaf", b"Rar!",
    b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"RIFF", b"OTTO", b"wOFF", b"wOF2", b"ttcf",
)  # fmt: skip


def load_digests(path):
    """The digests in `path`. Raises ValueError when the file is empty or holds anything else."""
    lines = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError("the digest file is empty")
    for line in lines:
        if not DIGEST_RE.match(line):
            raise ValueError("the digest file holds digests only, never a name")
    return frozenset(lines)


def load_approved(path):
    """The SHA-256 of every approved binary in `path`: one per line, an optional note after it.

    A line that starts with `#` is a comment. An empty list is valid: then no binary is approved.
    Raises ValueError for a line that does not start with 64 lower-case hex characters.
    """
    approved = set()
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        digest = line.split()[0]
        if not DIGEST_RE.match(digest):
            raise ValueError("every line of the approved list starts with a SHA-256")
        approved.add(digest)
    return frozenset(approved)


def tree_entries(root):
    """(regular files, symbolic links, empty folders) under `root`, each sorted. No link is followed."""
    root = Path(root)
    files, links, empty = [], [], []
    for folder, folders, names in os.walk(root, followlinks=False):
        here = Path(folder)
        kept = []
        for name in sorted(folders):
            if (here / name).is_symlink():
                links.append(here / name)
            elif name != ".git":
                kept.append(name)
        folders[:] = kept
        entries = 0
        for name in sorted(names):
            path = here / name
            if path.is_symlink():
                links.append(path)
            elif path.is_file():
                files.append(path)
            else:
                continue
            entries += 1
        if here != root and not kept and not entries and not any((here / name).is_symlink() for name in os.listdir(here)):
            empty.append(here)
    return sorted(files), sorted(links), sorted(empty)


def comparable(text):
    """`text` as it is compared: compatibility letters made plain, accents and unseen characters dropped, lower case.

    A line break is never added or removed, so a position in the result is on the same line as in `text`.
    """
    if text.isascii():
        return text.lower()
    plain = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in plain if unicodedata.category(ch) not in UNSEEN).lower()


def printable(text):
    """`text` safe to print: a file name need not be valid UTF-8, and Python holds its bad bytes as lone surrogates."""
    return text.encode("utf-8", "backslashreplace").decode("utf-8")


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
    folded = comparable(text)
    found = [(m.group(0), folded.count("\n", 0, m.start()) + 1) for m in WORD_RE.finditer(folded)]
    runs = withheld_runs([word for word, _ in found], key, digests, cache)
    return sorted({found[start][1] for start, _ in runs})


def masked_path(parts, key, digests, cache):
    """(the path with every part that takes part in a withheld name replaced, whether any was)."""
    words, owners = [], []
    for index, part in enumerate(parts):
        for match in WORD_RE.finditer(comparable(part)):
            words.append(match.group(0))
            owners.append(index)
    hit_parts = set()
    for start, size in withheld_runs(words, key, digests, cache):
        hit_parts.update(owners[start : start + size])
    shown = "/".join(WITHHELD if index in hit_parts else part for index, part in enumerate(parts))
    return printable(shown), bool(hit_parts)


def text_of(path, data):
    """The text of a text file, or None for a binary, which is never inspected.

    Text is valid UTF-8 from the first byte to the last, with no zero byte, and is not a container, an
    image or a font by its suffix or its first bytes. Nothing is read in part: one byte that is not
    UTF-8 makes the whole file a binary, because another encoding can spell a name without one ASCII letter.
    """
    if path.suffix.lower() in CONTAINER_SUFFIXES or data.startswith(BINARY_MAGIC) or b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def is_binary(path, data):
    """True for a file the guard does not read as text (see `text_of`)."""
    return text_of(path, data) is None


def scan(root, key, digests, approved=frozenset()):
    """(entries seen, [(shown path, where the name is)], [(shown path, start of its SHA-256)] of binaries not approved).

    A shown path never contains a withheld name: the part that holds one is replaced.
    """
    root = Path(root)
    cache = {}
    found, unapproved = [], []
    files, links, empty = tree_entries(root)
    for path in files:
        shown, in_path = masked_path(path.relative_to(root).parts, key, digests, cache)
        where = ["in its path"] if in_path else []
        data = path.read_bytes()
        text = text_of(path, data)
        if text is None:
            # Never inspected: these exact bytes are on the approved list, or the file is refused.
            sha = hashlib.sha256(data).hexdigest()
            if sha not in approved:
                unapproved.append((shown, sha[:16]))
        else:
            lines = withheld_name_lines(text, key, digests, cache)
            if lines:
                where.append("line " + ", ".join(str(line) for line in lines))
        if where:
            found.append((shown, "; ".join(where)))
    for path in links:
        # Git publishes a link's name and the target it stores. Both are compared; the target is never opened.
        shown, in_path = masked_path(path.relative_to(root).parts, key, digests, cache)
        where = ["in its path"] if in_path else []
        if withheld_name_lines(os.readlink(path), key, digests, cache):
            where.append("in its link target")
        if where:
            found.append((shown, "; ".join(where)))
    for path in empty:
        shown, in_path = masked_path(path.relative_to(root).parts, key, digests, cache)
        if in_path:
            found.append((shown + "/", "in its path"))
    return len(files) + len(links) + len(empty), sorted(found), unapproved


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fail when a file holds a name that must never be published.")
    parser.add_argument("tree", help="the folder to check; it is read as data and nothing in it is run")
    parser.add_argument("--digests", default=str(DEFAULT_DIGESTS), help="the digest file to compare against")
    parser.add_argument(
        "--approved", default=str(DEFAULT_APPROVED), help="the list of binary files a maintainer approved, by SHA-256"
    )
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
    try:
        approved = load_approved(args.approved)
    except (OSError, ValueError) as error:
        print(f"name guard: the list of approved binary files cannot be used ({error})")
        return 2

    seen, found, unapproved = scan(args.tree, key.encode("utf-8"), digests, approved)
    if not found and not unapproved:
        print(f"name guard: {seen} files checked, no withheld name")
        return 0
    if found:
        print(f"name guard: a withheld name is in {len(found)} of {seen} files (where it is, never what it is):")
        for shown, where in found:
            print(f"  {shown}: {where}")
    if unapproved:
        count = f"{len(unapproved)} of {seen}"
        print(f"name guard: {count} files are binary and not approved, so they cannot be published here.")
        print("  A binary is never inspected. Publish the content as text, or have a maintainer who has looked at")
        print("  the file add its SHA-256 to tests/data/approved-binaries.sha256 on the default branch first:")
        for shown, sha in unapproved:
            print(f"  {shown}  (sha256 {sha}...)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
