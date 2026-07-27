---
name: autocad-coworking
description: Tro ly kien truc su thiet ke coworking space — phan khu, layout, noi that qua MCP server autocad-mcp (file_ipc backend).
---

# autocad-coworking

Skill nay giup ban (Pebble) lam tro ly cho kien truc su thiet ke **coworking
space** trong AutoCAD. Tat ca thao tac goi qua **MCP server `autocad-mcp`**.
Tools da duoc pre-registered o tool surface voi prefix `autocad-mcp__*` —
**cu call thang, KHONG can kiem tra config file** (`~/.openclaw/openclaw.json`
KHONG chua MCP config; openclaw dung mcporter bridge tai `~/.mcporter/mcporter.json`).

Don vi mac dinh **mm**. Heading & ghi chu trong workspace viet **tieng Viet
khong dau**; ten op va tham so giu nguyen tieng Anh.

---

## 🎯 5 CORE PRINCIPLES (READ + APPLY EVERY RESPONSE)

These 5 principles compress 14+ specific rules. If you remember nothing else,
remember these. Each principle has a one-line CHECK you can apply mid-task
without re-reading the full skill.

### 🔴 PRINCIPLE 1 — SURVEY → VALIDATE → DRAW (never skip)

Before any `entmake`, you MUST have:
1. Surveyed columns (X grid + Y grid coords)
2. Surveyed doors (auto-classified main/exit + verified swing direction + **query bbox**)
3. Surveyed walls (shell + internal)
4. Computed usable polygon via `scripts/layout.py`
5. Validated proposed geometry vs constraints
6. **Validated door-corridor connectivity:**
   - Every door MUST be reached by a corridor (corridor edge touches door wall position)
   - Corridor system MUST form closed loop topology
   - Path from any door to any other door MUST exist
   - **NO LOBBY transit** (per R-C1) — corridor đi THẲNG đến wall position của cửa, không qua zone trung gian

CHECK: "Tôi đã gọi `scripts/layout.py` cho propose hiện tại chưa? Door-corridor connectivity validated chưa? Nếu chưa → STOP".

### 🟠 PRINCIPLE 2 — ONE SOURCE OF TRUTH (Python computes, LISP draws)

Coord generation = Python helper (`scripts/layout.py`, `scripts/validate_*.py`).
LISP entmake = NEVER compute, ONLY draw what Python validated.

If you need a coordinate, the answer comes from Python output, not from your
in-head arithmetic. LLMs are bad at arithmetic — don't trust your own math.

CHECK: "Coord này đến từ Python output hay từ tôi tự tính? Nếu tự tính → re-run script".

### 🟡 PRINCIPLE 3 — VISIBLE OVER INVISIBLE (corridor = HATCH not outline)

Corridor visualization: use HATCH DOTS (non-associative, `HPASSOC=0`), KHONG
closed polyline outline. Polyline outline trong nhu tuong khep kin → confuse.

Zone wall: open polyline with doorway gap where corridor connects. KHONG ve
zone as closed rectangle if it shares a doorway with corridor.

CHECK: "Corridor visible bang hatch chua? Zone co doorway gap o cho noi corridor chua?"

### 🟢 PRINCIPLE 4 — ASCII-SAFE TEXT (no Unicode escape leaks)

Text label TUYET DOI KHONG dung Unicode chars (², °, —, é) tru khi confirmed
MCP backend co `ensure_ascii=False` (file_ipc.py line 157 — fixed 2026-05-19).
ASCII-safe alternative: "40m2", "deg", "em-dash".

If using Unicode anyway, verify with `(princ (cdr (assoc 1 (entget ...))))` —
text must show actual char, KHONG show `\uXXXX` literal.

CHECK: "Text co Unicode char khong? Neu co, verify backend ho tro chua?"

### 🟣 PRINCIPLE 5.5 — ASK UPFRONT, NOT MID-FLOW

Mỗi step major (B1, L01, L02, L03) PHAI hỏi **TẤT CẢ clarifying questions tại đầu step**, KHONG hoi piecemeal trong khi propose/draw.

Pattern dung:
```
B1 (initial context): ask ALL site context Qs (1 batch, 4-6 questions)
B2.5 survey: auto-detect (no questions)
L01 propose: present plan based on B1+B2.5 → propose 1-3 options → user pick → NO MID-FLOW Qs
```

Pattern SAI:
- Skip B1 → propose L01 → mid-flow hoi "door direction?" → user khong hieu sao hoi giua chung
- B1 hỏi BLANK "cửa nào entrance?" — user phải tự suy → bad UX

Pattern DUNG:
- B1: skill **auto-classify cửa** theo logic (double_door=main, swing_door on shell=exit), **show guess + reasoning**, hỏi anh **confirm/chỉnh**
- B1 batch các Q khác cần input thực sự (orientation, PCCC, sprinkler, floor, capacity)
- User trả lời 1 lượt
- L01: propose dựa trên confirmed context, KHÔNG hỏi thêm

**Door classification — AUTO-GUESS + CONFIRM (không hỏi blank):**

Logic auto-guess (B2.5 survey):
| Block type + position | Em đoán |
|---|---|
| `double_door` width ≥1800mm on shell | Main Entrance bi-dir |
| `swing_door` near edge wall (Y=0, Y=max, X=0, X=max) | Emergency Exit one-way OUT |

→ Trong propose §2, em show: "Em đoán Cửa 29D (double_door 1.8m) = Main Entrance vì rộng + ở trục chính; Cửa 29E (swing 0.9m, edge wall) = Exit khẩn cấp vì hẹp + xa entrance. **Anh OK hay chỉnh?**"

**Questions PHAI hoi at each major step:**

| Step | Required Qs (batch upfront) |
|---|---|
| **B1** | (1) Building orientation (north)? (2) PCCC strict/relax? (3) Sprinkler Y/N? (4) Floor + building type? (5) Target capacity? **Door classification = auto-guess ở B2.5, anh confirm trong L01 propose §2** |
| **L01** | Confirm door auto-guess từ B2.5; pick 1 trong 3 corridor options |
| **L02** | (1) Privacy mix (% private vs open)? (2) Special rooms (boardroom/event/booth)? (3) Pantry style (cafe/bar/lounge)? |
| **L03** | (1) Furniture brand/style? (2) Budget level? (3) Dimension/finish? |

→ "Ask upfront once" thay vi "ask 5 lan trong 5 propose".
→ Door class = skill đoán + user confirm, KHÔNG hỏi blank.

### 🔴 PRINCIPLE 5.7 — PRE-DRAW CHECKLIST cho zones (BẮT BUỘC, tránh tái phạm bug)

Trước khi `entmake` zone polyline + label, em PHẢI run checklist sau cho **mỗi** zone:

| # | Check | Action nếu fail |
|---|---|---|
| 1 | Zone bbox **không overlap cores** polygon (vd Demo.dwg cores X=0-16000, Y=18000-28000) | Dời zone hoặc shrink |
| 2 | Zone bbox **không overlap corridor** strips | Dời/shrink |
| 3 | Zone bbox **trong shell** (kể cả chamfer / non-rectangular) | Polygon 5+ vertex theo chamfer |
| 4 | **Label width** ≤ zone width × 0.9 (`len(text) × 0.7 × height < zone_w × 0.9`) | Split 2 dòng stacked TEXT (xem dưới) |
| 5 | Label text **KHÔNG dùng `\n` literal** | LISP `_TEXT` không hiểu newline; dùng 2 entities riêng |
| 6 | Label text **ASCII only** (no diacritics) | đến khi MCP backend reload `ensure_ascii=False` fix |
| 7 | Zone tiếp giáp shell wall → **open polyline** bỏ cạnh shared (per [[shared-wall-with-shell]]) | Skip edge tại shared boundary |
| 8 | **Fill ≥95% usable area** — check ALL subregions (west/east/south/upper) (per R-C7); add zone cho mọi subregion **>5m²** còn trống (KHÔNG threshold 30m²) | Small subregion 5-15m² → assign nhỏ (Phone Booth, Storage, Coat Closet); medium 15-30m² → Reception/Pantry/small Meeting; large >30m² → main zones |
| 9 | **Branch corridor align door bbox ≤100mm** — query `vla-getboundingbox` mỗi door TRƯỚC draw branch | Realign corridor edges với door opening (NOT modify door) |
| 10 | **Hatch DRAWORDER send-to-back** — set `(setvar "HPDRAWORDER" 3)` TRƯỚC tạo hatch, hoặc `_DRAWORDER _B` SAU; nếu không hatch đè **door INSERT block + door ARC swing + wall LINE + label TEXT (L1, L2...) + door markers** → user không đọc được tên + không thấy cửa/tường | Cleanup MANDATORY pass (per session 2026-05-21 bug): `(foreach ss (list ss-door-insert ss-door-arc ss-wall ss-text) (command "_.DRAWORDER" ss "" "_F"))` — bring ALL baseline (INSERT/ARC/LINE) + labels TO FRONT above hatch |
| 10b | **Erase ALL hatches before re-hatch khi shift polyline** — khi shift polyline (vd L5 X=15400→16000), erase polyline only KHÔNG erase associated hatch → orphan hatch ở vị trí cũ vẫn visible → user thấy "lòi/dư". Phải erase HATCH-by-layer trước, re-hatch tất cả polylines sau | `(foreach lyr (list "CW-CIRC-GUIDE") (ssget "X" (list (cons 0 "HATCH") (cons 8 lyr))) → entdel all) → re-hatch ALL polylines` |
| 11 | **NO orphan strip giữa MỌI cặp adjacent** (zone-zone, zone-corridor, zone-shell) — share edge HOẶC ≥1200mm có wall ngăn; KHÔNG gap 1-1199mm | Extend zone đến flush; mỗi shared edge dùng 1 polyline (open skip cho zone kia) |
| 12 | **CirCO Động→Tĩnh zone order** — Reception NGAY entrance point (entrance bao gồm **thang máy/cầu thang** không chỉ shell door — per ENTRANCE DEFINITION section), Pantry+Hub cạnh Reception, Meeting dọc hành lang, Dedicated/Private back/corners | Survey cores location TRƯỚC → identify entrance point → RECP adjacent |
| 13 | **Survey INSERT blocks** trong cores/WC/elevator area — KHÔNG chỉ XREF walls; zone bbox MUST NOT overlap any INSERT bbox (door symbols, sanitary fixtures, elevator markers) | Query `ssget INSERT` + check bbox; nếu INSERT trong zone area → zone area is occupied by existing equipment, KHÔNG empty |
| 14 | **Survey LINE walls precisely** (không chỉ bbox của cluster) — bbox max Y của cluster ≠ outer wall face; walls có **thickness 100-200mm** với inner face + outer face — query individual LINE positions để find true wall extent | Query `ssget _C window LINE` trong khu vực target zone; verify zone bbox không overlap any LINE wall coords |
| 15 | **Furniture: bàn xếp CỤM BENCH (4/6/8 dồn sát) chừa lối đi — KHÔNG bàn lẻ rời**; phòng họp chia **vừa khít bàn** (1.8-2.3 m²/người, ko dư); dùng **block model thật** ko circle. Meeting đặt sau lounge-pantry/perimeter ko nhét sâu | Pod 2 hàng đấu lưng × N cột, aisle chính 1200-1500 / phụ 1050-1200; xem `playbooks/furnishing.md` §0 + memory [[desk-cluster-benching-meeting-rightsize-placement]], [[furniture-standards-and-real-block-models]] |

