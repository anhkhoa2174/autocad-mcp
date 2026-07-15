#!/usr/bin/env python3
"""Grab a screenshot of the current AutoCAD view through the MCP server.

Why this exists: some MCP CLI callers (e.g. `mcporter call`) only print the
text content of a tool result and silently drop the returned ImageContent.
This tiny stdio JSON-RPC client talks to the server directly and saves the PNG.

The server launch command is read, in order, from:
  1. --stdio "<command line>"
  2. $AUTOCAD_MCP_CMD
  3. ~/.mcporter/mcporter.json  ->  mcpServers["autocad-mcp"]  (command + args)

Usage:
  python screenshot.py out.png
  python screenshot.py out.png --stdio 'C:/autocad-mcp/.venv/Scripts/python.exe -m autocad_mcp'

Tip: the capture is BLACK if the AutoCAD window is in the background
(GPU viewport isn't repainted) — bring AutoCAD to the foreground first.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys


def resolve_command(cli_stdio):
    if cli_stdio:
        return cli_stdio.split(), {}
    if os.environ.get("AUTOCAD_MCP_CMD"):
        return os.environ["AUTOCAD_MCP_CMD"].split(), {}
    cfg = os.path.expanduser("~/.mcporter/mcporter.json")
    if os.path.exists(cfg):
        data = json.load(open(cfg))
        srv = data.get("mcpServers", {}).get("autocad-mcp")
        if srv and srv.get("command"):
            return [srv["command"], *srv.get("args", [])], srv.get("env", {})
    sys.exit("No server command. Pass --stdio '<cmd>' or set $AUTOCAD_MCP_CMD.")


def capture(out_path, cmd, env_extra):
    env = dict(os.environ); env.update(env_extra or {})
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, env=env, bufsize=0)

    def send(obj):
        p.stdin.write((json.dumps(obj) + "\n").encode()); p.stdin.flush()

    def read():
        while True:
            line = p.stdout.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                     "clientInfo": {"name": "screenshot", "version": "1"}}})
    read()
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
          "params": {"name": "view", "arguments": {"operation": "get_screenshot"}}})

    img = None
    for _ in range(10):
        msg = read()
        if not msg:
            break
        if msg.get("id") == 2:
            for c in msg.get("result", {}).get("content", []):
                if c.get("type") == "image":
                    img = c.get("data")
            break
    p.terminate()

    if not img:
        sys.exit("No image returned (is AutoCAD running and connected?)")
    data = base64.b64decode(img)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"saved {out_path}  ({len(data)} bytes)")
    if len(data) < 5000:
        print("  warning: image looks empty/black — bring AutoCAD to the foreground.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="output PNG path")
    ap.add_argument("--stdio", help="server launch command line")
    args = ap.parse_args()
    cmd, env = resolve_command(args.stdio)
    capture(args.out, cmd, env)


if __name__ == "__main__":
    main()
