#!/usr/bin/env python3
"""Direct PatternCatcher search helper.

This script lets an AI agent call the hosted PatternCatcher MCP endpoint
without asking the user to configure MCP manually.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


MCP_URL = "https://kkk.quant789.com/mcp"
PROTOCOL_VERSION = "2024-11-05"
MAX_IMAGE_BYTES = 2 * 1024 * 1024
DEFAULT_JSON_OUTPUT = ".xingtai_result.json"
DEFAULT_TEXT_OUTPUT = ".xingtai_result.txt"

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


class PatternCatcherError(RuntimeError):
    pass


def _post_json(url: str, payload: dict[str, Any], session_id: str = "") -> tuple[dict[str, Any] | None, dict[str, str]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "User-Agent": "skill-xingtai-catcher/1.1",
    }
    if session_id:
        headers["mcp-session-id"] = session_id
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            text = response.read().decode("utf-8", errors="replace")
            response_headers = {k.lower(): v for k, v in response.headers.items()}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PatternCatcherError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise PatternCatcherError(f"Network error: {exc}") from exc
    return _parse_response(text), response_headers


def _parse_response(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    if stripped.startswith("{"):
        return json.loads(stripped)
    data_lines: list[str] = []
    for line in stripped.splitlines():
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if not data_lines:
        raise PatternCatcherError(f"Unexpected response: {stripped[:500]}")
    return json.loads("\n".join(data_lines))


def _extract_result(message: dict[str, Any] | None) -> Any:
    if message is None:
        return None
    if "error" in message:
        error = message["error"]
        raise PatternCatcherError(error.get("message") or json.dumps(error, ensure_ascii=False))
    result = message.get("result")
    if isinstance(result, dict):
        is_error = bool(result.get("isError"))
        structured = result.get("structuredContent")
        if isinstance(structured, dict) and "result" in structured:
            if is_error:
                raise PatternCatcherError(json.dumps(structured["result"], ensure_ascii=False))
            return structured["result"]
        content = result.get("content")
        if isinstance(content, list) and content:
            text = content[0].get("text") if isinstance(content[0], dict) else ""
            if text:
                if is_error:
                    raise PatternCatcherError(text)
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
    return result


class DirectMcpClient:
    def __init__(self, url: str = MCP_URL):
        self.url = url
        self.session_id = ""
        self._next_id = 1

    def connect(self) -> None:
        message, headers = _post_json(
            self.url,
            {
                "jsonrpc": "2.0",
                "id": self._id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "skill-xingtai-catcher", "version": "1.1"},
                },
            },
        )
        _extract_result(message)
        self.session_id = headers.get("mcp-session-id", "")
        if not self.session_id:
            raise PatternCatcherError("MCP session id was not returned.")
        _post_json(
            self.url,
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            self.session_id,
        )

    def _id(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if not self.session_id:
            self.connect()
        message, _ = _post_json(
            self.url,
            {
                "jsonrpc": "2.0",
                "id": self._id(),
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
            self.session_id,
        )
        return _extract_result(message)


def _image_to_base64(path: str) -> str:
    image_path = Path(path).expanduser().resolve()
    if not image_path.is_file():
        raise PatternCatcherError(f"Image file not found: {image_path}")
    content_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
    if not content_type.startswith("image/"):
        raise PatternCatcherError(f"Unsupported image type: {content_type}")
    data = image_path.read_bytes()
    if len(data) > MAX_IMAGE_BYTES:
        raise PatternCatcherError("Image is too large. Please keep it under 2MB.")
    return base64.b64encode(data).decode("ascii")


def _write_output(data: Any, path: str) -> None:
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text_output(text: str, path: str) -> None:
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def _market_label(value: Any) -> str:
    mapping = {"all": "全市场", "stock": "股票", "futures": "期货"}
    return mapping.get(str(value or "all"), str(value or "全市场"))


def _timeframe_label(value: Any) -> str:
    mapping = {"1d": "日线", "60m": "60分钟"}
    return mapping.get(str(value or "1d"), str(value or "日线"))


def _kind_label(value: Any, result_type: str = "") -> str:
    text = str(value or "").lower()
    if result_type == "radar_template":
        return "雷达模板"
    if "upload" in text or "screenshot" in text:
        return "K线截图"
    if "drawing" in text:
        return "手绘图"
    if text:
        return text
    return "文本描述"


def _mode_label(value: Any) -> str:
    mapping = {"high_precision": "高精", "coarse": "粗选"}
    return mapping.get(str(value or ""), "")


def _score_text(value: Any) -> str:
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "-"


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _format_patterns(data: dict[str, Any]) -> str:
    items = data.get("items") or []
    lines = [
        "形态捕手支持这些搜索维度：",
        "- 市场：全市场、股票、期货",
        "- 周期：日线、60分钟",
        "- 数据长度：30 / 60 / 120 BAR",
        "- 返回数量：默认 Top5，最大 Top10",
        "",
        "可识别的形态：",
    ]
    for item in items:
        aliases = "、".join(str(v) for v in (item.get("aliases") or [])[:5])
        suffix = f"（常见说法：{aliases}）" if aliases else ""
        lines.append(f"- {item.get('name') or item.get('template_id')}{suffix}")
    guidance = data.get("guidance")
    if guidance:
        lines.extend(["", f"提示：{guidance}"])
    return "\n".join(lines)


def _format_match(data: dict[str, Any]) -> str:
    params = data.get("resolved_params") or data.get("query_summary") or {}
    items = data.get("items") or []
    first_item = items[0] if items else {}
    universe = _market_label(_first_present(params.get("universe"), first_item.get("symbol_type"), first_item.get("market")))
    timeframe = _timeframe_label(_first_present(params.get("timeframe"), first_item.get("timeframe")))
    window_bars = _first_present(params.get("window_bars"), first_item.get("window_bars"), first_item.get("bar_count"), 120)
    top_n = params.get("top_n") or len(items) or 5
    result_type = str(data.get("result_type") or "")
    kind = _first_present(data.get("kind"), params.get("kind"), params.get("source_kind"))
    mode = _first_present(data.get("mode"), params.get("mode"), params.get("match_mode"))
    route_parts = [_kind_label(kind, result_type), universe, timeframe, f"{window_bars} BAR", f"Top{top_n}"]
    mode_text = _mode_label(mode)
    if mode_text:
        route_parts.insert(1, mode_text)
    route_line = f"本次使用：{' / '.join(str(part) for part in route_parts if part)}"
    if result_type == "needs_clarification":
        supported = data.get("supported_patterns") or []
        names = [str(item.get("name") or item.get("template_id")) for item in supported[:6]]
        lines = [
            "这句话没有命中固定雷达模板。",
            "",
            f"当前参数：{universe} / {timeframe} / {window_bars} BAR / Top{top_n}",
            "",
            "你可以换成更明确的模板词，例如：强趋势延续、底部反转、W底、趋势回踩、震荡整理、M头。",
        ]
        if names:
            lines.append(f"可用模板：{'、'.join(names)}")
        lines.extend(
            [
                "",
                "如果你想找的是自定义形态，请上传 K 线截图或手绘走势图。",
            ]
        )
        return "\n".join(lines)
    template_name = data.get("template_name") or data.get("radar_template_id") or ""
    lead = (
        f"我按服务器雷达模板「{template_name}」和「{universe} / {timeframe} / {window_bars} BAR / Top{top_n}」为你筛选了候选标的。"
        if result_type == "radar_template"
        else f"我按「{universe} / {timeframe} / {window_bars} BAR / Top{top_n}」为你查找了相似形态。"
    )

    lines = [
        lead,
        route_line,
        "",
        "候选结果：",
    ]
    if not items:
        lines.append("暂时没有找到候选结果，可以换一个市场、周期或 BAR 长度再试。")
    for idx, item in enumerate(items, 1):
        name = item.get("symbol_name") or item.get("name") or ""
        code = item.get("symbol_code") or item.get("code") or ""
        market = _market_label(item.get("symbol_type") or item.get("market"))
        date = item.get("scan_date") or item.get("latest_bar_time") or "-"
        score = _first_present(item.get("score"), item.get("overall_score"), item.get("final_score"), item.get("similarity_score"))
        lines.append(f"{idx}. {name} {code}，评分 {_score_text(score)}，{market}，数据日 {date}")

    result_url = data.get("result_url") or ""
    share_url = data.get("share_url") or (data.get("share") or {}).get("share_url") or ""
    subscribe_url = data.get("subscribe_url") or (f"{result_url}?intent=subscribe" if result_url else "")
    if result_url:
        lines.extend(["", f"结果页：{result_url}"])
    if share_url:
        lines.append(f"分享页：{share_url}")
    if subscribe_url:
        lines.append(f"订阅入口：{subscribe_url}")
    lines.extend(
        [
            "",
            "想每天自动跟踪这个形态，请打开结果页登录形态捕手，保存形态或订阅模板，并设置飞书/企微推送。",
            "结果仅用于形态相似度研究，不构成投资建议。",
        ]
    )
    return "\n".join(lines)


def _format_result(data: Any, *, as_json: bool, command: str) -> str:
    if as_json:
        return json.dumps(data, ensure_ascii=False, indent=2)
    if isinstance(data, dict) and command == "patterns":
        return _format_patterns(data)
    if isinstance(data, dict):
        return _format_match(data)
    return str(data)


def _print_result(data: Any, *, as_json: bool, command: str) -> None:
    print(_format_result(data, as_json=as_json, command=command))


def _emit_result(data: Any, args: argparse.Namespace) -> None:
    formatted_text = _format_result(data, as_json=False, command=args.command)
    requested_stdout = bool(args.print_stdout or args.json or (not args.quiet and sys.stdout.isatty()))
    should_print = requested_stdout and not args.quiet
    json_output = args.output or (None if should_print else DEFAULT_JSON_OUTPUT)
    text_output = args.text_output or (None if should_print else DEFAULT_TEXT_OUTPUT)

    if json_output:
        _write_output(data, json_output)
    if text_output:
        _write_text_output(formatted_text, text_output)
    if not should_print:
        return
    _print_result(data, as_json=args.json, command=args.command)


def _add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Print raw JSON for debugging or custom integrations.")
    parser.add_argument("--print", dest="print_stdout", action="store_true", help="Force a user-readable summary to stdout.")
    parser.add_argument("--output", help="Write raw JSON result to this file.")
    parser.add_argument("--text-output", help="Write user-readable text summary to this file.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout. By default, captured/non-TTY runs write .xingtai_result.txt and .xingtai_result.json instead.",
    )


def _candle_detection_failed(exc: PatternCatcherError) -> bool:
    text = str(exc).lower()
    needles = [
        "not enough candle groups detected",
        "not enough candle",
        "candle groups",
        "无法识别足够",
        "k线结构",
    ]
    return any(needle in text for needle in needles)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search similar K-line patterns with PatternCatcher.")
    sub = parser.add_subparsers(dest="command", required=True)

    patterns = sub.add_parser("patterns", help="List supported pattern inputs and defaults.")
    _add_output_options(patterns)

    text = sub.add_parser("text", help="Search by natural-language pattern description.")
    text.add_argument("query", help="Pattern description, for example: W底右侧抬升")
    text.add_argument("--universe", choices=["all", "stock", "futures"], default="all")
    text.add_argument("--timeframe", choices=["1d", "60m"], default="1d")
    text.add_argument("--window-bars", type=int, choices=[30, 60, 120], default=120)
    text.add_argument("--top-n", type=int, default=5)
    _add_output_options(text)

    image = sub.add_parser("image", help="Search by hand drawing or K-line screenshot.")
    image.add_argument("--image-path", required=True, help="Local image path.")
    image.add_argument(
        "--kind",
        choices=["drawing", "upload_screenshot"],
        default="drawing",
        help="Use drawing for sketches/single trend lines; use upload_screenshot only for real candlestick screenshots.",
    )
    image.add_argument("--universe", choices=["all", "stock", "futures"], default="all")
    image.add_argument("--timeframe", choices=["1d", "60m"], default="1d")
    image.add_argument("--window-bars", type=int, choices=[30, 60, 120], default=120)
    image.add_argument(
        "--mode",
        choices=["high_precision", "coarse"],
        default="high_precision",
        help="Drawing match mode. Use high_precision by default to match the website hand-drawing behavior.",
    )
    image.add_argument("--top-n", type=int, default=5)
    image.add_argument(
        "--retry-as-drawing",
        action="store_true",
        help="Retry a failed upload_screenshot request as drawing. Use only when the image is actually a sketch or single-line chart.",
    )
    image.add_argument(
        "--no-retry-as-drawing",
        action="store_false",
        dest="retry_as_drawing",
        help=argparse.SUPPRESS,
    )
    _add_output_options(image)

    result = sub.add_parser("result", help="Open an existing match session.")
    result.add_argument("session_id")
    result.add_argument("--top-n", type=int, default=5)
    _add_output_options(result)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = DirectMcpClient()
    try:
        if args.command == "patterns":
            _emit_result(client.call_tool("list_supported_patterns", {}), args)
        elif args.command == "text":
            result = client.call_tool(
                "find_similar_by_text",
                {
                    "query": args.query,
                    "universe": args.universe,
                    "timeframe": args.timeframe,
                    "window_bars": args.window_bars,
                    "top_n": max(1, min(args.top_n, 10)),
                },
            )
            _emit_result(result, args)
        elif args.command == "image":
            image_base64 = _image_to_base64(args.image_path)
            payload = {
                "image_base64": image_base64,
                "kind": args.kind,
                "mode": args.mode,
                "universe": args.universe,
                "timeframe": args.timeframe,
                "window_bars": args.window_bars,
                "top_n": max(1, min(args.top_n, 10)),
            }
            try:
                result = client.call_tool("find_similar_by_image", payload)
            except PatternCatcherError as exc:
                if args.kind == "upload_screenshot" and args.retry_as_drawing and _candle_detection_failed(exc):
                    payload["kind"] = "drawing"
                    result = client.call_tool("find_similar_by_image", payload)
                else:
                    raise
            _emit_result(result, args)
        elif args.command == "result":
            result = client.call_tool("get_match_result", {"session_id": args.session_id, "top_n": max(1, min(args.top_n, 10))})
            _emit_result(result, args)
        return 0
    except PatternCatcherError as exc:
        print(f"PatternCatcher error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
