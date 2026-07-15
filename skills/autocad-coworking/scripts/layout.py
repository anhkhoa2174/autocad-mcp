#!/usr/bin/env python3
"""Helper hinh hoc cho skill autocad-coworking.

Doc input JSON tu stdin, in output JSON ra stdout. Khong noi MCP — bot la
client, day chi la pure-function helper chay tren WSL Python.

Hai mode:

    compute_usable
        Input : {shell, obstacles?, columns?, column_buffer?}
        Output: {ok, usable_polygon, usable_area_m2, bbox}
        Tac dung: tinh vung kha dung = shell - obstacles - column_buffer.

    validate_zones
        Input : {usable_polygon, zones, corridor_min?}
        Output: {ok, results[], warnings[]}
        Voi moi zone {name, rect:[x1,y1,x2,y2]}, kiem tra:
          - rect.within(usable) (cho phep tolerance 1mm)
          - dien tich >= min_area neu co
          - khoang cach giua cac zone >= corridor_min
          - usable - sum(zones) van connected (loi di khong bi cat)

Don vi mm. Su dung shapely 2.x.

Vi du:
    echo '{"mode":"compute_usable","shell":[[0,0],[20000,0],[20000,15000],[0,15000]]}' | python3 layout.py
"""
from __future__ import annotations

import json
import sys
from typing import Any

from shapely.geometry import Polygon, box, MultiPolygon
from shapely.ops import unary_union


TOLERANCE = 1.0  # mm


def _to_polygon(points: list[list[float]]) -> Polygon:
    if len(points) < 3:
        raise ValueError(f"polygon needs >=3 points, got {len(points)}")
    return Polygon(points).buffer(0)  # buffer(0) tu sua self-intersect


def compute_usable(payload: dict[str, Any]) -> dict[str, Any]:
    shell = _to_polygon(payload["shell"])
    obstacles_raw = payload.get("obstacles", [])
    columns = payload.get("columns", [])
    col_buffer = float(payload.get("column_buffer", 300))

    obs_polys = [_to_polygon(o) for o in obstacles_raw]
    if columns:
        col_polys = [box(cx - col_buffer, cy - col_buffer,
                         cx + col_buffer, cy + col_buffer)
                     for cx, cy in columns]
        obs_polys.extend(col_polys)

    if obs_polys:
        usable = shell.difference(unary_union(obs_polys))
    else:
        usable = shell

    if usable.is_empty:
        return {"ok": False, "error": "usable region empty after subtract"}

    # Output usable polygon (largest piece if multi)
    if isinstance(usable, MultiPolygon):
        pieces = sorted(usable.geoms, key=lambda p: p.area, reverse=True)
        main = pieces[0]
        warnings = [f"usable bi chia thanh {len(pieces)} mieng, lay mieng lon nhat"]
    else:
        main = usable
        warnings = []

    coords = [[round(x, 1), round(y, 1)] for x, y in main.exterior.coords[:-1]]
    minx, miny, maxx, maxy = main.bounds
    return {
        "ok": True,
        "usable_polygon": coords,
        "usable_area_m2": round(main.area / 1_000_000, 2),
        "bbox": [round(minx, 1), round(miny, 1), round(maxx, 1), round(maxy, 1)],
        "warnings": warnings,
    }


