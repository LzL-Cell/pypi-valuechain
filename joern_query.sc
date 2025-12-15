val out = new java.io.PrintWriter("data/functions.csv")

out.println("package,function")

cpg.method.foreach { m =>
  out.println(s"${project.name},${m.fullName}")
}

out.close()
