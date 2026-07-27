# Playbook: WORKFLOW B0 → B7 (quy trinh ve day du)

> Tach tu SKILL.md de giu SKILL gon. **Doc file nay TRUOC KHI VE.**
> Moi rule / con so / ghi chu session giu NGUYEN VAN, khong doi.

## Workflow

### B0.5. Load tiêu chuẩn CirCO + Confirm

Load `reference/circo-standard.md` → show user bảng tiêu chuẩn chính (mật độ, VP riêng %, hành lang, tiện ích) → confirm trước khi vẽ.

### B1. Hieu hien trang & yeu cau

**Site context (HOI USER neu chua biet):**
- Huong: cua so chinh hoac mat dai voi cua so o canh nao? (Bac/Nam/Dong/Tay)
- View: nhin ra gi? (cong vien / pho / building khac)
- Tang so may? (anh huong egress travel distance + acoustic neighbor)
- Loai building: van phong / nha pho / shophouse / warehouse convert?
- Co sprinkler khong? (egress travel limit khac giua sprinklered vs non)
- Building code: IBC US / EU / VN TCVN? (anh huong corridor width, exit count)

Daylight rule: priority dat hot desk / dedicated trong vong **7.5m tu cua so**.
Phone booth / quiet room ngoai hoac canh tuong khong cua so. Lounge dau tien
khi vao = gan loi vao chinh.

Tu Buoc 0. Chot rang buoc thanh 1 doan ngan, xac nhan voi user truoc khi ve.

### B2. Setup bo layer chuan cua skill

**Luon tao bo layer rieng** theo `reference/layers.md`, **khong reuse**
layer co san trong file user (de giu nhat quan giua cac session/du an, va
de user freeze/isolate rieng phan skill ve). Goi `layer(operation="list")`
truoc → so sanh; layer nao thieu thi `layer(operation="create", ...)`. Goi
`layer(operation="set_current", ...)` truoc moi nhom thao tac.

### B2.5. Survey hinh hoc — **DEEP SURVEY truoc khi propose**

**9 buoc BAT BUOC tinh xong moi propose corridor / zone. Bo qua = 9 issue
nhu lan demo truoc (overlap cot, dam tuong, bo cua thoat...).**

Xem chi tiet `reference/geometry.md`. Tom tat:

1. `entity(operation="list")` → tra ve `[{type, handle, layer}, ...]`
   (KHONG co toa do). Phan loai entity thanh shell / core
   (WC/ELEV/STAIR) / cot dua tren type + layer.

   Voi tung handle can lay toa do cu the:
   `entity(operation="get", entity_id=H)` (luu y `entity_id` la **top-level**,
   khong gom trong `data`).

   **Han che server (KHONG phai loi backend):** `entity.get` chi tra toa do
   cho `LINE` va `CIRCLE`. Voi `LWPOLYLINE` (rectangle, polyline tuong/zone),
   `MTEXT`, `INSERT` block, `ARC`, `ELLIPSE`, `HATCH` → server chi tra
   `{type, handle, layer}` — **DAY LA BEHAVIOR BINH THUONG, KHONG suy luan
   "backend reset" hoac "lisp chua load"**. Neu `entity.list` work → backend
   van OK. Neu `entity.get` thieu coord cho mot trong cac type tren → KHONG
   reload lisp, KHONG goi system.execute_lisp de "self-load".

   Khi can vertex cua LWPOLYLINE: dung workaround `system.execute_lisp`
   doc DXF group code 10 (xem `reference/mcp-tools.md`), HOAC don gian hon
   la **hoi user nhap kich thuoc / toa do** roi feed thang vao layout.py.
2. Pipe payload JSON vao helper `scripts/layout.py` mode `compute_usable`:

```bash
python3 skills/autocad-coworking/scripts/layout.py <<'JSON'
{"mode":"compute_usable","shell":[...],"obstacles":[...],"columns":[...],"column_buffer":300}
JSON
```

3. Luu lai `usable_polygon`, `usable_area_m2`, `bbox` tu output. Day la
   con so chinh xac de tinh ty le tung zone — **khong dung dien tich shell
   tho** vi se sai.

4. **Extract door coordinates + AUTO-CLASSIFY direction** — entrance + exit khan cap:
   ```
   entity.list layer="A-DOOR" → INSERT handles
   for each handle H:
     system.execute_lisp:
       (princ (cons (cdr (assoc 2 e))     ; block name (swing_door / double_door / sliding_door)
                    (cdr (assoc 10 e))    ; insert point
                    (cdr (assoc 50 e))))  ; rotation angle radians
   ```

   **AUTO-GUESS rule (KHÔNG hỏi blank — em đoán + show trong propose cho user confirm):**

   | Block name | Default classification | Reason |
   |---|---|---|
   | `double_door` (≥1800mm wide) | **MAIN ENTRANCE bidirectional** | Cua to nhat, 2 chieu, member daily traffic |
   | `swing_door` near edge wall (Y=0, Y=max, X=0, X=max) | **EMERGENCY EXIT exit-only** | PCCC khan cap, panic bar, 1 chieu OUT |
   | `swing_door` interior (between zones) | **INTERNAL door bidirectional** | Trong nha, between rooms |
   | `sliding_door` | **INTERNAL phong nho** | Tiet kiem khong gian, between rooms < 10m² |
   | Single door 800-900mm at building wall | **SECONDARY ENTRANCE bidirectional** | Cua phu |

   **Note rule:** Mọi shell wall = ngoai building (boundary cua usable polygon). Door
   tren shell wall + width >= 1800mm → main entrance. Door tren shell + width
   < 1800mm + xa main entrance > 5m → emergency exit.

   **In propose (template L01) §2 PHAI show classification + HỎI confirm:**

   ```
   §2. DOORS (em đoán — anh confirm/chỉnh):
   | Handle | Name | Coord | Width | Em đoán | Lý do |
   | 29D | double_door | (16000, 19900) | 1800 | Main Entrance bi-dir | Cửa 2 lá rộng, trục chính, daily traffic |
   | 29E | swing_door | (9800, 18000) | 900 | Emergency Exit | Cửa 1 lá nhỏ, edge wall, PCCC egress |
   
   → **Anh OK 2 cái này hay chỉnh?** Vd: "29E là entrance" → em re-design BR-W.
   ```

   **KHÔNG hỏi blank "cửa nào vào, cửa nào ra"** — em đoán trước, show reasoning, user confirm/chỉnh.

   **PCCC: PHAI co ≥2 exit. Loop circulation PHAI noi MAIN ENTRANCE + EXIT
   KHẨN, KHONG bo cua thoat.**

