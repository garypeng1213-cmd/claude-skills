#!/usr/bin/env bash
# 把上游審美 skill 原封不動 clone 到本機 vendor 資料夾（不進 claude-skills 倉庫）。
# 已存在就 git pull 更新。上游授權各自不同，所以這裡只做下載，不改任何檔案。
set -euo pipefail

VENDOR="${GARY_STYLE_VENDOR:-$HOME/.claude/gary-style-vendor}"
mkdir -p "$VENDOR"

REPOS=(
  LiamGvchi/gc-minimal-zine-poster
  ZzzLc0405/photo-abstract-editorial
  wnby/photo-relic-editorial
  dacnay816y62-hub/photo-revival
  Zeejay0/gathered-scenes-zine-skill
  Evianis/travel-photo-abstraction
  joeseesun/qiaomu-mondo-poster-design
  v92388375-gif/pixel-style-poster-skill
  Fannie0715/kimi-inspired-poster
  Hchen1218/heytea-style
  TaiT-tt/tait-crt-interface-skill
  AndrwewHan/dreamcore-collage-poster
  eachlabs/skills
)

for r in "${REPOS[@]}"; do
  dir="$VENDOR/${r#*/}"
  if [ -d "$dir/.git" ]; then
    git -C "$dir" pull -q --ff-only && echo "updated  $r" || echo "FAILED   $r (pull)"
  else
    git clone -q --depth 1 "https://github.com/$r" "$dir" && echo "cloned   $r" || echo "FAILED   $r (clone)"
  fi
done

# skills_collection 很大，只取 github-trending-wan-skill 這一個子資料夾
dir="$VENDOR/skills_collection"
if [ -d "$dir/.git" ]; then
  git -C "$dir" pull -q --ff-only && echo "updated  wwwzhouhui/skills_collection" || echo "FAILED   wwwzhouhui/skills_collection (pull)"
else
  git clone -q --depth 1 --filter=blob:none --sparse https://github.com/wwwzhouhui/skills_collection "$dir" \
    && git -C "$dir" sparse-checkout set github-trending-wan-skill \
    && echo "cloned   wwwzhouhui/skills_collection (github-trending-wan-skill)" \
    || echo "FAILED   wwwzhouhui/skills_collection (clone)"
fi

echo "vendor: $VENDOR"
