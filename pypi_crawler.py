import os, re, csv, requests

PYPI = "https://pypi.org/pypi/{}/json"

def clean_dep(dep):
    dep = dep.split(";")[0]
    m = re.match(r"[A-Za-z0-9_.-]+", dep.strip())
    return m.group(0) if m else None

def crawl(root="requests", limit=10):
    visited, queue = set(), [root]
    edges = []

    while queue and len(visited) < limit:
        pkg = queue.pop(0)
        if pkg in visited:
            continue

        print(f"[PyPI] {pkg}")
        info = requests.get(PYPI.format(pkg), timeout=10).json()
        visited.add(pkg)

        for dep in info["info"].get("requires_dist") or []:
            d = clean_dep(dep)
            if d:
                edges.append((pkg, d))
                if d not in visited:
                    queue.append(d)

        download_sdist(pkg, info)

    return visited, edges

def download_sdist(pkg, info):
    for v in sorted(info["releases"], reverse=True):
        for f in info["releases"][v]:
            if f["packagetype"] == "sdist":
                os.makedirs(f"sources/{pkg}", exist_ok=True)
                path = f"sources/{pkg}/{f['filename']}"
                if not os.path.exists(path):
                    r = requests.get(f["url"])
                    open(path, "wb").write(r.content)
                return
