import os, tarfile, zipfile

def extract_all():
    for pkg in os.listdir("sources"):
        pkg_dir = f"sources/{pkg}"
        for f in os.listdir(pkg_dir):
            path = f"{pkg_dir}/{f}"
            out = f"{pkg_dir}/src"
            if f.endswith(".tar.gz"):
                tarfile.open(path).extractall(out)
            elif f.endswith(".zip"):
                zipfile.ZipFile(path).extractall(out)
