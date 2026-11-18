# PDF → DXF 轉換細節

工具：Python venv 裝 `pymupdf ezdxf shapely scipy pillow numpy`。讀外來 PDF 時，Python 用 `-I` 執行。

## 1. 座標與單位

- PDF 頁面可能是「直式頁 + 旋轉」：第 17 張的原始座標 (x_raw, y_raw) 和畫面上看到的方向不同。
  - 顯示座標：`X = y_raw`，`Y = 842 − x_raw`（Y 向下）。
  - 模型座標：`mdl(x,y) = (y*K, x*K)`。
  - 紙面座標：`pap(x,y) = (y*S, x*S)`。
  - CAD 角度 = 180 − 顯示角度。
- 換算常數：
  - `S = 25.4/72 = 0.352778`（pt → 紙面 mm）
  - `K = S × 比例分母 / 10`（pt → 模型 cm），1:50 時 `K = 1.763889`
- 模型單位一律 cm（`$INSUNITS=5`、`$MEASUREMENT=1`）。圖放模型空間，圖框和標題欄放圖紙空間。
- **每個案子先確認頁面旋轉和 mediabox**：`p.rect`、`p.rotation`、`p.mediabox`。不要直接套上面的公式。

## 2. 拆解與分層

- `get_drawings()` 統計 `(type, color, fill, round(width,3), dashes)` 出現次數。每種線寬對應一個圖層，寫成 `WMAP`。第 17 張的對應：

  | 線寬 pt | 圖層 |
  |---|---|
  | 0.84 | 構造物 |
  | 0.72 | 尺寸標註 |
  | 0.54 | 鋼軌樁 |
  | 0.42 | 引線及詳圖 |
  | 0.36 | 臨時設施／填充 |
  | 0.24 | 地形線 |
  | 0.12 | 細線 |
  | 1.14 | 鋼筋 |

- 同線寬但用途不同的，用範圍框（例：回填區 `HATCH_BOX`）再分。
- 先把每種線寬上不同顏色畫成一張 `widths.png` 給自己看，確認分類對了再轉。
- 判斷物件屬於圖紙空間：落在標題欄高度以下（Y ≥ 771），或尺寸大於 600 pt（圖框）。
- 圓：由 4 段貝茲曲線組成的路徑，辨識後轉成 CIRCLE。其他曲線先攤平成折線。

## 3. 文字

- PDF 文字多半是「字形填色路徑」，不是可抽取的文字。做法：
  1. 小於 60 pt 的填色路徑用 STRtree 依間距（約 1.6 pt）聚成群（`scripts/cluster.py`）。
  2. 人工建 `texts.py` 清單：`(群組編號, 內容, 旋轉角, 類別, 選項)`。
     - 類別：N 說明、D 尺寸數字、T 圖名、P 標題欄。
     - 內容是 list 時，表示把一群切成多段。
     - **內容逐字照原圖**，包含全形符號（∮、°、～、：）。
- 字型：`LiSongPro.ttf`（儷宋 Pro，最接近細明體）。尺寸文字另建樣式 `明體-尺寸`，寬度係數 0.8。
- 位置校正（`scripts/calib.py`）：用 PIL 取該字型的墨跡框，對齊原圖字群外框，算出插入點和字高，存成 `cal.json`。**校正結果存檔後不要重跑**。
- 交付前一定要做：用 `get_text('words')` 抽出新 PDF 的文字，和清單逐字比對，並比對中心位置。

## 4. 填充（HATCH）—— Gary 要求 #4

- 先找內建圖樣：例如牆面交叉線用 `ANSI37`，scale 照原圖線距換算（`2.715*K/3.175`）。
- 內建沒有就自建 .pat。以**紙面 mm** 定義，hatch scale = 比例/10（1:50 → 5）。第 17 張回填土：

  ```
  *BACKFILL, Backfill soil (paper mm, scale 5 at 1:50 cm)
  45, 0,0, 0,1.27
  135, 0,0, <shift>,1.27, 3.175,-1.905
  ```

  做法：量原圖兩組線的角度、線距、短線長和週期；交錯位移（shift）由實際線位置推算。
