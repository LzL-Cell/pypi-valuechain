#!/bin/bash

JOERN=/home/lzl/bin/joern/joern-cli/joern

for pkg in sources/*; do
  NAME=$(basename "$pkg")
  SRC="$pkg/src"

  if [ -d "$SRC" ]; then
    echo "[Joern] Import $NAME"

    $JOERN <<EOF
importCode("$SRC", "$NAME", "python")
cpg.method.map(m => "$NAME," + m.fullName).l.foreach(println)
cpg.call.nameNot("<operator>.*")
  .map(c => c.method.fullName + "," + c.name)
  .l.foreach(println)
exit
EOF

  fi
done
