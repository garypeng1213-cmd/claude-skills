# photo-style-router

圖文設計的「選風格」總入口。分析素材與用途 → 推薦風格 → 載入該風格的上游規則 → 用 codex-imagegen 出圖。

清單與分類參考自 [AIPMAndy/Andy-Photo-Skill](https://github.com/AIPMAndy/Andy-Photo-Skill)（MIT）。

## 為什麼不把上游 skill 收進來

這個資料夾會隨 `claude-skills` 倉庫推上 GitHub，但上游授權不一：

| 上游 | 授權 | 處理 |
|---|---|---|
| gc-minimal-zine-poster、photo-relic-editorial、photo-revival、qiaomu-mondo-poster-design、pixel-style-poster-skill、heytea-style | MIT | 可收，但為了一致與方便更新，同樣只在本機 clone |
| photo-abstract-editorial | 保留所有權利，限個人非商用 | 不收，只在本機 clone |
| gathered-scenes-zine-skill | 個人非商用授權 | 不收，只在本機 clone |
| travel-photo-abstraction | 禁止修改與散布，可自用 | 不收，只在本機 clone、原樣使用 |

所以本資料夾只放：我自己寫的路由規則（`SKILL.md`）、風格摘要（`styles.md`）、下載腳本（`setup.sh`）。上游原檔由 `setup.sh` 下載到 `~/.claude/photo-style-vendor/`，不進版控。

## 安裝／更新上游

```bash
bash ~/.claude/skills/photo-style-router/setup.sh
```

## 上游作者

- gc-minimal-zine-poster — LiamGvchi
- photo-abstract-editorial — ZzzLc0405
- photo-relic-editorial — wnby
- photo-revival — dacnay816y62-hub
- gathered-scenes-zine-skill — Zeejay0
- travel-photo-abstraction — Evianis
- qiaomu-mondo-poster-design — joeseesun
- pixel-style-poster-skill — v92388375-gif
- heytea-style — Hchen1218
