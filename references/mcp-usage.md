# PatternCatcher Direct And MCP Usage

## 推荐路径

根据宿主平台能力选择：

- 已连接 MCP 工具时，直接调用 MCP tools。
- 没有 MCP 但能运行脚本时，调用 `scripts/xingtai_search.py`。
- 在 QCLAW、WorkBuddy 这类会捕获命令输出的平台里，脚本默认写入 `.xingtai_result.txt` 和 `.xingtai_result.json`，不要把命令输出里的 `System (untrusted)` 或 `Exec completed` 发给用户。

服务地址已经写在脚本里：

```text
https://kkk.quant789.com/mcp
```

用户不需要自己部署服务，也不需要配置 token。

## 参数确认

搜索前必须确认：

- `timeframe`: `1d` 或 `60m`
- `window_bars`: 通常 `60` 或 `120`，只有用户明确要求短窗口时使用 `30`

如果用户没有说清楚周期或 BAR 长度，先问：

```text
你想按哪个周期和长度匹配？可以选：日线 120 BAR、日线 60 BAR、60分钟 120 BAR、60分钟 60 BAR。你也可以说“默认”，我就用日线 120 BAR。
```

只有用户说“默认”“你看着办”“都行”时，才直接用 `timeframe=1d`, `window_bars=120`。

## 文字搜索

固定模板词直接走服务器雷达模板，不要让智能体临时画图：

- 强趋势延续、强趋势、主升浪
- 底部反转、筑底、低位转强
- W底、双底、圆弧底、二次探底
- 趋势回踩、均线回踩、突破回踩
- 震荡整理、箱体、横盘整理
- M头、双顶、顶部反转

示例：

```bash
python scripts/xingtai_search.py text "找 W 底右侧抬升的 A 股" --universe stock --timeframe 1d --window-bars 120 --top-n 5
```

## 图片搜索

图片附件必须留在图片路由。用户提供了图片时：

- 不要先描述图片再用文字搜索。
- 不要重新画一张合成图再搜索。
- 不要在原图可用时改走雷达模板，除非用户明确说忽略图片、改看某个模板。

如果图片类型不清楚，先问用户这是“手绘走势图”还是“真实 K 线截图”。

手绘图、单线走势图、画布截图使用 `drawing`：

```bash
python scripts/xingtai_search.py image --image-path ./drawing.png --kind drawing --mode high_precision --universe all --timeframe 1d --window-bars 120 --top-n 5
```

手绘图默认保留 `mode=high_precision`，这样更接近网站手绘页的匹配效果。

真实 K 线蜡烛图截图使用 `upload_screenshot`：

```bash
python scripts/xingtai_search.py image --image-path ./chart.png --kind upload_screenshot --universe all --timeframe 1d --window-bars 120 --top-n 5
```

如果真实 K 线截图报 `not enough candle groups detected`，先让用户裁剪图表区域、去掉多余 UI、提高分辨率后再试。只有用户确认这张图其实是手绘/单线图，或调用方显式传 `--retry-as-drawing`，才可以改成 `drawing` 重试。

## 输出模式

默认 AI 平台用法：

```bash
python scripts/xingtai_search.py text "找底部反转" --timeframe 1d --window-bars 120
```

然后读取：

- `.xingtai_result.txt`: 面向用户的摘要
- `.xingtai_result.json`: 结构化字段

终端调试时可以强制打印：

```bash
python scripts/xingtai_search.py text "找底部反转" --timeframe 1d --window-bars 120 --print
```

不要把原始 JSON 贴给用户，除非用户明确要机器可读结果。

## 已有 Session

```bash
python scripts/xingtai_search.py result session_xxx --top-n 5
```

## 参数映射

| 用户说法 | 参数 |
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
| 强趋势延续、强趋势、主升浪 | 雷达模板 `strong_trend` |
| 底部反转、筑底、低位转强 | 雷达模板 `bottom_reversal` |
| W底、双底、二次探底、圆弧底 | 雷达模板 `w_bottom` |
| 趋势回踩、均线回踩、突破回踩 | 雷达模板 `trend_pullback` |
| 震荡、箱体、横盘整理、平台整理 | 雷达模板 `range_consolidation` |
| M头、双顶、顶部反转 | 雷达模板 `top_reversal` |

不支持的值要归一化到最近的可用选项，并在回复里说清楚实际使用参数。

## 形态上下文

- W 底搜索最好包含前置下跌、两次探底和右侧抬升。
- M 头搜索最好包含前置上涨、两次冲顶和右侧走弱。
- 标准模板请求优先用服务器雷达模板；只有自定义形态才建议用户上传截图或手绘。

## 可选 MCP 配置

只有宿主平台支持 MCP 配置时才需要：

```json
{
  "mcpServers": {
    "xingtai-catcher": {
      "url": "https://kkk.quant789.com/mcp"
    }
  }
}
```

## 回复模板

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
