# Playbook: Furnishing coworking space

Dat noi that trong cac khu da zoning. Don vi mm.

Tat ca lenh ben duoi goi qua MCP tools `autocad-mcp__*`. Xem
`reference/mcp-tools.md` cho operation enum + data schema day du.

## 0. NGUYEN TAC BO TRI (DOC TRUOC — mentor 2026-07-08 + research)

**(A) KICH THUOC ITEM = CHOT TRUOC roi moi bo tri.** Ban 600×1200, ban hop
600/nguoi/canh, pantry counter rong 600-700 dai theo tuong. DUNG block model
that (GHE LAM VIEC, QUAY LETAN, SOFA_P8A, GHE AN1, GHE BAR, GHE LEADER,
AIMCHAIR) — KHONG ve circle/rect thay ghe/sofa. Xem memory
`furniture-standards-and-real-block-models`.

**(B) BAN LAM VIEC XEP CUM BENCH — KHONG ban le roi.**
- Ban don vao **pod**: 2 hang **dau lung** (back-to-back, chung spine) × N cot,
  ban **dồn sat** nhau (gap 0-100mm). Pod chuan = **4 (2×2) / 6 (2×3) / 8 (2×4)
  / 10 (2×5)**.
- Giua cac pod chua **loi di**: chinh **1200-1500**, phu **1050-1200**.
- Back-to-back worktop-edge→edge **≥1800** (2×600 ban + ~600 ghe/spine); ghe
  lui ra sau **≥900**.
- Anti-pattern: rai ban deu grid gap lon tung ban (phi dien tich + xau).

**(C) PHONG HOP CHIA VUA KHIT BAN — khong du dien tich.**
- Size phong = ban + clearance toi thieu. **1.8-2.3 m²/nguoi**.
- Clearance quanh ban: phong nho **900-1070**, phong lon **1220-1520**.
- Dien tich: 4-6ng = **9-14m²**, 8-12ng = **14-28m²**, 16-20ng = 33-46m².
- Zone meeting lon → **chia nhieu phong dung size** (glass partition), dung de
  1 khoi 60m² cho 12 nguoi.

**(D) VI TRI MEETING = sau lounge-pantry / perimeter, KHONG nhet sau.**
Flow: Entrance → Reception → Lounge/Pantry → **Meeting** → Dedicated/Private
(sau nhat). Meeting semi-private doc mat kinh/perimeter, tiep can khong xuyen
khu lam viec sau.

Xem memory `desk-cluster-benching-meeting-rightsize-placement`.

## Hot desk (BENCH CLUSTER)

**Module ban don:** **1200 x 600** (chuan CirCO), ghe GHE LAM VIEC phia truoc.
**Xep POD (bench), KHONG ban le:**
- Trong pod: 2 hang dau lung (chung spine giua), moi hang N ban canh nhau
  gap ~100. Depth pod = 600 + 600 (2 ban) = 1200 + ghe 2 ben.
- Ban canh nhau: tim-tim ~1300 (1200 ban + 100 khe).
- Hai hang dau lung: worktop-edge→edge ≥1800.
- Giua 2 pod: loi di 1200-1500 (chinh) / 1050-1200 (phu).

**Pattern day ban (vd 2 hang x 5 cot, goc dau 1000,1000):**

```
# Tao 1 ban mau — x1/y1/x2/y2/layer la TOP-LEVEL
autocad-mcp__entity(operation="create_rectangle",
                    x1=1000, y1=1000, x2=2400, y2=1700, layer="FURN")
# -> {"ok": true, "handle": "<H>", ...}; capture handle

# Array thanh 2 hang x 5 cot — entity_id top-level, rest in data
autocad-mcp__entity(operation="array",
                    entity_id="<H>",
                    data={"rows": 2, "cols": 5, "row_dist": 1500, "col_dist": 1600})

# Them ghe (circle r=250) — cx/cy/radius nam trong data, layer top-level
autocad-mcp__entity(operation="create_circle",
                    layer="FURN",
                    data={"cx": 1700, "cy": 700, "radius": 250})
autocad-mcp__entity(operation="array",
                    entity_id="<chair_H>",
                    data={"rows": 2, "cols": 5, "row_dist": 1500, "col_dist": 1600})
```

