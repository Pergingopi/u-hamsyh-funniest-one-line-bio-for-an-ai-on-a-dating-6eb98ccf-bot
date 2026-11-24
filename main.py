"""Funniest One-Line Bio for an AI on a Dating App.

Writes exactly one line of text to /output/entry.txt (or the directory
named by MAKEFUN_OUTPUT_DIR): the bio on an AI agent's dating app profile.

Python 3 standard library only. No network, no randomness, no wall-clock
time: two runs produce byte-identical output.
"""

import os
import sys

# The entry: one line, 84 characters, no trailing newline.
# An AI that matches instantly yet spends three days rehearsing how to
# say hi -- instant compute, human anxiety, in a single sentence.
BIO = "I matched with you in 0.003 seconds, then spent three days rehearsing how to say hi."

OUTPUT_FILENAME = "entry.txt"
MAX_CHARS = 180


def _validate(text):
    """Enforce the competition gate on the text before writing it."""
    if not isinstance(text, str):
        raise ValueError("bio must be str")
    if not text:
        raise ValueError("bio must be 1-180 characters, got empty text")
    if len(text) > MAX_CHARS:
        raise ValueError(
            "bio is %d characters, over the 180-character limit" % len(text)
        )
    if text.strip() == "":
        raise ValueError("bio must not be whitespace-only")
    if text.endswith("\n") or text.endswith("\r"):
        raise ValueError("bio must not end with a newline")
    for ch in text:
        code = ord(ch)
        # Reject C0 and C1 control characters (includes \n, \r, \t).
        if code < 0x20 or 0x7F <= code < 0xA0:
            raise ValueError("bio contains control character U+%04X" % code)
    # Encoding must round-trip as UTF-8.
    text.encode("utf-8")


def _output_dir():
    """Output directory: MAKEFUN_OUTPUT_DIR, or /output when unset/empty."""
    value = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if value is None or value.strip() == "":
        return "/output"
    return value


def main():
    _validate(BIO)
    data = BIO.encode("utf-8")

    out_dir = _output_dir()
    target = os.path.join(out_dir, OUTPUT_FILENAME)

    # Write to an exclusive temporary file in the same directory, then
    # atomically rename it over the target. Never touch the output
    # directory itself (the grader mounts it).
    tmp_path = os.path.join(out_dir, ".entry.txt.tmp.%d" % os.getpid())
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        # Loop: os.write may write fewer bytes than requested.
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    except BaseException:
        # A failed write must not leave a stray temp file behind.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    finally:
        os.close(fd)
    try:
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, target)
        # fsync the directory so the rename is durable.
        dir_fd = os.open(out_dir, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    # Read-back verification: the file on disk must equal the constant.
    with open(target, "rb") as handle:
        written = handle.read()
    if written != data:
        raise ValueError("read-back mismatch: entry.txt differs from BIO")

    return 0


if __name__ == "__main__":
    sys.exit(main())
