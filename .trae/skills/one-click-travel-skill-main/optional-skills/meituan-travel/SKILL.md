---
name: one-click-travel-meituan-adapter
description: Required adapter notes for using an installed meituan-travel skill inside one-click-travel. Read before collecting Meituan hotel, attraction, ticket, rating, price, or purchase-link data.
---

# Meituan Travel Adapter

This is not a standalone replacement for the external `meituan-travel` skill. It documents how one-click-travel must use that skill before generating a travel guide.

## Availability Check

Require `meituan-travel` to appear in the current available skills/tools. If it is missing, pause and ask the user to install or enable it before continuing. Do not use public web/search results as a replacement for required Meituan data.

## Setup Prompt

Before using the external `meituan-travel` skill, confirm that its Token is configured. If it is missing or the tool reports an authentication error, pause and ask:

```text
要使用美团实时酒旅数据，需要配置美团旅行 API Token。
请前往美团开发者中心创建 Token：
https://developer.meituan.com/zh/v2/dev/token
创建后把 Token 发给我，我会保存到本地配置后继续查询。Token 属于敏感凭证，我不会在最终页面或回复里明文展示。
```

Save the token according to the installed `meituan-travel` skill's own instructions. If the user does not want to provide a Token, pause generation; do not continue with public web/search fallback or leave `meituan_url` empty as a substitute.

## Queries

Attractions:

```text
{destination} 热门景点 TOP10 门票 评分 地址 图片
```

Hotels:

```text
{hotel_city} 酒店 明天入住 1晚 {budget} 连锁品牌 近地铁 评分4.5以上 返回酒店名称 地址 明天价格 美团评分 美团链接
```

Cross-city transit/ports:

```text
{departure} 到 {destination} 口岸 交通 过关 酒店
```

## Mapping

Map returned fields into `references/data-schema.md`:

- hotel/attraction name -> `name`
- address/area -> `address`
- longitude/latitude -> `lng`/`lat`
- price text -> `price` exactly as returned
- Meituan rating -> `rating` exactly as returned, preferably in a form like `美团真实评分4.8`
- Meituan detail or booking link -> `meituan_url` for hotels, `source_url` for attractions
- image URL -> `image_url`
- platform name -> `source_name: "美团"`
- real-time or direct listing data -> `confidence: "high"`

Never reconstruct masked prices such as `￥4XX起`. Preserve them exactly.

## Blocking Conditions

When Meituan is unavailable or authentication fails:

- Pause the one-click-travel workflow before hotel or attraction collection.
- Ask the user to install/enable `meituan-travel` or configure a valid Meituan Travel API Token.
- Resume only after `meituan-travel` returns usable price, rating, and link data.
