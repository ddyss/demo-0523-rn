---
name: one-click-travel-rednote-adapter
description: Required adapter notes for using an installed rednote-skill inside one-click-travel. Read before collecting Xiaohongshu notes, note IDs, UGC highlights, or app deep links.
---

# Rednote Adapter

This is not a standalone replacement for the external `rednote-skill`. It documents how one-click-travel must use that skill before generating a travel guide.

## Availability Check

Require `rednote-skill` to appear in the current available skills/tools. If it is missing, pause and ask the user to install or enable it before continuing. Do not use public web search snippets as a replacement for required Xiaohongshu data.

## Login Prompt

Before using the external `rednote-skill`, validate login with its cookie validation script. If login is missing or expired, pause and ask:

```text
要获取小红书笔记内容和可跳转的攻略链接，需要先登录小红书。
我会打开登录窗口，请在浏览器里完成登录，完成后关闭窗口；登录状态会保存在本地 cookies 文件中。
如果你暂时不想登录，可以回复“暂停小红书”，我会暂停生成；完成登录后再继续。
```

Only run note search/extraction after login validation succeeds. If the user skips login, pause generation; do not keep `rednote_url` and `rednote_note_id` empty as a substitute for required Xiaohongshu data.

## Queries

Search notes:

```text
{destination} 必去景点 攻略
{destination} 避坑 交通 美食
{destination} 酒店 推荐 {budget}
```

For cross-city trips:

```text
{departure} 去 {destination} 过关 攻略
{hotel_city} 口岸附近酒店
```

## Mapping

Map returned fields into `references/data-schema.md`:

- note title/content summary -> `summary` or item research notes
- note URL -> `rednote_url`
- note ID parsed from `/explore/{noteId}` -> `rednote_note_id`
- note images -> `image_url` only when stable and directly usable
- platform name -> `source_name: "小红书"`
- public note detail extracted by installed skill -> `confidence: "medium"` unless verified by another source

Use Xiaohongshu content to enrich reasons to visit and practical tips. Do not use it as the only source for prices, opening status, or official policy.

## Attraction Recommendation Use

For one-click-travel, Xiaohongshu must influence attraction selection and ordering:

- Search 3-6 notes for destination routes and must-visit attractions.
- Dump the most relevant notes and extract repeated attraction names, route order, practical warnings, and tags.
- Add `rednote_url` to attraction cards when a stable URL is available.
- Add tags such as `小红书热推`, `小红书路线`, or `小红书高频` only when supported by extracted notes.
- Keep official/map sources for factual fields such as address, coordinates, price, opening rules, and booking requirements.

## Blocking Conditions

When Rednote is unavailable or login is blocked:

- Pause the one-click-travel workflow before attraction recommendation and route ordering.
- Ask the user to install/enable `rednote-skill` or complete Xiaohongshu login.
- Resume only after `rednote-skill` returns usable note, route, or attraction signal data.
