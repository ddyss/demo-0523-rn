# Data Schema

Use this JSON shape between collection, geocoding, rendering, and deployment scripts.

```json
{
  "trip": {
    "destination": "香港",
    "departure": "深圳",
    "hotel_city": "深圳",
    "budget": "300元左右",
    "hotel_checkin_date": "2026-06-04",
    "hotel_checkout_date": "2026-06-05",
    "mode": "cross-city",
    "updated_at": "2026-06-03",
    "notes": ["价格、开放状态以平台实时信息为准"]
  },
  "attractions": [
    {
      "name": "太平山顶",
      "city": "香港",
      "address": "香港中西区",
      "lng": 114.1503,
      "lat": 22.2759,
      "rating": "4.7",
      "price": "以平台实时信息为准",
      "summary": "适合俯瞰维港夜景。",
      "tags": ["夜景", "地标"],
      "image_url": "",
      "source_url": "https://example.com",
      "source_name": "官方旅游网站",
      "meituan_url": "",
      "rednote_url": "",
      "rednote_note_id": "",
      "confidence": "medium"
    }
  ],
  "hotels": [
    {
      "name": "示例酒店",
      "city": "深圳",
      "address": "深圳福田口岸附近",
      "lng": 114.068,
      "lat": 22.515,
      "price": "300元左右",
      "rating": "美团真实评分4.8",
      "review_count": "",
      "summary": "近口岸，适合次日过关。",
      "tags": ["近口岸", "连锁"],
      "source_url": "https://example.com",
      "source_name": "酒店平台",
      "meituan_url": "",
      "confidence": "medium"
    }
  ],
  "transit": [
    {
      "name": "福田口岸",
      "type": "port",
      "address": "深圳市福田区",
      "lng": 114.068,
      "lat": 22.515,
      "summary": "适合深圳市区前往香港市区。",
      "source_url": "",
      "confidence": "medium"
    }
  ],
  "routes": [
    {
      "day": 1,
      "title": "中轴线经典路线",
      "summary": "酒店出发，串联核心景点后返回酒店。",
      "color": "#667eea",
      "points": [
        {
          "name": "示例酒店",
          "position": [116.391, 39.895],
          "day": 1,
          "transport": null,
          "type": "start"
        },
        {
          "name": "天安门广场",
          "position": [116.3978, 39.9034],
          "day": 1,
          "transport": "metro",
          "transport_detail": "建议地铁优先，坐到天安门东站/天安门西站后步行；具体线路以实时导航为准。",
          "transport_duration": "约30-60分钟",
          "time": "09:00",
          "stay_duration": "建议停留1-3小时",
          "description": "适合首次到访的核心景点，建议提前确认预约。",
          "ticket_price": "以平台实时信息为准",
          "nearest_station": "天安门东站/天安门西站",
          "tip": "热门预约点建议提前确认预约、安检和入场时间。",
          "type": "attraction"
        },
        {
          "name": "示例酒店",
          "position": [116.391, 39.895],
          "day": 1,
          "transport": "taxi",
          "type": "end"
        }
      ]
    }
  ],
  "sources": [
    {
      "name": "官方旅游网站",
      "url": "https://example.com",
      "used_for": "景点介绍"
    }
  ],
  "map": {
    "amap_key": "",
    "amap_security_js_code": "",
    "center_lng": 114.16,
    "center_lat": 22.28,
    "zoom": 11
  },
  "weather": {
    "city": "香港",
    "province": "广东",
    "report_time": "2026-06-25",
    "forecasts": [
      {
        "date": "2026-06-25",
        "week": "周四",
        "day_weather": "多云",
        "night_weather": "多云",
        "day_temp": "32",
        "night_temp": "26",
        "day_wind_power": "3",
        "night_wind_power": "2",
        "day_wind_dir": "东南",
        "night_wind_dir": "南"
      }
    ],
    "tips": ["天气预报良好，适合户外活动"]
  },
  "foods": [
    {
      "name": "餐厅名称",
      "city": "香港",
      "address": "详细地址",
      "lng": 114.17,
      "lat": 22.28,
      "rating": "4.5",
      "avg_price": "120",
      "review_count": "326",
      "recommended_dishes": ["招牌菜1", "招牌菜2"],
      "category": "restaurant",
      "source_url": "https://www.dianping.com/shop/xxxxx",
      "shop_id": "xxxxx"
    }
  ]
}
```

Rules:

- Keep unknown fields empty rather than inventing them.
- `confidence` may be kept internally as one of `high`, `medium`, or `low`, but do not render it in the final HTML.
- Hotel `price` defaults to tomorrow's 1-night check-in price. When Meituan is available, preserve the exact returned price string.
- Hotel `rating` defaults to Meituan rating. Do not render non-Meituan ratings as the primary hotel rating unless the source is explicitly labeled.
- Use source fields for every item that came from live research.
- Store Meituan and Xiaohongshu links separately from generic source links so buttons can be shown conditionally.
- `routes` is the independent route-planning data layer. Generate it by default from hotels, attractions, transit, and coordinates before rendering.
- `RoutePoint.type` must be one of `start`, `end`, `transit`, or `attraction`.
- `RoutePoint.transport` may be `metro`, `walk`, `ferry`, `tram`, `bus`, `taxi`, `train`, or `null`.
- Route points may include `time`, `stay_duration`, `description`, `ticket_price`, `transport_detail`, `transport_duration`, `nearest_station`, and `tip`.
- Attraction ticket prices should prefer Meituan exact returned prices and purchase links when Meituan is available; otherwise keep official/public prices or "以平台实时信息为准".
- Prefer concrete transport suggestions such as metro line/station, train station, taxi, or walking when verified or reasonably inferable. If exact line/station data is unavailable, say to use real-time navigation rather than inventing exact lines.
- Keep route points structured; do not encode route order only as prose.
