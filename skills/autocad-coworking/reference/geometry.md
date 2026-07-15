# Reference: tinh toan hinh hoc truoc khi ve

Skill goi MCP de DOC ban ve hien co, dung helper Python `scripts/layout.py`
de tinh **vung kha dung (usable region)** + **validate zone de xuat**, roi
moi goi MCP de VE. Muc tieu: het chuyen ve zone tran ra ngoai vach, chong
core, hoac de be cot.

Helper chay tren WSL Python (khong phai Windows). Da cai `shapely` global.

## Khi nao chay

Bat buoc trong **buoc B0.5** (chen giua B0 probe va B3 propose zone).
Khong bo qua tru khi user yeu cau ve free-hand thu nghiem.

## Pipeline

```
entity.list  ──►  classify entities  ──►  layout.py compute_usable  ──►  propose zones
                  (shell/core/cot)        (shapely difference)            (text + bbox)
                                                                              │
                                                                              ▼
                                          layout.py validate_zones  ◄── user confirm
                                          (within / overlap / corridor)       │
                                                                              ▼
                                                                       MCP entity.create_polyline
```

## B0.5.1 — Lay du lieu hinh hoc tu ban ve

```
autocad-mcp__entity(operation="list")
```

Tra ve **chi `{type, handle, layer}`** — KHONG co coordinate. Voi tung
handle quan trong, goi:

```
autocad-mcp__entity(operation="get", entity_id="<handle>")
```

(luu y `entity_id` la top-level, KHONG nam trong `data`).

**Han che cua server:** `entity.get` chi tra toa do cho `LINE` (start/end)
va `CIRCLE` (center/radius). Voi `LWPOLYLINE` (rectangle, ZONE polyline,
tuong shell), `MTEXT`, `INSERT` (block), `ARC`, `ELLIPSE`, `HATCH` →
chi tra `{type, handle, layer}` khong co toa do.

**Workaround khi can vertex cua LWPOLYLINE:** dung
`system(operation="execute_lisp", data={"code": "..."})` doc DXF group
code 10 — xem `reference/mcp-tools.md` muc "entity.list / entity.get
LIMITATION" cho code mau. Confirm voi user truoc khi chay LISP.

**Workaround don gian:** neu user da biet kich thuoc shell + vi tri core,
**hoi user nhap toa do** thu cong, tien thang vao layout.py. Nhanh va an
toan hon parse DXF.

**Phan loai (heuristic, hieu chinh theo file user):**

| Vai tro | Cach nhan dien |
|---|---|
| **Shell** (vach toa nha) | `LWPOLYLINE` closed co bbox lon nhat, hoac chuoi `LINE` tao thanh chu vi ngoai cung. Layer thuong la `WALL`, `0`, hoac `A-WALL`. |
| **Core** (WC, ELEV, STAIR) | Cum polyline / rectangle nho **co text label** ben trong (`MTEXT`/`TEXT` voi noi dung "WC", "ELEV", "STAIR"). Loc `annotation` truoc, mapping text-position vao polyline bao quanh. |
| **Cot** (column) | `LWPOLYLINE` closed nho (200-800mm canh) lap lai theo grid, hoac block `COLUMN`/`COL`. |
| **Vach trong** | Line/polyline ngan trong long shell, khong tao thanh polygon dong. Bo qua o B0.5; xu ly o B6 khi ve furniture. |

Neu kien truc su xac nhan layer naming chuan (vd `A-WALL-EXTR` cho vach
ngoai), uu tien loc theo layer hon la theo bbox.

## B0.5.2 — Goi `compute_usable`

Build payload JSON, pipe vao `python3 scripts/layout.py`. Tu workspace
goc:

```bash
python3 skills/autocad-coworking/scripts/layout.py <<'JSON'
{
  "mode": "compute_usable",
  "shell": [[x1,y1],[x2,y2],...],
  "obstacles": [
    [[wc_pts]],
    [[elev_pts]],
    [[stair_pts]]
  ],
  "columns": [[cx1,cy1],[cx2,cy2],...],
  "column_buffer": 300
}
JSON
```

Output:
```json
{
  "ok": true,
  "usable_polygon": [[x,y],...],
  "usable_area_m2": 280.56,
  "bbox": [minx, miny, maxx, maxy],
  "warnings": []
}
```

