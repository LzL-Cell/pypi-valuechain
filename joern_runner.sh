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
    continue
  fi

  echo "[Joern] Import $NAME"

  SRC="$SRC" NAME="$NAME" OUT="$OUT_ROOT" \
  "$JOERN" --script joern_repl.sc

done
