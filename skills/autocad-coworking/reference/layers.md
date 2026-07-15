# Reference: Chuan layer naming

**Day la bo layer chuan rieng cua skill `autocad-coworking`. Luon tao bo nay
khi vao mot ban ve, khong reuse layer co san trong file user** (du ten co the
trung). Ly do:

- Nhat quan giua cac session va du an: tong hop screenshot, dimension, hatch
  deu cung quy uoc.
- User co the freeze / isolate / tat toan bo phan skill ve bang cach freeze
  prefix `ZONE-*` / `FURN*` ma khong dong cham layer ban dau cua ho.
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

## Bang layer chuan

| Layer | Color | Linetype | Muc dich |
|---|---|---|---|
| `WALL` | white (7) | CONTINUOUS | Tuong bao, tuong ngan dac |
| `WALL-GLASS` | cyan (4) | CONTINUOUS | Vach kinh ngan zone (meeting, phong giam doc) |
| `WALL-EXIST` | 8 (gray) | CONTINUOUS | Tuong hien trang giu nguyen |
| `DOOR` | red (1) | CONTINUOUS | Cua + cung mo cua |
| `WINDOW` | cyan (4) | CONTINUOUS | Cua so |
| `COLUMN` | 8 (gray) | CONTINUOUS | Cot ket cau (khong sua) |
| `CIRC` | magenta (6) | DASHED | Loi di / luong giao thong |
| `ZONE-HOTDESK` | yellow (2) | CONTINUOUS | Khu hot desk |
| `ZONE-DEDICATED` | 42 (cam) | CONTINUOUS | Khu dedicated desk |
| `ZONE-MEETING` | green (3) | CONTINUOUS | Phong meeting |
| `ZONE-PHONE` | 140 (xanh ngoc) | CONTINUOUS | Phone booth |
| `ZONE-LOUNGE` | 31 (hong) | CONTINUOUS | Lounge / khu nghi |
| `ZONE-PANTRY` | 191 (tim nhat) | CONTINUOUS | Pantry / coffee |
| `ZONE-RECEPTION` | 11 (do nhat) | CONTINUOUS | Reception |
| `ZONE-WC` | 8 (gray) | CONTINUOUS | WC |
| `ZONE-STORAGE` | 9 (gray nhat) | CONTINUOUS | Kho |
| `FURN` | blue (5) | CONTINUOUS | Noi that (ban, ghe, sofa, tu) |
| `FURN-FIXED` | 5 + lineweight day | CONTINUOUS | Noi that co dinh (counter, vach booth) |
| `EQUIP` | 30 (cam dam) | CONTINUOUS | Thiet bi (tu lanh, may pha cafe...) |
| `DIM` | 8 (gray) | CONTINUOUS | Kich thuoc |
| `TEXT` | white (7) | CONTINUOUS | Nhan khu, ghi chu |
| `HATCH` | 8 (gray) | CONTINUOUS | Hatch trang tri / phan biet khu |
| `GRID` | 8 (gray) | DASHED | Luoi tham chieu |

## Setup nhanh dau session

Lap qua bang layer chuan, goi `layer.create` cho moi layer chua ton tai:

```
for (name, color) in [
    ("WALL", "white"), ("DOOR", "red"), ("WINDOW", "cyan"),
    ("CIRC", "magenta"), ("FURN", "blue"), ("DIM", 8), ("TEXT", "white"),
    ("ZONE-HOTDESK", "yellow"), ("ZONE-DEDICATED", 42),
    ("ZONE-MEETING", "green"), ("ZONE-PHONE", 140),
    ("ZONE-LOUNGE", 31), ("ZONE-PANTRY", 191),
    ("ZONE-RECEPTION", 11),
]:
    autocad-mcp__layer(operation="create", data={"name": name, "color": color})
```

Vi du 1 lenh:
```
autocad-mcp__layer(operation="create", data={"name": "WALL", "color": "white"})
```

## Quy uoc

- Ten layer **chu hoa**, **dau gach noi `-`** phan tach (khong dung khoang trang).
- Prefix `ZONE-` cho khu chuc nang, `FURN` / `EQUIP` cho do dac, khac giu nguyen.
- Khi vao mode chinh sua khu nao, set layer hien tai bang
  `autocad-mcp__layer(operation="set_current", data={"name":".."})` truoc khi ve.
