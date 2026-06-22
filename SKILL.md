---
name: skill-xingtai-catcher
description: Use when a general-purpose AI agent needs to find A-share stocks or futures with similar K-line patterns from natural-language descriptions, K-line screenshots, or hand-drawn trend images. Supports daily and 60-minute timeframes, 30/60/120 BAR windows, hosted MCP tools, and a direct helper script for platforms without MCP. Standard template words such as strong trend continuation, bottom reversal, W-bottom, trend pullback, range consolidation, and M-top must route to server radar templates before any generated drawing. Image attachments must route through image search directly. Also covers user-facing result formatting and routing users to the PatternCatcher website for saved patterns and daily Feishu/WeCom subscriptions.
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

# 形态捕手 Skill

用这个 Skill 让通用智能体根据文字描述、K 线截图或手绘走势，在 A 股和期货数据里查找相似形态，并返回候选标的、评分、结果页和分享页。

结果仅用于形态相似度研究，不构成投资建议。

## 核心规则

- 搜索前先确定 `timeframe` 和 `window_bars`。如果用户没有说明，也不能从上下文推断，就先问一个简短问题。
- 只有当用户说“默认”“你看着办”“都行”时，才使用默认参数：`universe=all`, `timeframe=1d`, `window_bars=120`, `top_n=5`。
- 只要用户提供了图片附件，必须优先走图片搜索。不要先把图片改写成文字，不要重新生成或重画一张图，也不要在原图可用时改走文字/模板搜索。
- 如果图片类型不清楚，只问一句：“这是手绘走势图，还是 K 线截图？”
- 手绘线条、单线趋势图、画布截图、没有清晰蜡烛 K 线的图片，按 `kind=drawing` 处理。
- `kind=drawing` 默认使用 `mode=high_precision`，除非用户明确要求快速粗选。
- 真实 K 线蜡烛图截图才使用 `kind=upload_screenshot`。
- 真实 K 线截图如果报 `not enough candle groups detected` 或类似蜡烛识别错误，不要静默改成 `drawing`。先让用户裁剪得更清楚，或者等用户确认它其实是手绘/单线图后再按 `drawing` 重试。
- 标准模板词优先走服务器雷达模板。如果用户说“强趋势延续”“底部反转”“W底”“双底”“趋势回踩”“震荡整理”“箱体”“M头”“顶部反转”，直接调用 `find_similar_by_text`，不要自己临时画图。
- 只有用户描述的是自定义形态，且不是固定雷达模板，也没有上传图片时，才走自定义文字/画图匹配。
- 不要编造标的、评分、图表地址、结果页、分享页或 session。
- 不要把 `System (untrusted)`、`Exec completed`、原始 JSON 或工具调用日志贴给用户。读取 `.xingtai_result.txt` 后，用正常语言总结。
- 如果用户想每天跟踪，提示他打开返回的形态捕手结果页，登录后保存形态或订阅模板，并配置飞书/企业微信推送。

## 参数维度

支持这些维度：

- 市场：`all`, `stock`, `futures`
- 周期：`1d` 日线，`60m` 60 分钟
- 匹配长度：`30`, `60`, `120` BAR。默认优先 120 BAR；用户明确要短窗口时才用 30 BAR。
- 返回数量：默认 Top5，最多 Top10

如果周期或 BAR 长度缺失，先问：

```text
你想按哪个周期和长度匹配？可以选：日线 120 BAR、日线 60 BAR、60分钟 120 BAR、60分钟 60 BAR。你也可以说“默认”，我就用日线 120 BAR。
```

常见表达映射：

- `强趋势延续`, `强趋势`, `主升浪`, `趋势延续` -> 雷达模板 `strong_trend`
- `底部反转`, `筑底`, `低位转强`, `底部抬升` -> 雷达模板 `bottom_reversal`
- `W底`, `双底`, `二次探底`, `圆弧底` -> 雷达模板 `w_bottom`
- `趋势回踩`, `均线回踩`, `突破回踩`, `回踩不破` -> 雷达模板 `trend_pullback`
- `震荡`, `箱体`, `横盘整理`, `平台整理` -> 雷达模板 `range_consolidation`
- `M头`, `双顶`, `顶部反转`, `顶部风险` -> 雷达模板 `top_reversal`
- `股票`, `A股` -> 优先 `universe=stock`
- `期货`, `商品期货` -> 优先 `universe=futures`
- `60分钟`, `小时线`, `分钟`, `短线` -> 优先 `timeframe=60m`
- `日线`, `中线`, `波段`, `最近半年` -> 优先 `timeframe=1d`, `window_bars=120`
- `60根`, `60 BAR` -> `window_bars=60`
- `120根`, `120 BAR`, `最近半年` -> `window_bars=120`

## 形态上下文

- W 底手绘图应包含前置下跌，再画第一个底、反弹、第二个底、右侧抬升。不要只画最后一个 W。
- M 头手绘图应包含前置上涨，再画第一个顶、回落、第二个顶、右侧走弱。不要只画最后一个 M。
- 如果用户手绘 W/M 形态，提醒他加一小段前置趋势，匹配质量会更高。
- 如果用户只是说固定模板名，例如“底部反转”“强趋势延续”，直接用雷达模板，不要手动画图。

## 直连脚本模式

当平台没有 MCP 工具，但可以运行本地脚本时，使用 `scripts/xingtai_search.py`。

脚本默认把结果写入 `.xingtai_result.txt` 和 `.xingtai_result.json`，不要直接把 stdout 里的工具日志发给用户。

文字模板或文字描述：

```bash
python scripts/xingtai_search.py text "找 W 底右侧抬升的 A 股" --universe stock --timeframe 1d --window-bars 120 --top-n 5
```

手绘图或单线图：

```bash
python scripts/xingtai_search.py image --image-path ./drawing.png --kind drawing --mode high_precision --universe all --timeframe 1d --window-bars 120 --top-n 5
```

真实 K 线截图：

```bash
python scripts/xingtai_search.py image --image-path ./chart.png --kind upload_screenshot --universe all --timeframe 1d --window-bars 120 --top-n 5
```

如果人工调试需要打印结果，加 `--print`：

```bash
python scripts/xingtai_search.py text "找底部反转" --timeframe 1d --window-bars 120 --print
```

读取 `references/mcp-usage.md` 获取脚本、MCP 配置和回复格式细节。

## MCP 模式

如果平台已经暴露 `xingtai-catcher` MCP 工具：

- 用户问支持哪些市场、周期、BAR 长度、默认值、限制时，调用 `list_supported_patterns`。
- 纯文字形态请求，调用 `find_similar_by_text`。
- 图片请求，调用 `find_similar_by_image`。手绘图传 `kind=drawing, mode=high_precision`；真实 K 线截图才传 `kind=upload_screenshot`。
- 用户要重开或总结已有结果时，调用 `get_match_result`。
- 结果没有分享页，或用户明确要分享链接时，再调用 `create_share_link`。

## 回复格式

中文用户建议这样回复：

```text
我按「手绘图 / 高精 / 全市场 / 日线 / 120 BAR / Top5」为你查找了相似形态。

候选结果：
1. 标的名称 代码，评分 xx.x，股票/期货，数据日 yyyy-mm-dd
2. ...

结果页：https://...
分享页：https://...

想每天自动跟踪这个形态，请打开结果页登录形态捕手，保存形态或订阅模板，并设置飞书/企微推送。

结果仅用于形态相似度研究，不构成投资建议。
```
