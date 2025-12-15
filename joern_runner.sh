#!/bin/bash

JOERN=/home/lzl/bin/joern/joern-cli/joern
PYSRC2CPG=./frontends/pysrc2cpg/pysrc2cpg.sh

mkdir -p cpgs

for pkg in sources/*; do
  NAME=$(basename "$pkg")
  SRC="$pkg/src"
  OUT="cpgs/$NAME.cpg.bin"

  if [ -d "$SRC" ]; then
    echo "[CPG] Building $NAME"
    $PYSRC2CPG "$SRC" -o "$OUT"

    echo "[Joern] Query $NAME"
    $JOERN --load "$OUT" <<EOF
cpg.method.map(m => "$NAME," + m.fullName).l.foreach(println)
exit
EOF
  fi
done
