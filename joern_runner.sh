#!/bin/bash

JOERN=~/bin/joern/joern-cli/joern
PYSRC2CPG=~/joern/joern-cli/frontends/pysrc2cpg/target/universal/stage/bin/pysrc2cpg

mkdir -p cpgs results

for pkg in sources/*; do
  NAME=$(basename "$pkg")
  SRC="$pkg/src"
  CPG="cpgs/$NAME.cpg.bin"

  if [ -d "$SRC" ]; then
    echo "[CPG] Generating $NAME"
    $PYSRC2CPG "$SRC" -o "$CPG"

    echo "[Joern] Query $NAME"
    $JOERN --import "$CPG" --script joern_query.sc \
      --params pkg="$NAME" > "results/$NAME.csv"
  fi
done

