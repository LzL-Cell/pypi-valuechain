#!/bin/bash
# joern_runner.sh - 自动生成 Python CPG 并导出方法和调用数据

# Joern Python 前端路径（确保已用 sbt build 好）
PY_SRC2CPG="./frontends/pysrc2cpg/target/universal/stage/bin/pysrc2cpg"

# CPG 输出目录
CPG_DIR="./cpgs"
mkdir -p "$CPG_DIR"

# Data 输出目录
DATA_DIR="./data"
mkdir -p "$DATA_DIR"

# 遍历 sources 目录
for pkg in sources/*; do
    NAME=$(basename "$pkg")
    SRC="$pkg/src"

    if [ -d "$SRC" ]; then
        echo "[Joern] Processing $NAME ..."

        # 生成 CPG
        CPG_OUT="$CPG_DIR/$NAME.cpg.bin"
        "$PY_SRC2CPG" "$SRC" -o "$CPG_OUT"

        if [ ! -f "$CPG_OUT/cpg.bin" ]; then
            echo "[Error] CPG not generated for $NAME"
            continue
        fi

        # 调用 Joern REPL 导出方法和调用
        joern --script <<EOF
// 加载 CPG
val cpg = io.shiftleft.semanticcpg.io.CpgLoader.load("$CPG_OUT")

// 导出方法
import java.io._
val methodFile = new PrintWriter(new File("$DATA_DIR/${NAME}_methods.csv"))
methodFile.println("methodFullName")
cpg.method.fullName.l.foreach(methodFile.println)
methodFile.close()

// 导出调用
val callFile = new PrintWriter(new File("$DATA_DIR/${NAME}_calls.csv"))
callFile.println("caller,callee")
cpg.call.foreach { call =>
  val caller = call.method.fullName
  val callee = call.name
  callFile.println(s"\$caller,\$callee")
}
callFile.close()

EOF
        echo "[Joern] Finished $NAME"
    fi
done

echo "[Joern] All packages processed."