def validate_zones(payload: dict[str, Any]) -> dict[str, Any]:
    usable = _to_polygon(payload["usable_polygon"])
    zones_in = payload["zones"]
    corridor_min = float(payload.get("corridor_min", 1200))

    results = []
    zone_polys = []
    warnings = []

    for z in zones_in:
        name = z["name"]
        rect = z["rect"]  # [x1,y1,x2,y2]
        x1, y1, x2, y2 = rect
        zp = box(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        area_m2 = zp.area / 1_000_000

        issues = []
        # Check within usable (tolerance)
        if not usable.buffer(TOLERANCE).contains(zp):
            outside = zp.difference(usable)
            outside_pct = outside.area / zp.area * 100 if zp.area > 0 else 0
            issues.append(f"vuot vung kha dung {outside_pct:.1f}% dien tich")

        # Check min area
        min_area = z.get("min_area_m2")
        if min_area and area_m2 < min_area:
            issues.append(f"dien tich {area_m2:.1f}m2 < min {min_area}m2")

        # Check min dim
        min_dim = z.get("min_dim")
        if min_dim:
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            if min(w, h) < min_dim:
                issues.append(f"canh ngan {min(w, h):.0f}mm < min {min_dim}mm")

        results.append({
            "name": name,
            "area_m2": round(area_m2, 2),
            "ok": not issues,
            "issues": issues,
        })
        zone_polys.append(zp)

    # Pairwise check: cac zone khong overlap, va neu khong chung vach
    # phai cach >= corridor_min.
    for i in range(len(zone_polys)):
        for j in range(i + 1, len(zone_polys)):
            a, b = zone_polys[i], zone_polys[j]
            na, nb = results[i]["name"], results[j]["name"]
            if a.intersects(b):
                inter = a.intersection(b)
                if inter.area > TOLERANCE * TOLERANCE:
                    warnings.append(f"{na} va {nb} chong nhau {inter.area/1e6:.2f}m2")
                # neu chi cham bien (area=0) -> chung vach, OK
            else:
                gap = a.distance(b)
                if 0 < gap < corridor_min:
                    warnings.append(
                        f"{na} - {nb} cach {gap:.0f}mm < corridor_min {corridor_min:.0f}mm"
                    )

    # Loi di con lai connected khong?
    leftover = usable.difference(unary_union(zone_polys)) if zone_polys else usable
    if isinstance(leftover, MultiPolygon):
        big_pieces = [p for p in leftover.geoms
                      if p.area > corridor_min * corridor_min]
        if len(big_pieces) > 1:
            warnings.append(
                f"loi di bi cat thanh {len(big_pieces)} mieng - co the bi ket zone"
            )

    coverage_pct = sum(p.area for p in zone_polys) / usable.area * 100 if usable.area else 0

    return {
        "ok": all(r["ok"] for r in results) and not warnings,
        "results": results,
        "warnings": warnings,
        "coverage_pct": round(coverage_pct, 1),
        "leftover_area_m2": round(leftover.area / 1_000_000, 2)
                            if not leftover.is_empty else 0,
    }


def compute_corridor_region(payload: dict[str, Any]) -> dict[str, Any]:
    """Tinh corridor region = shell - cores - zones.

    Input:
      shell: [[x,y],...] outer boundary
      cores: list of [[x,y],...] core regions (WC/ELEV/STAIR)
      zones: list of {"name":str, "rect":[x1,y1,x2,y2]} or {"name":str, "polygon":[[x,y],...]}

    Output:
      corridor_polygons: list of polygons (mỗi cái = exterior + holes nếu có)
      corridor_area_m2: total area
      bbox: bbox của corridor region
      multipolygon_count: số polygon riêng biệt

    Universal fix: thay vì ve corridor polylines (gay duplicate edge),
    skill compute region nay roi HATCH region da co => no duplicate ever.
    """
    shell = _to_polygon(payload["shell"])
    core_polys = [_to_polygon(c) for c in payload.get("cores", [])]
    zones_in = payload.get("zones", [])

    zone_polys = []
    for z in zones_in:
        if "rect" in z:
            x1, y1, x2, y2 = z["rect"]
            zone_polys.append(box(min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2)))
        elif "polygon" in z:
            zone_polys.append(_to_polygon(z["polygon"]))

    interior = shell
    if core_polys:
        interior = interior.difference(unary_union(core_polys))
    if zone_polys:
        corridor = interior.difference(unary_union(zone_polys))
    else:
        corridor = interior

    if corridor.is_empty:
        return {"ok": False, "error": "corridor region empty"}

    # Convert to list of polygons (exterior + interior holes)
    polys = list(corridor.geoms) if isinstance(corridor, MultiPolygon) else [corridor]
    out_polys = []
    for p in polys:
        exterior = [[round(x,1), round(y,1)] for x,y in p.exterior.coords[:-1]]
        holes = [[[round(x,1), round(y,1)] for x,y in h.coords[:-1]]
                 for h in p.interiors]
        out_polys.append({
            "exterior": exterior,
            "holes": holes,
            "area_m2": round(p.area / 1_000_000, 2),
        })

    minx, miny, maxx, maxy = corridor.bounds
    return {
        "ok": True,
        "corridor_polygons": out_polys,
        "corridor_area_m2": round(corridor.area / 1_000_000, 2),
        "bbox": [round(minx,1), round(miny,1), round(maxx,1), round(maxy,1)],
        "multipolygon_count": len(out_polys),
    }