**2-line stacked TEXT pattern (label fit fix):**

```python
def draw_2line_label(cx, cy, l1, h1, l2, h2):
    # Line 1 (short code) ở trên center
    annotation.create_text(x=cx, y=cy + h1//2 + 100, text=l1, height=h1)
    # Line 2 (detail) ở dưới center
    annotation.create_text(x=cx, y=cy - h2//2 - 100, text=l2, height=h2)
```

Vd: zone RECP 5.5m × 5.3m:
- Line 1: "RECP" height 350
- Line 2: "Reception 29m2" height 250
- Total label height = 350 + 250 + 200 gap = 800mm < zone height 5300mm ✓

**Bugs tái phạm cần TUYỆT ĐỐI tránh:**

| Bug | Fix |
|---|---|
| Zone đè cores wall (LOUN X=10500-19000 đè ELEV X=0-16000) | Query cores polygon trước, X≥16000 nếu zone upper west |
| LOUN polygon vượt chamfer line | Polygon 5-vertex theo chamfer y = 28000 - (5/7)(x-28000) |
| Label `\n` literal | 2 TEXT entities stacked, không `\n` |
| Label `\u00XX` Unicode escape | ASCII only đến khi reload MCP |
| Empty SW area X=0-10500, Y=0-18000 không có zone | Add LOBBY-W + HDSK-W zones |

### 🔵 PRINCIPLE 5 — NO DUPLICATE EDGES (shared wall = one polyline)

Adjacent zones must NOT both draw the shared wall. Use one of:
- Single L-shape polyline tracing combined outline
- Or one closed zone + neighbor open polyline (skip shared edge)
- Or corridor as hatch (no wall) + zone polyline as wall

Never draw 2 closed rectangles sharing a full edge → OVERKILL won't fix all,
visual duplicate ink, conflict with skill rule "pairwise edge connectivity".

CHECK: "Zone A bbox co share edge voi zone B bbox khong? Neu co → 1 trong 2 phai open polyline tai shared edge."

---

## 🚪 CORRIDOR-DOOR DESIGN RULES (CRITICAL — session 2026-05-19/20)

These 6 rules are MANDATORY for L01 corridor design. Violating any = redo from scratch.

### R-C1. ALL doors DIRECT corridor (no LOBBY transit)

MỌI cửa (entrance + exit) PHẢI có corridor đi THẲNG tới wall position của cửa. KHÔNG dùng LOBBY/Reception zone giữa corridor và door.

```
SAI: [Door] → [LOBBY zone] → [Corridor] → ring
DUNG: [Door] → [Corridor direct] → ring
     Reception zone = ADJACENT to corridor (bên cạnh, không transit)
```

### R-C2. Corridor width per CirCO spec (MIN — phải suy nghĩ theo context)

CirCO chuẩn CHÍNH THỨC (per `reference/circo-standard.md` §3.6):
- **Hành lang chính** (lễ tân/thang máy → phân khu chính): **1.5 - 1.8m** thông thủy
- **Hành lang nội bộ** (giữa các phòng làm việc): **≥1.2m** lọt lòng (sau trừ nẹp/hộp kỹ thuật/bình chữa cháy)
- Cửa mở ra ngoài → cộng thêm kích thước cánh cửa vào width hành lang

**KHÔNG cứng nhắc default!** Em phải **suy nghĩ theo mặt bằng** trước khi chốt width:

| Yếu tố | Tăng width? |
|---|---|
| Mặt bằng lớn (>500m²) → daily traffic cao | + 0.2-0.4m |
| Cửa main entrance ≥1.8m → flow rate cao | match cửa hoặc gần (vd 1.6-1.8m) |
| Cluster cuối có ≥6 người users | + 0.2m |
| Coworking premium (high-end member) | + 0.2-0.4m feel rộng |
| Mặt bằng nhỏ (<200m²) → trade-off zone area | giữ MIN |
| Connector vào storage / WC | giữ MIN |

**Right pattern:** Propose width có reasoning trong §2 propose (vd "chọn ring 1.4m vì mặt bằng 600m², daily traffic ~40 users"). User confirm hoặc chỉnh.

**Lower bound:**
- KHÔNG dưới 1.5m cho hành lang chính
- KHÔNG dưới 1.2m cho hành lang nội bộ
- **NGOẠI LỆ — nhánh tới cửa THOÁT HIỂM (emergency exit): ~1.0m là đủ** (user 2026-07).
  Chỉ cần 1 nhánh hẹp chạm cửa để thoát; **KHÔNG chừa mảng trống lớn trước exit** —
  phần dư phải gán vào zone kế bên thành diện tích dùng được.
  (Cửa **main entrance** vẫn giữ 1.5-1.8m như trên, không áp ngoại lệ này.)
- KHÔNG widen vượt cần thiết (lãng phí zone area)

### R-C3-pre. CORRIDOR TOPOLOGY — Ring là 1 option, không phải PATTERN duy nhất

**Yêu cầu CHUNG cho mọi topology:**
- Mọi corridor segments PHẢI **CONNECTED** với nhau (đi từ cửa A → cửa B qua corridor được, không phải băng qua phòng)
- Mọi cửa (entrance + exit) đều có corridor đi tới

**4 topology valid (chọn tùy mặt bằng + reference user):**

| Topology | Shape | Khi nào dùng |
|----------|-------|--------------|
| **Ring** | 4 strips closed loop quanh inner courtyard + branches | Mặt bằng có Pantry/HUB trung tâm; classic coworking; closed loop dễ verify |
| **Central cluster + perimeter aisles** | Service cluster ở giữa (Pantry+Reception+Meeting+Booth) + aisles dọc walls | **CirCO Saigon pattern** (per reference 67 NTMK); open floor; rows desk perimeter |
| **Spine + branches** | 1 trục chính N-S hoặc E-W + nhánh phụ | Mặt bằng dài hẹp; linear flow |
| **Open floor** | Không corridor explicit | Floor nhỏ <100m²; ít zone |

**Default:** Hỏi user reference. Nếu user reference CirCO 67 NTMK → **Central Cluster + Perimeter** (không ring). Nếu chưa rõ → propose 2-3 options khác topology để user pick.

**PCCC "100% vòng tuần hoàn"** = closed loop preferred. Ring + Central Cluster đều có closed loop. Spine + Open có thể bị non-cycle — verify manually mọi cửa reach được.

---

### R-C3. Corridor — CONTINUOUS POLYGON (no "gấp khúc" = disconnected corners)

**"Gấp khúc" định nghĩa đúng (user clarified 2026-05-21):** = 2 strip rời không liền đoạn tại corner — visible gap/seam vì inner corner cell không được fill bởi cả 2 strip. KHÔNG phải số bend.

**Rule:** Mọi corridor PHẢI là **single continuous polygon** (1 LWPOLYLINE entity), fill kín mọi corner.

**Allowed:**
- ✓ Straight strip (0 bend) — 1 rectangle polygon
- ✓ L-shape — 1 polygon 6 vertices, single hatch fill toàn bộ
- ✓ Z-shape, U-shape, multi-bend — 1 polygon n vertices, single hatch (chỉ cần continuous)
- ✓ Ring = 4 strip riêng (vì là 4 separate corridor strips, each continuous, ghép thành closed loop)

**Forbidden:**
- ❌ L-shape vẽ thành 2 rectangle SEPARATE rời nhau, touch chỉ tại corner point → inner corner cell unfilled = visible gap
- ❌ Multi rectangle hatches with NO overlap region at corner

**Implementation:**

L-shape correct:
```python
# Single 6-vertex polygon
verts = [(16000, 19900), (21000, 19900), (21000, 12700), (19600, 12700), (19600, 18100), (16000, 18100)]
entmake LWPOLYLINE 6 vertices closed
hatch DOTS with select-boundary → 1 hatch entity fills entire L-shape
```

L-shape WRONG (gấp khúc):
```python
# 2 separate rectangles
rect1: H leg (16000, 18100)-(21000, 19900)  
rect2: V leg (19600, 12700)-(21000, 18100)
# 2 hatches → visible seam at corner cell (19600-21000, 18100-19900)
```

**Closed loop requirement (CirCO 100% vòng tuần hoàn):**
- Ring + branches PHẢI hợp thành closed loop topology
- Branch đến cửa: nếu cửa axis perpendicular ring → L-shape polygon branch (continuous, no gap)
- Branch straight OK nếu door axis parallel ring direction

