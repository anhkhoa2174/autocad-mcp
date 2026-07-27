# Reference: AutoCAD MCP tools (autocad-mcp)

Skill goi MCP server `autocad-mcp` (cau hinh san o `~/.openclaw/openclaw.json`).
Server expose **8 consolidated tools** voi prefix `autocad-mcp__`. File nay
mo ta day du **7 tools dung trong coworking** (`drawing`, `entity`, `layer`,
`block`, `annotation`, `view`, `system`). Tool `pid` khong dung — bo qua.

Truong hop ngo van de cau hinh: dung `openclaw mcp list` /
`openclaw mcp show autocad-mcp` / `openclaw mcp logs autocad-mcp`. **Khong**
sua source MCP.

---

## Param shape — nguyen tac chung

Param shape **khong dong nhat** giua cac tool:

| Tool | Param shape |
|---|---|
| `drawing` | `operation, data?, include_screenshot?` — moi field nam trong `data` |
| `entity` | `operation, x1, y1, x2, y2, points, layer, entity_id` (top-level) + `data` (field phu) + `include_screenshot?` |
| `layer` | `operation, data?, include_screenshot?` — moi field trong `data` |
| `block` | `operation, data?, include_screenshot?` — moi field trong `data` |
| `annotation` | `operation, data?, include_screenshot?` — moi field trong `data` |
| `view` | `operation, x1, y1, x2, y2` (top-level) — **KHONG** co `data`, **KHONG** co `include_screenshot` |
| `system` | `operation, data?, include_screenshot?` — moi field trong `data` |

`include_screenshot: bool = False` — set `True` de tra ve kem screenshot
trong cung response (1 roundtrip thay vi 2). Co o **6/7 tools** (tat ca tru
`view`).

**Gia tri tra ve chung:**
- Success: `{"ok": true, ...payload}` (text/JSON content). Voi
  `include_screenshot=True`, them ImageContent inline.
- Failure: `{"ok": false, "error": "...", "type": "..."}`.

---

## 1. `drawing` — File / drawing management

Khi nao dung: bootstrap dau session (kiem tra ban ve), save / export khi
user yeu cau, undo / redo neu lo tay.

### Operations

| Operation | Data | Tra ve | Khi nao dung |
|---|---|---|---|
| `create` | `{name?: str}` | `{ok}` | **Reset doc hien tai** (erase + purge). Confirm voi user truoc — pha huy |
| `open` | `{path: str}` | `{ok}` | Mo file `.dwg` / `.dxf` o duong dan tuyet doi (Windows: `C:/...`) |
| `info` | — | `{entity_count: int, layers: [str, ...]}` | Probe sau status — biet bao nhieu entity, danh sach layer co san |
| `save` | `{path?: str}` | `{ok}` | Khong path → QSAVE; co path → SAVEAS. **Confirm voi user truoc** |
| `save_as_dxf` | `{path: str}` | `{ok}` | Xuat DXF ra path. Confirm voi user |
| `plot_pdf` | `{path: str}` | `{ok}` | Plot PDF. Confirm voi user |
| `purge` | — | `{ok}` | Purge unused. Confirm voi user (xoa block/layer khong dung) |
| `get_variables` | `{names?: [str, ...]}` | `{ACADVER, DWGNAME, CLAYER, ...}` | Doc bien he thong. Khong `names` → tra default `{ACADVER, DWGNAME, CLAYER}` |
| `undo` | — | `{ok}` | Undo 1 buoc |
| `redo` | — | `{ok}` | Redo 1 buoc |

**Luu y:**
- `info` chi tra `entity_count` + `layers`. KHONG tra `extmin/extmax/blocks/active_layer`
  du docstring server co noi (giam su tin tuong vao docstring; tin code).
- Muon biet active layer → `get_variables(names=["CLAYER"])`.
- Muon biet bbox ban ve → khong co tu MCP, phai survey thu cong.

### Pattern

```
# Bootstrap dau session
autocad-mcp__system(operation="status")
autocad-mcp__drawing(operation="info")
# → quyet dinh tiep theo dua tren entity_count va layers
```

---

## 2. `entity` — Entity CRUD + modification

