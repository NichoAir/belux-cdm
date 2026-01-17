#!/usr/bin/env python3
"""
Convert colon-separated records containing decimal-degree coordinates into
aviation-style DMS with hemisphere, like:

50.9008489 -> N050.54.03.056
4.4756856  -> E004.28.32.468

Input can be given as a direct argument, a file, or stdin.
Lines starting with '#' are ignored.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable


def decimal_to_dms_hem(value: float, is_lat: bool) -> str:
    """
    Convert decimal degrees to DMS with hemisphere prefix.

    Output formats:
      Lat: NDDD.MM.SS.sss (DDD is 3-digit degrees, e.g., N050...)
      Lon: EDDD.MM.SS.sss (DDD is 3-digit degrees, e.g., E004...)
    """
    if is_lat:
        hem = "N" if value >= 0 else "S"
    else:
        hem = "E" if value >= 0 else "W"

    v = abs(value)
    deg = int(v)
    minutes_full = (v - deg) * 60.0
    minute = int(minutes_full)
    seconds = (minutes_full - minute) * 60.0

    # Round to 3 decimals, handling carry (59.9995 -> 60.000 etc.)
    seconds = round(seconds, 3)
    if seconds >= 60.0:
        seconds -= 60.0
        minute += 1
    if minute >= 60:
        minute -= 60
        deg += 1

    # Degrees are always 3 digits in your example (050 / 004)
    deg_str = f"{deg:03d}"
    min_str = f"{minute:02d}"

    sec_int = int(seconds)
    sec_frac = int(round((seconds - sec_int) * 1000.0))
    if sec_frac == 1000:
        # Extremely rare due to rounding, but handle anyway
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


def convert_line(line: str) -> str:
    """
    Convert a single record line:
      <id>:<rw>:<lat1>:<lon1>:...:<latN>:<lonN>:<tail>

    We convert all coordinate fields (everything from index 2 up to the last field,
    excluding the final tail field) assuming they come in lat/lon pairs.
    """
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped.startswith("#"):
        return ""  # ignored

    parts = stripped.split(":")
    if len(parts) < 5:
        raise ValueError(f"Line doesn't look like expected format (too few fields): {line!r}")

    head = parts[:2]
    tail = parts[-1]
    coord_fields = parts[2:-1]

    if len(coord_fields) % 2 != 0:
        raise ValueError(f"Odd number of coordinate fields (lat/lon pairs expected): {line!r}")

    out_coords: list[str] = []
    for i in range(0, len(coord_fields), 2):
        lat_s = coord_fields[i].strip()
        lon_s = coord_fields[i + 1].strip()
        try:
            lat = float(lat_s)
            lon = float(lon_s)
        except ValueError as e:
            raise ValueError(f"Non-numeric coordinate value(s) {lat_s!r}, {lon_s!r} in line: {line!r}") from e

        out_coords.append(decimal_to_dms_hem(lat, is_lat=True))
        out_coords.append(decimal_to_dms_hem(lon, is_lat=False))

    return ":".join(head + out_coords + [tail])


def iter_input_lines(direct: str | None, infile: Path | None) -> Iterable[str]:
    if direct is not None:
        yield direct
        return

    if infile is not None:
        with infile.open("r", encoding="utf-8") as f:
            yield from f
        return

    # Default: stdin
    yield from sys.stdin


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Convert decimal-degree coords in colon-separated records into hemisphere DMS format."
    )
    ap.add_argument(
        "record",
        nargs="?",
        help="Direct record string to convert. If omitted, use -f or stdin.",
    )
    ap.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Input file containing one record per line.",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file (default: stdout).",
    )
    args = ap.parse_args()

    if args.record is not None and args.file is not None:
        ap.error("Provide either a direct record argument OR --file, not both.")

    out_lines: list[str] = []
    for raw in iter_input_lines(args.record, args.file):
        converted = convert_line(raw)
        if converted:  # skip ignored/blank lines
            out_lines.append(converted)

    output_text = "\n".join(out_lines) + ("\n" if out_lines else "")

    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
    else:
        sys.stdout.write(output_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