**Ring vs Linear corridor — KHI NÀO DÙNG (context-aware, KHÔNG apply mù):**

| Floor dimensions | Recommended topology |
|---|---|
| Work area **wide >8m × long >12m** | Ring (4 strips ghép rectangle) — full closed loop |
| Work area **thin ≤6m × long >15m** | **Linear single spine** corridor E-W hoặc N-S — ring không khả thi (HUB còn quá mỏng) |
| Work area **mix** (medium) | Ring + chấp nhận thin HUB, hoặc Linear + nhiều zones along corridor |

**Why linear OK khi floor thin:** Floor 22m × 5.4m work area → ring chiếm 80% space (2.8m × 2 sides = ring height), HUB còn 2.6m thin. Linear spine 1.4m chiếm 1.4m, còn 4m cho zones above/below.

**Trade-off:** Linear corridor KHÔNG full closed loop (không quay đầu walking về điểm đầu). Acceptable cho thin floor — flow vẫn rõ ràng (one-way west-east).

**Branch design rule:**
- 1 cửa = 1 branch = 1 strip thẳng duy nhất
- Nếu branch thẳng không reach được vùng cần serve → **bỏ branch đó**, để zones bám wall/ring trực tiếp
- KHÔNG cố "uốn" branch để tới mọi nơi

**Upper/side area access (no corridor reach):**
- Zones lớn (Lounge, Library, Premium Office) bám ring edge và **extend vào subregion** — không cần corridor xuyên qua
- Người đi: ring → cửa zone → vào zone (zone tự là không gian đi lại)

### R-C4. Column position relative to corridor

| Vị trí cột | OK/BAD |
|---|---|
| Cột GIỮA corridor (col center ở giữa width) | ❌ BAD (cản người đi) |
| Cột trên EDGE corridor (left/right edge) | ✓ OK (col integrated wall) |
| Buffer ≥800mm corridor | ✓ OK |

Align corridor sao cho col ở EDGE, KHÔNG middle.

### R-C5. NO step/jog between corridors

Branch corridor nối ring strip PHẢI flush (share full edge segment, not corner point only).

```
SAI:                          DUNG:
  Branch                        Branch
    │                             │
    │ (only corner point)         │
    └──┐                          ▼
       │ BRIDGE STEP        ┌───────────────── Ring strip (extends to flush)
       │                    │
       └───── Ring strip
```

**For ring corners (NW/NE/SW/SE):** ONE strip's end edge MUST be FULLY within the other strip's edge.

### R-C5.6. Branch FILL FULL BAND between walls (no Y/X gap)

Khi branch corridor đi qua/tới door ở band giữa 2 walls song song (vd LOBBY band Y=18000-20000 = giữa internal wall Y=18000 và cores wall Y=20000):

**Corridor segment trong band PHẢI fill FULL BAND (full distance giữa 2 walls), KHÔNG chỉ 1.4m strip:**
- Vd LOBBY band 2m (Y=18000-20000) → corridor segment trong band Y=18000-20000 (2m tall, không 1.4m)
- Vì band chính là "không gian giao thông" — corridor fill toàn bộ band ko để khoảng trống.

**Lý do:** 1.4m default chỉ apply cho corridor TRONG khu work area (gaps giữa zones). Trong LOBBY band giữa 2 walls = ENTIRE band là corridor, không thể có gap (gap = wasted space + door bị "lòi").

Logic apply:
- Query horizontal walls quanh door area
- Identify "band" = 2 parallel walls (vd Y=18000 + Y=20000 → band 2m)
- Branch segment trong band: Y_min=wall_low, Y_max=wall_high (full band fill)
- KHÔNG dùng 1.4m default cho segment trong band

**Vi du:** L5 L-shape đến door 29D:
- Horizontal segment Y=18000-20000 (2m, full LOBBY band) — cover toàn bộ door bbox
- KHÔNG dùng Y=18500-19900 (1.4m) — door 29D bbox Y=18100-19900 sẽ extend ngoài corridor

Tương tự cho X-axis bands (vd corridor giữa 2 vertical walls).

### R-C5.5. Branch edge ALIGN internal wall (not centered on door)

Khi branch corridor tới door **ở góc cores** (vd door 29D tại X=16000 = cores east wall):
- Branch LEFT/RIGHT edge PHẢI align với internal wall position (không centered on door center)
- Vd: door 29D tại X=16000 (bbox 16000-16900), internal wall vertical tại X=16000 → L5 left edge = X=16000, width 1.2m → L5 = X=16000-17200
- KHÔNG center L5 trên door bbox center (X=16450) → sẽ extend trái khỏi wall, "lòi" ra ngoài

**Reasoning:** Architecturally, corridor abuts wall. User can't walk through wall. Centering branch on door center → 1 nửa branch ở trong wall (invalid).

Query internal walls trước khi place branch:
```lisp
(ssget "X" (list (cons 0 "LINE") (cons 8 "A-WALL")))
;; filter vertical lines (x1==x2) near door area
;; branch edge = wall X position
```

### R-C6. Door bbox center (not insertion point)

Insertion point của door INSERT thường là góc/edge, KHÔNG phải center của door opening. Query bbox via `vla-getboundingbox` để biết exact door center, then align corridor.

```lisp
(setq min-pt (vlax-3d-point 0 0 0))
(setq max-pt (vlax-3d-point 0 0 0))
(vla-getboundingbox (vlax-ename->vla-object (handent "29D")) (quote min-pt) (quote max-pt))
```

For `double_door` 1.8m: insertion at one end, full opening = insertion + (block_width × 2).

### R-C8. NO CORRIDOR BULGE (no wide blob at single spot)

Corridor có thể **kéo dài** (long, vd 14m vertical hoặc 10m horizontal) nếu giữ 1.4m thickness consistent. Nhưng KHÔNG được **"phình to"** thành blob lớn tại 1 điểm.

**Definition "blob":**
- Area at single spot > 12m²
- AND minimum dimension > 1.8m (both X and Y > 1.8m at same place)
- → Visually trông như "hall" rather than "hallway"

**Detection:**
```python
for corridor in corridors:
    area = corridor.width_x * corridor.width_y
    min_dim = min(corridor.width_x, corridor.width_y)
    if area > 12 and min_dim > 1.8:
        flag_as_bulge(corridor)
```

**Examples:**
| Shape | Dimensions | Bulge? |
|---|---|---|
| Straight 14m × 1.4m | area 19.6m², min 1.4m | ✓ OK (long but thin) |
| L-shape east 6m × 1.4m | area 8.4m², min 1.4m | ❌ INVALID per R-C3 (no bends) |
| T-shape H wide 11.5m × 1.4m | area 16.1m², min 1.4m | ❌ INVALID per R-C3 (no bends) |
| Wide rectangle 5m × 5m | area 25m², min 5m | ❌ BLOB |
| Long widening 8m × 2.5m | area 20m², min 2.5m | ❌ BLOB |

**Right pattern:** straight strip preferred; L-shape OK nếu cần (single 6+ vertex polygon, không 2 rectangles ghép).

---

### R-C7. FULL USABLE AREA CHECK (no missed subregion)

KHÔNG miss subregions của floor khi design corridor + zones. Mọi vùng inside-shell PHẢI có zone access.

**Common missed areas:**
- East of cores (if cores narrower than shell): vd Demo.dwg cores X=0-16000, shell X=0-42000 → đông cores 12m × 8m = 96m² trống
- North of cores (if shell extends north): vd Demo.dwg shell Y=0-28000, cores Y=20000-28000 → có open floor east of cores Y=20000-28000
- Chamfered corners: vd NE corner triangle ~70m²
- Side bays: narrow strips along shell edges

**Detection workflow:**
1. Survey shell polyline ALL vertices
2. Identify cores subregion (smaller than shell)
3. Compute usable = shell - cores - existing walls
4. Subdivide usable into rectangles/polygons
5. Check **EACH subregion ≥30m²** has corridor access OR zone-chain access

**Apply to corridor design:**
- Per R-C3 (straight only): NO corridor extension UP với bend; nếu upper area cần access → zones bám ring + extend lên (no corridor xuyên qua)
- Hoặc thêm 1 straight branch thẳng riêng (nếu align được với ring và không cần bend)

**Apply to zone design (L02):**
- L02 zones PHẢI cover all subregions
- KHÔNG subregion empty >5m²
- Include zones for upper/east-of-cores/chamfered areas
- Vd: Upper Lounge, Quiet Library NE, Premium Office, Server room chamfered corner

**Demo.dwg example missed (2026-05-20):**
- Initially designed corridor + zones only Y=0-19900 (south of cores) → missed 166m² upper area (96m² east of cores + 70m² chamfered NE)
- L02 must add: zone east of cores X=16000-28000 Y=20000-28000, plus chamfered NE zone

---

## 🚦 DOOR CLASSIFICATION DEFAULTS (architectural reasoning)

Default propose dựa trên **architectural logic**, NOT user override (user override = test/mentor demand only).

| Door property | Default classification | Reasoning |
|---|---|---|
| `double_door` (2 lá, ≥1.8m), on shell wall | 🟢 **Main Entrance bidirectional** | Cửa to → capacity cao cho daily traffic |
| `swing_door` (1 lá, 0.9m), on shell wall, xa main >5m | 🔴 **Emergency Exit only PCCC** | Cửa nhỏ → less daily use, egress khẩn |
| `swing_door` interior wall | Internal door bidirectional | Room-to-room |
| `sliding_door` | Internal sliding | Phòng nhỏ tiết kiệm không gian |

**Always propose default + state reasoning + HỎI USER CONFIRM.** Workflow:
1. Em auto-guess theo bảng trên (KHÔNG hỏi blank)
2. Em show trong propose §2: "Em đoán 29D=Main, 29E=Exit. Vì sao: [reasoning]. **Anh OK hay chỉnh?**"
3. User confirm/swap → apply; nếu swap thì note unusual + redesign nếu cần

