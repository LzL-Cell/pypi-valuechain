import os
import re
import csv
import time
import json
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# =========================
# 全局配置
# =========================

PYPI_SIMPLE = "https://pypi.org/simple/"
PYPI_JSON = "https://pypi.org/pypi/{}/json"

BASE_DIR = "pypi_data"
SDIST_DIR = os.path.join(BASE_DIR, "sdist")
META_DIR = os.path.join(BASE_DIR, "meta")
EDGE_FILE = os.path.join(BASE_DIR, "dependencies.csv")

HEADERS = {
    "User-Agent": "Academic PyPI crawler (contact: your_email@example.com)"
}

REQUEST_DELAY = 0.2  # 限速，防止封 IP

os.makedirs(SDIST_DIR, exist_ok=True)
os.makedirs(META_DIR, exist_ok=True)

# =========================
# 工具函数
# =========================

def clean_dep(dep: str):
    """
    从 requires_dist 中提取包名
    """
    dep = dep.split(";")[0]
    m = re.match(r"[A-Za-z0-9_.-]+", dep.strip())
    return m.group(0).lower() if m else None


def get_all_packages():
    """
    从 PyPI Simple API 获取所有包名
    """
    print("[*] Fetching PyPI package index ...")
    r = requests.get(PYPI_SIMPLE, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    packages = sorted({a.text.strip().lower() for a in soup.find_all("a")})

    print(f"[+] Total packages found: {len(packages)}")
    return packages


def download_latest_sdist(pkg, info):
    """
    下载最新版本的 sdist
    """
    releases = info.get("releases", {})
    for version in sorted(releases, reverse=True):
        for f in releases[version]:
            if f.get("packagetype") == "sdist":
                path = os.path.join(SDIST_DIR, f["filename"])
                if not os.path.exists(path):
                    r = requests.get(f["url"], headers=HEADERS, timeout=30)
                    with open(path, "wb") as out:
                        out.write(r.content)
                return


def process_package(pkg, writer):
    """
    处理单个包：
    - 下载 JSON
    - 抽取依赖
    - 下载 sdist
    """
    meta_path = os.path.join(META_DIR, f"{pkg}.json")
    if os.path.exists(meta_path):
        return  # 已处理，断点续跑

    try:
        r = requests.get(PYPI_JSON.format(pkg), headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return

        info = r.json()

        # 保存元数据
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(info, f)

        # 写依赖边
        requires = info["info"].get("requires_dist") or []
        for dep in requires:
            d = clean_dep(dep)
            if d:
                writer.writerow([pkg, d])

        # 下载源码
        download_latest_sdist(pkg, info)

    except Exception as e:
        print(f"[!] Error processing {pkg}: {e}")


# =========================
# 主程序
# =========================

def main():
    packages = get_all_packages()

    with open(EDGE_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(["from", "to"])

        for pkg in tqdm(packages):
            process_package(pkg, writer)
            time.sleep(REQUEST_DELAY)


if __name__ == "__main__":
    main()
