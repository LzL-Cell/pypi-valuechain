#!/bin/bash
JOERN=/home/lzl/bin/joern/joern-cli/joern

mkdir -p data cpgs

for pkg in sources/*; do
  NAME=$(basename "$pkg")
  SRC="$pkg/src"
  OUT="cpgs/$NAME.cpg.bin"

  if [ -d "$SRC" ]; then
    echo "[Joern] Building CPG for $NAME"
    ./frontends/pysrc2cpg/target/universal/stage/bin/pysrc2cpg \
      "$SRC" -o "$OUT"

    echo "[Joern] Exporting data for $NAME"
    $JOERN --load "$OUT" joern_export.sc
  fi
done

