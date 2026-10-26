---
name: codex-imagegen
description: Use when the user asks to generate, create, or edit a raster image — 生圖、畫一張圖、插畫、icon、海報素材、網站配圖、概念圖、改圖、換背景、去背、主體替換 — and the result should be a PNG bitmap rather than SVG, HTML/CSS, or code-drawn graphics
---

# Codex Image Generation

## Overview

Claude Code 沒有內建生圖。點陣圖透過本機 Codex CLI 的內建 `image_gen` 產生。

**分工原則：Codex 只做「呼叫 image_gen 一次」這一步，其餘全部由 Claude Code 做**——寫 prompt、挑參考圖、存檔、看圖驗收、決定要不要重生。

原因：Codex 每做一個動作就是一輪，每一輪都重送整包上下文（約 2 萬 tokens 起跳）。讓它自己找檔、複製、看圖、重生，一張圖會從 2 輪膨脹到 4–12 輪。

**不適用：** SVG / icon 系統 / 圖表 / 可用 HTML、CSS、canvas 直接畫出來的東西——那些直接寫程式。

## 指令

一律用同資料夾的 `codex_image.py`，不要自己組 `codex exec`（單張約 1–2 分鐘；Bash `timeout` 見下方「逾時規則」）：

```bash
# 純生圖
python3 ~/.claude/skills/codex-imagegen/codex_image.py --out "<資料夾>/<檔名>.png" \
  'A flat vector-style fox mascot, centered, 1:1, plain white background'

# 改圖／帶參考圖：--ref 可重複，最多 5 張；prompt 長就寫進檔案
python3 ~/.claude/skills/codex-imagegen/codex_image.py --out "<資料夾>/<檔名>.png" \
  --ref "<場景圖>" --ref "<主體照片>" --prompt-file "<prompt.txt>"
```

腳本會：把參考圖縮到長邊 1536 的暫存副本、以路徑交給 `image_gen`（不附進對話）、從 `~/.codex/generated_images/<session id>/` 取出 PNG 複製到 `--out`，最後印出 `saved:` 與 `usage:`（輪數、tokens、5 小時與每週額度已用百分比）。

輸出約 1254×1254（1:1 時）；其他比例在 prompt 指定，再用 `sips` 縮放。

## 逾時規則（2026-10-12 起）

**60 秒內沒開工作階段，或 5 分鐘內圖沒生出來，就把 Codex 整個關掉重來。** 腳本已內建，不用自己包迴圈：

- **60 秒啟動檢查**（`--startup`）：正常的 Codex 一兩秒內就會建立工作階段；卡住的那種永遠不會建立。60 秒還沒有就直接關掉重來，這種情況沒生成也沒扣額度。判斷方式是看 `~/.codex/sessions/` 有沒有出現記錄這次暫存工作目錄的 rollout 檔。

- **啟動卡住的已知原因（2026-10-13）**：`codex exec` 會等繼承來的 stdin（log 第一行 `Reading additional input from stdin...`），stdin 沒關就永遠不開工作階段。腳本已用 `stdin=DEVNULL` 啟動 Codex；修正前前景執行 8 次卡 7 次，背景執行 3 次全過，修正後前景第 1 次就過（只驗證了這 1 次）。自己直接跑 `codex exec` 時記得加 `< /dev/null`。
- 每次嘗試上限 300 秒（`--timeout`）。到時間就關掉 Codex 的**整個行程樹**再重跑，預設最多 3 次（`--attempts`）。3 次都失敗就停下來回報使用者，不要再包一層迴圈硬跑。
- 依據：實測 45 張成功的圖，中位數 63 秒、最慢 185 秒；卡住的那種永遠不會自己好。
- **一定要關整個行程樹**：`codex` 是 node 外殼包原生程式，只殺外殼會留下原生行程變孤兒，一次一個越積越多（2026-10-12 實際發生，積了 5 個）。腳本用 process group 加逐一補殺處理；不要改回 `subprocess.run(timeout=...)`。
- 逾時那一刻如果圖其實已經存下來，腳本會直接採用，不會重生重扣。
- 腳本印出的訊息會說明是哪一種：`no session after 60s`（啟動卡住，沒扣額度）或 `no image after 300s`（工作階段開了但沒出圖，可能已扣額度）。
- Bash `timeout` 要蓋過全部嘗試：最壞情況是 3×300 秒，設 `960000`；長時間的請用背景執行。
- 懷疑有殘留行程時檢查：`ps -axo pid,ppid,etime,command | grep codex-darwin | grep codex-image-`，ppid 是 1 的就是孤兒。

## 流程

1. 用 Read 看過參考圖，把需求寫成完整英文 prompt。背景（white / transparent / 指定色）一定明講；改圖要把「保留什麼」逐項寫出來。
2. 參考圖最多 5 張：場景／原圖 1 張，其餘給主體的正臉、全身比例、最接近目標姿勢的照片。prompt 裡用 `reference image 1…5` 依 `--ref` 順序指稱。
3. `--out` 的資料夾要先存在；使用者沒指定就放專案的 `assets/`。
4. 先跑 **1 張**，看 `usage:` 的額度百分比，再決定後面怎麼跑。
5. **用 Read 看圖驗收**，不要只看到 `saved:` 就回報完成。
6. 不符需求就改 prompt 重跑，**最多重試 2 次**，還不行就把現況和問題回報使用者。

## 常見錯誤

| 錯誤 | 正解 |
|---|---|
| 叫 Codex「複製到某路徑」「回報路徑」「檢查結果」 | 每件事多一輪以上。Codex 只生圖，其餘腳本和 Claude 做 |
| 用 `-i` 把參考圖附給 Codex | 圖會進對話、每輪重送。用 `--ref`，腳本改傳路徑 |
| 參考圖超過 5 張 | `image_gen` 直接報錯。挑最關鍵的 5 張 |
| prompt 開頭加 `$imagegen` | 會載入 Codex 的 19KB 生圖技能，它會要求自己複製檔案和驗收 |
| 改圖只說「其他不變」 | 背景仍可能被換掉（實測透明底變黑底）。把要保留的背景寫明 |
| 主體描述照抄使用者給的文字 | 先對照實際照片；描述和照片不符時模型會跟著文字走 |
| 一次平行全開 | 額度會在看到結果前燒完。先 1 張，之後每批 2–3 張，盯著 `usage:` |
| 沒設 Bash timeout | 預設 2 分鐘，會在生完前被中斷；要蓋過 3 次嘗試，設 `960000` |
| 逾時後自己再包迴圈重試 | 腳本已經會關掉重來 3 次；外面再包一層，Codex 掛掉時會空轉幾十分鐘。3 次失敗就回報 |

## 成本

計入使用者的 ChatGPT 方案額度。實測（2026-10，Plus 方案）：

| 做法 | 輪數 | input tokens／張 | 5 小時額度／張 |
|---|---|---|---|
| 本腳本（帶 5 張參考圖） | 2 | 約 4.6–4.8 萬 | 約 1% |
| 舊做法（`-i` 附圖 + 叫 Codex 存檔） | 4–12 | 21–62 萬 | 約 5% |

整批要生的圖超過 5 張，開跑前先跟使用者確認張數。`usage:` 顯示 5 小時額度用到 80% 就停下來回報，不要硬跑。
