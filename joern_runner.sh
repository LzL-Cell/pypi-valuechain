#!/bin/bash
set -e

# ===============================
# Joern 可执行文件路径
# ===============================
JOERN="$HOME/bin/joern/joern-cli/joern"
PYCPG_BIN="$HOME/joern/joern-cli/frontends/pysrc2cpg/target/universal/stage/bin/pysrc2cpg"

WORKSPACE="$HOME/example/pypi-valuechain/workspace"
CPG_DIR="$WORKSPACE/cpgs"
CSV_DIR="$WORKSPACE/data"   # 改成 data 文件夹

mkdir -p "$WORKSPACE" "$CPG_DIR" "$CSV_DIR"

# ===============================
# 遍历 sources 下所有 Python 包
# ===============================
for pkg in sources/*; do
  NAME=$(basename "$pkg")
  SRC="$pkg/src"

  if [ -d "$SRC" ]; then
    echo "[Joern] Processing $NAME"

    OUT="$CPG_DIR/$NAME.cpg.bin"
    METHOD_CSV="$CSV_DIR/${NAME}_methods.csv"
    CALL_CSV="$CSV_DIR/${NAME}_calls.csv"

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
      echo "[INFO] CPG exists for $NAME, skipping CPG generation."
    fi

    # ===========================
    # 生成查询脚本
    # ===========================
    QUERY_SCRIPT=$(mktemp /tmp/joern_query_XXXX.sc)
    cat > "$QUERY_SCRIPT" <<EOF
import io.shiftleft.semanticcpg.language._

// loadCpg 返回 Option[Cpg]
val cpgOpt = loadCpg("$OUT")

cpgOpt match {
  case Some(cpg) =>
    // 输出方法 CSV
    val methodFile = new java.io.PrintWriter("$METHOD_CSV")
    cpg.method.map(_.fullName).l.foreach(methodFile.println)
    methodFile.close()

    // 输出调用 CSV
    val callFile = new java.io.PrintWriter("$CALL_CSV")
    cpg.call.nameNot("<operator>.*").map(c => c.method.fullName + "," + c.name).l.foreach(callFile.println)
    callFile.close()

  case None =>
    println(s"[ERROR] Failed to load CPG from $OUT")
}

exit
EOF

    # ===========================
    # 调用 Joern 执行查询
    # ===========================
    echo "[Joern] Running queries for $NAME..."
    "$JOERN" --script "$QUERY_SCRIPT"

    rm -f "$QUERY_SCRIPT"
  fi
done

echo "[Joern] All done. Methods and calls CSVs are in $CSV_DIR"
