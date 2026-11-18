# 出圖樣式表（CTB）

Gary 要求 #7：CAD 裡不設線寬，筆寬全部放 CTB，依顏色決定。

## 檔案格式

```
48 bytes 檔頭：b'PIAFILEVERSION_2.0,CTBVER1,compress\r\npmzlibcodec'
12 bytes：struct '<III' = (adler32(壓縮資料), 解壓後長度, 壓縮後長度)
其後：zlib 壓縮的文字內容
```

## 正確做法（`scripts/mkctb.py`）

1. 用 `ezdxf.addons.acadctb.new_ctb()` 建表，依顏色設定筆寬。
2. **不要用 `ctb.save()`**，它有 bug：會寫出 8 bytes 的整數，線寬表也會多出第 26 格以後的項目，結果出現 2.11 mm 的粗線。要自己組檔頭：

   ```python
   m = StringIO(); ctb.write_content(m); m.write(chr(0))
   body = m.getvalue().encode('cp1252'); comp = zlib.compress(body, 9)
   f.write(b'PIAFILEVERSION_2.0,CTBVER1,compress\r\npmzlibcodec')
   f.write(struct.pack('<III', zlib.adler32(comp) & 0xffffffff, len(body), len(comp)))
   f.write(comp)
   ```

3. **線寬只能用標準表的索引 0–26**：

   ```
   [0.0,0.05,0.09,0.1,0.13,0.15,0.18,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.53,
    0.6,0.65,0.7,0.8,0.9,1.0,1.06,1.2,1.4,1.58,2.0,2.11]
   ```

   每個 `Color_n` 區塊的 `lineweight=` 寫索引值；`custom_lineweight_table{}` 就寫這 27 格。

4. **全部出黑色**：每個顏色區塊寫

   ```
   color=-16777216
   color_policy=5
   ```

   不能用 ezdxf 預設的 `color=-1040187392 / mode_color / color_policy=1`，那樣出圖仍是彩色。

5. 用 ASCII 檔名（例 `P17-LW.ctb`），複製到 `Plotters/Plot Styles/`，配置頁設 `current_style_sheet`，`plot_layout_flags |= 1|128`。

## 筆寬怎麼訂

- 量原圖 PDF 的線寬（pt），換成 mm（× 0.3528），取最接近的標準值。
- 第 17 張的對應（顏色 → mm）：

  | 顏色 | 4 | 1 | 30 | 5 | 140 | 3 | 8 | 6 | 7 | 2 | 其他 |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | mm | 0.30 | 0.25 | 0.20 | 0.15 | 0.05 | 0.13 | 0.09 | 0.40 | 0.25 | 0.25 | 0.13 |

- 驗證：用 `acadctb.load()` 讀回，檢查幾個顏色的 `get_lineweight()` 和 `color`；再實際出圖，和原圖疊圖比對。
