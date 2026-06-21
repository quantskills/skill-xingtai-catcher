# PatternCatcher MCP Usage

## Remote MCP Config

Use this hosted MCP server:

```json
{
  "mcpServers": {
    "xingtai-catcher": {
      "url": "https://kkk.quant789.com/mcp"
    }
  }
}
```

No user-visible token is required. The backend token stays on the hosted MCP server.

For QCLAW/OpenClaw-style clients:

```bash
openclaw mcp add xingtai-catcher https://kkk.quant789.com/mcp
openclaw mcp probe xingtai-catcher
openclaw mcp tools xingtai-catcher
```

If the client supports explicit transport options, use streamable HTTP:

```bash
openclaw mcp add xingtai-catcher \
  --url https://kkk.quant789.com/mcp \
  --transport streamable-http
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

## Tool Inputs

### `find_similar_by_text`

Required:

- `query`: natural-language pattern description.

Optional:

- `universe`: `all`, `stock`, `futures`.
- `timeframe`: `1d`, `60m`.
- `window_bars`: `30`, `60`, `120`.
- `top_n`: default `5`, maximum `10`.

### `find_similar_by_image`

Provide one image source:

- `image_base64`
- `image_path`
- `image_url`

Optional:

- `kind`: use `drawing` for hand drawings; use `upload_screenshot` for K-line screenshots when the platform distinguishes them.
- `universe`, `timeframe`, `window_bars`, `top_n`.

Original images are capped by the hosted MCP server. Prefer compressed screenshots or image URLs.

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
