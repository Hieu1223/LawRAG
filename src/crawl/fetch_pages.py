import os
import time
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(BASE_DIR, "work_dir")
LINKS_ROOT = os.path.join(WORK_DIR, "links")
PAGES_ROOT = os.path.join(WORK_DIR, "pages")
os.makedirs(PAGES_ROOT, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}
BASE_URL = "https://congbobanan.toaan.gov.vn"

def safe_filename(url):
    name = url.strip("/").replace("/", "_")
    if not name:
        name = "index"
    return name + ".html"

def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    for category in sorted(os.listdir(LINKS_ROOT)):
        cat_dir = os.path.join(LINKS_ROOT, category)
        if not os.path.isdir(cat_dir):
            continue
        links_file = os.path.join(cat_dir, "all_links.txt")
        if not os.path.exists(links_file):
            print(f"No all_links.txt in {category}, skip.")
            continue
        with open(links_file, encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        pages_dir = os.path.join(PAGES_ROOT, category)
        os.makedirs(pages_dir, exist_ok=True)

        total = len(urls)
        for i, path in enumerate(urls, 1):
            url = path if path.startswith("http") else BASE_URL + path
            out = os.path.join(pages_dir, safe_filename(path))
            if os.path.exists(out):
                print(f"[{category}][{i}/{total}] skip (exists): {path}")
                continue
            print(f"[{category}][{i}/{total}] fetching: {path}", end=" ")
            try:
                resp = session.get(url, verify=False, timeout=30)
                resp.raise_for_status()
                with open(out, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                print(f"OK ({len(resp.text)} bytes)")
            except Exception as e:
                print(f"FAILED: {e}")
            time.sleep(1.0)

if __name__ == "__main__":
    main()