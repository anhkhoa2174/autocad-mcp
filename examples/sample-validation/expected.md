# Sample validation — CIRCO 222DBP, Lầu 7 (MB Hiện Trạng)

Bộ đối chiếu để kiểm tra tool đo diện tích chạy đúng.
Xem `plan.png` = ảnh bản vẽ, vùng **xanh** = phần office tool đã trích/tô.

Đơn vị bản vẽ: **mm**. Diện tích quy ra **m²**.

---

## Kết quả mong đợi (expected output)

| Hạng mục | Kích thước | Diện tích |
|---|---|---|
| Bao nhà (building footprint) | 20.15 m × 20.55 m | **414 m²** |
| − Lõi thang/WC/pantry (góc dưới-trái) | 7.70 m × 8.25 m | −64 m² |
| − Thang máy + thang bộ (giữa-dưới) | ~4.85 m × 4.95 m | −23 m² |
| **= Office (vùng xanh)** | | **≈ 327 m²** |

> Mốc đo: office = *bao nhà − lõi − thang máy* (net, phần sử dụng được).
> Nếu đo *bao nhà gồm cả lõi* thì = 414 m² — khác định nghĩa, không phải sai.

---

## Toạ độ vùng (drawing units, mm)

- Building rect: `(764953, -81938)` → `(785104, -61384)`
- Hole 1 — lõi trái: `(764953, -81938)` → `(772654, -73684)`
- Hole 2 — thang máy: `(772654, -81938)` → `(777500, -77000)`

Đường bao office (polygon chữ L bậc thang, 8 đỉnh):
```
(785104,-61384) (764953,-61384) (764953,-73684) (772654,-73684)
(772654,-77000) (777500,-77000) (777500,-81938) (785104,-81938)
```

---

## Cách tái tạo (reproduce)

1. Mở `CIRCO 222DBP L7.dwg` trong AutoCAD, export DXF:
   ```
   (setvar "FILEDIA" 0)
   (command "_.DXFOUT" "C:/Users/.../222DBP.dxf" "_V" "2013" "16")
   ```
2. Chạy tool:
   ```bash
   python examples/measure_area.py 222DBP.dxf --rects \
       --building 764953 -81938 785104 -61384 \
       --hole 764953 -81938 772654 -73684 \
       --hole 772654 -81938 777500 -77000
   ```
3. Output phải ra:
   ```
   >>> AREA = 327 m2
   ```

Sai số chấp nhận: **±2%** (do làm tròn kích thước lõi/thang máy đọc từ bản vẽ).

---

## Đối chiếu chéo (cross-check, file khác)

Trên `CIRCO 177HBT`, tool đo office = **656 m²**, CirCO báo **645 m²** → lệch 1.7%.
Cùng phương pháp, chứng tỏ tool đọc đúng.