5. **Survey COLUMN GRID** — KHONG dat corridor xuyen cot:
   ```
   entity.list layer="A-COLUMN" → 18 HATCH handles
   for each: system.execute_lisp lay BOUNDARY vertex
   ```
   Tinh column grid (vd 8m × 8m), luu `[(cx, cy)]` cua moi cot. Khi
   propose loop polyline, **moi vertex PHAI cach cot ≥800mm**. Hatch cot
   chiem ~400×400mm, plus buffer 400mm = 800mm clear.

6. **Survey INTERNAL WALLS** — tranh ve corridor overlap tuong noi that:
   ```
   entity.list layer="A-WALL" → 11 entities (1 LWPOLYLINE shell + 10 LINE internal)
   for each LINE: get endpoints via execute_lisp (assoc 10 + assoc 11)
   ```
   Liet ke tat ca cac LINE internal wall. Corridor outer / branch edge
   KHONG duoc trung toa do voi internal wall (gay render bug + logic
   conflict). Cach internal wall **≥200mm** neu loop song song.

7. **Survey DOOR SWING ARCS** — corridor KHONG dam vung swing:
   - Moi cua INSERT trong A-DOOR co radius swing ~900-1500mm (single/double).
   - Vung swing = quarter-circle ban kinh ~900mm tu hinge.
   - Corridor end / zone edge KHONG duoc xam pham vung swing arc.
   - Vi du cua 29D double_door tai (16000, 19900): swing arc ~1500mm
     radius ve phia trong → corridor end PHAI cach (16000, 19900) ≥1500mm.

8. **Verify usable region** — sau khi tinh:
   - usable_polygon = shell - cores - cot×buffer
   - PHAI co da giac, KHONG rong, KHONG multipolygon nhieu rời rac
   - Print bbox + area cho user xac nhan truoc B3

9. **PAIRWISE OVERLAP CHECK** — BAT BUOC truoc khi entmake:

   Sau khi lap bang toa do tat ca polyline du dinh ve (corridor strips +
   branches + zones), chay manual check tung cap (P1, P2):
   
   ```
   for P1 in proposals:
     for P2 in proposals:
       if P1 == P2: continue
       # BBox intersection
       if P1.x_min < P2.x_max and P1.x_max > P2.x_min and
          P1.y_min < P2.y_max and P1.y_max > P2.y_min:
         # Edge overlap
         shared_x = min(P1.x_max, P2.x_max) - max(P1.x_min, P2.x_min)
         shared_y = min(P1.y_max, P2.y_max) - max(P1.y_min, P2.y_min)
         if shared_x > 100 and shared_y > 100:
           # Area overlap (interior) — REJECT, redesign
         elif shared_x > 100 or shared_y > 100:
           # Edge shared (corridor adjacent zone) — OK if intended
   ```
   
   **Cac dang overlap:**
   - **Interior overlap** (shared_x > 100 AND shared_y > 100) → BUG,
     2 polyline chong nhau dien tich → REJECT, redesign 1 trong 2.
   - **Edge shared** (1 dimension overlap, kia 0) → OK neu intended shared
     wall (zone + corridor giap edge). Nhung neu 2 corridor (LOBBY + BR-N)
     gap nhau o canh → trim 1 trong 2 de chi 1 polyline ve canh do.
   
   **Vi du fail tu demo truoc:**
   - LOBBY (8800,18000)→(16400,19400) va BR-N (15400,12000)→(16400,19400)
   - Bbox X overlap [15400, 16400] = 1000mm, Y overlap [18000, 19400] = 1400mm
   - Interior overlap → BUG → fix: trim LOBBY den X=15400 (Option 1).
   - Sau khi trim: LOBBY (8800,18000)→(15400,19400), door 29D tai (16000,19900)
     → gap Y = 500mm → EXTEND LOBBY Y2 = 20000 (100mm overshoot qua door).

   **Corridor-to-door reach check (THEM VAO sau overlap check):**

   Sau khi pairwise overlap pass, kiem tra TUNG corridor/lobby endpoint
   co REACH toi door INSERT tuong ung (tu survey step 4):

   ```
   for each target_door in survey_doors:
     nearest_corridor_end = min distance among all branch/lobby endpoints
     gap = |nearest_corridor_end - target_door|  (theo truc chinh)
     if gap > 200:   # mm
       → EXTEND corridor endpoint den target_door + 100mm overshoot
       → Re-run pairwise overlap check sau extend
   ```

   - Gap ≤ 200mm → OK (endpoint cham goc cua hoac trong buffer).
   - Gap > 200mm → EXTEND. KHONG de gap — gap = hanh lang bi ngat,
     nguoi di khong vao duoc cua, PCCC fail (exit khong reach).
   - **Vi du DUNG:** door 29D Y=19900 → LOBBY Y2 = 20000 (+100mm over).
   - **Vi du DUNG:** door 29E X=9800 → Branch W X2 = 9800 (exact match OK).