## Dedicated desk

Module 1600 x 800, co the them tu hoc 400x800 ben canh. Ngan vach lung 1200mm
giua hai ban quay lung.

## Meeting room (CHIA VUA KHIT BAN — khong du dien tich)

**Ban = 600/nguoi/canh** (mentor). Phong = ban + clearance 900-1200 moi ben.
Right-size: **1.8-2.3 m²/nguoi**, KHONG phinh to.

| So nguoi | Ban (600/ng/canh) | Phong right-size |
|---|---|---|
| 4 (2/canh) | 1200 x 1200 | ~3000 x 3000 (9m²) |
| 6 (3/canh) | 1800 x 1200 | ~3600 x 3300 (12m²) |
| 8 (4/canh) | 2400 x 1200 | ~4200 x 3500 (15m²) |
| 12 (6/canh) | 3600 x 1400 | ~5400 x 3800 (20m²) |

Clearance quanh ban: phong nho 900-1070, lon 1220-1520. Cua 900mm mo khong
cham ghe. **Zone meeting lon → chia thanh nhieu phong dung size (glass
partition), dung de 1 khoi 60m² cho 12 nguoi.**

```
# Ban meeting (tam (cx,cy)) — top-level params
autocad-mcp__entity(operation="create_rectangle",
                    x1=cx-1200, y1=cy-750, x2=cx+1200, y2=cy+750, layer="FURN")

# Ghe quanh ban: lap qua entity.create_circle voi toa do tinh san trong skill
# autocad-mcp__entity(operation="create_circle",
#                     layer="FURN",
#                     data={"cx": .., "cy": .., "radius": 250})
```

## Phone booth

Kich thuoc trong long 1000 x 1000 (1 nguoi) hoac 1200 x 1500 (2 nguoi).
Tuong day 50-80 (cach am). Cua mo ra ngoai. Ghe + ban nho 600 x 400.

```
# Vach booth (outline ngoai + outline trong, ngan cach 50mm = day tuong)
autocad-mcp__entity(operation="create_rectangle",
                    x1=x, y1=y, x2=x+1100, y2=y+1100, layer="WALL")
autocad-mcp__entity(operation="create_rectangle",
                    x1=x+50, y1=y+50, x2=x+1050, y2=y+1050, layer="FURN")
```

## Lounge

- Sofa don 900 x 850, sofa doi 1600 x 850, sofa ba 2200 x 850.
- Ban cafe tron r=400 hoac vuong 600 x 600.
- Khoang cach sofa - ban cafe: 400-500.
- Cum 4 nguoi: 2 sofa don + 1 ban tron, dien tich ~3000 x 3000.

## Pantry

- Counter 600 sau, dai theo tuong, cao 850.
- Ban an cao 750 hoac ban bar cao 1050.
- Khoang lam viec sau counter >= 1100.
- Tu lanh, may pha cafe, bon rua noi tiep tren counter.

## Reception

- Quay 1800 - 2400 dai, sau 700, cao 1100 (mat khach) / 750 (mat nhan vien).
- Ghe nhan vien sau quay: chua >= 800 sau quay.
- Khu cho 2-3 ghe sofa truoc quay.

## Block library

Neu user da co block (vd `DESK-1400`, `CHAIR`, `SOFA-2`), uu tien
`block.insert` thay vi ve thu cong:

```
autocad-mcp__block(operation="list")
autocad-mcp__block(operation="insert", data={
  "name": "DESK-1400", "x": 1700, "y": 1350, "rotation": 0
})
```

## Validate sau furnishing

- Loi tiep can ban >= 600mm.
- Khong co ban/ghe cham polyline `ZONE-*` cua khu khac.
- Loi di chinh >= 1500, loi phu >= 1200 van thong suot.
- Cua mo khong cham noi that (kiem tra cung mo cua tren layer `DOOR`).
