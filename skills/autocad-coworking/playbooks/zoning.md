# Playbook: Zoning coworking space

Quy trinh phan khu mat bang coworking. Don vi mm.

## Cac khu chuc nang co ban

| Khu | Ty le tham chieu (% dien tich net) | Ghi chu |
|---|---|---|
| Hot desk | 30 - 45% | Khu lon nhat, can sang tu nhien |
| Dedicated desk | 10 - 20% | Co the ngan vach lung thap |
| Meeting room | 8 - 15% | 4 - 8 nguoi/phong, vach kinh |
| Phone booth | 3 - 6% | 1 - 2 nguoi, cach am |
| Lounge / break | 8 - 12% | Sofa, ban thap, gan pantry |
| Pantry / coffee | 5 - 8% | Gan loi vao phu, xa khu yen tinh |
| Reception | 3 - 5% | Sat cua chinh |
| Circulation | 20 - 25% | Loi di, khong ke vao khu chuc nang |

Tong cac khu chuc nang ~75 - 80% dien tich san net (tru WC, kho, ky thuat).

## Nguyen tac dat khu

1. **Reception** sat cua chinh, nhin thay ngay khi buoc vao.
2. **Pantry** va **phone booth** xa khu hot desk can tap trung; pantry thuong
   o goc xa cua chinh, gan loi thoat phu.
3. **Meeting room** uu tien ven tuong (ngan vach kinh) hoac loi cua so (lay
   sang). Tranh dat giua san vi chia cat luong di lai.
4. **Hot desk** dat doc theo cua so, ban quay mat ra cua so hoac vuong goc
   voi cua so de tranh nguoc sang man hinh.
5. **Lounge** dem giua khu lam viec va pantry, dong thoi la khong gian buffer
   am thanh.
6. **Phone booth** dat thanh cum 2-3 cai, gan loi di nhung khong chan cua.

## Chung vach vs khong chung vach

Hai zone ke nhau co the:

**A. Chung vach** — co tuong / vach kinh that ngan giua hai zone.
- Dung cho: meeting room, phone booth, phong giam doc, WC, kho — nhung khu
  can cach am hoac kin dao.
- Ve: `draw_line` / `draw_polyline` doan tuong tren layer `WALL` (hoac
  `WALL-GLASS` neu vach kinh). **Ve 1 lan**; polyline cua 2 zone o 2 phia
  trung doan vach do.
- Tinh dien tich zone: tinh den tim tuong (hoac long net tuy quy uoc, noi
  ro voi user).

**B. Khong chung vach** — hai zone mo, ngan cach bang khong gian trong.
- Dung cho: hot desk - lounge, lounge - reception, hot desk - hot desk khac
  goc, dedicated - hot desk... — cac khu open-plan.
- Ve: 2 polyline `ZONE-*` dat **cach nhau >= bo rong loi di yeu cau**.
  Khoang ho giua chung **chinh la loi di**, khong can ve them tuong.
- Optional: ve centerline tren layer `CIRC` cho ro luong di chuyen.

**Loi di yeu cau** (xem chi tiet `reference/standards.md`):
- Loi chinh xuyen suot tu cua chinh den khu xa nhat: >= 1500mm, khuyen
  nghi 1800mm.
- Loi phu giua hai cum zone open: >= 1200mm.
- Loi nhanh / cuc bo (giua 2 zone phong booth): >= 900mm.

Khi propose zoning, **noi ro voi user** moi cap zone ke nhau dung A hay B,
va loi di se rong bao nhieu o dau.

## Quy trinh ve (thuc hien sau khi user confirm zoning plan)

Goi qua MCP tools `autocad-mcp__*`. Xem `reference/mcp-tools.md` cho
operation enum + data schema day du.

```
# 1. Outline san — x1/y1/x2/y2/layer la TOP-LEVEL params
autocad-mcp__entity(operation="create_rectangle",
                    x1=0, y1=0, x2=W, y2=H, layer="A-WALL")

# 2. Voi moi khu, tinh dien tich tuc thoi:
#    area_zone = total_net_area * percent
#    chon hinh chu nhat phu hop dat o vi tri logic theo nguyen tac tren

# 3. Ve polyline dong kin tren layer ZONE-*
#    points & layer la top-level; `closed` nam trong data
autocad-mcp__entity(operation="create_polyline",
                    points=[[x1,y1],[x2,y1],[x2,y2],[x1,y2]],
                    layer="CW-ZONE-BOUNDARY",
                    data={"closed": true})

# 4. Voi cap chung vach: ve doan WALL / WALL-GLASS chung
autocad-mcp__entity(operation="create_line",
                    x1=wx1, y1=wy1, x2=wx2, y2=wy2, layer="A-WALL")

# 5. Nhan khu (text). Voi annotation: tat ca field nam trong `data`
#    (`layer` nam trong data, KHONG top-level).
autocad-mcp__annotation(operation="create_text", data={
  "x": cx, "y": cy, "text": "HOT DESK", "height": 250, "layer": "CW-ZONE-LABEL"
})
```

## Validate sau khi zoning xong

- Tong dien tich cac khu <= dien tich san net.
- Moi cap zone ke nhau **khong chung vach** co khoang ho >= bo rong loi di yeu cau.
- Co it nhat 1 loi di lien tuc tu cua chinh den moi zone (khong zone nao
  bi ket).
- Loi di chinh khong bi noi that hoac vach booth chia nho duoi 1200mm.
- Reception nhin thay tu cua chinh.
- Co the do bang `autocad-mcp__annotation(operation="create_dimension_linear", data={"x1":..,"y1":..,"x2":..,"y2":..,"dim_x":..,"dim_y":..})` neu can chac chan. (Op dimension KHONG nhan `layer`; set_current truoc neu can layer rieng.)

Sau khi zoning chot va ve xong, sang `playbooks/furnishing.md` de propose
ke hoach noi that. **Khong** ve noi that ngay sau zone — phai propose va
cho user confirm truoc.
