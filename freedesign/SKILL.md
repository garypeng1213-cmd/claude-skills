---
name: freedesign
description: Use when the user says 「看一下那份指南／設計指南／FreeDesign」, or asks to pick a tech stack, UI component library, color palette, font pairing, animation/icon library, or landing-page template for a new project or a UI redesign. A curated developer design-resource guide (by scenario and industry) with recommended stacks, palettes with hex codes, fonts, and anti-pattern / accessibility checklists — read it first, then build the matching design.
---

# FreeDesign 設計資源指南

來源：[AIPMAndy/FreeDesign](https://github.com/AIPMAndy/FreeDesign)（MIT，作者 Andy Liu，資料最後更新 2026-09-14）。完整內容在 `references/freedesign-guide.md`（簡體中文，約 1000 行）。

這是一份**選型與風格參考**，不是實作規範。用它決定「用什麼」，實作仍交給 `frontend-design`（以及選風格時的 `ui-ux-pro-max`）。

## 使用流程

1. **釐清專案情境**：平台（網站／小程序／APP／後台）、產業（SaaS、電商、醫療、金融、創意、AI 產品…）、技術棧限制、既有品牌色。若是重新設計既有介面，先看現有程式碼用了哪些框架與元件庫，不要建議整套換掉，除非使用者要。
2. **只讀相關章節**：不要整份讀進來。用下方行號表 `sed -n 'A,Bp' references/freedesign-guide.md` 或 `grep -n` 取需要的段落。行號若對不上，先 `grep -nE '^#{2,3} ' references/freedesign-guide.md` 重新取得目錄。
3. **一定要看的三段**：對應產業的「精選技術棧組合」、「設計避坑指南」（含產業反模式）、「可訪問性檢查清單」。
4. **向使用者提出選型摘要**（框架、元件庫、配色 hex、字體、動畫、圖示、風格、要避開的反模式），一段簡短清單即可，然後動手做。
5. **實作時**：依選型產出程式碼；避坑清單中的反模式要逐條對照，可訪問性至少 WCAG AA。

## 章節行號表

| 主題 | 行號 |
|---|---|
| AI 代碼生成與設計工具 | 56–72 |
| Figma 設計插件 | 73–116 |
| 網站 UI 組件庫（React / Tailwind / Vue / 其他） | 117–162 |
| 現代設計風格 + 風格組合推薦 | 163–190 |
| 配色方案（工具、按行業、情緒配色） | 191–247 |
| 字體組合（經典、技術類、中文字體、配對工具） | 248–292 |
| 微交互組件（按鈕、載入、表單、通知、骨架屏） | 293–339 |
| 3D 可視化 | 340–351 |
| 動畫庫（React / CSS / 通用） | 352–380 |
| 圖標庫 | 381–393 |
| 小程序開發 | 394–406 |
| 移動 APP（React Native / Flutter / SwiftUI） | 407–440 |
| 後台管理系統 | 441–454 |
| 圖表可視化 | 455–466 |
| 開源設計工具 | 467–475 |
| AI Agents UI 框架 | 476–489 |
| 設計系統 | 490–505 |
| **精選技術棧組合**（SaaS、電商、醫療、金融、移動、創意、AI 產品） | 506–642 |
| **設計避坑指南**（通用誤區、產業反模式、可訪問性清單） | 643–807 |
| Landing Page 模板 | 808–819 |
| 更多資源（插畫、靈感、圖片影片、漸層） | 820–861 |
| 使用指南（5 個場景範例） | 862–893 |
| 推薦資源（最適合 AI 的元件庫、按行業速查） | 894–929 |

## 注意

- 指南是簡體中文；回覆使用者時用繁體中文。
- 資源連結與版本可能過時；要安裝套件時以官方文件／npm 為準。
- 中文字體段落偏大陸環境；台灣專案優先考慮 Noto Sans TC / 思源黑體繁中等。
- 更新指南：重新下載上游 README 覆蓋 `references/freedesign-guide.md`，再用 `grep -nE '^#{2,3} '` 更新上方行號表。
