#!/usr/bin/env python3
"""
Convert colon-separated runway records containing coordinates between:
- decimal degrees  <->  aviation-style DMS with hemisphere, like:
    50.9008489 -> N050.54.03.056
    4.4756856  -> E004.28.32.468

Input can be given as a direct argument, a file, or stdin.

Behavior:
- Comment lines (starting with '#', ignoring leading whitespace) are passed through unchanged.
- Blank lines are passed through unchanged.
- Only the 8 LAT/LON fields are converted (fields 2..9). TAXITIME and optional REMS are preserved.
- Supported formats:
    AIRPORT:RUNWAY:BL_LAT:BL_LON:TL_LAT:TL_LON:TR_LAT:TR_LON:BR_LAT:BR_LON:TAXITIME
    AIRPORT:RUNWAY:BL_LAT:BL_LON:TL_LAT:TL_LON:TR_LAT:TR_LON:BR_LAT:BR_LON:TAXITIME:REM1,REM2,...

Auto-detect:
- If --reverse is not explicitly forced, the script will inspect coordinate fields:
  - If they look like DMS (e.g., N049.38.04.530), it will choose reverse mode.
  - If they look like decimals (e.g., 50.9019), it will choose forward mode.
- If user supplied --reverse but input looks decimal (or vice versa), it warns on stderr.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


DMS_RE = re.compile(r"^[NSEW]\d{3}\.\d{2}\.\d{2}\.\d{3}$", re.IGNORECASE)


def looks_like_dms(s: str) -> bool:
    return bool(DMS_RE.match(s.strip()))


def looks_like_decimal(s: str) -> bool:
    try:
        float(s.strip())
        return True
    except ValueError:
        return False


def decimal_to_dms_hem(value: float, is_lat: bool) -> str:
    if is_lat:
        hem = "N" if value >= 0 else "S"
    else:
        hem = "E" if value >= 0 else "W"

    v = abs(value)
    deg = int(v)
    minutes_full = (v - deg) * 60.0
    minute = int(minutes_full)
    seconds = (minutes_full - minute) * 60.0

    seconds = round(seconds, 3)
    if seconds >= 60.0:
        seconds -= 60.0
        minute += 1
    if minute >= 60:
        minute -= 60
        deg += 1

    deg_str = f"{deg:03d}"
    min_str = f"{minute:02d}"

    sec_int = int(seconds)
    sec_frac = int(round((seconds - sec_int) * 1000.0))
    if sec_frac == 1000:
        sec_frac = 0
        sec_int += 1
        if sec_int >= 60:
            sec_int = 0
            minute += 1
            if minute >= 60:
                minute = 0
                deg += 1
                deg_str = f"{deg:03d}"
                min_str = f"{minute:02d}"

    sec_str = f"{sec_int:02d}.{sec_frac:03d}"
    return f"{hem}{deg_str}.{min_str}.{sec_str}"


def dms_hem_to_decimal(text: str, is_lat: bool) -> float:
    s = text.strip()
    if len(s) < 2:
        raise ValueError(f"Too short for DMS: {text!r}")

    hem = s[0].upper()
    if is_lat and hem not in ("N", "S"):
        raise ValueError(f"Latitude must start with N or S, got {text!r}")
    if (not is_lat) and hem not in ("E", "W"):
        raise ValueError(f"Longitude must start with E or W, got {text!r}")

    rest = s[1:]
    parts = rest.split(".")
    if len(parts) != 4:
        raise ValueError(f"DMS must look like HDDD.MM.SS.sss, got {text!r}")

    try:
        deg = int(parts[0])
        minute = int(parts[1])
        sec = int(parts[2])
        msec = int(parts[3])
    except ValueError as e:
        raise ValueError(f"Non-numeric DMS components in {text!r}") from e

    if not (0 <= minute < 60):
        raise ValueError(f"Minutes out of range in {text!r}")
    if not (0 <= sec < 60):
        raise ValueError(f"Seconds out of range in {text!r}")
    if not (0 <= msec < 1000):
        raise ValueError(f"Milliseconds out of range in {text!r}")

    seconds = sec + (msec / 1000.0)
    dec = deg + (minute / 60.0) + (seconds / 3600.0)
    if hem in ("S", "W"):
        dec = -dec
    return dec


def format_decimal(value: float, places: int) -> str:
    return f"{value:.{places}f}"


def detect_mode(parts: list[str]) -> bool | None:
    """
    Returns:
      True  -> should be reverse (DMS -> decimal)
      False -> should be forward (decimal -> DMS)
      None  -> cannot tell
    """
    coord_fields = parts[2:10]
    dms_hits = sum(1 for s in coord_fields if looks_like_dms(s))
    dec_hits = sum(1 for s in coord_fields if looks_like_decimal(s))

    if dms_hits == 8 and dec_hits == 0:
        return True
    if dec_hits == 8 and dms_hits == 0:
        return False

    # Mixed/ambiguous
    if dms_hits > dec_hits and dms_hits >= 4:
        return True
    if dec_hits > dms_hits and dec_hits >= 4:
        return False
    return None


def convert_record_line(line: str, reverse: bool, decimal_places: int) -> str:
    stripped = line.strip()
    if not stripped:
        return line.rstrip("\n")

    parts = stripped.split(":")
    if len(parts) not in (11, 12):
        raise ValueError(
            f"Unexpected field count {len(parts)} (expected 11 or 12) in line: {line!r}"
        )

    out = parts[:]
    # Convert ONLY indices 2..9 (8 coordinate fields)
    for j, idx in enumerate(range(2, 10)):
        is_lat = (j % 2 == 0)
        raw = parts[idx].strip()
        if reverse:
            dec = dms_hem_to_decimal(raw, is_lat=is_lat)
            out[idx] = format_decimal(dec, places=decimal_places)
        else:
            dec = float(raw)
            out[idx] = decimal_to_dms_hem(dec, is_lat=is_lat)

    return ":".join(out)


def iter_input_lines(direct: str | None, infile: Path | None) -> Iterable[str]:
    if direct is not None:
        yield direct
        return
    if infile is not None:
        with infile.open("r", encoding="utf-8") as f:
            yield from f
        return
    yield from sys.stdin


def warn(msg: str) -> None:
    sys.stderr.write(f"WARNING: {msg}\n")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Convert runway record coordinate fields between decimal degrees and hemisphere DMS."
    )
    ap.add_argument("record", nargs="?", help="Direct record string to convert. If omitted, use -f or stdin.")
    ap.add_argument("-f", "--file", type=Path, help="Input file containing one record per line.")
    ap.add_argument("-o", "--output", type=Path, help="Output file (default: stdout).")
    ap.add_argument("--reverse", action="store_true", help="Convert from hemisphere DMS back to decimal degrees.")
    ap.add_argument(
        "--force",
        action="store_true",
        help="Do not auto-detect; strictly follow --reverse (or lack of it).",
    )
    ap.add_argument(
        "--decimal-places",
        type=int,
        default=7,
        help="Decimal places to output when converting to decimal (default: 7).",
    )
    args = ap.parse_args()

    if args.record is not None and args.file is not None:
        ap.error("Provide either a direct record argument OR --file, not both.")

    out_lines: list[str] = []

    for raw in iter_input_lines(args.record, args.file):
        # Pass through comments + blank lines unchanged
        if raw.lstrip().startswith("#") or raw.strip() == "":
            out_lines.append(raw.rstrip("\n"))
            continue

        stripped = raw.strip()
        parts = stripped.split(":")
        if len(parts) not in (11, 12):
            raise ValueError(
                f"Unexpected field count {len(parts)} (expected 11 or 12) in line: {raw!r}"
            )

        chosen_reverse = args.reverse
        if not args.force:
            detected = detect_mode(parts)
            if detected is not None and detected != args.reverse:
                # User "should have used" the other direction
                if detected:
                    warn(f"Input looks like DMS but --reverse was not set; auto-enabling --reverse for: {stripped!r}")
                else:
                    warn(f"Input looks like decimal but --reverse was set; auto-disabling --reverse for: {stripped!r}")
                chosen_reverse = detected

        try:
            converted = convert_record_line(raw, reverse=chosen_reverse, decimal_places=args.decimal_places)
        except ValueError as e:
            # If force mode caused failure, add a helpful hint.
            hint = ""
            if args.force:
                coord_fields = parts[2:10]
                if any(looks_like_dms(s) for s in coord_fields) and not args.reverse:
                    hint = " (Hint: these look like DMS; try --reverse or remove --force)"
                elif any(looks_like_decimal(s) for s in coord_fields) and args.reverse:
                    hint = " (Hint: these look like decimals; remove --reverse or remove --force)"
            raise ValueError(f"{e}{hint}") from e

        out_lines.append(converted)

    output_text = "\n".join(out_lines) + ("\n" if out_lines else "")

    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
    else:
        sys.stdout.write(output_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
