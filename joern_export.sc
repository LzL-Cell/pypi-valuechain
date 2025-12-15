import java.io._

def writeCsv(path: String, rows: Seq[String]): Unit = {
  val pw = new PrintWriter(new File(path))
  rows.foreach(pw.println)
  pw.close()
}

// 当前包名（由 bash 传进来）
val pkg = project.name

// 1. 函数节点
val funcs =
  cpg.method
    .map(m => s"$pkg,${m.fullName}")
    .l

writeCsv(s"data/${pkg}_functions.csv", funcs)

// 2. 函数调用边
val calls =
  cpg.call
    .nameNot("<operator>.*")
    .map(c => s"$pkg,${c.method.fullName},${c.name}")
    .l

writeCsv(s"data/${pkg}_calls.csv", calls)