10. **Tabulate survey output** — bang summary cho user:
   ```
   | Element | Count | Coord range |
   |---|---|---|
   | Shell | 1 polyline | (0,0)→(42000,28000) |
   | Doors | 2 INSERT | 29D=(16000,19900) main, 29E=(9800,18000) exit |
   | Columns | 18 hatches | grid 8m × 8m, vi tri X=[0,8000,16000,24000,32000,40000] Y=[0,8000,16000] |
   | Internal walls | 10 LINE | Y=18000 (between cores+work), Y=20000 (cores boundary), ... |
   | Cores | 2 WC + 3 elev + 1 stair | (0-16000, 20000-28000) |
   | Usable region | polygon | area ~985m² |
   ```
   User confirm bang nay roi moi sang B2.7.

Neu khong xac dinh duoc shell / core (ban ve trong hoac qua nhieu noi
nhieu), hoi kien truc su input thu cong (kich thuoc & vi tri core), van
chay helper de co usable region truoc khi propose.

### B2.7. Propose CIRCULATION — 3 OPTIONS, ALL viable, DRAW VISIBLE

**[MENTOR RULE] ROOM-FIRST WORKFLOW:**
VẼ PHÒNG RIÊNG TRƯỚC (55-80% sàn) → hành lang = khoảng trống giữa phòng → verify width ≥1.5m chính / ≥1.2m nội bộ. KHÔNG vẽ hành lang trước rồi ép phòng vào.

**RULE COT LOI (UPDATED 2026-05-18):**

Moi option propose PHAI:
1. **Column-aware** — corridor center = midpoint giua 2 col lines (vd
   grid 8m → centers X={4000,12000,20000,28000,36000}, Y={4000,12000})
2. **Closed loop verified** — topology check 100% ring + 2-exit
3. **CirCO compliant** — hành lang chính 1.5-1.8m, nội bộ ≥1.2m (per R-C2)
4. **Travel ≤25m PCCC** hoac note exception ro rang
5. **Difference between options PHAI MEANINGFUL** — khong artificial labels.
   Vi du KHONG dung "Spine-branches" vs "Perimeter-loop" neu khong cau
   nao build duoc cho mat bang nay.

**3 options HOP LE thuong khac o TOPOLOGY (per R-C3-pre):**
- **Option A — Ring:** 4 strips closed loop + branches (classic)
- **Option B — Central Cluster + Perimeter:** service cluster giữa + aisles dọc walls (CirCO 67 NTMK pattern)
- **Option C — Spine + branches:** 1 trục chính + nhánh phụ (linear flow)

KHONG default ring cho mọi mặt bằng. Nếu user reference CirCO 67 NTMK → Option B priority. Hỏi user reference trước khi chọn default.

Khac biet khac trong cung topology (nếu user pick 1 topology rồi):
- Pantry position: center / east-bias / west-bias
- Pantry size: medium 96m² / large 144m² / small 64m²
- LOBBY position: N-mid / N-west / N-east (tuy cua entrance)
- Branch count: 2 / 3 / 4 (anh huong zone access)

**Pre-flight VALIDATE truoc khi present 3 options:**

```python
for option in [A, B, C]:
    # 1. Cot collision check
    for corridor in option.corridors:
        assert corridor_clear_of_columns(corridor.bbox, col_grid)
    
    # 2. Closed loop topology
    assert is_closed_loop(option.corridors) == True
    
    # 3. Width compliance
    for c in option.main_corridors: assert c.width >= 1400
    for c in option.branches: assert c.width >= 1200
    
    # 4. Travel distance
    far_corner = compute_far_corner(option.zones)
    travel = shortest_path(far_corner, option.doors)
    assert travel <= 25000 or option.note_exception
    
    # 5. Door reach
    for door in [29D, 29E]:
        assert door_in_lobby_or_at_branch_end(door, option)
```

Neu **bat ky option nao fail check → BO option do, KHONG present**. Tha
present 1 option dam bao build duoc, **con hon present 3 option voi 2
cai khong work** (ex session 2026-05-18: A workable, B impossible no-loop,
C impossible col-on-wall — user nhin thay confuse, "đề xuất tùm lum").

**Khi gõ `vẽ`:** entmake polyline outline + hatch DOTS scale 50 tren layer
`CW-CIRC-GUIDE` (DASHED color 8). VISIBLE on screen. KHONG silent negative
space ("đang tàng hình").

---

**Corridor lifecycle (per session 2026-05-22 user spec):**
- **STEP 1 (L01):** Draw corridor visible với hatch DOTS scale 50 (per "DRAW VISIBLE" rule trên) — để user thấy topology
- **STEP 2 (L02 zones drawn):** Erase corridor hatch (per B4.5) — zones giờ define không gian
- Keep corridor polyline outline + labels L1-L7 cho reference

### Density & mix reference

→ **Số chuẩn CirCO đầy đủ ở section B3.7 "CirCO ZONE PATTERN" (bên dưới)** — gồm: VP riêng 55-80%, hotdesk min 16, lễ tân 01, phòng họp 1/50 min 2, pantry 15-20m², hành lang 1.5-1.8m chính / 1.2m phụ, mật độ 3.8-5.5 m²/vị trí, ngân sách ≤6tr VNĐ/m². KHÔNG lặp lại ở đây để tránh sai lệch giữa 2 chỗ.

**Kich thuoc noi that CirCO chuan:**

| Item | Size (mm) |
|---|---|
| Ban lam viec | **1200×600** hoac **1400×600** (KHONG dung 700 sau) |
| Ban hop | rong ≥**900**, dai = 600×so ghe |
| Phone booth | **1000×1000** interior |
| Ghe pullout clearance | **700-800mm** sau ban (cho ngoi keo ra) |
| Loi di trong phong | ≥**900mm** (neu khong phai truc giao thong) |
| Truc giao thong chinh | **≥1400mm** (ring + branch đến cửa shell) |
| Truc giao thong phu | **≥1200mm** (connector vào zone phụ, sub-cluster) |

**Vach + cua chuan CirCO:**
- Private office: **vach kinh khung nhom** (giu sang + minh bach).
- Phong nho diện tích < 10m²: **cua lua** (tiet kiem hanh lang).
- Phong lon: cua thuong, swing theo huong vao.

