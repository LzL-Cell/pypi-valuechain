#!/bin/bash
set -e

# ===============================
# Joern 可执行文件路径
# ===============================
JOERN="$HOME/bin/joern/joern-cli/joern"
PYCPG_BIN="$HOME/joern/joern-cli/frontends/pysrc2cpg/target/universal/stage/bin/pysrc2cpg"
WORKSPACE="$HOME/example/pypi-valuechain/workspace"
CPG_DIR="$WORKSPACE/cpgs"

mkdir -p "$WORKSPACE" "$CPG_DIR"

# ===============================
# 遍历 sources 下所有 Python 包
# ===============================
for pkg in sources/*; do
  NAME=$(basename "$pkg")
  SRC="$pkg/src"

  if [ -d "$SRC" ]; then
    echo "[Joern] Processing $NAME"

    OUT="$CPG_DIR/$NAME.cpg.bin"

    # ===========================
    # 生成 CPG
    # ===========================
    if [ ! -f "$OUT" ]; then
      if [ ! -f "$PYCPG_BIN" ]; then
        echo "[ERROR] pysrc2cpg 可执行文件不存在，请先 build: $PYCPG_BIN"
        exit 1
      fi

      echo "[Joern] Generating CPG for $NAME..."
      "$PYCPG_BIN" "$SRC" -o "$OUT"
    else
      echo "[INFO] CPG already exists for $NAME, skipping generation."
    fi

    # ===========================
    # 调用 Joern 查询
    # ===========================
    echo "[Joern] Loading CPG for $NAME"
    "$JOERN" --script <<EOF
// 加载 CPG
cpg = io.shiftleft.codepropertygraph.CpgLoader.loadFrom("$OUT")

// 输出方法信息
cpg.method.name.l.foreach(println)

// 输出调用信息
cpg.call.nameNot("<operator>.*").map(c => c.method.fullName + "," + c.name).l.foreach(println)
exit
EOF

  fi
done

