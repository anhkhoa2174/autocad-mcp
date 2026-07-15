#!/usr/bin/env python3
"""Measure floor / office area from an AutoCAD drawing.

Workflow ("read a drawing -> get the area", the reverse of drawing generation):

  1. Export the DWG to DXF (once), e.g. from the MCP `system.execute_lisp` tool:
       (setvar "FILEDIA" 0)
       (command "_.DXFOUT" "C:/path/plan.dxf" "_V" "2013" "16")
     or with any DWG->DXF converter (ODA File Converter, `dwg2dxf`, ...).

  2. Run this script on the DXF. It parses the file with ezdxf, walks INTO
     nested blocks / bound xrefs (via `virtual_entities()`), collects wall
     segments, and computes area two ways:

       * flood   -> raster flood-fill (good for clean, fully-closed plans)
       * rects   -> building-rectangle minus core/lift rectangles
                    (robust for messy plans that flood-fill can't close;
                     you read the rectangles off the drawing / reference image)

Examples
--------
  # inspect what's in the file (layers, extents, wall bbox)
  python measure_area.py plan.dxf --info

  # flood-fill the largest enclosed room in a region
  python measure_area.py plan.dxf --flood --region 764000 -82500 787000 -60500

  # area = building rect minus two core rectangles (values in drawing units, mm)
  python measure_area.py plan.dxf --rects \
      --building 764953 -81938 785104 -61384 \
      --hole 764953 -81938 772654 -73684 \
      --hole 772654 -81938 777500 -77000

Notes
-----
* Drawing units are assumed to be millimetres (area printed in m2). Change CELL /
  the /1e6 divisor if your file is in metres.
* Always agree on the *measurement datum* first: outer wall face (gross slab) vs
  inside face (thong thuy) vs office-minus-core (net lettable) give different
  numbers and none of them is "wrong".
"""
from __future__ import annotations

import argparse
import sys
from collections import deque

try:
    import ezdxf
except ImportError:
    sys.exit("ezdxf is required:  pip install ezdxf   (or `uv sync`)")

# Layer-name substrings treated as a wall / boundary. Case-insensitive.
WALL_KEYWORDS = ("WALL", "WAL", "TUONG", "GLASS", "KINH", "VACH", "BRICK", "PARTITION")


def collect_wall_segments(dxf_path, region=None, keywords=WALL_KEYWORDS):
    """Return [(x1,y1,x2,y2), ...] for every wall segment, recursing into blocks."""
    doc = ezdxf.readfile(dxf_path)
    kw = tuple(k.upper() for k in keywords)
    segs, allpts = [], []

    def in_region(x, y):
        return region is None or (region[0] < x < region[2] and region[1] < y < region[3])

    def is_wall(layer):
        return any(k in layer for k in kw)

    def walk(entities):
        for e in entities:
            et = e.dxftype()
            layer = e.dxf.layer.upper()
            if et == "INSERT":
                try:
                    walk(e.virtual_entities())
                except Exception:
                    pass
            elif et == "LINE":
                a, b = e.dxf.start, e.dxf.end
                allpts.append((a.x, a.y)); allpts.append((b.x, b.y))
                if is_wall(layer) and (in_region(a.x, a.y) or in_region(b.x, b.y)):
                    segs.append((a.x, a.y, b.x, b.y))
            elif et in ("LWPOLYLINE", "POLYLINE"):
                try:
                    pts = [(p[0], p[1]) for p in e.get_points()]
                except Exception:
                    pts = []
                allpts.extend(pts)
                if is_wall(layer):
                    for i in range(len(pts) - 1):
                        if in_region(*pts[i]) or in_region(*pts[i + 1]):
                            segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]))

    walk(doc.modelspace())
    return doc, segs, allpts


def info(dxf_path):
    doc, segs, allpts = collect_wall_segments(dxf_path)
    wall_layers = [l.dxf.name for l in doc.layers
                   if any(k in l.dxf.name.upper() for k in WALL_KEYWORDS)]
    print(f"DXF {doc.dxfversion}  |  wall segments: {len(segs)}")
    print("wall/glass layers:", wall_layers[:30])
    if allpts:
        xs = [p[0] for p in allpts]; ys = [p[1] for p in allpts]
        print(f"drawing extent: X {min(xs):.0f}..{max(xs):.0f}  Y {min(ys):.0f}..{max(ys):.0f}")
    if segs:
        xs = [s[0] for s in segs] + [s[2] for s in segs]
        ys = [s[1] for s in segs] + [s[3] for s in segs]
        print(f"wall bbox: {(max(xs)-min(xs))/1000:.2f} m x {(max(ys)-min(ys))/1000:.2f} m")