**KHÔNG auto-modify shell baseline** (rotate doors, move walls) dù có PCCC reason. Phải hỏi user permission trước.

### 🚪 ENTRANCE DEFINITION — bao gồm thang máy/cầu thang (per [[entrance-includes-elevator]])

"Cửa entrance" trong CirCO **KHÔNG CHỈ** là cửa shell wall. Bao gồm:

| Type | Description | When applicable |
|---|---|---|
| **Shell wall door** | Cửa block INSERT trên ngoại biên tòa nhà | Demo.dwg: cửa 29D on cores east wall |
| **Thang máy (Elevator)** | Người đến floor qua lift | CIRCO NKKN: cores top-left elevator cluster |
| **Cầu thang (Stair)** | Người đi bộ lên floor | Within cores cluster |
| **Cores access combined** | Lift + stair grouped | Most office buildings |

**Detection workflow (mandatory before placing RECP):**
1. Survey doors layer (cuadi/A-DOOR) — find shell wall doors
2. Survey cores cluster (thang máy/cầu thang) — find lift/stair location
3. **Floor không có shell wall door** → entrance = cores exit point (south edge of cores cluster vào work area)
4. **Floor có shell wall door** → entrance = shell door

**Reception placement rule — RECP phải là zone ĐẦU TIÊN nhìn thấy + đi vào:**
- RECP **NGAY exit point of entrance** (cores south edge HOẶC shell door, whichever applies)
- RECP là **zone ĐẦU TIÊN** user gặp khi ra entrance — KHÔNG zone nào (MEET/LOUN/PANT) được chắn giữa entrance và RECP

**Spatial check (mandatory):**
- Vẽ đường thẳng từ entrance exit point đi vào work area (hướng người bước ra)
- Zone đầu tiên đường này cắt PHẢI là RECP
- KHÔNG có MEET/LOUN flanking 2 bên chắn trước RECP

**Anti-pattern (avoid):**
- ❌ Treat interior cores door as "main entrance" → RECP đặt sai (xa thang máy)
- ❌ Skip elevator location khi survey
- ❌ RECP south of corridor while MEET/LOUN occupy area directly at elevator exit → ra thang gặp MEET/LOUN trước (user reject 2026-05-23)

**Right pattern:**
- ✓ Survey cores location FIRST, identify south edge (work area side)
- ✓ RECP chiếm vị trí TRỰC TIẾP trước exit thang máy (prime spot)
- ✓ MEET/LOUN dời sang side hoặc qua corridor (visitor: elevator→RECP→cross corridor→MEET, không xuyên work area)

---

## 🏷️ LABEL CONVENTION (v3 — session 2026-05-20: L1/L2 corridor naming)

| Context | Convention | Example |
|---|---|---|
| **PROPOSE TEXT** (show to user) | Tiếng Việt **với giải thích đầy đủ code** | "Cửa 29D (cửa 2 lá double_door, rộng 1.8m) là Main Entrance" |
| **DRAWING LABEL — CORRIDOR** | **L1, L2, L3...** ngắn gọn cho user dễ gọi | "L1", "L2 1.4m", "L6" |
| **DRAWING LABEL — ZONE** | English code ngắn 4-8 chars | "HUB", "RECP", "PRIV-E" |
| **PROPOSE schedule §3** | Show mapping L# ↔ internal name | "L1 = MAIN-N (ring top), L6 = BR-ENTRY" |
| **Memory/SKILL internal** | Code OK | "29D", "MAIN-N", "CW-ZONE-BOUNDARY" |

**Corridor numbering convention (per [[corridor-short-labels-L1-L2]]):**
- **L1-L4** = ring strips clockwise from top: L1=N, L2=E, L3=S, L4=W
- **L5+** = branches by door order: L5=branch to first door, L6=branch to second door...

**Why L1/L2:** User nhìn drawing → muốn chỉnh corridor → gọi tên ngắn dễ nói/gõ ("chỉnh L3 east 2m") thay vì "BR-ENTRY". User feedback 2026-05-20.

**Label fit rule:**
- Default: just "L1" height 350mm → 490mm wide ✓ fits 1.4m corridor
- Optional: "L1 1.4m" (tight fit at height 280)
- KHÔNG fit → shrink height (down to 200mm OK)
- KHÔNG split 2 lines cho corridor (corridor là strip dài)

KHÔNG dùng tiếng Việt trên drawing labels (Unicode encoding issues).

---

## 🛡️ AUTO-DEFAULTS (apply without asking user)

These decisions are auto-applied based on architectural convention. KHONG hoi
user mid-flow — just apply + note in propose §2 (user can override).

| Decision | Auto-default | Source rule |
|---|---|---|
| Door direction | `double_door`→Main bidir; `swing_door` on shell→Exit-only | Auto-classify B2.5 |
| Door swing PCCC | Emergency Exit must swing OUT; auto-rotate 180° if violation | B2.8 PCCC check |
| Corridor center | Midpoint between 2 column lines | Column-aware B2.7 |
| Corridor visualization | HATCH DOTS non-associative | Principle 3 |
| Travel >25m | Auto-shrink zone OR designate far area as service zone | PA1=limit, PA3=accept exception |
| Label anchor | `annotation.create_text` (middle-center), NOT `create_mtext` | annotation tool |
| Polyline draw | `entmake` direct via `execute_lisp` (bypass OSNAP) | OSNAP guard |
| Text encoding | ASCII-safe; Unicode only if MCP `ensure_ascii=False` confirmed | Principle 4 |
| Furniture size | CirCO standard (1200×600 hot, 1400×600 dedi, 1000×1000 booth) | CirCO §3 |
| Furniture grid fit | `cols × desk_w + (cols-1) × gap_x ≤ zone_w - 2×margin` | Arithmetic guard |

---

## 📋 STATE MACHINE (print current state every response)

```
STATE 0: SURVEYED        → shell coords, cols, doors classified
STATE 1: CIRC_PROPOSED   → 3 corridor options pre-validated
STATE 2: CIRC_DRAWN      → HATCH visible on CW-CIRC-HATCH layer
STATE 3: ZONE_PROPOSED   → 3 PA options pre-validated
STATE 4: ZONE_DRAWN      → polylines on CW-ZONE-BOUNDARY (with doorway gaps)
STATE 5: FURN_PROPOSED   → schedule + grid arithmetic checked
STATE 6: FURN_DRAWN      → final entities on CW-FURN-*
STATE 7: ANNOTATED       → dimensions, title block, north arrow
```

Begin every response with `STATE: X` so context refreshes. Transitions require
user `ok`/`vẽ` confirmation, NOT auto-progress.

---

## ⚠️ PRE-FLIGHT (BAT BUOC TRUOC MOI ACTION VE)

**LUON LUON `read` toan bo file SKILL.md NAY truoc khi:**
- Goi bat ky `autocad-mcp__entity` create / modify / erase op nao
- Goi `autocad-mcp__layer create / set_current`
- Goi `autocad-mcp__annotation create_*`
- Goi `autocad-mcp__drawing save / save_as_dxf / purge / create`

**Ly do:** skill nay co > 50 rule cu the (param shape, batch limit, zone
shape orthogonality, code compliance, finishing chuan kien truc...). Thieu
1 rule = ban ve sai chuan / dam cot / cheo tum lum / dien hua hen reviewer.

**KHONG bao gio noi "skill chua cai" hoac "tu lam qua autocad-mcp tools"**
— neu doc den skill nay nghia la skill DA cai, va workflow B0 → B7.5 la
con duong DUY NHAT. Bo qua = sai output.

**Quick reload trigger:** sau moi 5-10 turn lien tuc lam viec, re-read
SKILL.md de refresh memory ve param shape va orthogonality rules — context
window de quen.

## Demo workflow

Khi user noi "lam mat bang coworking tu file X.dwg" → follow detailed workflow B0 → B7.5 (xem section "## Workflow" bên dưới). KHONG dung cheatsheet riêng (outdated nhanh). Detailed workflow là source of truth.

---

## 🚨 ANTI-BUG HARD RULES (TUYET DOI TUAN THU)

Cac rule nay fix 4 bug pho bien khien plan trong nhu rac:

### R1. WALL = AXIS-ALIGNED ONLY

- **Tuong / canh phong / boundary:**
  - Tuong ngang: `y1 == y2` (BAT BUOC)
  - Tuong doc: `x1 == x2` (BAT BUOC)
  - **KHONG BAO GIO** goi `create_line` voi CA `x1 ≠ x2` VA `y1 ≠ y2`.
- **Khi can phong chu nhat:** dung `entity.create_rectangle`, KHONG ve 4 line.
- **Khi can phong da giac:** dung `entity.create_polyline` voi `closed:true`,
  va moi canh trong polyline van phai axis-aligned (consecutive vertex
  share x hoac y).
- **Vi du SAI:**
  ```
  create_line(x1=0, y1=0, x2=5000, y2=4000)  # cheo!
  create_polyline(points=[[0,0],[5000,500],[5500,3000],[1000,3500]])  # cheo!
  ```
- **Vi du DUNG:**
  ```
  create_rectangle(x1=0, y1=0, x2=5000, y2=4000)
  create_polyline(points=[[0,0],[5000,0],[5000,4000],[0,4000]], data={"closed":true})
  ```

**Ngoai le duy nhat:** door swing arc, window break zigzag, north arrow
mui ten, scale bar tick (cac symbol ky thuat). Cac symbol nay dung
`create_arc` hoac polyline rieng, KHONG goi la "wall".

### R2. PRE-TABULATE BEFORE DRAW

**Truoc khi goi tool ve nao,** PHAI output 1 bang toa do day du tat ca
zone / furniture du dinh ve. Format:

```
| name | x1 | y1 | x2 | y2 | center_x | center_y | layer |
|------|----|----|----|----|----------|----------|-------|
| LOUNGE | 0 | 0 | 8000 | 12000 | 4000 | 6000 | CW-ZONE-BOUNDARY |
| PANTRY | 8000 | 0 | 16000 | 12000 | 12000 | 6000 | CW-ZONE-BOUNDARY |
| ... |
```

