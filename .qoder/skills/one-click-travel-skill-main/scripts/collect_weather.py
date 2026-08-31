#!/usr/bin/env python3
"""Collect weather forecast data from AMap Weather API."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def fetch_weather(amap_key: str, city: str, extensions: str = "all") -> dict[str, Any]:
    """Fetch weather data from AMap Weather API.
    
    Args:
        amap_key: AMap API key
        city: City name (Chinese) or adcode
        extensions: "base" for current weather, "all" for 3-day forecast
    
    Returns:
        Weather data dict with forecasts
    """
    params = {
        "key": amap_key,
        "city": city,
        "extensions": extensions,
        "output": "json",
    }
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("status") != "1":
                return {"error": f"API error: {data.get('info', 'Unknown error')}"}
            
            forecasts = data.get("forecasts", [])
            if not forecasts:
                return {"error": "No forecast data available"}
            
            return parse_forecast(forecasts[0])
    except Exception as e:
        return {"error": f"Failed to fetch weather: {str(e)}"}


def parse_forecast(forecast: dict[str, Any]) -> dict[str, Any]:
    """Parse AMap forecast response into normalized format."""
    result = {
        "city": forecast.get("city", ""),
        "province": forecast.get("province", ""),
        "report_time": forecast.get("reporttime", ""),
        "forecasts": [],
    }
    
    for day in forecast.get("casts", []):
        day_data = {
            "date": day.get("date", ""),
            "week": day.get("week", ""),
            "day_weather": day.get("dayweather", ""),
            "night_weather": day.get("nightweather", ""),
            "day_temp": day.get("daytemp", ""),
            "night_temp": day.get("nighttemp", ""),
            "day_wind_power": day.get("daypower", ""),
            "night_wind_power": day.get("nightpower", ""),
            "day_wind_dir": day.get("daywind", ""),
            "night_wind_dir": day.get("nightwind", ""),
        }
        result["forecasts"].append(day_data)
    
    return result


def generate_weather_tips(weather_data: dict[str, Any]) -> list[str]:
    """Generate travel tips based on weather forecast."""
    tips = []
    
    if "error" in weather_data:
        return [f"天气数据获取失败：{weather_data['error']}"]
    
    forecasts = weather_data.get("forecasts", [])
    if not forecasts:
        return ["暂无天气预报数据"]
    
    # Analyze weather patterns
    rainy_days = []
    cold_days = []
    hot_days = []
    
    for day in forecasts:
        date = day.get("date", "")
        day_weather = day.get("day_weather", "")
        night_weather = day.get("night_weather", "")
        
        try:
            day_temp = int(day.get("day_temp", "20"))
            night_temp = int(day.get("night_temp", "15"))
        except (ValueError, TypeError):
            day_temp = 20
            night_temp = 15
        
        # Check for rain
        if any(keyword in day_weather or keyword in night_weather 
               for keyword in ["雨", "雷", "阵雨", "小雨", "中雨", "大雨"]):
            rainy_days.append(date)
        
        # Check temperature
        if day_temp >= 35:
            hot_days.append(date)
        elif night_temp <= 10:
            cold_days.append(date)
    
    # Generate tips
    if rainy_days:
        tips.append(f"{'、'.join(rainy_days)}有雨，建议携带雨具，优先安排室内景点")
    
    if hot_days:
        tips.append(f"{'、'.join(hot_days)}气温较高（≥35℃），注意防晒补水，避免长时间户外活动")
    
    if cold_days:
        tips.append(f"{'、'.join(cold_days)}气温较低（≤10℃），建议携带保暖衣物")
    
    if not tips:
        tips.append("天气预报良好，适合户外活动")
    
    return tips


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect weather forecast from AMap Weather API.")
    parser.add_argument("--amap-key", required=True, help="AMap API key")
    parser.add_argument("--city", required=True, help="City name (Chinese) or adcode")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()
    
    weather_data = fetch_weather(args.amap_key, args.city)
    
    if "error" not in weather_data:
        weather_data["tips"] = generate_weather_tips(weather_data)
    
    Path(args.output).write_text(
        json.dumps(weather_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    if "error" in weather_data:
        print(f"Warning: {weather_data['error']}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Weather forecast collected for {weather_data.get('city', args.city)}")


if __name__ == "__main__":
    main()