def check_door_overlap(payload: dict[str, Any]) -> dict[str, Any]:
    """Detect polyline xam pham door INSERT bbox.

    Input:
      polylines: list of {"id":str, "bbox":[x1,y1,x2,y2]}
      door_bboxes: list of {"id":str, "bbox":[x1,y1,x2,y2]}
      tolerance: mm² (default 10000 = 100×100)

    Output:
      conflicts: list of {polyline_id, door_id, overlap_mm2}
    """
    pls = payload.get("polylines", [])
    doors = payload.get("door_bboxes", [])
    tol = float(payload.get("tolerance", 10000))

    conflicts = []
    for pl in pls:
        plbb = pl["bbox"]  # [x1,y1,x2,y2]
        for d in doors:
            dbb = d["bbox"]
            ox = max(0, min(plbb[2], dbb[2]) - max(plbb[0], dbb[0]))
            oy = max(0, min(plbb[3], dbb[3]) - max(plbb[1], dbb[1]))
            overlap = ox * oy
            if overlap > tol:
                conflicts.append({
                    "polyline_id": pl["id"],
                    "door_id": d["id"],
                    "overlap_mm2": round(overlap, 1),
                })

    return {
        "ok": len(conflicts) == 0,
        "conflicts": conflicts,
    }


def check_edge_duplicate(payload: dict[str, Any]) -> dict[str, Any]:
    """Detect duplicate edge segments giua polylines.

    Input:
      polylines: list of {"id":str, "points":[[x,y],...], "closed":bool}
      tolerance: mm (default 100)

    Output:
      duplicates: list of {a_id, b_id, shared_length_mm}
      total_duplicate_segments: count
    """
    from shapely.geometry import LineString
    pls_in = payload.get("polylines", [])
    tol = float(payload.get("tolerance", 100))

    # Build edges per polyline
    edges_by_id = {}
    for pl in pls_in:
        pid = pl["id"]
        pts = pl["points"]
        closed = pl.get("closed", False)
        edges = []
        for i in range(len(pts)-1):
            edges.append(LineString([pts[i], pts[i+1]]))
        if closed and len(pts) > 1:
            edges.append(LineString([pts[-1], pts[0]]))
        edges_by_id[pid] = edges

    duplicates = []
    ids = list(edges_by_id.keys())
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            a_id, b_id = ids[i], ids[j]
            shared = 0
            for ea in edges_by_id[a_id]:
                for eb in edges_by_id[b_id]:
                    if ea.distance(eb) < 1.0:
                        inter = ea.intersection(eb.buffer(1.0))
                        if hasattr(inter, "length") and inter.length > tol:
                            shared += inter.length
            if shared > tol:
                duplicates.append({
                    "a_id": a_id, "b_id": b_id,
                    "shared_length_mm": round(shared, 1),
                })

    return {
        "ok": len(duplicates) == 0,
        "duplicates": duplicates,
        "total_duplicate_segments": len(duplicates),
    }


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"invalid JSON stdin: {e}"}))
        sys.exit(1)

    mode = payload.get("mode")
    try:
        if mode == "compute_usable":
            out = compute_usable(payload)
        elif mode == "validate_zones":
            out = validate_zones(payload)
        elif mode == "compute_corridor_region":
            out = compute_corridor_region(payload)
        elif mode == "check_edge_duplicate":
            out = check_edge_duplicate(payload)
        elif mode == "check_door_overlap":
            out = check_door_overlap(payload)
        else:
            out = {"ok": False, "error": f"unknown mode: {mode!r}"}
    except Exception as e:
        out = {"ok": False, "error": f"{type(e).__name__}: {e}"}

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
