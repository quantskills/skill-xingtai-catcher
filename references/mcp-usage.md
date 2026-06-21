# PatternCatcher Direct And MCP Usage

## Recommended Path: Direct Script

Use this path when the host platform cannot create MCP connections.

The service address is already hardcoded in `scripts/xingtai_search.py`:

```text
https://kkk.quant789.com/mcp
```

The user does not need to configure MCP, fill a token, or deploy a server.

### Text Search

```bash
python scripts/xingtai_search.py text "找 W底右侧抬升的 A 股" --universe stock --timeframe 1d --window-bars 120 --top-n 5
```

### Image Search

```bash
python scripts/xingtai_search.py image --image-path ./chart.png --kind upload_screenshot --universe all --timeframe 1d --window-bars 120 --top-n 5
```

Use `--kind drawing` for hand drawings.

### Existing Session

```bash
python scripts/xingtai_search.py result session_xxx --top-n 5
```

## Parameter Mapping

| User wording | Tool parameter |
|---|---|
| 全部、都行、全市场 | `universe="all"` |
| 股票、A股 | `universe="stock"` |
| 期货、商品期货 | `universe="futures"` |
| 日线、波段、中线、最近半年 | `timeframe="1d"` |
| 60分钟、小时线、分钟、短线 | `timeframe="60m"` |
| 30根、短窗口 | `window_bars=30` |
| 60根、中等窗口 | `window_bars=60` |
| 120根、默认、最近半年 | `window_bars=120` |
| Top5、默认 | `top_n=5` |
| Top10、多一点 | `top_n=10` |

Clamp unsupported values to the nearest allowed option and mention the resolved parameters in the reply.

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

For QCLAW/OpenClaw-style clients that expose MCP commands:

```bash
openclaw mcp add xingtai-catcher https://kkk.quant789.com/mcp
openclaw mcp probe xingtai-catcher
openclaw mcp tools xingtai-catcher
```

## Reply Template

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
