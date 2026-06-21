---
name: skill-xingtai-catcher
description: Use when a general-purpose AI agent needs to find A-share stocks or futures with similar K-line patterns from natural-language descriptions, K-line screenshots, or hand-drawn trend images. Supports daily and 60-minute timeframes, 30/60/120 BAR windows, hosted MCP tools, and a direct helper script for platforms without MCP. Also covers when to prefer server radar templates such as strong trend continuation and bottom reversal, how to format user-facing results, and how to route users to the PatternCatcher website for saved patterns and daily Feishu/WeCom subscriptions.
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

Use this skill to search for similar A-share stock and futures K-line patterns from text, K-line screenshots, or hand-drawn trend images.

## Core Rules

- Resolve `timeframe` and `window_bars` before searching. If the user did not clearly specify them and they cannot be inferred, ask one short clarification question.
- Default only when the user says "默认", "你看着办", or "都行": `universe=all`, `timeframe=1d`, `window_bars=120`, `top_n=5`.
- Treat hand sketches, single-line trend drawings, canvas drawings, and images without visible candles as `kind=drawing`.
- Use `kind=upload_screenshot` only for real K-line/candlestick screenshots.
- If screenshot recognition fails with "not enough candle groups detected" or similar candle-detection errors, retry once as `kind=drawing` before telling the user it failed.
- Prefer server radar templates for standard screening requests such as "强趋势延续" and "底部反转"; use custom text/image search only when the user describes or provides a custom shape.
- Never invent symbols, scores, chart URLs, result pages, share pages, or sessions.
- Never paste raw execution transcripts, `System (untrusted)` blocks, `Exec completed` logs, or raw JSON to the user. Summarize the parsed result in normal language.
- Results are pattern-similarity research references, not investment advice.
- If the user wants daily tracking, send them to the returned PatternCatcher result/share URL to log in, save the pattern or subscribe to a radar template, and configure Feishu or WeCom push settings.

## Parameter Clarification

Supported dimensions:

- Universe: `all`, `stock`, `futures`
- Timeframe: `1d` for 日线, `60m` for 60分钟
- Window length: `30`, `60`, `120` BAR. Prefer 60 or 120; use 30 only when the user explicitly asks for a short window.
- Results: default Top5, maximum Top10

If timeframe or BAR length is missing, ask:

```text
你想按哪个周期和长度匹配？可以选：日线 120 BAR、日线 60 BAR、60分钟 120 BAR、60分钟 60 BAR。你也可以说“默认”，我就用日线 120 BAR。
```

Interpret common Chinese wording:

- `W底`, `双底`, `底部反转` -> bottoming or reversal intent
- `M头`, `双顶`, `顶部风险` -> topping or risk intent
- `趋势`, `强趋势`, `趋势延续` -> trend-continuation intent
- `震荡`, `箱体`, `平台整理` -> range or consolidation intent
- `股票`, `A股` -> prefer `universe=stock`
- `期货`, `商品期货` -> prefer `universe=futures`
- `60分钟`, `小时线`, `分钟`, `短线` -> prefer `timeframe=60m`
- `日线`, `中线`, `波段`, `最近半年` -> prefer `timeframe=1d` and `window_bars=120`
- `60根`, `60 BAR` -> use `window_bars=60`
- `120根`, `120 BAR`, `最近半年` -> use `window_bars=120`

## Shape Context

When explaining generated drawings:

- W-bottom drawings should include preceding weakness: draw a down move first, then first bottom, bounce, second bottom, and right-side lift. Do not draw only the final W.
- M-top drawings should include preceding strength: draw an up move first, then first top, pullback, second top, and breakdown/right-side fade. Do not draw only the final M.
- If the user hand-draws W/M patterns, remind them that adding a short pre-trend improves matching quality.

## Direct Mode

Use direct mode when MCP tools are not available and the host can run local scripts:

```bash
python scripts/xingtai_search.py text "找 W 底右侧抬升的 A 股" --universe stock --timeframe 1d --window-bars 120 --top-n 5
```

For hand drawings or single-line sketches:

```bash
python scripts/xingtai_search.py image --image-path ./drawing.png --kind drawing --universe all --timeframe 1d --window-bars 120 --top-n 5
```

For real K-line screenshots:

```bash
python scripts/xingtai_search.py image --image-path ./chart.png --kind upload_screenshot --universe all --timeframe 1d --window-bars 120 --top-n 5
```

If the host platform exposes command stdout as a visible `System (untrusted)` block, do not use normal stdout mode. Use quiet file-output mode and summarize the parsed file content:

```bash
python scripts/xingtai_search.py text "找底部反转" --timeframe 1d --window-bars 120 --output .xingtai_result.json --quiet
```

Use `--json` only for debugging or custom integrations. Never paste raw JSON into the user-facing answer.

Read `references/mcp-usage.md` for direct script commands, optional MCP configuration, and response formatting details.

## MCP Mode

If the host platform already exposes the `xingtai-catcher` MCP tools:

- Call `list_supported_patterns` when the user asks what markets, periods, BAR lengths, defaults, or limits are supported.
- Call `find_similar_by_text` for text-only pattern requests.
- Call `find_similar_by_image` for K-line screenshots or hand-drawn trend images. Pass `kind=drawing` for sketches and `kind=upload_screenshot` only for candlestick screenshots.
- Call `get_match_result` when the user asks to reopen or summarize an existing `session_id`.
- Call `create_share_link` only when the result does not already include a share URL or the user asks for a shareable link.

## Response Contract

Reply in the user's language. For Chinese users, use this shape:

```text
我按「全市场 / 日线 / 120 BAR / Top5」为你查找了相似形态。

候选结果：
1. 标的名称 代码，评分 xx.x，股票/期货，数据日 yyyy-mm-dd
2. ...

结果页：https://...
分享页：https://...

想每天自动跟踪这个形态，请打开结果页登录形态捕手，保存形态或订阅模板，并设置飞书/企微推送。
结果仅用于形态相似度研究，不构成投资建议。
```
