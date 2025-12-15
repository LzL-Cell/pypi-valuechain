import csv, subprocess
from pypi_crawler import crawl
from extract_sources import extract_all

pkgs, edges = crawl()

# 保存 package 图
with open("data/package_edges.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["from", "to"])
    w.writerows(edges)

with open("data/packages.csv", "w") as f:
    for p in pkgs:
        f.write(p + "\n")

extract_all()

# 调用 Joern
subprocess.run(["bash", "joern_runner.sh"])
