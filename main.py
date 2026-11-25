#!/usr/bin/env python3
"""Publish the office joke for make.fun's
"The Funniest Office Joke, Judged Head to Head".

``entry.txt`` holds the joke, one line. This script checks it
against the gate (UTF-8, one line, between 1 and 200 characters)
and copies its exact bytes to ``entry.txt`` under the output
directory, then reads the copy back to prove nothing changed
on the way. The joke is never edited, trimmed, or re-encoded.

Usage: python3 main.py [--out DIR] [--check] [--silent]
The output directory defaults to $MAKEFUN_OUTPUT_DIR, else /output.
"""

import sys
import os
from pathlib import Path

LIMIT = 200
NAME = "entry.txt"


class JokeError(Exception):
    """The entry fails the gate, or an argument is unusable."""


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    return 1


def read_source():
    source = Path(__file__).resolve().parent / NAME
    try:
        return source.read_bytes()
    except FileNotFoundError:
        raise JokeError("no entry.txt beside main.py")
    except OSError as exc:
        raise JokeError(f"cannot read entry.txt ({exc})")


def gate(raw):
    """Decode ``raw`` and check it against the gate; return the joke line."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise JokeError(f"entry.txt is not UTF-8 ({exc})")
    line = text[:-1] if text.endswith("\n") else text
    if not line.strip():
        raise JokeError("entry is empty")
    if "\n" in line or "\r" in line:
        raise JokeError("entry must be one line")
    if len(line) > LIMIT:
        raise JokeError(f"entry is {len(line)} characters; the limit is {LIMIT}")
    return line


def parse(argv):
    """Read the command line; return (output directory, check only, silent)."""
    out = None
    check = False
    silent = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--out":
            i += 1
            if i >= len(argv):
                raise JokeError("--out needs a directory after it")
            out = argv[i]
        elif arg.startswith("--out="):
            out = arg[len("--out="):]
            if not out:
                raise JokeError("--out needs a directory after it")
        elif arg == "--check":
            check = True
        elif arg == "--silent":
            silent = True
        else:
            raise JokeError(f"unknown argument: {arg}")
        i += 1
    if out is None:
        out = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    return Path(out), check, silent


def run(argv):
    try:
        directory, check, silent = parse(argv)
        raw = read_source()
        line = gate(raw)
    except JokeError as exc:
        return fail(str(exc))
    if check:
        if not silent:
            print(f"entry ok: {len(line)} characters, {len(raw)} bytes")
        return 0
    target = directory / NAME
    try:
        directory.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        if target.read_bytes() != raw:
            return fail("published copy differs from entry.txt")
    except OSError as exc:
        return fail(f"cannot publish entry.txt ({exc})")
    if not silent:
        print(f"published {target}: {len(line)} characters, {len(raw)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
