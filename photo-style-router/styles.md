# 風格卡

每張卡是我自己整理的摘要，用來「選」風格。真正的審美規則和 prompt 模板在上游原檔，選定後才去讀。

`$V` = `~/.claude/photo-style-vendor`

欄位說明：
- **素材**：需要照片／只要文字／都可以
- **照片處理**：保留原照（照片原樣出現在成品）／重繪（照片只當參考，成品是插畫）
- **商用**：✅ MIT 可商用（保留出處）／❌ 只限個人非商用

---

## A. minimal-zine — 極簡紙感 Zine 海報

- 上游：gc-minimal-zine-poster（MIT ✅）
- 素材：都可以（一句話、主題、文章、物件、照片）
- 長相：大量留白、紙張質感、一個小小的拼貼或焦點物、實驗性排版、只有一個強調色
- 情緒：安靜、詩意、輕聲說話
- 最適合：一句話海報、金句卡、文章封面、安靜的 IG/小紅書首圖
- 不適合：要很吵、很滿、很有衝擊力的封面
- 入口：`$V/gc-minimal-zine-poster/SKILL.md`（它會指示再讀 `references/` 下的 style-system、prompt-compiler、variation-engine、quality-gate）

## B. photo-relic — 照片＋版畫記憶

- 上游：photo-relic-editorial（MIT ✅）
- 素材：需要照片
- 照片處理：保留原照（上方）＋下方暖白紙上的「記憶版畫」
- 長相：直式；下半部是幾筆墨塊、深藍／墨黑／灰綠，偶爾一點朱紅或暖金；小而詩意的標籤式標題
- 情緒：克制、東方、時間感、記憶
- 最適合：家庭照、建築、街景、黃昏；要做成「系列」的封面（抖音、IG 連載）
- 跟 C、D 的差別：有紙感與版畫墨塊，最有「作品感」
- 入口：`$V/photo-relic-editorial/SKILL.md` ＋ `references/afterimage-editorial-prompt.md`

## C. abstract-editorial — 照片＋乾淨抽象面板

- 上游：photo-abstract-editorial（自訂授權，非商用 ❌）
- 素材：需要照片
- 照片處理：保留原照（上方）＋下方平整象牙白面板上的抽象構成
- 長相：沒有紙紋、沒有漸層，極乾淨；抽象記號只畫照片裡的空間關係；英文襯線小標題（2～5 字）
- 情緒：理性、建築感、美術館目錄
- 最適合：構圖本身就漂亮的照片（建築、幾何、人在大空間裡）
- 跟 B 的差別：更冷、更乾淨、更「設計」，沒有手作溫度
- 入口：`$V/photo-abstract-editorial/SKILL.md` ＋ `references/photo-abstract-editorial-prompt.zh-CN.md`

## D. travel-abstraction — 旅行照抽象化（嚴格版）

- 上游：travel-photo-abstraction（自訂授權：不得修改、不得散布，可自用 ⚠️ 商用請先讀原文）
- 素材：需要照片（最好是旅行照，最好有 EXIF 日期）
- 照片處理：保留原照，**像素級不動**（原尺寸、不縮放）＋下方新生成的抽象面板，帶一個數字、日期、短句
- 長相：上下雙聯；下方是從照片拆解、提煉後重組的構成，參考上游附的 19 張風格圖
- 最適合：旅行紀錄、一地一張的系列貼文
- 注意：流程最嚴格，要跑上游的 Python 腳本（`scripts/finalize_artwork.py`）合成並驗證，看到 `DELIVERY PASS` 才算成功；需要 Pillow
- 入口：`$V/travel-photo-abstraction/travel-photo-abstraction/SKILL.md`

## E. photo-revival — 照片重繪成手繪插畫

- 上游：photo-revival（MIT ✅）
- 素材：需要照片
- 照片處理：重繪（成品沒有照片，是手繪插畫）
- 長相：3:4 直式；80～88% 白紙留白；主體很小（約 10～16%）、局部鮮豔顏色；鉛筆、水彩質感；小小的手寫字或日期
- 情緒：日記、溫柔、日常
- 最適合：日常隨拍、寵物、人像、餐點，想要「手帳感」
- 入口：`$V/photo-revival/SKILL.md`（很短，整份讀完）