**Adjacency rules:**
- Lounge / cafe **gan loi vao** (encourage chance encounter)
- Focus / quiet rooms **xa pantry & circulation** (perimeter)
- Phone booth **clustered gan hot desk**, KHONG buried trong quiet zone
- Pantry o **vi tri ep nguoi di qua** (force serendipity)
- Avoid west-facing screens (chong loa man hinh chieu nang chieu)

### B3. Propose zone planning (KHONG VE) — **3 OPTIONS**

Xem `playbooks/zoning.md`. Dua **vao usable region** tu B2.5, **luon de
xuat 3 phuong an khac biet ro ret** ve triet ly bo tri (khong phai 3
bien the cua cung 1 layout). User chon 1, sau do moi sang B3.5.

**3 archetype options (per CirCO OFFICIAL — văn phòng riêng dominant):**

| Option | Cơ cấu phòng riêng (55-80% sàn) | Hotdesk | Seats |
|---|---|---|---|
| **A. Nhiều phòng nhỏ** | 08-10 phòng 15-20m² + 02 vừa 30m² | ≥16 chỗ | ~140/500m² |
| **B. Mix cân bằng** | 04 vừa 30m² + 06 nhỏ + 01 lớn 50m² | ≥16 chỗ | ~140/500m² |
| **C. Ít phòng lớn** | 02 lớn 50-100m² + 04 nhỏ | ≥16 chỗ | ~100/500m² |

**Mỗi option PHẢI có (per CirCO official §3):**
1. **Văn phòng riêng 55-80%** (mật độ 2.2-2.5 m²/ghế)
2. **01 Lễ tân** (CHỈ 1)
3. **Hotdesk ≥16 chỗ** (gần lễ tân/sảnh)
4. **Phòng họp ≥2** (1/50 TV/tầng)
5. **Phòng ĐT 1-2/tầng**
6. **Pantry 15-20m²**
7. **Hành lang chính 1.5-1.8m, nội bộ ≥1.2m**

**Output mỗi option:**
- Cơ cấu phòng (số lượng + loại + diện tích)
- Sức chứa tổng
- Trade-off 1-2 dòng

**Format output:** 3 block ro rang, danh so 1/2/3, ket thuc bang cau hoi
"Anh chon option nao? (1/2/3, hoac yeu cau dieu chinh)". KHONG validate
helper o buoc nay — chi validate option duoc chon o B3.5.

Sau khi user chon → sang B3.5 voi DUY NHAT option do.

### B3.5. Validate zones bang helper (BAT BUOC TRUOC B4)

Pipe payload zones de xuat vao `scripts/layout.py` mode `validate_zones`.
Doi `ok: true` truoc khi ve. Neu fail → sua zone, validate lai. Cho phep
ve sau khi:

- Moi zone `ok: true` (within usable, dat min_dim/min_area).
- `warnings` rong (khong overlap, khong bi ket, khoang cach >= corridor_min).
- `coverage_pct` trong khoang ~70-85%.

**3 flaw thuong gap (CHECK TRUOC khi pipe vao validate):**

1. **Zone overlap nhau** — vd "Hot Desk Wings nam trong Hot Desk Core" la
   SAI. Cac zone phai DISJOINT (giao nhau = 0). Neu can sub-zone, dung
   layer `CW-ZONE-SUBLABEL` rieng + KHONG ve polyline. Hoac chia Core thanh
   L-shape (tru Wings) bang polygon nhieu vertex.

2. **Zone bbox de len core** — Lounge / HotDesk / Meeting bbox phai bi
   CLIP boi `usable_polygon` tu B2.5 (da tru WC + thang + cot buffer).
   KHONG dung bbox tho cua shell. Neu zone vuot usable → polygon nuot
   nha ve sinh / thang. Re-clip bang `shapely.intersection(zone_bbox,
   usable_polygon)` trong layout.py mode `clip_to_usable`.

3. **Zone canh tuong vat cheo** — neu shell co doan diagonal (vd
   `(28000,28000) → (42000,18000)`), zone polygon cham canh do PHAI co
   vertex bam diem chuyen (28000,28000) va (42000,18000). KHONG dung 4
   diem chu nhat de "ngang qua" diagonal — se dam vao tuong / hut khoang
   ngoai shell.

**Edge case (handle them khi gap):**

4. **Tuong cong / cua vom (ARC, ELLIPSE, SPLINE)** — approximate thanh
   polyline 16-32 segment (tuy ban kinh: r<2000mm dung 16, r>=2000mm
   dung 32). Sample point bang `numpy.linspace` hoac LISP loop. Zone
   touching arc dung cung 16/32 vertex chu KHONG flat 1 chord.

5. **Multi-floor plan** — skill nay chi handle 1 sang. Neu file co nhieu
   tang (paper space layout / xref tang khac), HOI user chon tang nao,
   chay workflow rieng cho moi tang. KHONG mix entities cua 2 tang.

6. **Plan nho < 50m²** — coverage_pct target xuong **85-95%** (vi loi di
   chiem ty le lon hon). min_dim cho meeting xuong 2200mm thay 3000mm.
   Phone booth co the bo. Bao user "khong gian < 50m² it phu hop coworking
   chuan, suggest hot desk + 1 phong hop nho".

7. **Shell T/U/L-shape phuc tap** — `compute_usable` co the tra
   multipolygon (vai vung roi). Treat moi vung nhu 1 sub-zone, phan zone
   theo tung vung. Neu 1 vung qua nho (< 20m²), gop vao usable
   adjacent neu thong nhau, hoac danh dau "dead zone" KHONG ve gi.

8. **Cot khong deu / lech grid** — KHONG dung 1 column_buffer chung.
   Truyen `columns=[{cx,cy,r}]` voi r per cot vao layout.py. Buffer mac
   dinh 300mm; cot lon (>800mm) tang buffer len 500mm.