Luu `usable_polygon` va `bbox` vao memory turn — feed vao buoc validate.

**Don vi:** mm cho coordinate, m2 cho area output.

**Column buffer 300mm** la default an toan; tang len 500mm neu kien truc
su muon co khoang lui ban quanh cot.

## B0.5.3 — Propose zones (text, KHONG ve)

Tu `usable_area_m2` va ty le tham chieu (xem `playbooks/zoning.md`), tinh
muc dien tich tung khu. Voi shape la chu nhat / L / canh xeo, de xuat
**bbox cu the** cho moi zone (`[x1, y1, x2, y2]`):

- Chia theo chieu dai cua usable bbox.
- Chua dat zone vao goc / canh xeo / khu canh shell tre — danh cho lounge
  hoac luu thong.
- Snap toa do vao **column grid** neu phat hien duoc (vd 8400mm). Doc
  lai column positions tu B0.5.1 → suy ra grid spacing → snap zone edges
  vao bo so hop ly.

Trinh bay user 1 bang text + screenshot mockup neu phuc tap. **Cho confirm.**

## B0.5.4 — Goi `validate_zones`

```bash
python3 skills/autocad-coworking/scripts/layout.py <<'JSON'
{
  "mode": "validate_zones",
  "usable_polygon": [[x,y],...],
  "corridor_min": 1500,
  "zones": [
    {"name":"HOTDESK", "rect":[x1,y1,x2,y2], "min_dim":3000, "min_area_m2":80},
    {"name":"MEETING", "rect":[...], "min_dim":3000},
    ...
  ]
}
JSON
```

Output:
```json
{
  "ok": true,
  "results": [
    {"name":"HOTDESK", "area_m2":80.0, "ok":true, "issues":[]},
    ...
  ],
  "warnings": [],
  "coverage_pct": 52.2,
  "leftover_area_m2": 146.75
}
```

**Quy tac dung:**
- `ok: false` o bat ky zone nao → **khong duoc ve**, sua zone roi validate lai.
- `warnings` co entry "chong nhau" hoac "bi ket" → review voi user, sua.
- `coverage_pct` quanh 75-80% la lanh manh (con lai la circulation).
  Neu < 60% → de xuat them zone hoac scale up. Neu > 85% → cat bot, khong
  con loi di.
- `leftover_area_m2` chinh la **dien tich circulation** thuc te.

Chi sang B4 (ve zone) sau khi `ok: true`.

## Truong hop dac biet

**Shell co canh xeo** (nhu hinh user gui truoc): truyen polyline co diem
xeo vao `shell`, **khong** lay bbox. Helper se ne canh xeo dung.

**Core khong duoc box san trong file:** neu user chi co text "WC" / "ELEV"
ma chua ve polygon, hoi user kich thuoc roi tu dung polygon bao trong
payload. Khong doan.

**Cot khong deu:** truyen lan luot toa do tam tung cot, helper buffer
deu. Neu chi co mot vai cot lon (vach chiu luc), tang `column_buffer`
hoac tach thanh `obstacles` rieng.

## Cay quyet dinh khi gap loi

| Output helper | Y nghia | Xu ly |
|---|---|---|
| `compute_usable.ok: false, error: "usable region empty"` | Obstacles lon hon shell, hoac shell self-intersect | Kiem tra lai diem shell (tu giao?), giam column_buffer |
| `compute_usable.warnings: "chia thanh N mieng"` | Core cat doi san | Xac nhan voi user san co thuc su bi chia hay sai input |
| `validate_zones` issue: `vuot vung kha dung` | Zone nho ra ngoai shell hoac chong core | Co kich thuoc / di chuyen zone, validate lai |
| `validate_zones` warning: `chong nhau` | 2 zone overlap (khong phai chung vach) | Lui mot zone, hoac neu chu y chung vach thi cho 2 rect cham canh chinh xac (area intersect ~0) |
| `validate_zones` warning: `bi ket` | Cau hinh zone chan loi di | Re-arrange, dam bao loi chinh xuyen suot tu cua chinh |

## Helper API tom tat

`scripts/layout.py` doc JSON tu stdin, in JSON ra stdout. Khong side
effects, khong network, khong file IO ngoai stdio. An toan goi nhieu lan.

Mode: `compute_usable` | `validate_zones`. Xem docstring trong file de
biet schema day du.