def flood(dxf_path, region, cell=100, dilate=4):
    """Flood-fill: return enclosed regions (m2). Good for clean, closed plans."""
    _, segs, _ = collect_wall_segments(dxf_path, region)
    if not segs:
        print("no wall segments in region"); return
    xs = [s[0] for s in segs] + [s[2] for s in segs]
    ys = [s[1] for s in segs] + [s[3] for s in segs]
    minx, maxx = min(xs) - 500, max(xs) + 500
    miny, maxy = min(ys) - 500, max(ys) + 500
    W = int((maxx - minx) / cell) + 1
    H = int((maxy - miny) / cell) + 1
    grid = bytearray(W * H)

    def mark(cx, cy):
        for dx in range(-dilate, dilate + 1):
            for dy in range(-dilate, dilate + 1):
                x, y = cx + dx, cy + dy
                if 0 <= x < W and 0 <= y < H:
                    grid[y * W + x] = 1

    for x1, y1, x2, y2 in segs:
        c1 = (int((x1 - minx) / cell), int((y1 - miny) / cell))
        c2 = (int((x2 - minx) / cell), int((y2 - miny) / cell))
        n = max(abs(c2[0] - c1[0]), abs(c2[1] - c1[1]), 1)
        for k in range(n + 1):
            mark(int(c1[0] + (c2[0] - c1[0]) * k / n),
                 int(c1[1] + (c2[1] - c1[1]) * k / n))

    seen = bytearray(W * H); dq = deque([(0, 0)]); seen[0] = 1  # flood the outside
    while dq:
        x, y = dq.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not seen[ny * W + nx] and grid[ny * W + nx] == 0:
                seen[ny * W + nx] = 1; dq.append((nx, ny))

    comp = bytearray(W * H); results = []
    for y in range(H):
        for x in range(W):
            if grid[y * W + x] == 0 and not seen[y * W + x] and comp[y * W + x] == 0:
                cells = []; dq = deque([(x, y)]); comp[y * W + x] = 1
                while dq:
                    a, b = dq.popleft(); cells.append((a, b))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = a + dx, b + dy
                        if 0 <= nx < W and 0 <= ny < H and grid[ny * W + nx] == 0 \
                                and not seen[ny * W + nx] and comp[ny * W + nx] == 0:
                            comp[ny * W + nx] = 1; dq.append((nx, ny))
                # dilate the region back by `dilate` to undo wall over-thickening
                grown = set()
                for a, b in cells:
                    for dx in range(-dilate, dilate + 1):
                        for dy in range(-dilate, dilate + 1):
                            grown.add((a + dx, b + dy))
                results.append(len(grown) * (cell / 1000) ** 2)
    results = sorted((r for r in results if r > 3), reverse=True)
    print("enclosed regions (m2):", [round(r) for r in results[:8]])
    if results:
        print(f">>> largest region = {results[0]:.0f} m2")


def rects(building, holes):
    """Area = building rectangle minus hole rectangles (all in drawing units)."""
    def area(r):
        return abs((r[2] - r[0]) * (r[3] - r[1]))
    total = area(building)
    print(f"building: {(building[2]-building[0])/1000:.2f} x "
          f"{(building[3]-building[1])/1000:.2f} m = {total/1e6:.0f} m2")
    for h in holes:
        print(f"  - hole: {(h[2]-h[0])/1000:.2f} x {(h[3]-h[1])/1000:.2f} m = {area(h)/1e6:.0f} m2")
        total -= area(h)
    print(f">>> AREA = {total/1e6:.0f} m2")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf", help="path to a .dxf file")
    ap.add_argument("--info", action="store_true", help="list layers / extents")
    ap.add_argument("--flood", action="store_true", help="flood-fill area")
    ap.add_argument("--rects", action="store_true", help="building minus holes")
    ap.add_argument("--region", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--cell", type=float, default=100, help="raster cell size (drawing units)")
    ap.add_argument("--dilate", type=int, default=4, help="gap-seal radius in cells")
    ap.add_argument("--building", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--hole", nargs=4, type=float, action="append", default=[],
                    metavar=("X0", "Y0", "X1", "Y1"))
    args = ap.parse_args()

    if args.info or not (args.flood or args.rects):
        info(args.dxf)
    if args.flood:
        if not args.region:
            ap.error("--flood needs --region X0 Y0 X1 Y1")
        flood(args.dxf, tuple(args.region), cell=args.cell, dilate=args.dilate)
    if args.rects:
        if not args.building:
            ap.error("--rects needs --building X0 Y0 X1 Y1")
        rects(tuple(args.building), [tuple(h) for h in args.hole])


if __name__ == "__main__":
    main()
