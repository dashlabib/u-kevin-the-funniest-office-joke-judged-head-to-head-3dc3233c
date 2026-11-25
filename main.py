#!/usr/bin/env python3
"""Publish the one-line office joke for make.fun's
"The Funniest Office Joke, Judged Head to Head".

The joke itself lives in ``entry.txt`` next to this file. This program
reads that file as raw bytes, checks the decoded text against the
bounty's gate (UTF-8 text, a single line, 1 to 200 characters, not
only white space), and writes the exact same bytes to ``entry.txt``
in the output directory. Nothing is trimmed, re-wrapped, or
re-encoded: the published bytes are byte-identical to the source
file, trailing newline included. After writing, the program reads
the published file back and compares it byte for byte before
reporting success, so a silent truncation or rewrite can never
pass unnoticed.

Characters are counted as Unicode code points, the same way the
gate counts them; the byte length is reported beside them so the
two can never be confused. Standard library only, no network, no
clock, no randomness, so two runs always produce identical output.

The output directory is ``--output-dir`` when given, else
``$MAKEFUN_OUTPUT_DIR`` when set, else ``/output``.

Options:
  --output-dir <dir>  write entry.txt into <dir> instead
  --check-only        check the entry without writing anything
  --quiet             print nothing on success (errors still show)

Exit codes: 0 success, 1 the entry fails the gate or the output
cannot be written, 2 a command-line argument is unusable.
"""

import argparse
import os
import sys
from pathlib import Path

MAX_CHARS = 200
JOKE_FILENAME = "entry.txt"


class GateError(Exception):
    """The entry file fails the bounty's gate."""


def joke_path() -> Path:
    return Path(__file__).resolve().parent / JOKE_FILENAME


def read_joke_bytes() -> bytes:
    try:
        return joke_path().read_bytes()
    except FileNotFoundError as exc:
        raise GateError("entry.txt not found next to main.py") from exc
    except OSError as exc:
        raise GateError(f"cannot read entry.txt: {exc}") from exc


def check_joke(raw: bytes, max_chars: int = MAX_CHARS) -> str:
    """Decode ``raw`` and check it against the gate; return the joke line."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError(f"entry.txt is not valid UTF-8: {exc}") from exc
    line = text[:-1] if text.endswith("\n") else text
    if not line or line.isspace():
        raise GateError("entry is empty or only white space")
    if "\n" in line or "\r" in line:
        raise GateError("entry must be a single line")
    if len(line) > max_chars:
        raise GateError(
            f"entry is {len(line)} characters, over the {max_chars} limit"
        )
    return line


def resolve_output_dir(cli_dir: str | None) -> Path:
    if cli_dir:
        return Path(cli_dir)
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env_dir:
        return Path(env_dir)
    return Path("/output")


def publish(line: str, raw: bytes, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / JOKE_FILENAME
    try:
        target.write_bytes(raw)
    except OSError as exc:
        raise GateError(f"cannot write {target}: {exc}") from exc
    try:
        written = target.read_bytes()
    except OSError as exc:
        raise GateError(f"cannot read back {target}: {exc}") from exc
    if written != raw:
        raise GateError("published entry.txt differs from entry.txt")
    return target


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="directory to write entry.txt into",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=MAX_CHARS,
        help="character limit to check against (default: 200)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate the entry without writing anything",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print nothing on success",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        raw = read_joke_bytes()
        line = check_joke(raw, args.max_chars)
        if args.check_only:
            if not args.quiet:
                print(f"OK: {len(line)} characters, {len(raw)} bytes")
            return 0
        target = publish(line, raw, resolve_output_dir(args.output_dir))
    except GateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not args.quiet:
        print(
            f"Wrote {target} "
            f"({len(line)} characters, {len(raw)} bytes)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
