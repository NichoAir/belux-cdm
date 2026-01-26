#!/usr/bin/env python3
"""
Convert apron/taxi coordinate lines in the format:

AIRPORT:RUNWAY:BOTTOM_LEFT_LAT:BOTTOM_LEFT_LON:TOP_LEFT_LAT:TOP_LEFT_LON:TOP_RIGHT_LAT:TOP_RIGHT_LON:BOTTOM_RIGHT_LAT:BOTTOM_RIGHT_LON:TAXITIME[:REM1,REM2,...]

...into GeoJSON Features.

- Ignores blank lines and lines starting with '#'
- If 4 corners are present -> Polygon
- If only 2 points are present -> LineString (useful for runway segments like ELLX:24:lat:lon:lat:lon:taxitime:...)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _to_float(s: str) -> float:
    return float(s.strip())


def parse_line(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split(":")
    if len(parts) < 3:
        return None  # not a valid data line

    airport = parts[0].strip()
    runway = parts[1].strip()

    # Everything after airport/runway: some number of lat/lon pairs, then taxitime, then optional remarks
    rest = parts[2:]

    # Optional remarks are always in the *last* field if it contains commas.
    remarks: Optional[List[str]] = None
    if rest and ("," in rest[-1]):
        remarks = [r.strip() for r in rest[-1].split(",") if r.strip()]
        rest = rest[:-1]

    if not rest:
        return None

    # Last remaining item is taxitime
    taxitime_str = rest[-1].strip()
    coord_tokens = rest[:-1]

    # coord_tokens should be an even number: lat/lon pairs
    if len(coord_tokens) < 4 or (len(coord_tokens) % 2 != 0):
        raise ValueError(f"Bad coordinate token count on line: {line!r}")

    coords: List[Tuple[float, float]] = []
    for i in range(0, len(coord_tokens), 2):
        lat = _to_float(coord_tokens[i])
        lon = _to_float(coord_tokens[i + 1])
        coords.append((lon, lat))  # GeoJSON is [lon, lat]

    # Determine geometry
    if len(coords) == 4:
        # Polygon must be closed (first == last)
        ring = coords + [coords[0]]
        geometry = {"type": "Polygon", "coordinates": [ring]}
    elif len(coords) == 2:
        geometry = {"type": "LineString", "coordinates": coords}
    else:
        # If you ever have other shapes, use a LineString fallback (or make this a Polygon if desired)
        geometry = {"type": "LineString", "coordinates": coords}

    # Build properties
    props: Dict[str, Any] = {
        "airport": airport,
        "runway": runway,
    }

    # Try to parse taxitime as int/float if possible
    try:
        props["taxitime"] = int(taxitime_str)
    except ValueError:
        try:
            props["taxitime"] = float(taxitime_str)
        except ValueError:
            props["taxitime"] = taxitime_str

    if remarks is not None:
        props["remarks"] = remarks

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": props,
        "raw": line,  # handy for debugging; remove if you don't want it
    }


def convert_file(input_path: Path) -> Dict[str, Any]:
    features: List[Dict[str, Any]] = []

    for lineno, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            feat = parse_line(line)
        except Exception as e:
            raise ValueError(f"Error on line {lineno}: {e}") from e
        if feat:
            features.append(feat)

    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert apron/taxi lines to GeoJSON.")
    ap.add_argument("input", type=Path, help="Input text file")
    ap.add_argument("-o", "--output", type=Path, default=None, help="Output GeoJSON file (default: <input>.geojson)")
    args = ap.parse_args()

    out_path = args.output or args.input.with_suffix(".geojson")
    geojson = convert_file(args.input)

    out_path.write_text(json.dumps(geojson, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} ({len(geojson['features'])} features)")


if __name__ == "__main__":
    main()
