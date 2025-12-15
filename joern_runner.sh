#!/usr/bin/env bash
set -e

JOERN=/home/lzl/joern/joern-cli/joern
JOERN_IMPORT=/home/lzl/joern/joern-cli/joern-import

SRC_ROOT=./sources
OUT_ROOT=./output

mkdir -p "$OUT_ROOT"

for pkg in "$SRC_ROOT"/*; do
  NAME=$(basename "$pkg")
  SRC="$pkg/src"

  if [ ! -d "$SRC" ]; then
    continue
  fi

  echo "[Joern] Import $NAME"

  "$JOERN_IMPORT" "$SRC" --language python

  PKG="$NAME" OUT="$OUT_ROOT" \
  "$JOERN" --script joern_query.sc

done
