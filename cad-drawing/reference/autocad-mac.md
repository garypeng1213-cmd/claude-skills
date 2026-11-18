# AutoCAD 2025 for Mac 自動化

用 computer-use（`com.autodesk.AutoCAD2025`）控制畫面；指令盡量寫成 .scr 或 .lsp 檔，再用 `_SCRIPT` 執行。不要直接打長串 LISP，空白會打斷輸入。

## 1. 基本操作

- 指令輸入列在全螢幕座標約 (640,742)。每次先點一下輸入列、按 Esc，再輸入指令。
- F2 會開關指令歷史視窗：要讀結果時開，讀完要關掉，否則它會搶焦點。
- 若點擊時出現「A Claude window is covering that point」，先 `open_application` 把 AutoCAD 帶到前面再點。
- 執行腳本：

  ```
  FILEDIA ⏎ 0 ⏎ _SCRIPT ⏎ <.scr 絕對路徑> ⏎
  ```

  腳本最後要 `(setvar "FILEDIA" 1)`。
- 讀回結果：
  - LISP 用 `(princ ...)` 輸出到指令列，再開 F2 截圖讀。
  - 出圖結果直接檢查 PDF 檔有沒有產生。
- 先用小測試圖試新的做法，例如文字樣式、標註，確認可行再套到正式圖。

## 2. 支援檔路徑

```
~/Library/Application Support/Autodesk/AutoCAD 2025/R25.0/roaming/@en@/
  Support/                    ← .pat、.lin（.pat 也放 Support/Hatch Patterns）
  Plotters/Plot Styles/       ← .ctb
```

## 3. 關聯標註（DIMREASSOCIATE）

- 設定：`(setvar "OSMODE" 0) (setvar "OSOPTIONS" 7)`。
- 每道標註先 `ZOOM W` 到該標註附近，**不要用透明 zoom**（試過會失敗）。
- 指令格式（`""` 表示略過該點）：

  ```lisp
  (command "_ZOOM" "_W" p_min p_max)
  (command "_DIMREASSOCIATE" e "" "_endp" p1 "_nea" p2)
  ```

- 找吸附點（`scripts/snapfix.py`）：
  - 定義點如果剛好在幾何上，直接用。
  - 不在幾何上時，沿延伸線方向射 15 cm，找第一個交點。
  - 交點是頂點用 `_endp`，在線段中間用 `_nea`，都找不到就略過。
- 檢查：
  - 關聯狀態：DIMENSION 的 330 反應器指向 DIMASSOC 物件，看它的 group 90（1 = 第一點、2 = 第二點、3 = 兩點）。程式見 `scripts/chk.lsp`。
  - 量測值：看 group 42。
- **關聯後量測值變 0 或錯誤**時：
  1. DIMDISASSOCIATE。
  2. 用 entmod 把 group 13、14 改回原定義點。
  3. 只關聯能正確吸附的那一點。
- 不照比例的尺寸（文字覆寫的）或詳圖尺寸可能無法關聯，回報時要列出來。

## 4. 修正跑位（關聯或重生後必查）

- 文字位置（`scripts/txt.lsp`）：

  ```lisp
  (setq ed (subst (list 11 x y 0.0) (assoc 11 ed) ed))
  (setq ed (subst (cons 70 (logior 128 (cdr (assoc 70 ed)))) (assoc 70 ed) ed))
  (entmod ed) (entupd e)
  ```

  70 的 128 位元表示「使用者自訂文字位置」。
- 尺寸線位置（`scripts/dl.lsp`）：改 group 10。水平標註改 Y，垂直標註改 X。

## 5. 出圖（-PLOT）

**一定要先切到配置頁**。在模型頁跑，問答順序會不同，會卡在「是否繼續打印」。

```lisp
(setvar "CTAB" (car (layoutlist)))
(progn (setvar "FILEDIA" 0)
  (command "-PLOT" "Y" "" "DWG To PDF.pc3" "ISO full bleed A3 (420.00 x 297.00 MM)"
           "M" "L" "N" "L" "1:1" "0,0" "Y" "XXX-LW.ctb" "Y" "N" "N" "N"
           "/絕對路徑/輸出.pdf" "Y" "Y") (princ))
(setvar "FILEDIA" 1)
(command "_QSAVE")
```

- CTB 檔名必須是 ASCII，中文檔名在 -PLOT 裡選不到。
- 存檔：第一次用 `SAVEAS` 存成 2018 格式 DWG，之後用 QSAVE。
