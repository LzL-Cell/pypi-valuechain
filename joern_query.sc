val pkg = params("pkg")

cpg.method
  .map(m => s"$pkg,${m.fullName}")
  .l
  .foreach(println)

