---
name: skill-xingtai-catcher
description: Use when a general-purpose AI agent needs to find A-share stocks or futures with similar K-line patterns from natural-language descriptions, K-line screenshots, or hand-drawn trend images. Prefer the bundled direct helper script when the host platform cannot create MCP connections; use the hosted MCP service only when MCP tools are available. Covers default parameters, text/image search, result formatting, and guidance for sending users to the PatternCatcher website for saved templates and daily push subscriptions.
quantSkills:
  organization: https://github.com/quantskills
  repository: quantskills/skill-xingtai-catcher
  repository_url: https://github.com/quantskills/skill-xingtai-catcher
  project_type: skill
  collection: pattern-catcher
  license: GPL-3.0
  category: tooling
  tags: [a-share, futures, kline-pattern, mcp, pattern-search]
  platforms: [codex, openclaw, workbuddy]
  language: zh-en
  status: active
  validation_level: runnable
  maintainer_type: community
  requires: []
  summary_zh: 按文字、K线截图或手绘图查找相似股票和期货形态，支持无 MCP 直连脚本。
  summary_en: Find similar A-share stock and futures K-line patterns from text, screenshots, or hand drawings, with a direct helper script for non-MCP agents.
---

# Xingtai Pattern Catcher

Use this skill to search similar A-share stock and futures K-line patterns from text, K-line screenshots, or hand-drawn trend images.

## Primary Rule

Prefer direct mode unless the platform already exposes MCP tools.

- Direct mode: run `scripts/xingtai_search.py`. The hosted service address is already hardcoded in the script, so the user does not need to create an MCP server, fill a token, or deploy anything.
- MCP mode: use `xingtai-catcher` MCP tools only when the host platform has already connected the MCP service.
- Never invent symbols, scores, chart URLs, result pages, share pages, or sessions.
- Treat outputs as pattern-similarity research and screening references, not investment advice.
- If the user wants daily tracking, tell them to open the returned PatternCatcher URL, log in or register, save the pattern or subscribe to the template, then configure Feishu or WeCom push settings on the website.

## Default Parameters

When the user does not specify details, use:

- `universe="all"`
- `timeframe="1d"`
- `window_bars=120`
- `top_n=5`

Supported dimensions:

- Universe: `all`, `stock`, `futures`
- Timeframe: `1d`, `60m`
- Window length: `30`, `60`, `120` BAR
- Results: default `Top5`, maximum `Top10`

Interpret common Chinese wording:

- `W底`, `双底`, `底部反转` -> reversal or bottoming intent.
- `M头`, `双顶`, `顶部风险` -> topping or risk intent.
- `趋势`, `强趋势`, `趋势延续` -> trend-continuation intent.
- `震荡`, `箱体`, `平台整理` -> range or consolidation intent.
- `股票`, `A股` -> prefer `universe="stock"`.
- `期货`, `商品期货` -> prefer `universe="futures"`.
- `60分钟`, `小时线`, `分钟`, `短线` -> prefer `timeframe="60m"`.
- `日线`, `中线`, `波段`, `最近半年` -> prefer `timeframe="1d"` and `window_bars=120`.

## Direct Mode

Use direct mode when MCP tools are not available:

```bash
python scripts/xingtai_search.py text "找 W底右侧抬升的 A 股" --universe stock --timeframe 1d --window-bars 120 --top-n 5
```

For images:

```bash
python scripts/xingtai_search.py image --image-path ./chart.png --kind upload_screenshot --universe all --timeframe 1d --window-bars 120 --top-n 5
```

Read `references/mcp-usage.md` for direct script commands, optional MCP configuration, and response formatting details.

## MCP Mode

If the platform already exposes the `xingtai-catcher` MCP tools:

- Call `list_supported_patterns` when the user asks what markets, periods, BAR lengths, defaults, or limits are supported.
- Call `find_similar_by_text` for text-only pattern requests.
- Call `find_similar_by_image` when the user provides a K-line screenshot or hand-drawn trend image.
- Call `get_match_result` when the user asks to reopen or summarize an existing `session_id`.
- Call `create_share_link` only when the result does not already include a share URL or the user asks for a shareable link.

## Response Contract

Reply in the user's language. For Chinese users, use this shape:

```text
我按「全市场 / 日线 / 120 BAR / Top5」为你查找了相似形态。

候选结果
1. 标的名称 代码，评分 xx.x，股票/期货，数据日 yyyy-mm-dd
2. ...

结果页：...
分享页：...

如果要每天自动跟踪这个形态，请打开结果页登录形态捕手，保存形态或订阅模板，并设置飞书/企微推送。
结果仅用于形态相似度研究，不构成投资建议。
```