Tool **lon nhat va quan trong nhat**. Tat ca thao tac ve hinh deu qua tool
nay.

### Param shape (top-level + data)

`x1, y1, x2, y2, points, layer, entity_id` la TOP-LEVEL. Field "phu"
trong `data`. Lan dau xem hay nho: tham so nao dung de **goi command**
LISP (`_LINE`, `_RECTANG`, ...) thuong la top-level; tham so nao la
"option" (closed, dx, factor, ...) thi vao `data`.

### Create operations

Tat ca create op tra ve `{ok: true, entity_type: str, handle: str}`. Capture
`handle` de modify lan sau (hoac dung `entity_id="last"`).

| Operation | Top-level | Data | Output `entity_type` | Khi nao dung |
|---|---|---|---|---|
| `create_line` | `x1, y1, x2, y2, layer?` | — | `"LINE"` | Ve doan line — vach ngan, mui ten loi di, chia khu |
| `create_circle` | `layer?` | `{cx, cy, radius}` | `"CIRCLE"` | Ghe (r=250-300mm), cot tron, ban tron |
| `create_rectangle` | `x1, y1, x2, y2, layer?` | — | `"LWPOLYLINE"` | Ban, tu, vach booth, polygon zone don gian |
| `create_polyline` | `points: [[x,y],...], layer?` | `{closed?: bool}` | `"LWPOLYLINE"` | Zone hinh phuc tap, shell co canh xeo, tuong gay khuc |
| `create_arc` | `layer?` | `{cx, cy, radius, start_angle, end_angle}` | `"ARC"` | Cung cua, soi chi xoay |
| `create_ellipse` | `layer?` | `{cx, cy, major_x, major_y, ratio}` | `"ELLIPSE"` | Ban hinh trung, hinh trang tri |
| `create_mtext` | `layer?` | `{x, y, width, text, height?}` (`width` BAT BUOC) | `"MTEXT"` | Block text nhieu dong, ghi chu dai |
| `create_hatch` | `entity_id` | `{pattern?: str}` (default `"ANSI31"`) | `"HATCH"` | To boi cho zone — chi nhan **1 boundary entity_id** (closed) |

**Goc do (start_angle / end_angle / rotation):** **DEGREE** o tang server
(LISP convert sang radian). Truyen `0` la 3 gio, `90` la 12 gio.

**`create_hatch` chi 1 boundary:** muon hatch nhieu zone phai goi nhieu
lan, hoac union polyline truoc. Khong nhan list handles.

**`create_polyline` voi `closed=true`:** dong hinh — dung cho ZONE polygon.
Voi `closed=false`: pline ho — dung cho centerline luu thong.

### Read operations

| Operation | Top-level | Data | Output |
|---|---|---|---|
| `list` | `layer?` | — | `{entities: [{type, handle, layer}, ...]}` — KHONG co toa do |
| `count` | `layer?` | — | `{count: int}` |
| `get` | `entity_id` | — | `{type, handle, layer, ...type-specific}` |

**`entity.get` trace toa do:**
- `LINE` → `{start: [x,y], end: [x,y]}`
- `CIRCLE` → `{center: [x,y], radius}`
- Tat ca type khac (LWPOLYLINE, MTEXT, INSERT, ARC, ELLIPSE, HATCH,
  DIMENSION, TEXT) → CHI tra `{type, handle, layer}` khong co toa do.
  Workaround: `system.execute_lisp` doc DXF group code (xem section cuoi).

### Modify operations

Tat ca dung `entity_id` top-level. `entity_id="last"` = entity vua tao
truoc do (entlast).

