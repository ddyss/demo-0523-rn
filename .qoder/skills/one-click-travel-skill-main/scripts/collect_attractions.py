#!/usr/bin/env python3
"""Normalize attraction candidates into the one-click-travel schema."""

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


def normalize_item(item: dict[str, Any], city: str) -> dict[str, Any]:
    lng = first_present(item, "lng", "longitude", "经度", default="")
    lat = first_present(item, "lat", "latitude", "纬度", default="")
    return {
        "name": first_present(item, "name", "title", "景点名称"),
        "city": first_present(item, "city", "城市", default=city),
        "address": first_present(item, "address", "area", "位置", "地址"),
        "lng": lng,
        "lat": lat,
        "rating": str(first_present(item, "rating", "score", "评分")),
        "price": str(first_present(item, "price", "ticket_price", "价格", default="以平台实时信息为准")),
        "summary": first_present(item, "summary", "description", "desc", "描述"),
        "tags": normalize_tags(first_present(item, "tags", "标签", default=[])),
        "image_url": first_present(item, "image_url", "image", "图片URL"),
        "source_url": first_present(item, "source_url", "url", "link", "链接"),
        "source_name": first_present(item, "source_name", "source", "来源"),
        "rednote_url": first_present(item, "rednote_url", "xiaohongshu_url", "小红书链接"),
        "rednote_note_id": first_present(item, "rednote_note_id", "note_id", "笔记ID"),
        "confidence": first_present(item, "confidence", "置信度", default="medium"),
    }


def load_items(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("attractions", "items", "results", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError("Input JSON must be a list or contain attractions/items/results/data.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Raw attraction candidate JSON.")
    parser.add_argument("--output", required=True, help="Normalized attraction JSON output.")
    parser.add_argument("--city", default="", help="Default city for items without a city.")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    items = load_items(Path(args.input))
    normalized = [normalize_item(item, args.city) for item in items[: args.limit]]
    Path(args.output).write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
