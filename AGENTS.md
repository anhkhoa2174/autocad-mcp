# AGENTS.md — guide for AI agents using this repo

This repository is an **MCP server that lets an AI drive AutoCAD** (draw, edit,
read geometry, screenshot) and read floor plans back into numbers. Read this
before using the tools.

## What you get

- `src/autocad_mcp/` — the MCP server. Exposes **8 tools** over stdio:
  `drawing`, `entity`, `layer`, `block`, `annotation`, `pid`, `view`, `system`.
  Each tool takes an `operation` string plus a `data` object.
- `lisp-code/mcp_dispatch.lsp` — the AutoLISP bridge that must be **loaded inside
  AutoCAD** so the File-IPC backend can talk to it.
- `examples/` — `measure_area.py` (area from a drawing) and `screenshot.py`.

Two backends, same tools: **File IPC** (Windows + AutoCAD LT 2024+, live drawing)
and **ezdxf** (headless, any OS, no AutoCAD). See `README.md` for setup.

## Connecting

1. `uv sync` to install deps.
2. Start AutoCAD, then in its command line load the bridge:
   `(load "C:/autocad-mcp/lisp-code/mcp_dispatch.lsp")`
   (re-load it if calls start timing out — the dispatcher can get unloaded.)
3. Point your MCP client at `python -m autocad_mcp`
   (env `AUTOCAD_MCP_BACKEND=file_ipc`).

## Key tool operations

- `system.execute_lisp {code}` — run arbitrary AutoLISP. The escape hatch for
  anything the typed tools don't cover (surveying, `ssget`, `entmake`, `DXFOUT`).
- `entity.{create_*, move, copy, erase, list, ...}` — geometry CRUD.
- `view.get_screenshot` — PNG of the current view (see gotcha below).
- `drawing.{open, save, save_as_dxf, plot_pdf, undo, ...}`.

## Workflow: read a drawing → get an area ("reverse" direction)

Real drawings are often nested blocks / bound xrefs with no clean slab polyline,
so surveying live over the bridge is slow and incomplete. **Export to DXF and
parse with code instead:**

1. `system.execute_lisp` →
   `(setvar "FILEDIA" 0)(command "_.DXFOUT" "C:/path/plan.dxf" "_V" "2013" "16")`
   (`drawing.save_as_dxf` also works when it doesn't error.)
2. Run `examples/measure_area.py plan.dxf` — it walks INTO nested blocks via
   `ezdxf` `virtual_entities()`, then computes area by flood-fill (clean plans)
   or building-rectangle-minus-core-rectangles (messy plans; read the rectangles
   off the plan / a reference image).
3. **Agree the datum first**: outer wall face (gross) vs inside face (thông
   thủy) vs office-minus-core (net lettable) → different numbers, all valid.

## Gotchas

- **Screenshots are black when AutoCAD is in the background** (GPU viewport not
  repainted). Bring it to the foreground before `view.get_screenshot`.
- Some MCP CLIs drop the returned ImageContent — use `examples/screenshot.py`.
- If `execute_lisp` times out, re-load `mcp_dispatch.lsp` in AutoCAD.
- `OSNAP` can snap `entity.create_rectangle` coordinates — set `OSMODE 0` or
  `entmake` directly for exact geometry.
- Assume drawing units are millimetres (areas ÷ 1e6 → m²) unless told otherwise.