| Operation | Top-level | Data | Tra ve | Khi nao dung |
|---|---|---|---|---|
| `move` | `entity_id` | `{dx, dy}` | `"moved"` | Doi cho ban / ghe |
| `copy` | `entity_id` | `{dx, dy}` | `{handle: <new>}` | Nhan ban entity (1 ban) |
| `rotate` | `entity_id` | `{cx, cy, angle}` | `"rotated"` | Xoay quanh (cx, cy), angle DEG |
| `scale` | `entity_id` | `{cx, cy, factor}` | `"scaled"` | Phong to / thu nho quanh (cx, cy) |
| `mirror` | `entity_id, x1, y1, x2, y2` | — | `{handle: <new>}` | Phan chieu qua duong (x1,y1)-(x2,y2). Source giu nguyen (`erase=false`) |
| `offset` | `entity_id` | `{distance}` | `{handle: <new>}` | Offset song song (vd vach booth — outline trong) |
| `array` | `entity_id` | `{rows, cols, row_dist, col_dist}` | `"arrayed"` | **Lap day ban hot desk** (rectangular array) |
| `fillet` | — | `{id1, id2, radius}` | `"filleted"` | Bo goc 2 line / pline |
| `chamfer` | — | `{id1, id2, dist1, dist2}` | `"chamfered"` | Vat goc 2 line |
| `erase` | `entity_id` | — | `{ok}` | Xoa. Confirm voi user neu erase >5 entity |

**`array` rectangular only:** server khong support polar array. Muon polar
(ghe quanh ban tron) → tinh toa do tung ghe trong skill, goi
`create_circle` nhieu lan.

### Pattern thuc dung

```
# Ve ban mau roi array thanh day hot desk
autocad-mcp__entity(operation="create_rectangle",
                    x1=1000, y1=1000, x2=2400, y2=1700, layer="F-DESK")
# → {handle: "<H1>", entity_type: "LWPOLYLINE"}
autocad-mcp__entity(operation="array",
                    entity_id="<H1>",
                    data={"rows": 2, "cols": 5, "row_dist": 1500, "col_dist": 1600})

# Vach booth: outline ngoai + offset 50mm vao trong
autocad-mcp__entity(operation="create_rectangle",
                    x1=10000, y1=5000, x2=11100, y2=6100, layer="A-WALL")
autocad-mcp__entity(operation="offset", entity_id="last", data={"distance": -50})
```

---

## 3. `layer` — Layer management

Quan ly layer. Mac dinh ban ve da co layer `0`. Skill **luon tao bo layer
chuan rieng** (xem `reference/layers.md`).

### Operations

| Operation | Data | Tra ve | Khi nao dung |
|---|---|---|---|
| `list` | — | `{layers: [{name, color: int}, ...]}` | Probe truoc khi tao layer — neu da co thi skip |
| `create` | `{name: str, color?: str\|int, linetype?: str}` | `{name}` | Tao layer moi. Default `color="white"`, `linetype="CONTINUOUS"`. **KHONG** nhan `lineweight` |
| `set_current` | `{name: str}` | `{current_layer}` | Set layer hien tai truoc moi nhom thao tac ve. Bat buoc cho `annotation.create_dimension_*` |
| `set_properties` | `{name, color?, linetype?, lineweight?}` | `{ok}` | Sua thuoc tinh layer (lineweight chi co o day, khong o `create`) |
| `freeze` | `{name}` | `{ok}` | Freeze layer (an + khong tinh extents) |
| `thaw` | `{name}` | `{ok}` | Unfreeze |
| `lock` | `{name}` | `{ok}` | Lock — entity van hien nhung khong sua duoc |
| `unlock` | `{name}` | `{ok}` | Unlock |

**`color`:** chap nhan ten string (`"red"`, `"yellow"`, `"green"`, `"cyan"`,
`"blue"`, `"magenta"`, `"white"`) hoac so int 1-255 (ACI). Server LISP doi
string truoc khi map.

**`layer.list` chi tra `name + color`:** khong tra linetype, lineweight,
on/off, frozen state. Ngheo info — neu can chi tiet, dung
`system.execute_lisp` query bang `tblnext`.

### Pattern

```
# Setup bo layer chuan dau session
autocad-mcp__layer(operation="list")
# → {layers: [{name: "0", color: 7}, ...]}; biet layer nao da co

# Tao bo chuan
autocad-mcp__layer(operation="create", data={"name": "CW-ZONE-BOUNDARY", "color": 1})
autocad-mcp__layer(operation="create", data={"name": "CW-DIMENSION", "color": 7})

# Set current truoc khi ve
autocad-mcp__layer(operation="set_current", data={"name": "CW-ZONE-BOUNDARY"})
autocad-mcp__entity(operation="create_polyline", points=[...], data={"closed": true})
# (KHONG can pass layer="CW-ZONE-BOUNDARY" nua vi da set_current)
```