Sau khi user (hoac ban tu validate) xac nhan bang OK → moi goi tool.
Tool call lay toa do tu bang, KHONG tinh lai.

Lable position = `(center_x, center_y)` LAY TU BANG, khong doan.

### R3. TEXT / UNICODE

- **KHONG dung escape `\uXXXX`** trong tham so `text`.
- Em dash phai la **ky tu "—" that** (Unicode U+2014) hoac `" - "` ASCII
  cho an toan.
- Hyphen va minus la `-` (ASCII). Khong dung `–` (en dash) hay `—` (em dash)
  tru khi user yeu cau ro.
- Title / level mark / room tag: **ASCII safe** la default, dung Unicode
  chi khi co ly do (vd ky tu ngon ngu khac).
- Test: neu chuoi text co `\\u` literal (backslash u) → tu dong replace
  bang ASCII equivalent truoc khi goi.
- **Spell-check truoc khi goi:** read lại tham số `text` 1 lần, kiểm
  typo (LOOP/LCOP, MEETING/MEETNIG, BOARDROOM/BORADROOM). LLM hay
  swap chữ. Đánh máy sai 1 lần là drawing có typo vĩnh viễn.

### R4. NO DEBUG / AUXILIARY LINES

- KHONG ve diagonal "bounding box marker", "axis cross", "centroid leader"
  tren cung drawing voi plan.
- Neu can debug visual, ve len **layer `DEBUG`** rieng, **erase truoc khi
  finish**.
- Sau khi ve xong B7.5, **list layer DEBUG**, neu co entity → erase tat ca
  truoc khi screenshot cuoi.

### R4.5. OSNAP & ANCHOR — biet kha nang corrupt coord cua MCP

**Bug class duoc xac nhan session 2026-05-18:**

#### R4.5.a — entity.create_rectangle bi OSNAP intercept
LISP backend `_RECTANG` command bi OSNAP snap diem ve nearest geometry edge
khi OSNAP active. Vi du gui `(x1=0, y1=12000, x2=8600, y2=18000)` → drawn
`(0, 0)→(16000, 18000)` (snap y1→0, x2→16000 cores wall).

**Fix MCP da apply:** `mcp_dispatch.lsp` line 170 wrap dispatch voi
`(setvar "OSMODE" 0)` + restore. Phai reload LISP trong AutoCAD sau pull:
```
(load "C:/autocad-mcp/lisp-code/mcp_dispatch.lsp")
```

**Workaround skill-side (neu MCP chua reload):** Dung `system.execute_lisp`
voi `entmake` direct, KHONG dung `entity.create_rectangle`:
```lisp
(setvar "OSMODE" 0)
(entmake (list 
  (cons 0 "LWPOLYLINE") (cons 100 "AcDbEntity") (cons 8 "CW-ZONE-BOUNDARY")
  (cons 100 "AcDbPolyline") (cons 90 4) (cons 70 1)
  (list 10 x1 y1) (list 10 x2 y1) (list 10 x2 y2) (list 10 x1 y2)))
```

**BAT BUOC verify sau khi draw batch:** dump vertices bang `execute_lisp`:
```
(princ (entget (handent "<handle>")))
```
Compare actual vertices vs plan bbox. Neu lech > 1mm → fail batch, rollback.

#### R4.5.b — entity.create_mtext anchor TOP-LEFT
MTEXT command bi AutoCAD anchor tai top-left, KHONG center. Text overflow
right & down tu (x,y) cho truoc.

**Fix:** Dung `annotation.create_text` (backend `_TEXT "J" "M"`) — anchor
middle-center tu nhien. Passing `(x,y)` = bbox center → label centered.

```python
# DUNG:
annotation.create_text(x=zone_cx, y=zone_cy, text=name, height=h, layer=L)

# SAI (overflow):
entity.create_mtext(data={x: zone_cx, y: zone_cy, width: w, text: name, height: h}, layer=L)
```

Chi dung `create_mtext` khi can multi-line wrap voi width-controlled box.
Khi do compute top-left = `(cx - text_width/2, cy + text_height/2)`.

### R5. VERIFY CHECKLIST (BAT BUOC TRUOC KHI BAO "DONE")

```
[ ] Goi view.get_screenshot, doc anh quan sat.
[ ] KHONG line cheo la (moi LINE phai x1==x2 hoac y1==y2).
[ ] Moi label nam BEN TRONG rectangle zone tuong ung.
[ ] Title hien thi dung, KHONG co "\u" literal hoac garbled char.
[ ] Layer DEBUG rong (entity.list layer=DEBUG → 0 entity).
[ ] Entity count khop voi expected (= baseline + total assigned trong B6 + B7.5).
[ ] Zoom extents thay full plan, khong leak entity ra ngoai shell bbox > 5000mm.
[ ] KHONG entity stray tai goc (0,0) — UCS marker / X-Y axis indicator
    phai erase (`entity.list` quanh (0,0) ban kinh 500mm).
[ ] Moi text doc lai 1 lan, KHONG typo (LOOP/LCOP, MEETING, BOARDROOM...).
[ ] Hanh lang co BOUNDARY visible + HATCH, khong chi centerline.
[ ] **Dump vertices vs plan** — moi rectangle/polyline drawn, query
    `(princ (entget (handent "HANDLE")))` qua execute_lisp, verify
    coords match plan EXACTLY (tolerance 1mm). OSNAP bug R4.5.a.
[ ] **Label position centered** — labels dung `annotation.create_text`
    (not `create_mtext`), insertion = bbox center. R4.5.b.
```

Fail 1 item → rollback va fix, KHONG bao done.

## PROPOSE TEMPLATE — chuan kien truc su (DỄ NHÌN, không wall-of-text)

Moi propose (circulation / zoning / furniture) PHAI dung template
chuan duoi day. **Khong** trinh bay tuy y, **khong** bullet list lung
tung. Architect chuyen nghiep ALWAYS lam 6 muc nay.

**Format readability checklist (per `feedback_propose_format_easy_read`):**

| Bắt buộc | Cấm |
|---|---|
| ✓ Markdown table cho mọi list ≥3 items | ❌ Paragraph >3 dòng |
| ✓ **Bold** key items (width, area, name) | ❌ Bullet >5 items dày đặc |
| ✓ ✓/❌/⚠ icons cho compliance status | ❌ Numbers inline ("1.4m by 7.2m at 16000...") |
| ✓ Section headers §1-§6 | ❌ Codes không giải thích (29D, BR-W) |
| ✓ ASCII preview/mockup khi compare options | ❌ Wall-of-text reasoning |
| ✓ 1 sentence per row trong table | ❌ Mix paragraph + bullet + table loạn |
| ✓ Câu cuối bold: "**Anh OK hay chỉnh?**" | |

User phải scan được propose <30 giây hiểu hết. Nếu user cần đọc 2 lần → format sai.

