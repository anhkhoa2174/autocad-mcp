# Construction-Ready Drawing Rules (B7.6 → B7.12)

**CHỈ áp dụng khi user yêu cầu rõ:**
- "construction drawing" / "for thi cong" / "for contractor"
- "building permit" / "xin phep xay dung"
- "TCVN compliance" / "QCVN compliance"
- "production-ready" / "construction document"

**Default demo / concept layout / space planning → SKIP toàn bộ file này.** Stop ở B7.5 (title block + north arrow). Nhồi B7.6-B7.12 vào 1 sheet = CHAOS, mentor đọc không được. Architect chuyên nghiệp tách thành multi-sheet (L02 walls, L03 block plan, L05 egress...). Skip-default.

Liên quan: `feedback_autocad_demo_default.md` trong memory.

---

### B7.6. Dimension lines

Construction drawing PHAI co kich thuoc. Cho moi zone + corridor:

```
layer.set_current(data={"name":"CW-DIMENSION"})
annotation.create_dimension_linear(data={
  "x1": zone.x1, "y1": zone.y1, "x2": zone.x2, "y2": zone.y1,
  "dim_x": (zone.x1+zone.x2)/2, "dim_y": zone.y1 - 800
})
```

Vi tri dimension line:
- Tren cua zone (ngang): dim_y = zone.y1 - 800 (phia duoi zone, ngoai)
- Trai-phai cua zone (doc): dim_x = zone.x1 - 800 (phia trai zone, ngoai)
- Overall dimension: dat ngoai shell, vd dim_y = shell.y_min - 2000

Skip neu user explicit noi "concept-only" / "demo, khong can dim".

### B7.7. Wall thickness 200mm

Tuong don 1 line khong the hien thickness. Cho A-WALL boundary:
- Goi `entity.offset(entity_id=<wall_handle>, data={"distance": 200})` →
  tao parallel line 200mm phia trong.
- Hoac dung `MLINE` truc tiep neu backend support.

Skip neu skill ran o mode "concept layout" (demo, khong thi cong).

### B7.9. Fire egress annotations

> Required theo QCVN 06:2022 cho construction document + building permit.
> KHONG ve cho demo / concept / space planning sheet.

Bat buoc cho construction document + building permit submission.

Cho moi corridor:
1. **Mui ten thoat hiem**: polyline 3-vertex tam giac mui ten tai
   midpoint corridor, huong ve nearest exit. Layer `A-EXIT` color 1 (red).
   ```
   entmake LWPOLYLINE: 3 vertex tam giac (apex + base 2 vertex), closed
   ```

2. **Travel distance text**: MTEXT tai zone xa nhat tu exit, ghi
   "Travel: <X>m to nearest exit". `A-EXIT` color 1.

3. **Exit sign symbol**: tai door 29D + 29E (entrance/exit):
   - Rectangle 800x400mm
   - Text "EXIT" hoac symbol mui ten
   - Vi tri: gan door, layer `A-EXIT` color 1

**Tinh travel distance:** dung shortest path tu zone center → exit door,
qua corridor regions (compute_corridor_region trong layout.py). PCCC
VN ≤25m. Neu vuot → fail, redesign.

### B7.10. Line weight hierarchy

> Required theo AIA + TCVN cho construction document. Demo concept dung default lineweight.

Set lineweight per layer (3 levels):

| Layer group | Lineweight | Purpose |
|---|---|---|
| A-WALL, A-COLUMN | **0.50mm** | Cut elements (tuong, cot) — DAY DAM |
| A-DOOR, A-WINDOW, CW-FURN-* | **0.25mm** | Visible elements (cua, noi that) |
| ANNO-*, A-EXIT, CW-DIMENSION, CW-ANNOTATION | **0.13mm** | Annotations, dimensions — MONG NHAT |

Apply: `layer.update(data={"name":"A-WALL","lineweight":0.50})`. Lap
lai cho tat ca layer. Neu MCP khong support lineweight → goi
`system.execute_lisp` voi `(command "_.LWEIGHT" ...)`.

### B7.11. Door/window schedule + tags

> Required theo UK + AIA checklist cho construction. Demo concept skip.

Cho moi door + window trong ban ve:

1. **Tag**: text "D01", "D02", "W01"... dat next to door INSERT
   - Layer: `A-DOOR` (cho door tag) hoac `A-WINDOW` (cho window tag)
   - Text height 200mm, hexagon bubble optional
   - Vi tri: gan door INSERT, KHONG dat trong swing arc

2. **Schedule table** dat ngoai shell (gan title block):
   ```
   ┌────┬────────┬─────────┬───────────┬──────────┐
   │ ID │ TYPE   │ SIZE    │ HARDWARE  │ LOCATION │
   ├────┼────────┼─────────┼───────────┼──────────┤
   │D01 │ Single │ 900x2100│ LH lockset│ Reception│
   │D02 │ Double │ 1800x2100│ Panic bar │ Main entr│
   │... │
   └────┴────────┴─────────┴───────────┴──────────┘
   ```
   - 1 LWPOLYLINE rectangle frame
   - LINE dividers (rows + columns)
   - TEXT cho moi cell

3. **Numbering convention:** door 29D (main entrance) → D01, door 29E
   (exit) → D02, internal doors theo zone visit order D03, D04...

### B7.12. Accessibility turning circles

> Required theo TCVN 10380:2014 cho construction permit. Demo concept skip.

Wheelchair turning circle **ø1500mm** (1.5m diameter, r=750mm).

Vi tri BAT BUOC co turning circle:
- **Mai vi tri ngoai door 29D entrance** (khach disabled vao)
- **Trong WC accessible** (1 stall co ø1500)
- **Tai corridor junction** (giao loi)
- **Trong meeting room lon** (10+ chỗ)

Implement:
```
entity.create_circle(layer="A-ACCESS",
  data={"cx": <pos>, "cy": <pos>, "radius": 750})
```
Layer `A-ACCESS` color 3 (green), lineweight 0.13mm dashed.

KHONG ve neu user noi "khong can ADA / accessibility" — chi cho
project muc dich nha o thuong + ngan sach thap.
