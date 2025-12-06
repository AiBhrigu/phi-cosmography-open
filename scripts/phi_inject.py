import os
from bs4 import BeautifulSoup

HEADER = open("components/phi-header.html", encoding="utf8").read()
FOOTER = open("components/phi-footer.html", encoding="utf8").read()

CSS = """
<link rel="stylesheet" href="/theme/system.css">
<link rel="stylesheet" href="/theme/phi_theme.css">
"""

SKIP_DIRS = ["dist", "_backup", "_backup_A3", "_backup_phi", "_backup_mobile"]
SKIP_PREFIXES = ["_", "."]

def should_skip(path):
    parts = path.split("/")
    # skip if any directory matches skip dirs
    if any(d in parts for d in SKIP_DIRS):
        return True
    # skip backup-like directories
    if any("backup" in p.lower() for p in parts):
        return True
    # skip files with prefix
    if os.path.basename(path).startswith(tuple(SKIP_PREFIXES)):
        return True
    return False

def process(path):
    with open(path, "r", encoding="utf8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    if soup.head and "/theme/phi_theme.css" not in html:
        soup.head.append(BeautifulSoup(CSS, "html.parser"))

    body = soup.body
    if body:
        if "phi-header" not in html:
            body.insert(0, BeautifulSoup(HEADER, "html.parser"))
        if "phi-footer" not in html:
            body.append(BeautifulSoup(FOOTER, "html.parser"))

    with open(path, "w", encoding="utf8") as f:
        f.write(str(soup))

def walk():
    for root, dirs, files in os.walk("."):
        # prune dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and "backup" not in d.lower()]
        for file in files:
            if not file.endswith(".html"):
                continue
            path = os.path.join(root, file)
            if should_skip(path):
                continue
            print("→ Injecting into", path)
            process(path)

if __name__ == "__main__":
    walk()
    print("✓ φ-Inject v2.3 clean & safe")
