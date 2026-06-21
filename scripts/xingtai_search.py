#!/usr/bin/env python3
"""Direct PatternCatcher search helper.

This script lets an AI agent call the hosted PatternCatcher service without
configuring an MCP server in the host platform. It speaks the public MCP HTTP
endpoint directly, using only Python's standard library.
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


class PatternCatcherError(RuntimeError):
    pass


def _post_json(url: str, payload: dict[str, Any], session_id: str = "") -> tuple[dict[str, Any] | None, dict[str, str]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "User-Agent": "skill-xingtai-catcher/1.0",
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
                    "clientInfo": {"name": "skill-xingtai-catcher", "version": "1.0"},
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


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search similar K-line patterns with PatternCatcher.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("patterns", help="List supported pattern inputs and defaults.")

    text = sub.add_parser("text", help="Search by natural-language pattern description.")
    text.add_argument("query", help="Pattern description, for example: W底右侧抬升")
    text.add_argument("--universe", choices=["all", "stock", "futures"], default="all")
    text.add_argument("--timeframe", choices=["1d", "60m"], default="1d")
    text.add_argument("--window-bars", type=int, choices=[30, 60, 120], default=120)
    text.add_argument("--top-n", type=int, default=5)

    image = sub.add_parser("image", help="Search by hand drawing or K-line screenshot.")
    image.add_argument("--image-path", required=True, help="Local image path.")
    image.add_argument("--kind", choices=["drawing", "upload_screenshot"], default="drawing")
    image.add_argument("--universe", choices=["all", "stock", "futures"], default="all")
    image.add_argument("--timeframe", choices=["1d", "60m"], default="1d")
    image.add_argument("--window-bars", type=int, choices=[30, 60, 120], default=120)
    image.add_argument("--top-n", type=int, default=5)

    result = sub.add_parser("result", help="Open an existing match session.")
    result.add_argument("session_id")
    result.add_argument("--top-n", type=int, default=5)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = DirectMcpClient()
    try:
        if args.command == "patterns":
            _print_json(client.call_tool("list_supported_patterns", {}))
        elif args.command == "text":
            _print_json(
                client.call_tool(
                    "find_similar_by_text",
                    {
                        "query": args.query,
                        "universe": args.universe,
                        "timeframe": args.timeframe,
                        "window_bars": args.window_bars,
                        "top_n": max(1, min(args.top_n, 10)),
                    },
                )
            )
        elif args.command == "image":
            _print_json(
                client.call_tool(
                    "find_similar_by_image",
                    {
                        "image_base64": _image_to_base64(args.image_path),
                        "kind": args.kind,
                        "universe": args.universe,
                        "timeframe": args.timeframe,
                        "window_bars": args.window_bars,
                        "top_n": max(1, min(args.top_n, 10)),
                    },
                )
            )
        elif args.command == "result":
            _print_json(client.call_tool("get_match_result", {"session_id": args.session_id, "top_n": max(1, min(args.top_n, 10))}))
        return 0
    except PatternCatcherError as exc:
        print(f"PatternCatcher error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