9. **Cua so xuyen tuong (curtain wall)** — treat nhu 1 doan canh shell
   bi soft (zone duoc phep cham), KHONG can vertex chuyen. Nhung furniture
   B6 phai cach 600mm de mo bao tri.

**Zone shape orthogonality (BAT BUOC — fix "phong cheo tum lum"):**

13. **Default = rectangle 4 vertex.** Moi zone PHAI la hinh chu nhat
    truc Y/X (4 vertex, canh song song truc) tru khi co LY DO RO RANG
    de dung polygon phuc tap.

    **CHI duoc dung > 4 vertex khi:**
    - Theo doan diagonal cua shell (vd outer wall vat goc) — rule 3.
    - Tao L-shape de tru zone con (vd Core - Wings) — rule 1.
    - Ne cot loi ra giua zone (rare, chi neu cot LON >800mm va NAM HAN
      trong zone).

    **KHONG duoc:**
    - Zone hinh thang vi "trong dep hon" — sai chuan kien truc.
    - Polygon zigzag bam wall thread theo tung doan tuong nho — gop
      thanh rectangle bao quat.
    - Zone xien (canh khong song song X/Y axis) — luon snap vao truc.
    - Vertex thua de "lam cho phong co goc bo tron" — bo tron dung
      `entity.fillet` SAU khi ve, KHONG them vertex luc tao polyline.

    **Vi du sai (cheo tum lum):**
    ```
    points=[[0,0],[5000,500],[5500,3000],[1000,3500],[0,0]]
    # → polygon 4 canh deu xien, KHONG vuong goc
    ```

    **Vi du dung:**
    ```
    points=[[0,0],[5000,0],[5000,3000],[0,3000]]
    # rectangle thuong → CO THE thay bang create_rectangle don gian hon:
    entity(operation="create_rectangle", x1=0, y1=0, x2=5000, y2=3000, layer="...")
    ```

    **Snap rule:** moi vertex toa do PHAI chia het cho 100mm (vd 8000,
    12500, 16800), KHONG dung 8123 / 12567. Snap toa do truoc khi feed
    vao create_polyline.

**BLOCKING:** neu validate fail → KHONG sang B4. Sua zone, validate lai
cho den khi pass. Doc `reference/geometry.md` cho thuat toan clip.

**Code compliance check (BAT BUOC sau geometry validate):**

10. **Egress** — chon 1 trong 2 code:
    - **Vietnam PCCC (default cho CirCO + project tai VN):**
      - Travel distance toi exit ≤ **25m**.
      - Truc giao thong chinh ≥ **1400mm** (1.4m).
      - Truc giao thong phu ≥ **1200mm** (1.2m).
      - **100% closed loop** — KHONG hanh lang cut.
    - **IBC 2021 Group B (US):**
      - Travel ≤ **61m** unsprinklered, **91m** sprinklered.
      - Common path ≤ **23m** unsprinklered, **30m** sprinklered.
      - Corridor ≥ **1118mm** (occupant ≥50) hoac **914mm** (<50).
      - Dead-end ≤ **6m** unsprinklered, **15m** sprinklered.
    - Door swing **theo huong egress** neu phong chua ≥50 nguoi.
    - Tinh shortest path tu zone xa nhat → exit door. Neu vuot → fail,
      redesign loi di.

11. **ADA / accessibility (2010 ADA)** —
    - Wheelchair turning circle r=**762mm** (1525mm dia) trong moi zone.
    - Clear path width **914mm** (32 in pinch, 36 in normal).
    - Accessible toilet stall **1525×1422mm** (60×56 in).
    - Table knee clearance **762mm wide × 686mm high × 432mm deep**.
    - Door pull-side maneuvering **457mm beyond latch × 1525mm perp**.
    - Voi meeting room: 1 cho ngoi accessible (no chair, ban high) per phong.

12. **Acoustic (STC ratings)** —
    - Open-plan partition: **STC 40-45**.
    - Phone booth / standard meeting: **STC 45-50**.
    - Confidential boardroom: **STC 50-60**.
    - Phone booth cach quiet zone **≥3m**, hoac partition STC 45+.
    - Open-plan ceiling NRC ≥0.90 (sound absorbing).
    - **KHONG share demising wall** giua meeting room va open work voi
      assembly < STC 50.

### B3.7. CirCO ZONE PATTERN — Authoritative (per CirCO OFFICIAL standard)

**CirCO = VĂN PHÒNG RIÊNG DOMINANT (55-80%).** Hotdesk là phụ. Xem `reference/circo-standard.md`.

#### 1. VĂN PHÒNG RIÊNG = MAIN PRODUCT (55-80% diện tích sàn)

- **Phòng nhỏ** 15-20m² (~6-8 ghế, mật độ 2.2-2.5 m²/ghế)
- **Phòng vừa** 20-50m² (~13 ghế)
- **Phòng lớn** 50-500m² (~22+ ghế)
- Cơ cấu: tùy kế hoạch kinh doanh. Ví dụ 500m²/tầng → 325m² private = 01 lớn 50m² + 04 vừa 30m² + 08 nhỏ 15-20m²
- Vách: **kính cường lực khung nhôm** (sáng + minh bạch). Vách thạch cao cho khu cần riêng tư cao
- Cửa: **cửa lùa** cho phòng nhỏ (tiết kiệm hành lang). Cửa thường cho phòng lớn (mở VÀO TRONG)

**[MENTOR RULE] Chiều rộng tối thiểu phòng riêng:**
- Mọi Private Office PHẢI có **chiều rộng ≥3m**. Phòng hẹp dài (width <3m) khó bố trí bàn ghế. Exempt: phone booth, print area, utility.
- Phòng riêng KHÔNG nhỏ hơn **15m²** (per CirCO §3.2: phòng nhỏ = 15-20m²). Nếu phòng <15m² → gộp với phòng kề bên.

#### 2. HOTDESK = PHẦN PHỤ (min 16 chỗ)

