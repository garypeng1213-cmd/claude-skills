# scripts：第 17 張實際用過的腳本

這些是案例範例。座標、範圍框、群組編號、handle 都是第 17 張專用的，換案子要改。`$SP` 指當時的工作資料夾，用的時候換成新案子的路徑。

| 檔案 | 用途 | 換案子要改的地方 |
|---|---|---|
| `cluster.py` | 把 PDF 字形填色路徑依間距聚成群（`clusters.json`） | 間距參數（預設 1.6 pt） |
| `texts.py` | 文字清單：群組 → 內容（逐字照原圖）、角度、類別 | 整份重做 |
| `calib.py` | 用 LiSongPro 墨跡框校正文字位置和字高（`cal.json`） | 字型路徑 |
| `dims2.py` | 從原圖抽尺寸：尺寸線、延伸線、箭頭、文字（`dims.json`） | SKIP 清單（非尺寸符號）、箭頭長度 |
| `extra4.py` | 分類回填短線、草叢線段、鋼軌斷面；回填 .pat 定義；斷面外框 | BF_BOX、坡面線、RAILS 種子 |
| `conv4.py` | 主轉換：圖層、線條、線型、HATCH、圖塊、DIMENSION、文字、A3 配置 | LAYERS／WMAP、範圍框、視埠位置 |
| `snapfix.py` | 產生關聯標註 LISP（射線找吸附點）→ `assoc2.lsp` | 已知關聯狀態表 `st` |
| `chk.lsp` / `meas.lsp` | 在 AutoCAD 內列出每道標註的關聯狀態（DIMASSOC 90）和量測值 | 無 |
| `txt.lsp` / `dl.lsp` | 把尺寸文字（group 11）和尺寸線（group 10）改回原圖位置 | handle 和座標（由 dimlog.json 和 dims.json 產生） |
| `mkctb.py` | 依顏色給筆寬、全部出黑的 CTB，已避開 ezdxf 的 bug | `W` 字典 |
| `plot.scr` | -PLOT 出 PDF 加存檔（先切到配置頁再跑） | CTB 名稱、輸出路徑 |
| `review2.py` | 原圖和新圖雙向點陣比對，輸出對照拼圖 | 檔名、門檻 |
| `BACKFILL.pat` / `p17.lin` | 自建回填填充圖樣、虛線線型（紙面 mm） | 依原圖量測 |

需要的套件：`pymupdf ezdxf shapely scipy pillow numpy`（建一個 venv）。
