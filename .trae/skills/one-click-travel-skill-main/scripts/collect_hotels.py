#!/usr/bin/env python3
"""Normalize hotel candidates into the one-click-travel schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def first_present(item: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return default


def normalize_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        parts = value.replace("，", ",").split(",")
        return [part.strip() for part in parts if part.strip()]
    return []


def normalize_item(item: dict[str, Any], city: str, budget: str) -> dict[str, Any]:
    return {
        "name": first_present(item, "name", "hotel_name", "title", "酒店名称"),
        "city": first_present(item, "city", "城市", default=city),
        "address": first_present(item, "address", "area", "位置", "地址"),
        "lng": first_present(item, "lng", "longitude", "经度"),
        "lat": first_present(item, "lat", "latitude", "纬度"),
        "price": str(first_present(item, "price", "价格", default=budget or "以平台实时信息为准")),
        "rating": str(first_present(item, "rating", "score", "评分")),
        "review_count": str(first_present(item, "review_count", "comments", "点评数")),
        "summary": first_present(item, "summary", "description", "desc", "描述"),
        "tags": normalize_tags(first_present(item, "tags", "标签", default=[])),
        "source_url": first_present(item, "source_url", "url", "link", "链接"),
        "source_name": first_present(item, "source_name", "source", "来源"),
        "meituan_url": first_present(item, "meituan_url", "美团链接"),
        "confidence": first_present(item, "confidence", "置信度", default="medium"),
    }


def load_items(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("hotels", "items", "results", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError("Input JSON must be a list or contain hotels/items/results/data.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Raw hotel candidate JSON.")
    parser.add_argument("--output", required=True, help="Normalized hotel JSON output.")
    parser.add_argument("--city", default="", help="Default city for items without a city.")
    parser.add_argument("--budget", default="")
    parser.add_argument("--limit", type=int, default=4)
    args = parser.parse_args()

    items = load_items(Path(args.input))
    normalized = [normalize_item(item, args.city, args.budget) for item in items[: args.limit]]
    Path(args.output).write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
