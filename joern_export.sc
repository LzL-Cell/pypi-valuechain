// ===== 1. 读取脚本参数 =====
val codePath = scriptArgs("code")
val pkgName  = scriptArgs("name")

println(s"[Joern] codePath = $codePath")
println(s"[Joern] pkgName  = $pkgName")

// ===== 2. 导入源码（必须指定语言）=====
// Python 源码用 "python"
importCode(codePath, pkgName, "python")

// ===== 3. 包 → 函数 映射 =====
cpg.method
  .map(m => s"$pkgName,${m.fullName}")
  .l
  .foreach(println)

// ===== 4. 函数调用关系 =====
cpg.call
  .nameNot("<operator>.*")
  .map(c => s"${c.method.fullName},${c.name}")
  .l
  .foreach(println)