## F. gathered-scenes — 實景撕紙拼貼

- 上游：gathered-scenes-zine-skill／scenes-gathered-zine-v1-3（個人非商用授權 ❌）
- 素材：需要照片
- 照片處理：保留原照當「錨」，外面長出大片抽象插畫，照片和紙之間是明顯的手撕纖維邊
- 長相：3:5 直式；一個高彩度顏色當結構；大留白；小小的英文或中文短字
- 情緒：觸感、手作、安靜但有層次
- 最適合：風景、植物、街角，想要「拼貼 zine」感
- 注意：上游資料夾裡有一個 macOS `.app`（實況照片匯入器），**不要執行**
- 入口：`$V/gathered-scenes-zine-skill/skills/scenes-gathered-zine-v1-3/SKILL.md`

## G. scene-distillation — 影像蒸餾（照片只當靈感）

- 上游：gathered-scenes-zine-skill／scene-distillation-zine-v1-3（個人非商用授權 ❌）
- 素材：需要照片
- 照片處理：重繪（照片完全不出現，只取它的情緒與意象）
- 長相：3:5 或 5:3；一個藝術命題、一個情緒張力；高彩度；字體自由、可以很有作者感；可選「單色塊模式」
- 情緒：強烈、有觀點、像獨立藝術作品
- 最適合：想表達一種感受，而不是記錄一個地方
- 入口：`$V/gathered-scenes-zine-skill/skills/scene-distillation-zine-v1-3/SKILL.md`

## H. mondo — Mondo 絲網印刷海報

- 上游：qiaomu-mondo-poster-design（MIT ✅）
- 素材：只要文字（一句話、書名、片名、觀點）；也能圖生圖
- 長相：2～5 色絲網印刷、平塗色塊、網點、剪影、負空間說故事、復古字體
- 情緒：大膽、有衝擊力、有故事
- 最適合：影片封面、讀書筆記配圖、書封、專輯封面、觀點海報；內建平台比例（公眾號 21:9、小紅書 3:4、文章 16:9、書封 9:16、專輯 1:1）
- 注意：上游的 `scripts/generate_mondo*.py` 走它自己的 AI Gateway API，**不要用**；出圖一律走 codex-imagegen
- 入口：`$V/qiaomu-mondo-poster-design/SKILL.md`（需要時再讀 `references/artist-styles.md`、`genre-templates.md`）

## I. pixel-poster — 細點陣網點印刷海報

- 上游：pixel-style-poster-skill（MIT ✅）
- 素材：都可以（主題、物件、情緒、照片）
- 長相：3:4 直式；一兩個大主體用很細的點陣／網點組成，靠密度做明暗；單色或近單色；暖白紙；不是 8-bit 遊戲像素風
- 情緒：復古數位、冷靜、日系雜誌
- 最適合：AI／科技產品封面、人像特寫、動物、花
- 入口：`$V/pixel-style-poster-skill/SKILL.md`（很長，以 Fine Bitmap Prompt Compiler 段落為主）

## J. heytea-doodle — 實物照片＋歪扭塗鴉

- 上游：heytea-style（MIT ✅；但不得使用喜茶官方 logo、吉祥物、包裝，也不能暗示合作）
- 素材：需要照片，而且要有一個清楚的實物主體（飲料、食物、小物）
- 照片處理：保留實物照片，旁邊加粗黑線、兒童手寫字、小人塗鴉
- 長相：大量白底、笨拙可愛的手繪線、有字版或無字版
- 情緒：輕鬆、好笑、生活感
- 最適合：飲料、甜點、餐點、開箱，小紅書日常
- 不做：上游的「桌寵」流程（要安裝執行環境），除非使用者明確要求
- 入口：`$V/heytea-style/SKILL.md` ＋ `references/style-guide.md`（有字版再加 `references/lettering-guide.md`）

## K. mono-color — 單色／雙色印刷（本機已有）

- 來源：你本機的 `mono-color` skill（直接用 Skill 工具呼叫，不在 vendor 裡）
- 素材：都可以
- 長相：一到兩種油墨、孔版／risograph 感、強烈的襯線／無襯線字體張力、短句
- 最適合：文化活動海報、宣言、編輯頁面
