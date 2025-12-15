import java.io.PrintWriter

// 从环境变量读参数
val pkg = sys.env.getOrElse("pkg", "unknown")
val out = sys.env.getOrElse("out", "output")

// ========== 函数列表 ==========
val fFun = new PrintWriter(s"$out/${pkg}_functions.csv")
fFun.println("package,function")

cpg.method.name.l.foreach { m =>
  fFun.println(s"$pkg,$m")
}
fFun.close()

// ========== 调用关系 ==========
val fCall = new PrintWriter(s"$out/${pkg}_calls.csv")
fCall.println("caller,callee")

cpg.call
  .nameNot("<operator>.*")
  .l
  .foreach { c =>
    fCall.println(s"${c.method.fullName},${c.name}")
  }

fCall.close()
