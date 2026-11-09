# Gary-Style

Gary 的個人美感系統與圖文設計總入口（skill 名稱 `gary-style`）。

```
Gary 的偏好（my-taste.md）
   ↓ 疊加在所有成品上
Gary 的樣板（templates/）── 中國風、文字風、文字設計…，優先使用
   ↓ 沒有合適的才往下找
上游風格（styles.md A～P ＋ guide.md 選購指南）── 15 個第三方審美 skill
   ↓
codex-imagegen 出圖
```

選購指南整理自 [AIPMAndy/Andy-Photo-Skill](https://github.com/AIPMAndy/Andy-Photo-Skill)（MIT）。

## 檔案

| 檔案 | 用途 |
|---|---|
| `SKILL.md` | 流程：做圖、建立樣板、記錄偏好 |
| `my-taste.md` | Gary 的美感偏好與偏好紀錄 |
| `templates/index.md` | 樣板索引 |
| `templates/_template.md` | 新樣板格式 |
| `templates/<分類>/` | 各分類的樣板 |
| `templates/assets/` | 樣板參考圖（只放 Gary 自己的圖） |
| `styles.md` | 上游風格卡 A～P |
| `guide.md` | 選購指南與授權實查表 |
| `setup.sh` | 下載／更新上游 |

## 為什麼不把上游 skill 收進來

這個資料夾會隨 `claude-skills` 倉庫推上 GitHub，但上游授權不一（詳見 `guide.md`）：有的禁止修改與散布、有的限個人非商用、有的沒有授權檔。所以這裡只放自己寫的規則、摘要和樣板；上游原檔由 `setup.sh` 下載到 `~/.claude/gary-style-vendor/`，不進版控。

```bash
bash ~/.claude/skills/gary-style/setup.sh
```

## 上游作者

gc-minimal-zine-poster（LiamGvchi）、photo-abstract-editorial（ZzzLc0405）、photo-relic-editorial（wnby）、photo-revival（dacnay816y62-hub）、gathered-scenes-zine-skill（Zeejay0）、travel-photo-abstraction（Evianis）、qiaomu-mondo-poster-design（joeseesun）、pixel-style-poster-skill（v92388375-gif）、kimi-inspired-poster（Fannie0715）、github-trending-wan-skill（wwwzhouhui）、heytea-style（Hchen1218）、tait-crt-interface-skill（TaiT-tt）、dreamcore-collage-poster（AndrwewHan）、eachlabs/skills（eachlabs）。