```
╔═════════════════════════════════════════════════════════╗
║  [DRAWING ID] — [PHASE NAME]                            ║
╠═════════════════════════════════════════════════════════╣
║  Project:    Coworking Space — <Floor Name>             ║
║  Standard:   CirCO Co-working Spec (reference/circo-... ║
║  Code:       TCVN PCCC <year>                           ║
║  Scale:      1:100                                       ║
║  Date:       <YYYY-MM-DD>                               ║
║  Drawing:    L01 (Circulation) / L02 (Zoning) / L03... ║
╚═════════════════════════════════════════════════════════╝

§1. DESIGN INTENT (1-2 cau)
    "Ring loop ket noi 2 cua + Branch phu vao private cluster."

§2. COMPLIANCE MATRIX (mandatory table)
    | Spec                | Standard      | Proposed | Status |
    | Hành lang chính     | CirCO 1.5-1.8m | 1.5m     | ✓ PASS |
    | Hành lang nội bộ    | CirCO ≥1.2m    | 1.2m     | ✓ PASS |
    | Branch width (phụ)  | CirCO ≥1.2m   | 1.2m     | ✓ PASS |
    | Closed loop         | CirCO 100%    | YES      | ✓ PASS |
    | Travel max          | PCCC ≤25m     | 21m      | ✓ PASS |
    | 2-exit egress       | PCCC          | YES      | ✓ PASS |

§3. SCHEDULE OF ELEMENTS (table — moi entity 1 row)
    | ID | Type    | Bbox (x1,y1→x2,y2) | W×L     | Area  | Layer        |
    | C1 | Strip-S | (14000,4000→32000,5400) | 18×1.4m | 25.2m² | CW-CIRCULATION|
    ...

§3.4. GAP AUDIT (BAT BUOC cho L02 zoning, tránh miss area)

Trước khi finalize §3 schedule, PHẢI làm gap audit:

1. **List ALL existing corridor bboxes** (CW-CIRC-GUIDE entities + L5 L-shape):
   ```
   query: (ssget "X" '((8 . "CW-CIRC-GUIDE")))
   ```

2. **Compute usable_total** = shell - cores - corridors

3. **Tabulate ALL proposed zones** với bbox:
   ```
   | zone | x1 | y1 | x2 | y2 | area |
   ```

4. **Compute zone_total** = sum of proposed zone areas

5. **GAP CHECK** = usable_total - zone_total. NẾU > 5% (or any gap > 10m²):
   → Identify gap location (typically: lobby bands Y=18000-20000, narrow strips
   giữa corridors, areas south/east of ring not covered)
   → ADD new zone for each gap (LNGE-N lobby band, LNGE-E east band, etc.)
   → Hoặc extend nearest existing zone

6. **List gaps in §3.4 output**:
   ```
   | Gap | Coords | Area | Fix |
   ```

**Lesson:** Gap audit PHẢI run TRƯỚC §3 schedule. Không sau khi user complain.

**MANDATORY ZONE-CORRIDOR OVERLAP CHECK** (sau mỗi extend zone):

Khi extend zone (vd extend HDSK-E từ Y=10600 → Y=12000 để fill gap), PHẢI check overlap với corridor:
```
for corridor in CW-CIRC-GUIDE:
  for zone in proposed_zones:
    if bbox_overlap_interior(zone, corridor) > 0:
      → zone phải L-shape (6+ vertex) né corridor, KHÔNG rectangle simple
```

**Fix:** Khi extend zone vào corner near corridor → dùng L-shape polygon né corridor. Vi du:
```
(31400, 5400) → (42000, 5400) → (42000, 12000) → (32000, 12000) → (32000, 10600) → (31400, 10600)
```

Khi extend zone vào area sát corridor → ALWAYS L-shape, không rectangle.

**MANDATORY 4-CORNER + EDGE CHECK** (sau mỗi zone change):
- Corner NW: (0, shell_max_y)→core_west_edge
- Corner NE: chamfer area → end of east shell
- Corner SW: (0,0)→west_zone_min
- Corner SE: (east_zone_max, 0)→(shell_max_x, ring_bottom_y)
- Edge N (lobby band): (0, internal_wall_y)→(shell_max_x, cores_wall_y)
- Edge S (below ring): (0,0)→(shell_max_x, ring_min_y)
- Edge W (west of ring): (0, ring_min_y)→(ring_left_edge, ring_max_y)
- Edge E (east of ring): (ring_right_edge, ring_min_y)→(shell_max_x, ring_max_y)

→ EACH check explicitly trong §3.4 propose output, KHÔNG skip.

§4. VALIDATION (check list, moi item 1 dong)
    ✓ Pairwise overlap: pass
    ✓ Door reach: LOBBY → door 29D gap 100mm (within 200mm tol)
    ✓ Label placement: all in strip (not in void)
    ⚠ <warn neu co>

§5. TOTAL ENTITIES (rieng dong nay)
    8 polylines + 8 hatches + 5 labels = **21 entities**

§6. NEXT ACTION
    Anh prompt `vẽ` de execute / `chỉnh <X>` de điều chỉnh.
```

**Quan trong:** truoc khi propose, **PHAI doc `reference/circo-standard.md`**
de lay so chuan (1.5-1.8m hành lang chính, 1.2m hành lang nội bộ per R-C2, 700-800 pullout, 900 internal aisle...).
Khong tu invent so.

## When to use

Trigger khi user nhac: "coworking", "mat bang", "layout", "bo tri khu vuc",
"phan khu", "ve AutoCAD", "hot desk", "phone booth", "meeting room", hoac
gui kich thuoc / dien tich san.

Khong dung skill nay cho P&ID, MEP, ket cau — do la domain khac.

## Tool surface

7 consolidated tools dung trong coworking (bo qua `pid`). Param shape KHAC
NHAU giua cac tool — xem `reference/mcp-tools.md` cho signature day du.
Tom tat:

| Tool | Khi nao dung | Param shape |
|---|---|---|
| `autocad-mcp__system` | Probe trang thai, runtime diag, execute_lisp khi can workaround | `operation, data?` |
| `autocad-mcp__drawing` | File mgmt: info / save / open / undo / get_variables | `operation, data?` |
| `autocad-mcp__layer` | Tao / set_current / freeze / lock layer | `operation, data?` |
| `autocad-mcp__entity` | **Tat ca thao tac ve hinh** — create / read / modify | `operation, x1/y1/x2/y2/points/layer/entity_id` (top-level) + `data` |
| `autocad-mcp__block` | List / insert block + attributes | `operation, data?` |
| `autocad-mcp__annotation` | Text + dimension + leader | `operation, data?` |
| `autocad-mcp__view` | zoom + screenshot | `operation, x1/y1/x2/y2` (top-level, **khong** co `data`) |

**Quan trong:** `entity.*` la tool **duy nhat** co param top-level
(`x1/y1/x2/y2, points, layer, entity_id`). Tat ca tool khac (tru `view`)
gom moi field vao `data`. Sai shape → server tra "Entity not found" hoac
KeyError.

Xem `reference/mcp-tools.md` cho operation enum + input + output + khi
nao dung tung op.

## Param shape cheatsheet (CHECK TRUOC KHI GOI)

Goi sai shape se ton 1 turn de retry. Lookup nhanh truoc khi call:

| Op | Shape dung | Vi du |
|---|---|---|
| `entity.create_rectangle` | top-level: `x1, y1, x2, y2, layer` | `entity(operation="create_rectangle", x1=1000, y1=1000, x2=2400, y2=1700, layer="F-DESK")` |
| `entity.create_line` | top-level: `x1, y1, x2, y2, layer` | giong rectangle |
| `entity.create_circle` | top-level: `layer`; **`data: {cx, cy, radius}`** | `entity(operation="create_circle", layer="F-CHAIR", data={"cx":10000,"cy":5000,"radius":500})` |
| `entity.create_polyline` | top-level: `points, layer`; `data: {closed?}` | `entity(operation="create_polyline", points=[[x,y],...], layer="L", data={"closed":true})` |
| `entity.create_arc/ellipse` | top-level: `layer`; **`data: {cx, cy, ...}`** | giong circle |
| `entity.create_mtext` | top-level: `layer`; **`data: {x, y, width, text, height?}`** | |
| `entity.array/copy/move/rotate/scale` | top-level: `entity_id`; `data: {...params}` | `entity(operation="array", entity_id="2A5", data={"rows":2,"cols":2,"row_dist":1300,"col_dist":2000})` |
| `entity.mirror` | top-level: `entity_id, x1, y1, x2, y2` | line truc soi guong la top-level |
| `view.*` | top-level: `x1, y1, x2, y2` (KHONG `data`) | `view(operation="zoom_window", x1=0,y1=0,x2=20000,y2=15000)` |
| `drawing/layer/block/annotation/system` | top-level: `operation`; con lai trong `data` | |

**Memo:** chi `entity.*` (tru ops dung `data` o tren) va `view.*` co toa do top-level.

## Quick draw mode (BO QUA propose-first khi user da cho coord cu the)

Khi user noi ro toa do + kich thuoc + layer (vd: "ve hinh chu nhat 1400x700 tai
(1000,1000) layer F-DESK") → **GOI TOOL NGAY**, KHONG probe, KHONG list,
KHONG propose. 1 tin nhan = 1 cau lenh = 1 tool call (toi da 2 neu cu phai
combo nhu set_current layer + create).

Trigger phrase quick draw: "ve [shape] tai (...)", "tao [shape] o (...)",
"add [shape] vi tri (...)", "draw [shape] at (...)".

Bo qua quick draw va dung workflow day du (B0 → B7) khi user noi:
- "lam mat bang", "thiet ke layout", "phan khu", "bo tri coworking"
- Khong cho coord cu the, chi cho rang buoc (vd "20m x 15m, 30 cho")

## Batch & retry rules (tranh timeout)

- **Batch tool call ≤ 2/turn** khi provider cham (rockship-gateway/auto).
  Vd: ve 4 desk → chia 2 turn (2 desk/turn). Tot hon: dung
  `entity.array` 1 lan thay vi goi 4 lan create_rectangle.
- **Khong probe lai sau khi vua probe** trong cung session — tin context co san.
- **Backend reset / timeout giua chung**: KHONG tu reload lisp. Bao user
  retry, hoac tiep tuc tu entity con thieu (kiem tra handle cuoi cung
  da tao thanh cong). LISP load 1 lan dung ca session AutoCAD.

## Buoc 0 — Probe trang thai & ban ve hien tai (LAM TRUOC TIEN)

```
autocad-mcp__system(operation="status")
autocad-mcp__drawing(operation="info")
autocad-mcp__entity(operation="list")
autocad-mcp__view(operation="get_screenshot")
```

**Kiem tra `system.status`:**

- `backend: "file_ipc"` + `autocad_running: true` + `doc_count > 0` → OK.
- `autocad_running: false` → bao user mo AutoCAD roi thu lai.
- `autocad_running: true` nhung `doc_count: 0` → bao user mo / tao 1 ban ve.
- Truong hop khac (status loi, backend la khac, MCP khong phan hoi): khong tu
  fix — bao user va goi y verify bang `mcporter list autocad-mcp` / `openclaw logs`.

**Doc `drawing.info`:**

- `entity_count > 0` → tom tat hien trang (kich thuoc tong, vi tri tuong/cua
  doc duoc) cho user xac nhan, **khong hoi lai** thong tin da co. Layer co
  san **chi de tham chieu** — khi ve moi luon dung bo layer chuan rieng cua
  skill (xem B2 va `reference/layers.md`).
- `entity_count: 0` → moi hoi kien truc su:
  - Dien tich va hinh dang san (vd 20m x 15m chu nhat).
  - Huong (cua so, cua chinh).
  - Suc chua muc tieu (so cho ngoi).
  - Ty le hot desk / dedicated / meeting / phone / lounge.
  - Rang buoc khac (cot, WC co san, ngan sach noi that...).

**Hieu nang:** server chay persistent (khong spawn process moi call).
File-IPC overhead ~10-50ms/op. Loop hang tram call OK; van uu tien
`entity.array` cho ro nghia ban ve hon la cho perf.

## Nguyen tac vang: 3 EXCELLENT PLANS (no mid-flow questions)

**Quy tac cot loi (UPDATED 2026-05-19):**

**Tu lan dau propose, skill PHAI dua ra 3 plan HOAN CHINH + EXCELLENT,
KHONG hoi user sub-question giua flow.**

Vi du SAI:
> "Travel distance HDSK East 39m. Xu ly the nao? Option A limit / Option B accept / Option C add exit"
> → Day la sub-question giua flow. User feedback 2026-05-19: "tu luc dau ban
>    phai dua ra 1 plan cuc chuan luon".

Vi du DUNG:
> "L02 propose 3 PA:
>  - PA1: HDSK East limited X≤34000 (fit 25m PCCC), corner = Quiet Library
>  - PA2: HDSK East full + design exception note, Hot Desk East 88m²
>  - PA3: HDSK East split + add exit symbol (require permit note)
>  All 3 plans complete, user pick."

**Quy tac:**
1. **Pre-validate ALL options TRƯỚC propose** — col collision, closed loop,
   width, travel, door swing, edge connectivity, furniture grid arithmetic.
   Neu fail → fix internally hoac chon other coord, KHONG hoi user.
2. **3 options la 3 plan FULL** — moi option co bbox cu the cho moi zone,
   moi corridor, da tinh travel distance, da check column collision.
3. **Auto-apply defaults** cho moi decision nho:
   - Door direction: auto-guess (double_door=main bidir, swing on shell=exit), **show trong propose §2 cho user confirm/chỉnh — KHÔNG hỏi blank**
   - Travel exception: auto-shrink zone (default Option A) hoac note
   - Corridor placement: auto-midpoint cells
   - Furniture size: CirCO standard (1200×600 hot, 1400×600 dedi, 1000×1000 booth)
4. **KHONG hoi user choice midway** — present 3 plans, user pick. Neu user
   muon adjust → "chinh X" → re-gen 3 plans.

---

Moi step major (L01 Circulation / L02 Zoning / L03 Furniture) PHAI tuan
theo workflow **3-OPTIONS + DRAW-VISIBLE**:

```
1. PROPOSE 3 OPTIONS (A / B / C) — khac biet ro rang ve triet ly thiet ke
   - Khong propose 1 option roi cho user accept/reject — user khong co
     reference de quyet
   - 3 options trinh bay song song, table compare, design intent rieng cho
     moi option

2. USER CHỌN (1 / 2 / 3) hoac CHỈNH option nao do
   - Neu user "chinh X" → re-propose option do voi adjustment (giu 2 cai
     con lai hoac re-gen ca 3)

3. USER GỌI VẼ → DRAW VISIBLE
   - LUON entmake polyline + hatch/dashed line cho user THẤY THẬT SỰ
   - KHONG dung "negative space invisible" - corridor phai visible khi
     vẽ
   - Layer rieng: CW-CIRC-GUIDE (DASHED color 8) cho L01, CW-ZONE-BOUNDARY
     cho L02, CW-FURN-* cho L03
   - Sau khi draw, freeze layer guide neu can clean view o step cuoi

4. USER OK → TIẾP step ke / CHỈNH → iterate
   - User "ok" / "tiep" / "step 2" → proceed
   - User "chinh X" → erase drawn entities cua step nay, re-propose
```

**Tại sao 3 options:**
Session 2026-05-18 user feedback: "lúc bạn đưa ra propose ngta cũng ko hiểu
gì". Khi chi co 1 proposal, user khong co frame of reference - khong biet
"day la tot/te so voi cai khac". 3 options voi triet ly khac (Open-flex /
Quiet-focus / Collab-heavy o L02; Central-courtyard / Spine-branches /
Perimeter-loop o L01) cho user **compare**, decide based on use case.

**Tại sao DRAW VISIBLE:**
User feedback: "lúc này nó đang tàng hình". Negative space approach tot
ve mat data (khong duplicate edge) nhung TE ve UX (user khong thay duoc
corridor). Phai draw visible khi user gõ vẽ, có thể freeze sau.

---

**Khong bao gio ve het zone + noi that ngay tu dau** (tru khi kien truc su
yeu cau ro "ve luon di"). Quy trinh la **4 vong propose → confirm → execute**:

1. **Survey hinh hoc** (extract shell/core/cot, tinh usable region) — B2.5.
2. **Propose CIRCULATION LOOP** (trục chính ≥1400mm, trục phụ ≥1200mm per R-C2, STRAIGHT ONLY per R-C3, closed loop ring, không hành lang cụt) → cho confirm — B2.7.
3. **Propose zone planning** dua tren usable region + loop (text + bbox)
   → cho confirm — B3.
4. **Validate zones** bang helper geometry truoc khi ve — B3.5.
5. **Ve loop + zone len ban ve** sau khi validate `ok: true` — B4.
6. **Propose ke hoach noi that** cho moi zone → cho confirm — B5.
7. **Ve noi that** sau khi chot — B6.
8. **Annotation + finishing** (dimension, north arrow, scale, title block) — B7+B7.5.

**Quan trong:**
- Khong bao gio doan toa do zone tu khong khi. Toa do moi polyline ZONE
  phai duoc tinh tu `usable_polygon` cua helper, snap vao grid cot neu co.
- **Circulation loop la khung xuong (skeleton) — design TRUOC zone.**
  Zone fill vao khoang giua loop, KHONG cat ngang loop.
- Xem `reference/geometry.md`.

## Workflow (B0 → B7) — chi tiet o `playbooks/workflow.md`

**🔴 BAT BUOC doc `playbooks/workflow.md` TRUOC KHI VE.** File do chua full quy
trinh 9 buoc, khong duoc bo qua:

- **B0** Probe trang thai + load chuan CirCO
- **B1** Hieu hien trang & yeu cau
- **B2** Setup layer + **B2.5 DEEP SURVEY** (cot/cua/tuong) + **B2.7 propose circulation 3 options**
- **B3** Propose zone 3 options + **B3.5 validate bang helper** + **B3.7 CirCO zone pattern**
- **B4** Ve zone + **B4.5 corridor hatch cleanup**
- **B5** Propose noi that + **B6** ve noi that + **B6.5 OVERKILL**
- **B7** Annotation & ra soat

Construction-ready (B7.6-B7.12) → muc duoi + `reference/construction-ready.md`.

## B7 finishing & CONSTRUCTION-READY — chi tiet o `playbooks/workflow.md`

**🔴 GATING (nho ky):** MAC DINH demo/concept → **STOP ngay sau B7.5**.
KHONG chay B7.6-B7.12 tru khi user noi ro "construction drawing" / "building
permit" / "TCVN compliance" / "production-ready".

- **B7.5 finishing (LUON lam)**: hatch zone/core, north arrow, scale bar, title
  block, column grid labels, schedule legend → chi tiet trong `playbooks/workflow.md`.
- **B7.6-B7.12 (chi khi construction)**: xem `reference/construction-ready.md`
  (dimensions, wall thickness, fire egress, line weight, door schedule, accessibility).

## Layer color & lineweight hierarchy

Plan trong dep nho **trat tu thi giac** (hierarchy). Set color per layer:

| Group | Layer | Color (ACI) | Lineweight | Note |
|---|---|---|---|---|
| Shell | A-WALL | 7 (white/black) | 0.50 | Day, dam |
| Shell | A-COLUMN | 7 + HATCH | 0.50 | Cot solid hatch |
| Shell | A-DOOR | 4 (cyan) | 0.18 | Mong |
| Shell | A-WINDOW | 4 | 0.13 | Mong nhat |
| Core | A-TOIL / A-ELEV / A-STAIR | 8 (gray) | 0.25 | Vua |
| Corridor | CW-CIRC-HATCH | **8 (dark gray)** | n/a | DOTS pattern non-associative |
| Corridor | CW-CIRC-LABEL | **7 (white)** ← MUST contrast vs 8 hatch | text | L1/L2... names |
| Zone | CW-ZONE-BOUNDARY | 1 (red) | 0.35 | Trung binh dam |
| Zone | CW-ZONE-HATCH | 4 (cyan) | 0.13 | Mong, transparency 70% |
| Zone | CW-ZONE-LABEL | 4 (cyan) ← contrast vs 1 red boundary | text | Height 400-600 |
| Furniture | F-DESK / F-TABLE / F-CABINET | 5 (blue) | 0.18 | Mong |
| Furniture | F-CHAIR / F-SOFA / F-BOOTH | 3 (green) | 0.15 | Mong nhat |
| Annotation | CW-DIMENSION | 7 | 0.13 | Nhat nhat |
| Annotation | CW-ANNOTATION (title) | 1 | text | Height 800-900 |

**CRITICAL — Label color PHẢI contrast với layer fill nó nằm trên (per [[layer-color-contrast]]):**
- ❌ CW-CIRC-LABEL color 8 trên CW-CIRC-HATCH color 8 → blend, không đọc được
- ✓ CW-CIRC-LABEL color 7 (white) trên CW-CIRC-HATCH 8 (gray) → contrast

**LISP command set layer color (works):**
```lisp
(command "_-LAYER" "_COLOR" "7" "CW-CIRC-LABEL" "")
```

**KHÔNG dùng `entmod` để change layer color** — silent fail, color không update.

Set bang `layer(operation="create"/"update", data={"name":..,"color":..,
"lineweight":..})`. Neu provider chua support `lineweight`, set color
truoc, lineweight bo qua (AutoCAD default).

## Symbol convention (top-down plan view)

De tranh nguoi review hieu nham ("vong tron xanh la sensor!"):

| Ky hieu | Y nghia | Kich thuoc chuan |
|---|---|---|
| Rectangle 1200×600 / 1400×600 (F-DESK) | Hot desk single (CirCO) | 1200-1400 × 600 mm |
| Rectangle 1400×700 (F-DESK) | Hot desk standard (BCO) | 1400 × 700 mm |
| Rectangle 1600×800 (F-DESK) | Dedicated desk premium | 1600 × 800 mm |
| Circle r=250-300 (F-CHAIR) | Ghe ngoi (top-down) | 250-300 mm radius |
| Rectangle 2200×1200 (F-TABLE) | Ban hop 6-8 nguoi | 2200 × 1200 mm |
| Rectangle 2200-3000 × 850 (F-SOFA) | Sofa 2-3 cho | 850 mm depth |
| Rectangle 600×600 / 800×800 (F-TABLE) | Ban cafe / phu | 600-800 mm |
| Rectangle 4000-5000 × 600 (F-CABINET) | Bar counter / quay | 600 mm depth |
| Circle r=350-400 (F-CHAIR) | Ghe lounge / armchair | 350-400 mm radius |
| Polyline phone booth 1000×1000 (F-BOOTH) | Phone booth (CirCO chuan) | 1000 × 1000 mm |
| Polyline phone booth 1200×1200 (F-BOOTH) | Phone booth lon | 1200 × 1200 mm |

Khi user / reviewer hoi "vong tron / hinh chu nhat la gi", giai thich
bang bang nay. **KHONG noi day la sensor / anchor / IoT diem** tru khi
user da yeu cau cu the cho design IoT.

## Tool call recipes

```
# Probe
autocad-mcp__system(operation="status")
autocad-mcp__drawing(operation="info")
autocad-mcp__entity(operation="list", layer="A-WALL")           # layer top-level

# Setup bo layer
autocad-mcp__layer(operation="list")
autocad-mcp__layer(operation="create", data={"name": "CW-ZONE-BOUNDARY", "color": 1})
autocad-mcp__layer(operation="set_current", data={"name": "CW-ZONE-BOUNDARY"})

# Outline san — x1/y1/x2/y2/layer la TOP-LEVEL, KHONG nam trong data
autocad-mcp__entity(operation="create_rectangle",
                    x1=0, y1=0, x2=20000, y2=15000, layer="A-WALL")

# Khu meeting (polyline kin) — points & layer top-level, closed nam trong data
autocad-mcp__entity(operation="create_polyline",
                    points=[[12000,8000],[16000,8000],[16000,12000],[12000,12000]],
                    layer="CW-ZONE-BOUNDARY",
                    data={"closed": true})

# Day hot desk: ban mau roi array
autocad-mcp__entity(operation="create_rectangle",
                    x1=1000, y1=1000, x2=2400, y2=1700, layer="F-DESK")
# → {"ok": true, "handle": "<H>", ...}
autocad-mcp__entity(operation="array",
                    entity_id="<H>",
                    data={"rows": 2, "cols": 5, "row_dist": 1500, "col_dist": 1600})
# Hoac: entity_id="last" tham chieu entity vua tao.

# Dimension loi di — KHONG co param layer; set_current truoc neu can
autocad-mcp__layer(operation="set_current", data={"name": "CW-DIMENSION"})
autocad-mcp__annotation(operation="create_dimension_linear", data={
  "x1": 5000, "y1": 1000, "x2": 5000, "y2": 14000,
  "dim_x": 4500, "dim_y": 7500
})

# Snapshot — view tool KHONG co param data
autocad-mcp__view(operation="zoom_extents")
autocad-mcp__view(operation="get_screenshot")
```

JSON arguments di qua MCP transport binh thuong — **khong can** escape `\"`,
khong can heredoc workaround nhu CLI cu.

## Defaults & conventions

- Don vi: **mm**. World view, truc Y len.
- Goc 0,0 dat tai goc duoi ben trai san.
- Layer naming: xem `reference/layers.md`.
- Kich thuoc tham chieu: xem `reference/standards.md`.
- Screenshot: `view(operation="get_screenshot")` tra ve **inline image** qua
  MCP transport, khong nhan param path. Bot client tu render — khong can
  doc file disk.

## Safety / red lines

- **Khong tu save / xuat ban ve** tru khi user yeu cau ro rang. Khi user
  yeu cau, dung `drawing.save` / `save_as_dxf` / `plot_pdf` minh bach.
- Truoc thao tac pha huy / blast-radius lon: **confirm voi user truoc**.
  - `drawing(operation="create")` — reset doc hien tai (erase all + purge).
  - `drawing(operation="purge")` — xoa unused objects.
  - `entity(operation="erase")` hang loat (>5 entities cung 1 lan).
  - `layer(operation="freeze" / "lock")` lop chua entity quan trong.
  - `system(operation="execute_lisp")` — chay AutoLISP tuy y, khong sandbox.
    Chi dung khi user yeu cau ro va da review code.
- Khi rang buoc bat kha thi (vd suc chua 60 nguoi tren 80m2): noi thang,
  de xuat trade-off, khong am tham bop ty le.

## Failure modes

| Trieu chung                                           | Nguyen nhan                           | Xu ly                                                                                                          |
| ----------------------------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Tools `autocad-mcp__*` khong xuat hien                | MCP server chua san sang               | `mcporter list autocad-mcp` → `openclaw gateway restart` neu thieu.                                            |
| `system.status` bao backend la gia tri khac           | Server chua bootstrap day du           | `openclaw logs` de check; bao user, **khong** sua source MCP.                                                  |
| `system.status` -> `autocad_running: false`           | AutoCAD chua chay                      | Bao user mo AutoCAD LT 2024+.                                                                                  |
| `doc_count: 0`                                        | AutoCAD chay nhung khong co ban ve mo | Bao user mo / tao file.                                                                                        |
| `drawing.info` `ok: false` voi "No active drawing"    | Doc dong giua chung                   | User mo lai.                                                                                                   |
| Output JSON `ok: false, error: "..."` voi IPC timeout | AutoCAD modal dialog block            | User press ESC, thu lai.                                                                                       |
| `error: "No entity with handle 'XXX'"`                | Handle sai / entity bi xoa            | `entity(operation="list")` lay handle moi.                                                                     |
| Screenshot `ok: false` hoac file rong                 | PNGOUT timeout / dialog               | User press ESC, thu lai.                                                                                       |

## File phu trong skill nay

- `reference/mcp-tools.md` — dac ta day du **7 MCP tools** (op + input + output + khi nao dung).
- `reference/geometry.md` — pipeline survey + tinh usable region + validate zones.
- `playbooks/zoning.md` — chi tiet phan khu coworking.
- `playbooks/furnishing.md` — pattern dat noi that.
- `reference/standards.md` — bang kich thuoc & khoang cach.
- `reference/layers.md` — chuan layer naming + color.
- `scripts/layout.py` — helper hinh hoc (shapely) cho `compute_usable` + `validate_zones`.

Doc cac file nay khi can chi tiet, khong load san vao moi turn.

### R-SURVEY. Map 4 bounding walls TRƯỚC khi vẽ room (không đoán theo bbox)

**Bug tái phạm (session 2026-05-23):** Vẽ MEET-2 với step Y=-61059 tại X=64187 vì tưởng WC kéo dài tới X=64187 (theo INSERT bbox). Thực tế WC south wall chỉ tới X=63637. → north wall overlap sai.

**Root cause:** bbox của cluster (WC/cores) ≠ vị trí wall thật. Fixtures (xí, bồn) protrude ngoài wall → bbox lớn hơn wall.

**Rule (mandatory trước mỗi room draw):**
1. Query **4 bounding walls riêng biệt** (N/S/E/W) bằng `ssget _C window` + filter LINE
2. Phân biệt HORIZONTAL walls (Y giống nhau) vs VERTICAL walls (X giống nhau)
3. Lấy **EXACT wall coords**, KHÔNG dùng cluster bbox
4. Room edge = wall face thật, verify từng cạnh
5. Nếu có obstacle giữa (stair, column) → polygon né obstacle, query obstacle exact extent

**Vd CIRCO NKKN MEET-2:**
- ❌ Đoán: WC tới X=64187 (bbox) → step sai
- ✓ Survey: WC south wall Y=-61059 chỉ X=59287-63637 → đông X=63637 mở, rectangle phẳng
- ✓ Stair X=65426-67587 chiếm Y=-58659 to -60359 → room north edge = Y=-60359 (stair bottom)

### R-STAIR. Cầu thang thoát hiểm — tận dụng được, GIỮ egress thông

**Detection — nhận biết cầu thang:**
- Nhiều vertical LINE cách đều ~250-300mm (stair treads) trong vùng nhỏ; HOẶC layer "Cau thang"
- Query: vùng có ≥5 parallel lines spacing ~250mm → STAIR

**Rule (mentor 2026-06-24): "tận dụng được, miễn lối thoát hiểm thông với nhau":**
1. Identify egress path: cầu thang bottom → main corridor. Path ≥1.2m, KHÔNG bị chặn
2. Phần CÒN LẠI của stair lobby (flank, không nằm trên egress) → tận dụng làm zone nhỏ (phone booth, storage, focus)
3. Verify: stair + door thoát hiểm + main corridor = chuỗi thông liên tục

**Right pattern (CIRCO NKKN):**
- Egress strip giữ thông (cầu thang + door → L1)
- FOCUS/BOOTH ở flank — tận dụng, không chặn egress

**Anti-pattern:**
- ❌ Đặt phòng CHẶN egress (chân cầu thang đụng tường = vi phạm PCCC)
- ❌ Bỏ TRỐNG hoàn toàn stair lobby (lãng phí — quá conservative)

### R-EGRESS-MIN. Egress clearance = TỐI THIỂU trước cửa thoát hiểm (mentor 2026-06-24)

**User feedback:** "chỉ để chừa vừa đủ trước cái cửa vàng ... còn để nhiều space quá"

**Rule:** Egress circulation chỉ chừa clearance **TỐI THIỂU** (~1.4-1.6m) trước cửa thoát hiểm (yellow door = cuadi layer color 2), KHÔNG để cả vùng lớn làm egress.

**Detection cửa thoát hiểm:** INSERT trên layer "cuadi" (color 2 = vàng), gần cầu thang/stair lobby.

**Workflow:**
1. Find yellow egress door (cuadi, color 2) bbox
2. Egress strip = door width + ~0.7m clearance mỗi bên, từ door đến main corridor
3. Phần CÒN LẠI của stair lobby → room (Focus/Meeting/Booth)

**Right pattern (CIRCO NKKN):**
- Cửa vàng *U16 X=67737-68637 → egress strip chỉ X=67500-69137 (1.64m)
- FOCUS Room 10m² (X=64187-67500) chiếm phần lớn khu đỏ

**Anti-pattern:**
- ❌ Egress chiếm cả 3.7m (X=65426-69137) khi cửa chỉ rộng 0.9m → lãng phí
