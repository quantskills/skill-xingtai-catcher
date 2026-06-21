# PatternCatcher Direct And MCP Usage

## Recommended Path

Use whichever integration the host platform actually supports:

- If MCP tools are already connected, use the MCP tools directly.
- If MCP is not available but local script execution is available, use `scripts/xingtai_search.py`.
- If the host exposes command stdout as a visible `System (untrusted)` block, use the script's quiet file-output mode or avoid script execution in user-facing chat.

The hosted service address is already hardcoded in `scripts/xingtai_search.py`:

```text
https://kkk.quant789.com/mcp
```

The user does not need to configure a token or deploy a server.

## Clarification Gate

Before calling the direct script or MCP tools, resolve both:

- `timeframe`: `1d` or `60m`
- `window_bars`: normally `60` or `120`; use `30` only when the user explicitly asks for a short window.

If the user does not specify one of these dimensions, ask this first and wait:

```text
你想按哪个周期和长度匹配？可以选：日线 120 BAR、日线 60 BAR、60分钟 120 BAR、60分钟 60 BAR。你也可以说“默认”，我就用日线 120 BAR。
```

Only use `timeframe=1d` and `window_bars=120` without asking when the user says "默认", "你看着办", or "都行".

## Text Search

```bash
python scripts/xingtai_search.py text "找 W 底右侧抬升的 A 股" --universe stock --timeframe 1d --window-bars 120 --top-n 5
```

## Image Search

Use `drawing` for hand drawings, single-line sketches, or canvas screenshots:

```bash
python scripts/xingtai_search.py image --image-path ./drawing.png --kind drawing --universe all --timeframe 1d --window-bars 120 --top-n 5
```

Use `upload_screenshot` only for real K-line/candlestick screenshots:

```bash
python scripts/xingtai_search.py image --image-path ./chart.png --kind upload_screenshot --universe all --timeframe 1d --window-bars 120 --top-n 5
```

If an upload screenshot fails with `not enough candle groups detected`, retry as `drawing`. The bundled script does this automatically unless `--no-retry-as-drawing` is set.

## Quiet Mode

Some AI platforms display every shell command result as an untrusted system block. In that case, suppress stdout and write JSON to a file:

```bash
python scripts/xingtai_search.py text "找底部反转" --timeframe 1d --window-bars 120 --output .xingtai_result.json --quiet
```

Then parse `.xingtai_result.json` and produce a normal answer. Do not paste the file's raw JSON unless the user explicitly asks for machine-readable output.

## Existing Session

```bash
python scripts/xingtai_search.py result session_xxx --top-n 5
```

## Parameter Mapping

| User wording | Tool parameter |
|---|---|
| 全部、都行、全市场 | `universe=all` |
| 股票、A股 | `universe=stock` |
| 期货、商品期货 | `universe=futures` |
| 日线、波段、中线、最近半年 | `timeframe=1d` |
| 60分钟、小时线、分钟、短线 | `timeframe=60m` |
| 30根、短窗口 | `window_bars=30` |
| 60根、中等窗口 | `window_bars=60` |
| 120根、默认、最近半年 | `window_bars=120` |
| Top5、默认 | `top_n=5` |
| Top10、多一点 | `top_n=10` |

Clamp unsupported values to the nearest allowed option and mention the resolved parameters in the reply.

## Shape Context

- W-bottom searches should include a preceding decline before the W, then the right-side lift.
- M-top searches should include a preceding rise before the M, then the right-side fade or breakdown.
- Standard screening requests such as 强趋势延续 and 底部反转 should prefer server radar templates and their subscribe URLs. Ask the user to draw only for custom shapes.

## Optional MCP Config

Use this only if the host platform supports MCP server setup:

```json
{
  "mcpServers": {
    "xingtai-catcher": {
      "url": "https://kkk.quant789.com/mcp"
    }
  }
}
```

## Reply Template

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