---

## 4. `block` — Block library

Su dung block (do hoa tai su dung) — chu yeu cho noi that ban / ghe / sofa
neu user da co thu vien block.

### Operations

| Operation | Data | Tra ve | Khi nao dung |
|---|---|---|---|
| `list` | — | `{blocks: ["name", ...]}` | Probe truoc khi insert — biet thu vien co gi |
| `insert` | `{name, x, y, scale?, rotation?, block_id?}` | `{entity_type: "INSERT", handle}` | Insert block tai (x, y). `block_id` se gan vao attribute `ID` neu co |
| `insert_with_attributes` | `{name, x, y, scale?, rotation?, attributes: {tag: value}}` | `{entity_type: "INSERT", handle}` | Insert + dien attribute. **Luu y:** server LISP insert truoc roi yeu cau goi `update_attribute` rieng, **chua tu set attributes ngay**. An toan: dung `insert` + `update_attribute` lan luot. |
| `get_attributes` | `{entity_id}` | `{attributes: {tag: value, ...}}` | Doc attribute cua block instance |
| `update_attribute` | `{entity_id, tag, value}` | `{tag, value}` | Sua 1 attribute |
| `define` | `{name, entities: [...]}` | (file_ipc khong implement day du — ezdxf moi) | Tao block tu code — coworking thuong khong dung |

**Default:** `scale=1.0`, `rotation=0.0` (degrees).

### Pattern

```
# Kiem tra co block ban hot desk khong
autocad-mcp__block(operation="list")
# → {blocks: ["DESK-1400", "CHAIR", "SOFA-2"]}

# Insert
autocad-mcp__block(operation="insert",
                   data={"name": "DESK-1400", "x": 1700, "y": 1350, "rotation": 0})

# Khong co block? Fall back ve `entity.create_rectangle`
```

---

## 5. `annotation` — Text, dimensions, leaders

Ghi chu va kich thuoc. Tat ca op truyen qua `data`.

### Operations

| Operation | Data | Tra ve | Ghi chu |
|---|---|---|---|
| `create_text` | `{x, y, text, height?, rotation?, layer?}` | `{entity_type: "TEXT", handle}` | Single-line TEXT (khong phai MTEXT). Justify middle. **`layer` nam trong data** |
| `create_dimension_linear` | `{x1, y1, x2, y2, dim_x, dim_y}` | `{entity_type: "DIMENSION"}` | Kich thuoc linear giua (x1,y1) va (x2,y2). `dim_x/dim_y` la diem dat duong dim. **KHONG** nhan `layer` |
| `create_dimension_aligned` | `{x1, y1, x2, y2, offset}` | `{entity_type: "DIMENSION"}` | Kich thuoc theo huong canh. `offset` la khoang lui (1 so) |
| `create_dimension_angular` | `{cx, cy, x1, y1, x2, y2}` | `{entity_type: "DIMENSION"}` | Kich thuoc goc tu (cx,cy) qua 2 tia (x1,y1)-(x2,y2) |
| `create_dimension_radius` | `{cx, cy, radius, angle}` | `{entity_type: "DIMENSION"}` | Kich thuoc ban kinh. `angle` (DEG) chon huong text |
| `create_leader` | `{points: [[x,y],...], text}` | `{entity_type: "LEADER"}` | Mui ten dan (callout) |

**Khac biet quan trong:**
- `create_text` — `layer` **trong data**, KHONG top-level (khac voi `entity.*`).
- `create_dimension_*` va `create_leader` — KHONG nhan `layer`. Muon dim
  tren layer `DIM` → `layer.set_current(name="DIM")` truoc.
- `create_text` ghi TEXT (single-line). Muon multi-line block → dung
  `entity.create_mtext`.
- Default `height=2.5`, `rotation=0.0`. Voi don vi mm thi `height=2.5`
  qua nho — pass `height: 250` (250mm) cho nhin duoc.