- **Tối thiểu 16 chỗ** tại mọi địa điểm (bất kể diện tích sàn)
- Mở rộng tùy KHKD
- Vị trí: tầng có lễ tân, gần sảnh/pantry
- Bàn 1200×600mm, ghế xoay lưng lưới

#### 3. LỄ TÂN = CHỈ 01 (KHÔNG multi-reception)

- **01 khu vực lễ tân chung** mỗi địa điểm
- Vị trí: tầng trệt (nếu CirCO quản lý toàn bộ tòa nhà) hoặc tầng liền kề hotdesk
- Chức năng: brand touchpoint + kiểm soát ra vào
- **[MENTOR RULE] RECEPTION PHẢI đặt gần MAIN ENTRANCE** (door chính). Khách vào → thấy lễ tân đầu tiên. KHÔNG đặt reception gần emergency exit.

#### 4. TIỆN ÍCH (per CirCO standard §3.5)

| Tiện ích | Số lượng | Ghi chú |
|----------|---------|---------|
| Phòng họp | **1/50 thành viên/tầng, min 2** | Nhỏ 4-6p, vừa 8-10p, lớn 12-20+p. Bàn CỐ ĐỊNH (ko gấp/module). **[MENTOR] Phải có ≥1 phòng họp LỚN (≥20m², vừa bàn 12-20 người per CirCO §4.4). Không chỉ có phòng họp nhỏ.** |
| Phòng điện thoại | **1-2 / tầng** | KHÔNG 20+ booths. **[MENTOR] Gộp phone booth + print + utility nhỏ thành 1 zone UTILITY. Phone booth = cabin bên trong UTILITY zone.** |
| Pantry | 15-20m², ướt (bồn rửa) | Bể tách mỡ bắt buộc. **[MENTOR] Đặt ở TRUNG TÂM hoặc GIAO NHAU các trục hành lang. KHÔNG đặt pantry ở góc hoặc sát entrance.** |
| In ấn | ≥2m², 1/tầng | 1 máy photocopy + 1 máy hủy |
| Sảnh (Lounge) | Mở, tiếp khách/thư giãn | |
| Phòng máy chủ | 4-5m² | 2 máy lạnh backup |

#### 5. HÀNH LANG (updated per CirCO official)

| Loại | Chiều rộng |
|------|-----------|
| **Hành lang chính** (lễ tân → phân khu) | **1.5 - 1.8m** thông thủy |
| **Hành lang nội bộ** (giữa phòng) | **≥1.2m** lọt lòng |

Cửa mở ra ngoài → cộng thêm kích thước cánh cửa vào width hành lang.

#### 6. CORRIDOR VISIBILITY (per user preference B4.5)

STEP 1: vẽ corridor visible (hatch DOTS) → user thấy topology
STEP 2: zones drawn → erase corridor hatch (per B4.5 lifecycle)

#### 7. PROPOSE ≥3 OPTIONS

Mỗi option khác cơ cấu phòng riêng:
- **Option A — Nhiều phòng nhỏ** (08-10 phòng 15-20m² + 02 phòng vừa)
- **Option B — Mix cân bằng** (04 phòng vừa 30m² + 06 phòng nhỏ + 01 phòng lớn)
- **Option C — Ít phòng lớn** (02 phòng lớn 50-100m² + 04 phòng nhỏ)

**Right pattern diagram (per CirCO official §3.7):**
```
TẦNG ĐIỂN HÌNH 500m²:
┌──────────────────────────────────────────┐
│  VĂN PHÒNG RIÊNG 55-80% (325m²)         │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐    │
│  │Ph.nhỏ│ │Ph.nhỏ│ │Ph.vừa│ │Ph.vừa│    │
│  │15-20m│ │15-20m│ │ 30m² │ │ 30m² │    │
│  └──────┘ └──────┘ └──────┘ └──────┘    │
│  ┌──────┐ ┌──────┐ ┌────────────────┐   │
│  │Ph.nhỏ│ │Ph.nhỏ│ │ Ph.lớn  50m²  │   │
│  └──────┘ └──────┘ └────────────────┘   │
├──────────────────────────────────────────┤
│  TIỆN ÍCH + HÀNH LANG 20-35% (175m²)    │
│  Lễ tân(1) + Hotdesk(16-20) + Pantry    │
│  + 2 phòng họp + 2 phòng ĐT + Sảnh     │
│  + Hành lang 1.5-1.8m chính / 1.2m phụ  │
└──────────────────────────────────────────┘
```

### B4. Ve zone

**Pre-condition:** B3.5 da pass `ok: true` cho TAT CA zone. Neu chua →
ROLLBACK ve B3.5, KHONG ve.

Sau khi chot:

- Voi moi khu, ve `entity(operation="create_polyline", points=[...], layer="ZONE-...", data={"closed": true})`
  hoac `entity(operation="create_rectangle", x1=.., y1=.., x2=.., y2=.., layer="ZONE-...")`
  tren layer `ZONE-*` tuong ung. (`points`, `layer`, `x1/y1/x2/y2` la
  TOP-LEVEL params, KHONG nam trong `data`).
- **Chung vach**: 2 zone dung chung 1 doan polyline / line tren layer
  `WALL` (hoac vach kinh `WALL-GLASS`). Ve vach 1 lan, 2 zone polyline o 2
  phia.
- **Khong chung vach**: zone polyline cach nhau >= bo rong loi di yeu cau
  (xem bang loi di o `reference/standards.md`). Khoang ho do **chinh la
  loi di** — khong can ve them tuong.

**Cleanup truoc khi redraw (BAT BUOC neu retry):**

Khi retry sau 451 / timeout / partial draw:
1. `entity(operation="list", layer="CW-ZONE-BOUNDARY")` (va `CW-ZONE-LABEL`,
   `CW-ZONE-HATCH`).
2. Neu count > so zone du kien → co rogue tu lan ve truoc that bai. Identify:
   handles thap = cu, handles cao = moi.
3. Erase rogue (cu) bang `entity(operation="erase", entity_id=H)` truoc
   khi ve lai. KHONG ve chong them.
