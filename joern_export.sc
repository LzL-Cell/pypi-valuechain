// ===============================
// Joern script (params-based)
// ===============================

// 1. 读取命令行参数
val codePath = params("code")
val pkgName  = params("name")

println(s"[Joern] codePath = $codePath")
println(s"[Joern] pkgName  = $pkgName")

// 2. 导入源码（Python 项目必须指定 language）
importCode(codePath, pkgName, "python")

// 3. Package -> Function
cpg.method
  .map(m => s"$pkgName,${m.fullName}")
  .l
  .foreach(println)

// 4. Function call graph
cpg.call
  .nameNot("<operator>.*")
  .map(c => s"${c.method.fullName},${c.name}")
  .l
  .foreach(println)
