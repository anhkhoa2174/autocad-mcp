# Examples

Helper scripts that sit on top of the AutoCAD MCP server.

| Script | What it does |
|--------|--------------|
| [`measure_area.py`](measure_area.py) | Read a floor plan **from a drawing** and compute floor / office / core area (the "reverse" of drawing generation). |
| [`screenshot.py`](screenshot.py) | Save a PNG of the current AutoCAD view (recovers the ImageContent that some MCP CLIs drop). |

## Measure area from a drawing

The area workflow is DWG → DXF → parse with `ezdxf` → compute.

```bash
# 1. Export the open drawing to DXF (from the MCP `system.execute_lisp` tool):
#      (setvar "FILEDIA" 0)
#      (command "_.DXFOUT" "C:/path/plan.dxf" "_V" "2013" "16")

# 2. Inspect it
python examples/measure_area.py plan.dxf --info

# 3a. Clean, fully-closed plan  -> flood-fill
python examples/measure_area.py plan.dxf --flood \
    --region 764000 -82500 787000 -60500

# 3b. Messy plan (nested blocks / gaps / column grid) -> rectangles
#     Read the building + core/lift rectangles off the drawing (or a
#     reference image) and subtract:
python examples/measure_area.py plan.dxf --rects \
    --building 764953 -81938 785104 -61384 \
    --hole 764953 -81938 772654 -73684 \
    --hole 772654 -81938 777500 -77000
# -> AREA = 327 m2
```

**Pick the measurement datum first** — outer wall face (gross slab), inside
face (thông thủy), or office-minus-core (net lettable) give different numbers;
none is "wrong", they just answer different questions.

Requires `ezdxf` (already a dependency of this project — `uv sync`).

## Screenshot

```bash
python examples/screenshot.py view.png \
    --stdio 'C:/autocad-mcp/.venv/Scripts/python.exe -m autocad_mcp'
```

If the PNG is tiny / black, the AutoCAD window was in the background — click it
to the foreground and retry.