4. Check layer `TEMP` / `0` / cac layer khong-phai-CW-* xem co entity la
   khong. Erase neu la rogue.

Cleanup nay con apply khi user nhan "redraw / fix layout" — luon list +
erase truoc khi ve lai.

Sau buoc nay: `view(operation="zoom_extents")` +
`view(operation="get_screenshot")`,
gui user xem va xac nhan truoc khi sang B5.

### B4.5. CORRIDOR HATCH CLEANUP (sau khi vẽ zone — BAT BUOC)

**Lifecycle corridor hatch:**
- **STEP 1 (L01):** Draw corridor visible với HATCH DOTS scale 50 — để user **THẤY** corridor topology khi propose
- **STEP 2 (L02 zone vẽ xong):** Zones giờ define không gian → corridor hatch không cần nữa (redundant + clutter)
- **STEP 2.5 (THIS PHASE):** ERASE all hatches trên CW-CIRC-GUIDE. Giữ polyline outline + labels L1-L7 (cho reference, mỏng hơn)

**Implementation:**
```lisp
(setq ss (ssget "X" (list (cons 0 "HATCH") (cons 8 "CW-CIRC-GUIDE"))))
(if ss (progn (setq n (sslength ss)) (setq i 0)
  (while (< i n) (entdel (ssname ss i)) (setq i (+ i 1)))))
```

**Per user feedback session 2026-05-22:** "hành lang giữ màu trong step 1 để ngta thấy, sau khi fill zone thì xóa màu". Corridor visualization là **temporary aid** trong proposal phase, không phải permanent state.

### B5. Propose noi that (KHONG VE)

Xem `playbooks/furnishing.md`. Voi moi zone, tra ve cho user:

- So luong ban / ghe / sofa / phone booth se dat.
- Pattern (vd "2 hang 5 ban hot desk, quay mat ra cua so").
- Spacing du kien.
- Block co san se dung (sau khi `block(operation="list")`) hoac plan ve thu cong.

**Cho user confirm hoac sua.**

### B6. Ve noi that — chuan kien truc

**Nguyen tac:** noi that **KHONG** chi 1 hinh phang. Moi item gom 2-4
shape chong len nhau de trong nhu plan kien truc that, KHONG phai box
xanh chu nhat thuan.

**Symbol detail (multi-shape):**

- **Hot desk** (1400×700):
  1. Rectangle 1400×700 base = mat ban (layer F-DESK)
  2. Rectangle 350×100 sat canh sau (giua) = monitor stand (layer F-DESK)
  3. Polyline U-shape mep canh truoc 1200×50 = mep ban / can banh (optional)
  4. Circle r=250 dat truoc ban (cach 100mm) = ghe (layer F-CHAIR)
  5. Arc 180deg ban kinh 280 phia sau ghe = lung ghe (optional, layer F-CHAIR)

- **Dedicated workstation** (1600×800):
  1. Rectangle base 1600×800 (F-DESK)
  2. Rectangle monitor 400×100 sat canh sau (F-DESK)
  3. Rectangle storage box 400×400 ben canh (F-CABINET)
  4. Circle r=280 task chair (F-CHAIR)

- **Meeting table** (2200×1200):
  1. Rectangle 2200×1200 (F-TABLE)
  2. 6-8 circle r=250 dat deu xung quanh, cach mep ban 100mm (F-CHAIR)
  3. Optional: 1 rectangle nho 600×100 giua ban = power strip / cable tray

- **Lounge sofa** (2200-3000 × 850):
  1. Rectangle outer (F-SOFA)
  2. Rectangle inner offset 150mm = back cushion line (F-SOFA, line
     segments hoac polyline)
  3. 2-3 vertical lines giua = cushion divider (F-SOFA)

- **Coffee table** (800×800 hoac 1000×600 oval):
  1. Rectangle / ellipse (F-TABLE)
  2. KHONG ghe (lounge ghe rieng cach 800mm)

- **Bar counter** (4000-6000 × 600):
  1. Rectangle outer (F-CABINET)
  2. Polyline mep ngoai canh khach 6 lines diagonal = stool position hint
  3. 4-6 circle r=200 dat deu phia khach = bar stool (F-CHAIR)

- **Phone booth** (1200×1200):
  1. Rectangle outer 1200×1200 (F-BOOTH)
  2. Polyline cua arc 90deg goc = swing door
  3. Rectangle nho 600×400 ben trong = ban gap

- **Door swing** (vach mong):
  1. 2 line song song dai 900mm = canh cua (layer A-DOOR)
  2. Arc 90deg ban kinh 900mm noi 2 dau cua = swing path (A-DOOR)

- **Window break**:
  1. 2 line song song = window jamb
  2. Polyline zigzag giua = symbol kinh (optional)

**Tool call:** dung `entity.create_rectangle/line/arc/circle/polyline`
batch ≤2/turn (per Batch & retry rules).

**Block insert (uu tien neu library co):**
1. `block(operation="list")` xem block co san trong file.
2. Neu thay block ten kieu "DESK_1400", "CHAIR_OFFICE", "MEETING_TBL_2200"
   → `block(operation="insert", data={"name":..,"x":..,"y":..,"rotation":..})`.
   Block render dep va phong phu hon ve thu cong nhieu.
3. Neu khong co → fallback dung multi-shape o tren.

**Array cho cum ban hot desk:**
- Ve mau day du (desk + monitor + ghe) 1 lan → ghi nho handles.
- `entity(operation="array", entity_id=H_desk, data={"rows":2,"cols":3,"row_dist":1500,"col_dist":1600})`.
- Lap lai cho monitor + ghe voi cung row_dist/col_dist.

### B6.5. OVERKILL cuoi STEP 3 furniture (BAT BUOC)

Sau khi ve xong toan bo furniture (~200 entities) → `system.execute_lisp`:
```
(command "_.OVERKILL" "_All" "" "")
```
Auto-remove duplicate polyline (vd: zone boundary trung corridor edge,
desk overlap precision error). 1 lenh, KHONG can pairwise check thu cong.

