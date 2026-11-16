import os
import re
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAGES_ROOT = os.path.join(BASE_DIR, "work_dir", "pages")
OUTPUT_FILE = os.path.join(BASE_DIR, "work_dir", "pdf_links.txt")

def main():
    if not os.path.isdir(PAGES_ROOT):
        print(f"Pages folder not found: {PAGES_ROOT}. Run fetch_pages.py first.")
        return

    pdf_links = set()
    for root, _, files in os.walk(PAGES_ROOT):
        for name in files:
            if not name.lower().endswith(".html"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as f:
                html = f.read()
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(r"\.pdf(\?|$)", href, re.IGNORECASE):
                    pdf_links.add(href.strip())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for link in sorted(pdf_links):
            f.write(link + "\n")
    print(f"Found {len(pdf_links)} unique PDF links -> {OUTPUT_FILE}")

if __name__ == "__main__":
    main()