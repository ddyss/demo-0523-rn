# One Click Travel Skill

语言 / Language: [中文](#中文) | [English](#english)

## 中文

`one-click-travel` 是一个用于生成中文旅游攻略 HTML 页面 的 skill，可用于支持 skill 机制的 Agent。用户给出目的地城市后，它会结合高德地图、美团酒店实时价格、小红书攻略路线、景点/酒店卡片和 App/网页跳转链接，生成一个可分享、可本地打开的旅行攻略页。

### 在线 Demo

- Demo 页面：https://www.travel.aihub.wiki/shenzhen-hongkong-map.html

这个示例展示了地图优先布局、酒店卡片、跨城路线说明、景点 Tab 和 App/网页跳转的最终效果。

### 可以生成什么

- 一个自包含的 HTML 旅游攻略页面。
- 高德实时地图，标记景点、酒店和交通点位。
- 默认查询明天入住 1 晚的美团酒店价格。
- 结合小红书笔记路线热度生成景点推荐，再用官方/公开来源核验地址、票价、预约规则等事实信息。
- 移动端支持美团、小红书 App 唤起；失败时 fallback 到网页。
- 可选用 EdgeOne CLI 从本地直接部署，不需要 GitHub；返回可分享的预览 token 链接。

### 仓库结构

```text
one-click-travel/
├── SKILL.md
├── assets/
│   └── html-template/template.html
├── optional-skills/
│   ├── meituan-travel/SKILL.md
│   └── rednote-skill/SKILL.md
├── references/
│   ├── data-schema.md
│   └── edgeone-cli-deploy.md
└── scripts/
    ├── collect_attractions.py
    ├── collect_hotels.py
    ├── collect_routes.py
    ├── collect_weather.py
    ├── deploy_edgeone.py
    ├── generate_html.py
    └── geocode_amap.py
```

### 安装方法

把整个目录复制到 支持 skill 的 Agent 对应 skills 目录：

```powershell
Copy-Item -Recurse . "$env:USERPROFILE\.codex\skills\one-click-travel"
```

安装后重启对应 Agent，新的 skill 才会被发现。

### 前置 Skill 安装

使用 `one-click-travel` 前，请先安装并启用这两个强依赖 skill：

- 美团旅行 skill：https://developer.meituan.com/zh/v2/dev/aiHub/skillManage/detail/12
- 小红书 / Rednote skill：https://github.com/MrMao007/rednote-skills

安装后重启对应 Agent，确认当前会话能发现 `meituan-travel` 和 `rednote-skill`，再开始生成攻略。

### 必要配置

#### 高德地图

默认生成实时地图页面，因此需要高德 Web JS API Key。如果你的高德应用开启了安全密钥校验，还需要提供 `securityJsCode`。

- 创建 Key：https://console.amap.com/dev/key/app
- Web JS API 准备说明：https://lbs.amap.com/api/javascript-api-v2/guide/abc/prepare

如果没有 Key，只有在用户明确回复"跳过地图"后，skill 才会生成静态坐标清单版。

#### 天气数据

skill 会自动通过高德天气 API 获取目的地未来 3 天的天气预报，并在路线规划中根据天气调整行程（如雨天优先安排室内景点）。天气信息会以简洁格式显示在每日路线卡片中。

- 天气 API 需要高德 **Web 服务** Key（与地图使用的 JS API Key 不同）。
- 如果用户提供的 `amap_key` 仅支持 JS API，天气查询会返回 `USERKEY_PLAT_NOMATCH` 错误，此时 skill 会提示用户创建 Web 服务 Key 或跳过天气功能。
- 创建 Web 服务 Key：https://console.amap.com/dev/key/app
- 路线规划会根据天气智能调整：雨天优先室内景点，高温天提示防晒补水。

#### 美食推荐

skill 会在生成的攻略页面中展示目的地美食推荐，分为"正餐"和"小吃"两类，各以不同颜色的卡片和地图标记区分（🍽️ 正餐 / 🍜 小吃）。每张美食卡片包含餐厅名称、评分、人均价格、地址、简介、最近地铁站及步行时间、推荐菜和详情链接。

- 美食数据来源优先使用小红书笔记中推荐的餐厅信息，结合网络搜索补充。
- 如果已安装 `dianping-search` skill，可通过大众点评 API 获取更精准的餐厅评分、人均价格和推荐菜数据。
- 美食数据结构遵循 `references/data-schema.md` 中的 `foods` 字段，支持 `category`（restaurant/snack）、`nearest_station`、`walk_time`、`summary`、`recommended_dishes` 等字段。

#### 美团旅行

美团是硬依赖，必须配置后才能生成攻略。配置后可以获取真实酒店价格、评分和美团链接。

- Token 创建地址：https://developer.meituan.com/zh/v2/dev/token
- skill 会先检查本地是否已配置美团 Token。
- 如果美团不可用、Token 缺失或接口鉴权失败，skill 会暂停并要求完成配置，不会降级使用公开酒店来源替代。

#### 小红书 / Rednote

小红书是硬依赖，必须通过 `rednote-skill` 完成登录后才能生成攻略。登录后可以用于判断路线热度、景点排序、实用贴士和攻略链接。

- skill 会通过 `rednote-skill` 校验登录状态。
- 如果登录失效，会引导用户在浏览器中重新登录。
- 如果用户选择跳过登录，skill 会暂停生成，不会继续使用官方/公开来源替代小红书数据。

### 数据结构

生成页面使用的标准数据结构见：

```text
references/data-schema.md
```

关键默认值：

- `hotel_checkin_date`：默认使用用户时区的明天。
- `hotel_checkout_date`：默认入住后一天，即 1 晚。
- `hotel.price`：美团可用时保留美团返回的原始价格字符串。
- `hotel.rating`：优先使用美团评分。
- `confidence`：可在内部保留，但最终 HTML 页面不展示。

### 典型用法

```text
使用 $one-click-travel 帮我制作一个杭州旅游攻略
```

skill 会：

1. 解析目的地、预算和日期。
2. 如果没有高德 Key，先引导用户提供。
3. 通过高德天气 API 获取未来 3 天天气预报，生成天气出行贴士。
4. 确认美团已配置并查询明天入住 1 晚的酒店实时价。
5. 确认小红书已登录并读取攻略笔记用于景点路线、热度判断和美食推荐。
6. 用官方/公开来源核验地址、坐标、票价、开放和预约规则。
7. 生成路线规划数据，根据天气智能调整行程（雨天优先室内景点），渲染路线时间线和地图路线可视化。
8. 渲染美食推荐区域，分类展示正餐和小吃卡片。
9. 生成最终 HTML 页面。
10. 询问是否需要发布到 EdgeOne Pages；如果需要，用本地 EdgeOne CLI 部署并返回完整预览 token 链接。

### 注意事项

- 不建议把生成的攻略 HTML、截图或本地数据导出提交到仓库，除非你明确想保留示例。
- 不要提交高德 Key、美团 Token、小红书 cookies 或任何凭证文件。
- 酒店价格、评分、开放状态、预约规则都应视为实时平台数据，出行前需要再次核验。

## English

`one-click-travel` is a skill for agents that support skill-based workflows. It is used for generating a shareable Chinese travel-guide HTML page from a destination city. It combines map markers, Xiaohongshu-informed attraction planning, Meituan hotel prices, deep links, and a responsive HTML template.

### Online Demo

- Demo page: https://www.travel.aihub.wiki/shenzhen-hongkong-map.html

This demo shows the map-first layout, hotel cards, cross-city route guidance, attraction tabs, and app/web fallback links.

### What It Generates

- A self-contained HTML travel guide.
- Live AMap markers for attractions, hotels, and transit points.
- Hotel cards with tomorrow's 1-night Meituan price by default.
- Attraction cards informed by Xiaohongshu route notes, with official/public sources used for factual verification.
- Default route planning page with day-by-day route data and AMap route visualization.
- Mobile-friendly fallback links for Meituan, Xiaohongshu, and normal web pages.
- Optional local EdgeOne CLI deployment without GitHub, returning a shareable preview token URL.

### Repository Layout

```text
one-click-travel/
├── SKILL.md
├── assets/
│   └── html-template/template.html
├── optional-skills/
│   ├── meituan-travel/SKILL.md
│   └── rednote-skill/SKILL.md
├── references/
│   ├── data-schema.md
│   └── edgeone-cli-deploy.md
└── scripts/
    ├── collect_attractions.py
    ├── collect_hotels.py
    ├── collect_routes.py
    ├── collect_weather.py
    ├── deploy_edgeone.py
    ├── generate_html.py
    └── geocode_amap.py
```

### Installation

Copy this folder into your skills directory:

```powershell
Copy-Item -Recurse . "$env:USERPROFILE\.codex\skills\one-click-travel"
```

Restart your Agent after installation so the skill can be discovered.

### Required Skills

Install and enable these required skills before using `one-click-travel`:

- Meituan Travel skill: https://developer.meituan.com/zh/v2/dev/aiHub/skillManage/detail/12
- Xiaohongshu / Rednote skill: https://github.com/MrMao007/rednote-skills

Restart your Agent after installation and confirm the current session can discover `meituan-travel` and `rednote-skill` before generating a guide.

### Required Configuration

#### AMap

Live map pages require a 高德 Web JS API Key. If your AMap application enables security verification, also provide `securityJsCode`.

- Create a key: https://console.amap.com/dev/key/app
- Web JS API preparation guide: https://lbs.amap.com/api/javascript-api-v2/guide/abc/prepare

If no key is available, the skill can generate a static coordinate-list version only after the user explicitly chooses to skip the live map.

#### Weather Data

The skill automatically fetches a 3-day weather forecast for the destination via the AMap Weather API and adjusts route planning accordingly (e.g., prioritizing indoor attractions on rainy days). Weather is displayed concisely in each daily route card.

- The Weather API requires an AMap **Web Service** key (different from the JS API key used for maps).
- If the user's `amap_key` only supports JS API, the weather query returns `USERKEY_PLAT_NOMATCH`. The skill will prompt the user to create a Web Service key or skip weather.
- Create a Web Service key: https://console.amap.com/dev/key/app
- Route planning adjusts intelligently: indoor attractions on rainy days, sun protection tips for hot days.

#### Food Recommendations

The generated guide includes a food recommendation section with two categories: "Restaurants" and "Snacks", each with distinct card colors and map markers (🍽️ restaurants / 🍜 snacks). Each food card includes restaurant name, rating, average price, address, summary, nearest subway station with walking time, recommended dishes, and a detail link.

- Food data primarily comes from Xiaohongshu note recommendations, supplemented by web search.
- If the `dianping-search` skill is installed, more precise restaurant ratings, prices, and dish data can be fetched via the Dianping API.
- Food data follows the `foods` field in `references/data-schema.md`, supporting `category` (restaurant/snack), `nearest_station`, `walk_time`, `summary`, `recommended_dishes`, etc.

#### Meituan Travel

Meituan is required for real hotel prices, ratings, and links.

- Token page: https://developer.meituan.com/zh/v2/dev/token
- The skill checks for a configured token before using `meituan-travel`.
- If Meituan is unavailable, times out, or lacks a valid Token, the skill pauses for setup instead of falling back to public hotel sources.

#### Xiaohongshu / Rednote

Xiaohongshu is required for route popularity, attraction ordering, practical tips, and note links.

- The skill validates login through `rednote-skill`.
- If login is missing or expired, it asks the user to complete browser login.
- If the user skips login, the skill pauses generation instead of continuing with official/public sources as a substitute for Xiaohongshu data.

### Data Contract

The generated guide uses the schema documented in:

```text
references/data-schema.md
```

Important defaults:

- `hotel_checkin_date`: tomorrow in the user's timezone.
- `hotel_checkout_date`: one day after check-in unless otherwise specified.
- `hotel.price`: preserve the exact Meituan price string returned by `meituan-travel`.
- `hotel.rating`: prefer Meituan rating.
- `confidence`: may be kept internally but is not rendered in the final HTML.

### Typical Prompt

```text
Use $one-click-travel to create a Hangzhou travel guide.
```

The skill will:

1. Extract destination, budget, and dates.
2. Ask for AMap credentials if not already available.
3. Fetch 3-day weather forecast via AMap Weather API and generate weather-based travel tips.
4. Use Meituan for tomorrow's hotel prices when configured.
5. Use Xiaohongshu notes for route-informed attraction recommendations and food data when logged in.
6. Verify factual fields with official or public sources.
7. Generate default route planning data, adjusting for weather (indoor attractions on rainy days), and render the route timeline plus map route visualization.
8. Render the food recommendation section with categorized restaurant and snack cards.
9. Generate the final HTML file.
10. Ask whether to publish to EdgeOne Pages; if requested, deploy with the local EdgeOne CLI and return the full preview token URL.

### Notes

- Do not commit generated guide pages, screenshots, or local data exports unless you intentionally want examples in the repository.
- Do not commit API keys, Meituan tokens, Xiaohongshu cookies, or generated credential files.
- Prices, ratings, opening status, and booking rules should always be treated as real-time platform data.
