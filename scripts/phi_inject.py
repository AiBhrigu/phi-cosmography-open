import os
from bs4 import BeautifulSoup

HEADER = open("components/phi-header.html", encoding="utf8").read()
FOOTER = open("components/phi-footer.html", encoding="utf8").read()

CSS_LINKS = """
<link rel="stylesheet" href="/theme/system.css">
<link rel="stylesheet" href="/theme/phi_theme.css">
"""

def process_file(path):
    with open(path, encoding="utf8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # HEAD: add CSS if missing
    if soup.head:
        if "/theme/phi_theme.css" not in html:
            soup.head.append(BeautifulSoup(CSS_LINKS, "html.parser"))

    # BODY: wrap content inside grid + header/footer
    if soup.body:
        content = "".join(str(x) for x in soup.body.contents)
        new_body = f"<body>\n{HEADER}\n<div class='phi-grid'>\n{content}\n</div>\n{FOOTER}\n</body>"
        soup.body.replace_with(BeautifulSoup(new_body, "html.parser"))

    with open(path, "w", encoding="utf8") as f:
        f.write(str(soup))

def walk():
    for root, _, files in os.walk("."):
        if "dist" in root.lower():
            continue
        if "backup" in root.lower():
            continue
        for f in files:
            if f.endswith(".html"):
                path = os.path.join(root, f)
                print("→ Updating", path)
                try:
                    process_file(path)
                except Exception as e:
                    print("⚠ Error processing", path, ":", e)

if __name__ == "__main__":
    walk()