- ezdxf 寫法：

  ```python
  h = msp.add_hatch(color=256, dxfattribs={'layer': '填充'})
  h.paths.add_polyline_path(boundary, is_closed=True)
  h.set_pattern_fill('BACKFILL', color=256, scale=5.0, pattern_type=2, definition=defn)
  ```

  其中 `defn` 的每一列是 `[角度, 原點, 偏移, 虛線]`，單位紙面 mm。
- 被 HATCH 取代的原始短線要從輸出中排除：用線寬、角度、範圍框分類（`extra4.classify`）。
- .pat 檔要複製到 AutoCAD Support 資料夾，並放進交付的支援檔資料夾。

## 5. 圖塊（BLOCK）—— Gary 要求 #5、#6

- **重複符號**（例：草叢）：
  - 先挑出屬於它的線段，條件是線寬、長度 ≤ 12 pt、位在坡面線上方 0–15 pt 內。
  - 全部放進一個 BLOCK（`植生草叢`），圖塊內物件放 0 層、`color=0`（ByBlock），插入點設在左下。
- **斷面**（例：鋼軌 50 kg）：
  1. 從種子路徑 `grow()` 收集相連的同線寬路徑。
  2. 端點 0.08 pt 內吸附，貝茲攤平。
  3. shapely `polygonize` + `unary_union` 取外框，得到單一封閉 LWPOLYLINE。
  4. 以外框中心為基準點做 BLOCK。
  5. 同形狀判斷：Hausdorff 距離 < 1 cm 的共用同一圖塊（8 處 → 5 種）。

## 6. 虛線線型（LINETYPE）—— Gary 要求 #9

- 把原圖的虛線（`dashes` 不為空，或同一直線上等距的短線）依「線段長／間隙」歸類，每類一個線型。
- 線型以**紙面 mm** 定義，`$LTSCALE = 比例/10`（1:50 → 5），`$PSLTSCALE = 0`。
- 名稱用 ASCII（例 `DASH_32_19` = 3.2 mm 線、1.9 mm 間隙），同時寫出 `.lin`：

  ```
  *DASH_32_19,Dashed 3.2/1.9 mm __ __ __
  A,3.200,-1.900
  ```

## 7. 尺寸標註（DIMENSION）—— Gary 要求 #8

- 先從原圖抽出每道尺寸（`scripts/dims2.py` → `dims.json`），每道包含：
  - 尺寸線（線寬 0.72 的水平或垂直線）
  - 兩條延伸線
  - 箭頭（小的填色三角形）
  - 文字中心 `tc`
  - 定義點：延伸線遠端，要落在幾何上
- 先排除不是尺寸的東西，例如坡度比符號 0.3/1.0。
- 標註型式（第 17 張實測，1:50）：

  ```
  dimscale=5, dimtxt=9.2pt*S, dimasz=2, dimexe=0.6, dimexo=0, dimgap=0.6,
  dimtxsty=明體-尺寸, dimclrt=2, dimdec=0, dimzin=8, dimtad=1, dimtih=0, dimtoh=0,
  dimtofl=1, dimtmove=2
  ```

  `$DIMASSOC=2`。
- 文字照原圖：量測值等於原圖數字就用 `<>`。不照比例或是代號（W、h=50~100、L=50cm）時，用文字覆寫。詳圖比例不同時用 `dimlfac`（1/10 詳圖 → 0.2）。
- 用 `add_linear_dim(base, p1, p2, angle, text, override)` 產生標註，再用 `set_location(tc, leader=False, relative=False)` 把文字放到原圖位置。把 handle、p1、p2 存進 `dimlog.json`，給 AutoCAD 關聯用。
- 用原尺寸抽出的線段、箭頭要從一般線條中排除，避免重複。

## 8. 配置頁

- 版面名稱 `A3出圖`，用 `page_setup(size=(420,297), margins=0, device='DWG To PDF.pc3')`。
- 視埠放在圖框內、標題欄以上，view_height 等於紙高 × 5，顯示鎖定（flags |= 16384），放在 `視埠` 圖層（不出圖）。
- 套用出圖樣式表：`current_style_sheet='XXX.ctb'`，`plot_layout_flags |= 1|128`。
