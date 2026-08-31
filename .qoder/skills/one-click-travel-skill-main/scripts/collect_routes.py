#!/usr/bin/env python3
"""Build default route data from normalized hotel and attraction coordinates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_html import build_default_routes


def is_rainy_day(forecast: dict[str, Any]) -> bool:
    """Check if a forecast day has rainy weather."""
    rain_keywords = ["雨", "雷", "阵雨", "小雨", "中雨", "大雨", "暴雨"]
    day_weather = forecast.get("day_weather", "")
    night_weather = forecast.get("night_weather", "")
    return any(kw in day_weather or kw in night_weather for kw in rain_keywords)


def get_weather_tips_for_day(weather: dict[str, Any], day_index: int) -> str:
    """Get weather-based tip for a specific route day."""
    if not weather or "error" in weather:
        return ""
    forecasts = weather.get("forecasts", [])
    if day_index >= len(forecasts):
        return ""
    forecast = forecasts[day_index]
    if is_rainy_day(forecast):
        return "当天有雨，优先安排室内景点，携带雨具"
    day_temp = forecast.get("day_temp", "")
    try:
        temp = int(day_temp)
    except (ValueError, TypeError):
        return ""
    if temp >= 35:
        return "当天气温较高，注意防晒补水"
    if temp <= 5:
        return "当天气温较低，注意保暖"
    return ""


def apply_weather_to_routes(data: dict[str, Any]) -> None:
    """Add weather tips to route points based on weather forecast."""
    weather = data.get("weather", {})
    if not weather or "error" in weather:
        return
    routes = data.get("routes", [])
    for day_index, route in enumerate(routes):
        weather_tip = get_weather_tips_for_day(weather, day_index)
        if not weather_tip:
            continue
        # Prepend weather tip to route summary
        existing_summary = route.get("summary", "")
        if existing_summary:
            route["summary"] = f"{weather_tip}。{existing_summary}"
        else:
            route["summary"] = weather_tip
        # Add weather tip to each attraction point
        for point in route.get("points", []):
            if point.get("type") == "attraction":
                existing_tip = point.get("tip", "")
                if existing_tip:
                    point["tip"] = f"{weather_tip}。{existing_tip}"
                else:
                    point["tip"] = weather_tip


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Normalized trip JSON.")
    parser.add_argument("--output", required=True, help="Trip JSON with routes added.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing routes.")
    args = parser.parse_args()

    input_path = Path(args.input)
    data: dict[str, Any] = json.loads(input_path.read_text(encoding="utf-8-sig"))
    if args.overwrite or not data.get("routes"):
        data["routes"] = build_default_routes(data)
    apply_weather_to_routes(data)
    Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