### Pattern

```
# Nhan ten zone
autocad-mcp__annotation(operation="create_text", data={
  "x": 4000, "y": 2500, "text": "HOT DESK",
  "height": 250, "layer": "CW-ZONE-LABEL"
})

# Kich thuoc loi di — set_current truoc vi op khong nhan layer
autocad-mcp__layer(operation="set_current", data={"name": "CW-DIMENSION"})
autocad-mcp__annotation(operation="create_dimension_linear", data={
  "x1": 5000, "y1": 1000, "x2": 5000, "y2": 14000,
  "dim_x": 4500, "dim_y": 7500
})
```

---

## 6. `view` — Viewport / screenshot

KHONG co `data`, KHONG co `include_screenshot`. Param top-level.

### Operations

| Operation | Top-level | Tra ve | Khi nao dung |
|---|---|---|---|
| `zoom_extents` | — | `{ok}` | Zoom thay het ban ve. Goi truoc `get_screenshot` de capture du khu |
| `zoom_window` | `x1, y1, x2, y2` | `{ok}` | Zoom vao 1 cua so cu the (vd zoom 1 zone de check chi tiet) |
| `get_screenshot` | — | **Inline image** (TextContent + ImageContent base64 PNG) | Capture ban ve thanh anh, bot client tu render |

**`get_screenshot` khong nhan `path`/`data`:** server chup window qua
Win32 `PrintWindow`, base64 PNG return inline. Khong ghi file disk. Bot
client (OpenClaw) tu hien thi.

**Pattern khuyen nghi de show user:**

```
autocad-mcp__view(operation="zoom_extents")
autocad-mcp__view(operation="get_screenshot")
```

Hoac toi uu hon — set `include_screenshot=True` o tool khac:

```
autocad-mcp__entity(operation="create_polyline",
                    points=[...], data={"closed": true},
                    include_screenshot=True)
# → ve xong tra luon screenshot trong cung 1 call
```

---

## 7. `system` — Server / runtime

### Operations

| Operation | Data | Tra ve | Khi nao dung |
|---|---|---|---|
| `status` | — | `{backend, hwnd, ipc_dir, capabilities}` | **Buoc dau tien moi session** — kiem tra MCP san sang |
| `health` | — | `{ok, backend}` | Health check ngan |
| `get_backend` | — | giong `status` | Ten backend hien tai |
| `runtime` | — | `{platform, python, cwd, backend_env, wsl_interop}` | Diagnostic spawn — debug khi MCP loi |
| `init` | — | `{ok}` | Re-initialize backend (force reset) |
| `execute_lisp` | `{code: str}` | `{ok, result?}` | **Chay AutoLISP tuy y** — confirm voi user truoc |

**`status` shape thuc te:**

```json
{
  "ok": true,
  "backend": "file_ipc",
  "hwnd": 12345,
  "ipc_dir": "C:/temp",
  "capabilities": {
    "can_read_drawing": true,
    "can_modify_entities": true,
    "can_create_entities": true,
    "can_screenshot": true,
    "can_save": true,
    "can_plot_pdf": true,
    "can_zoom": true,
    "can_query_entities": true,
    "can_file_operations": true,
    "can_undo": true
  }
}
```

**`execute_lisp` use cases:**
- Doc vertex cua LWPOLYLINE (xem section LIMITATION).
- Set bien he thong (vd `DIMSCALE`, `LTSCALE`).
- Goi command nang cao server khong wrap (vd `_BLOCK` define on-the-fly).

Confirm voi user truoc khi run code, vi day la arbitrary execution.

---

## entity.list / entity.get LIMITATION

**Han che that, can biet de propose workaround:**

`entity.list` → `[{type, handle, layer}]` KHONG co toa do.

`entity.get` chi extract toa do cho `LINE` va `CIRCLE`. Cac type khac chi
tra `{type, handle, layer}` khong co geometry.

### Workaround 1: `system.execute_lisp` doc DXF group code

Khi can vertex LWPOLYLINE / vi tri MTEXT / insertion point block:

