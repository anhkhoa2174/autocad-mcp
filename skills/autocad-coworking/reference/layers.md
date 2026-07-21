# Reference: Chuan layer naming

**Day la bo layer chuan rieng cua skill `autocad-coworking`. Luon tao bo nay
khi vao mot ban ve, khong reuse layer co san trong file user** (du ten co the
trung). Ly do:

- Nhat quan giua cac session va du an: tong hop screenshot, dimension, hatch
  deu cung quy uoc.
- User co the freeze / isolate / tat toan bo phan skill ve bang cach freeze
  prefix `CW-*` / `F-*` ma khong dong cham layer ban dau cua ho.
- Tranh gan vao layer co color/linetype khong phu hop (vd layer `WALL` co
  san cua user co the la mau khac, lineweight khac).

Quy trinh: goi `autocad-mcp__layer(operation="list")` truoc → so sanh
ten → layer nao chua co thi
`autocad-mcp__layer(operation="create", data={"name":..,"color":..})`.
Neu trung ten nhung **khac thuoc tinh** thi van giu nguyen layer cua user
(khong overwrite); skill se ghi log canh bao va tiep tuc dung layer do (do
la quyet dinh cua user voi file goc).

Color tham chieu AutoCAD Color Index (ACI) hoac ten chuan ("red", "yellow",
"green", "cyan", "blue", "magenta", "white").

## 3 prefix

| Prefix | Nghia | Vi du |
|---|---|---|
| `A-` | **Shell/kien truc co san** (tuong, cot, cua, core) | `A-WALL`, `A-COLUMN` |
| `CW-` | **Thiet ke coworking** (zone, corridor, annotation) | `CW-ZONE-BOUNDARY` |
| `F-` | **Noi that** (ban, ghe, sofa, booth) | `F-DESK`, `F-CHAIR` |

## Bang layer chuan

Dong bo voi bang "Layer color & lineweight hierarchy" trong `SKILL.md` —
**hai noi phai luon khop nhau**.

| Group | Layer | Color (ACI) | Lineweight | Muc dich |
|---|---|---|---|---|
| Shell | `A-WALL` | 7 (white/black) | 0.50 | Tuong bao, tuong ngan dac |
| Shell | `A-COLUMN` | 7 + HATCH | 0.50 | Cot ket cau (solid hatch, khong sua) |
| Shell | `A-DOOR` | 4 (cyan) | 0.18 | Cua + cung mo cua |
| Shell | `A-WINDOW` | 4 (cyan) | 0.13 | Cua so |
| Core | `A-TOIL` / `A-ELEV` / `A-STAIR` | 8 (gray) | 0.25 | WC / thang may / thang bo |
| Corridor | `CW-CIRC-HATCH` | **8 (dark gray)** | n/a | DOTS pattern, non-associative |
| Corridor | `CW-CIRC-LABEL` | **7 (white)** | text | Ten hanh lang L1/L2... |
| Zone | `CW-ZONE-BOUNDARY` | 1 (red) | 0.35 | Ranh gioi khu |
| Zone | `CW-ZONE-HATCH` | 4 (cyan) | 0.13 | Hatch khu, transparency 70% |
| Zone | `CW-ZONE-LABEL` | 4 (cyan) | text | Nhan khu, height 400-600 |
| Furniture | `F-DESK` / `F-TABLE` / `F-CABINET` | 5 (blue) | 0.18 | Ban lam viec / ban / tu |
| Furniture | `F-CHAIR` / `F-SOFA` / `F-BOOTH` | 3 (green) | 0.15 | Ghe / sofa / phone booth |
| Annotation | `CW-DIMENSION` | 7 | 0.13 | Kich thuoc |
| Annotation | `CW-ANNOTATION` | 1 (red) | text | Title, height 800-900 |

**CRITICAL — mau nhan PHAI contrast voi fill nam duoi:**
- ❌ `CW-CIRC-LABEL` color 8 tren `CW-CIRC-HATCH` color 8 → blend, khong doc duoc
- ✓ `CW-CIRC-LABEL` color 7 (white) tren hatch color 8 (gray) → contrast

## Setup nhanh dau session

```
for (name, color) in [
    ("A-WALL", 7), ("A-COLUMN", 7), ("A-DOOR", 4), ("A-WINDOW", 4),
    ("A-TOIL", 8), ("A-ELEV", 8), ("A-STAIR", 8),
    ("CW-CIRC-HATCH", 8), ("CW-CIRC-LABEL", 7),
    ("CW-ZONE-BOUNDARY", 1), ("CW-ZONE-HATCH", 4), ("CW-ZONE-LABEL", 4),
    ("F-DESK", 5), ("F-TABLE", 5), ("F-CABINET", 5),
    ("F-CHAIR", 3), ("F-SOFA", 3), ("F-BOOTH", 3),
    ("CW-DIMENSION", 7), ("CW-ANNOTATION", 1),
]:
    autocad-mcp__layer(operation="create", data={"name": name, "color": color})
```

**Set mau bang LISP (chac an hon):**
```lisp
(command "_-LAYER" "_COLOR" "7" "CW-CIRC-LABEL" "")
```
**KHONG dung `entmod` de doi mau layer** — silent fail, mau khong update.

## Quy uoc

- Ten layer **chu hoa**, **dau gach noi `-`** phan tach (khong dung khoang trang).
- Prefix dung dung nhom: `A-` shell / `CW-` thiet ke / `F-` noi that.
- Khi vao mode chinh sua khu nao, set layer hien tai bang
  `autocad-mcp__layer(operation="set_current", data={"name":".."})` truoc khi ve.
