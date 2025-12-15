// ====== 参数由环境变量提供 ======
val src = sys.env("SRC")
val name = sys.env("NAME")
val out = sys.env.getOrElse("OUT", "output")

importCode(src, name, "python")

import java.io.PrintWriter

val fFun = new PrintWriter(s"$out/${name}_functions.csv")
fFun.println("package,function")
cpg.method.name.l.foreach { m =>
  fFun.println(s"$name,$m")
}
fFun.close()

val fCall = new PrintWriter(s"$out/${name}_calls.csv")
fCall.println("caller,callee")
cpg.call
  .nameNot("<operator>.*")
  .l
  .foreach { c =>
    fCall.println(s"${c.method.fullName},${c.name}")
  }
fCall.close()