```
autocad-mcp__system(operation="execute_lisp", data={"code":
  "(setq e (entget (handent \"2A1\")))
   (setq verts \"\")
   (foreach pair e
     (if (= 10 (car pair))
       (setq verts (strcat verts (if (= verts \"\") \"\" \",\")
                           \"[\" (rtos (cadr pair) 2 2) \",\"
                                (rtos (caddr pair) 2 2) \"]\"))))
   (princ (strcat \"{\\\"vertices\\\":[\" verts \"]}\"))"})
```

Group code thong dung:
- `10` (+ `20` y, `30` z) — vertex / start / center / insertion point
- `11` — line endpoint, dim definition point
- `40` — radius, height, scale x
- `41` — scale y; `42` — scale z
- `50` — rotation angle (DEG)
- `1` — text content / block name (cho INSERT)
- `2` — block name / table name
- `8` — layer
- `70` — flags (bit 1 = closed polyline)

Confirm voi user truoc khi run.

### Workaround 2: hoi user input toa do thu cong

Coworking thong thuong, hoi user "san dai bao nhieu, rong bao nhieu, core
o goc nao kich co bao nhieu" thay vi parse DXF. Nhanh + an toan hon.

---

## Bootstrap dau session

```
autocad-mcp__system(operation="status")
```

Quyet dinh:

| Result | Action |
|---|---|
| `backend: "file_ipc"` + ban ve mo (`drawing.info` co entity_count) | Tiep tuc workflow |
| `error` o status | `openclaw mcp list` / `openclaw mcp logs autocad-mcp`, bao user |
| `status.ok=true` nhung `drawing.info` bao "No active drawing" | Bao user mo / tao ban ve |

---

## Response shape — quy uoc chung

Tu top-level FastMCP return:
- Success text: `{"ok": true, ...}` (LISP serialize JSON inline string).
- Failure: `{"ok": false, "error": "..."}`.
- `entity.create_*` tra `entity_type` (vd `"LWPOLYLINE"`, `"INSERT"`,
  `"DIMENSION"`) trong khi `entity.get` tra `type`. Khac biet vat ly do
  LISP handler — workaround: parse ca 2 field.
- Modify op tra string ngan (`"moved"`, `"rotated"`, ...) hoac
  `{handle: <new>}` voi op tao ra entity moi (copy / mirror / offset).

---

## Error shape & xu ly

```json
{"ok": false, "error": "...", "type": "..."}
```

| Trieu chung | Nguyen nhan | Xu ly |
|---|---|---|
| MCP tool khong xuat hien | Server chua start / agent chua reload | `openclaw mcp list`, restart agent |
| `error: "Entity not found: ..."` | `entity_id` truyen sai shape (nho trong `data` thay vi top-level) | Truyen `entity_id` **top-level** |
| `entity.get` thieu toa do | LWPOLYLINE/MTEXT/INSERT/... — server khong support | Workaround `execute_lisp` |
| `error: "Block 'X' not found"` | Block name sai / block chua define trong file | `block(operation="list")` lay ten dung |
| `error: "AutoCAD LT window not found"` | AutoCAD chua chay | Mo AutoCAD LT 2024+ |
| `error: "No active drawing"` | Doc dong giua chung | User mo lai |
| IPC timeout (`Timeout waiting for result`) | AutoCAD modal dialog block / dispatcher chua load / lenh dang dang | User press ESC, thu lai |
| Screenshot `ok: false` / image rong | PNGOUT timeout / dialog | User press ESC, thu lai |
| KeyError (vd `data["x"]`) | Field bat buoc thieu trong `data` | Check signature trong file nay |

---

## Performance

- Server persistent — 1 process reuse. Khong overhead spawn.
- IPC overhead: write JSON cmd → PostMessage trigger LISP → LISP doc + run + write result → Python doc result. **~10-50ms / op**, default timeout 10s
  (config `AUTOCAD_MCP_IPC_TIMEOUT`).
- 1 op tai 1 luc (server lock single in-flight). Goi tuan tu, khong race.
- Loop hang tram lan OK. Nhung uu tien 1 cu `entity.array` thay vi 50 cu
  `entity.copy` — ban ve nhe hon, bot client de hieu hon.