### B7. Annotation & ra soat

- Kich thuoc canh chinh va loi di:
  `layer(operation="set_current", data={"name":"DIM"})` truoc, roi
  `annotation(operation="create_dimension_linear", data={"x1":..,"y1":..,"x2":..,"y2":..,"dim_x":..,"dim_y":..})`.
  (Op dimension KHONG nhan `layer` — phai set_current truoc).
- Nhan khu: `annotation(operation="create_text", data={"x":..,"y":..,"text":"HOT DESK","height":250,"layer":"TEXT"})`.
- **Vi tri title / level mark / project header**: dat NGOAI shell bbox
  (vd Y > shell_max_y + 1500, hoac X > shell_max_x + 1500). KHONG dat
  trong khu cores (WC / thang / pantry) — se de len text co san. Zone
  label nho thi dat tam zone OK (canh tranh thi giac it hon title lon).
- Ra soat: `view(operation="zoom_extents")` +
  `view(operation="get_screenshot")` + Read.
- **Khong tu save** tru khi user yeu cau ro. Neu can:
  `drawing(operation="save")` (QSAVE) hoac
  `drawing(operation="save_as_dxf", data={"path":"C:/.../out.dxf"})`.

---



---

## B7.6-B7.12 — CONSTRUCTION-READY (separate file)

**MAC DINH demo / concept layout → STOP ngay sau B7.5.** KHONG chay B7.6-B7.12 trừ khi user nói rõ "construction drawing" / "building permit" / "TCVN compliance" / "production-ready".

Khi cần construction-ready: xem `reference/construction-ready.md` cho 6 sections (dimensions, wall thickness, fire egress, line weight, door schedule, accessibility turning circles).

### B7.8. OVERKILL final + verify count

Cuoi B7.5 finishing → chay `(command "_.OVERKILL" "_All" "" "")` lan
cuoi. Verify entity_count khop voi expected (baseline + circulation +
zone + furniture + finishing + dim). Neu thua → co duplicate / rogue.

### B7.5. Architectural finishing (BAT BUOC de plan trong "thuc")

Plan KHONG co 5 thanh phan sau trong nhu draft, KHONG phai ban ve giao
khach hang. **Lam day du:**

1. **Hatch zone** — moi zone polyline duoc hatch nhe de phan biet:
   - Lounge / Pantry: `ANSI31` 45deg, scale 200, layer `CW-ZONE-HATCH`
   - Hot Desk / Dedicated: `DOTS` hoac `GRAVEL`, scale 100
   - Meeting: `SOLID` mau pastel (cyan 4, scale=1, transparency 70%)
   - Goi: `entity(operation="create_hatch", entity_id=<polyline_handle>,
     data={"pattern":"ANSI31","scale":200})`. Hatch ref polyline boundary.

2. **Hatch core** — WC / thang / pantry da co (giu nguyen). Neu thieu:
   `ANSI37` cho WC, `AR-CONC` cho thang.

3. **North arrow** — goc tren-phai ngoai shell (vd vi tri x=shell_max+2000,
   y=shell_max-2000):
   - Circle r=800 base (layer `CW-ANNOTATION`)
   - 1 polyline tam giac dinh huong Y+ (mui ten North)
   - 1 text "N" height=600 trong tam giac
   - Tong: 3 entity

4. **Scale bar** — goc duoi-phai ngoai shell:
   - 5 segment line 1000mm moi cai (1m), alternating filled/empty
   - Text "0  1  2  3  4  5 m" duoi
   - Khoang 7 entity

5. **Title block** — goc duoi-phai (ngoai shell, vi tri x=shell_max-8000,
   y=-3000):
   - Rectangle 8000×3000 outer
   - 2-3 line ngang chia row
   - Text:
     - "PROJECT: <ten du an>"
     - "DRAWING: <ten ban ve> | SCALE: 1:100 | DATE: <YYYY-MM-DD>"
     - "DRAWN BY: AutoCAD-Coworking Bot"
   - 5-7 entity

**Total ~20 entity bo sung sau B7.** Sau khi xong: zoom_extents +
get_screenshot lan cuoi xac nhan.

**6. Column grid labels (BBL chuan AIA)** — moi cot phai co bubble label:
- Truc ngang (horizontal grid): label A, B, C, D... (chu cai), bubble
  circle r=400 + text A/B/C... height=400, dat ngoai shell phia BAC
  (Y > shell_max + 1500).
- Truc doc (vertical grid): label 1, 2, 3, 4... (so), bubble + text dat
  ngoai shell phia DONG (X > shell_max + 1500).
- Vi du: cot luoi 8m. Bubble A tai (0, ymax+2000), B tai (8000, ymax+2000)...
- 1 line dashed noi bubble qua tam cot (tuy chon).
- Tong: 2 × ngrids entity.

**7. Schedule legend (KHONG ve, dat ngoai shell)** — bang text liet ke:
- **Furniture schedule** — count tung loai (vd "Hot Desk: 18, Dedicated: 8,
  Meeting Chair: 16, Sofa: 2..."). Total user capacity ket luan dong cuoi.
- **Door schedule** — door tag + size + swing direction + hardware (D1,
  D2... + 900×2100mm + LH/RH + lockset).
- **Symbol legend** — circle xanh = ghe / rectangle xanh = ban / line do =
  zone boundary... (theo Symbol convention table cuoi file).
- Dat layout 3 column o canh title block. Khong hatch, chi text monospace.
- Tong: 1 rectangle frame + ~30 text entry.

**8. Section / detail callout (neu plan co reference)** — bubble symbol
6 canh + arrow + sheet/detail number. Vi du noi diem co ban ve chi tiet
elevation cua quay bar.

**9. Revision cloud + tag** — neu version > v1, danh dau vung sua bang
spline cloud + revision triangle "1", "2"...

