#!/usr/bin/env bash
set -e

JOERN=/home/lzl/bin/joern/joern-cli/joern

SRC_ROOT=./sources
OUT_ROOT=./output

mkdir -p "$OUT_ROOT"

for pkg in "$SRC_ROOT"/*; do
  NAME=$(basename "$pkg")
  SRC="$pkg/src"

  if [ ! -d "$SRC" ]; then
    echo "[skip] $NAME (no src)"
    continue
  fi

  echo "[Joern] Import $NAME"

  # 1️⃣ 导入 Python 源码（关键）
  "$JOERN" --import "$SRC" \
           --language python \
           --project-name "$NAME"

  # 2️⃣ 运行查询脚本（函数 & 调用）
  "$JOERN" --script joern_query.sc \
           --param pkg="$NAME" \
           --param out="$OUT_ROOT"

done
