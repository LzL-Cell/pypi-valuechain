#!/bin/bash
JOERN=joern

rm -rf joern-workspace
mkdir joern-workspace

for pkg in sources/*; do
  SRC="$pkg/src"
  NAME=$(basename "$pkg")
  if [ -d "$SRC" ]; then
    echo "[Joern] Import $NAME"
    $JOERN --script joern_export.sc \
           --param code="$SRC" \
           --param name="$NAME"
  fi
done
