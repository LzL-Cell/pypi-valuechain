importCode(code, name)

// 包 → 函数
val pf = cpg.method.map(m => s"$name,${m.name}").l
pf.foreach(println)

// 函数调用
val fc = cpg.call
  .nameNot("<operator>.*")
  .map(c => s"${c.method.name},${c.name}")
  .l

fc.foreach(println)
