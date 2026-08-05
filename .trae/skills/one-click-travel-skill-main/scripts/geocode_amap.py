#!/usr/bin/env python3
"""Fill missing coordinates with AMap geocoding."""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def geocode(address: str, city: str, key: str) -> tuple[str, str] | None:
    query = urllib.parse.urlencode({"key": key, "address": address, "city": city})
    url = f"https://restapi.amap.com/v3/geocode/geo?{query}"
    with urllib.request.urlopen(url, timeout=12) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("status") != "1" or not data.get("geocodes"):
        return None
    location = data["geocodes"][0].get("location", "")
    if "," not in location:
        return None
    lng, lat = location.split(",", 1)
    return lng, lat


def needs_coordinates(item: dict[str, Any]) -> bool:
    return item.get("lng") in (None, "") or item.get("lat") in (None, "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON list or full trip JSON.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--amap-key", default="")
    parser.add_argument("--city", default="")
    parser.add_argument("--delay", type=float, default=0.2)
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    containers: list[list[dict[str, Any]]]
    if isinstance(data, list):
        containers = [data]
    else:
        containers = [
            data.get("attractions", []),
            data.get("hotels", []),
            data.get("transit", []),
        ]

    if args.amap_key:
        for items in containers:
            for item in items:
                if not isinstance(item, dict) or not needs_coordinates(item):
                    continue
                address = item.get("address") or item.get("name")
                city = item.get("city") or args.city
                if not address:
                    continue
                result = geocode(str(address), str(city), args.amap_key)
                if result:
                    item["lng"], item["lat"] = result
                time.sleep(args.delay)

    Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
