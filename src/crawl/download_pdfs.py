import os
import time
import requests
from urllib.parse import urljoin

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK_DIR = os.path.join(BASE_DIR, "work_dir")
PDF_LINKS_FILE = os.path.join(WORK_DIR, "pdf_links.txt")
PDF_ROOT = os.path.join(WORK_DIR, "pdf")
os.makedirs(PDF_ROOT, exist_ok=True)

BASE_URL = "https://congbobanan.toaan.gov.vn"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/pdf,*/*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

INVALID_CHARS = '<>:"/\\|?*'


def safe_filename(name):
    name = name.strip()
    for ch in INVALID_CHARS:
        name = name.replace(ch, "_")
    # collapse whitespace
    name = " ".join(name.split())
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


def unique_path(directory, filename):
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(directory, filename)
    if not os.path.exists(candidate):
        return candidate
    i = 1
    while True:
        candidate = os.path.join(directory, f"{base} ({i}){ext}")
        if not os.path.exists(candidate):
            return candidate
        i += 1


def main():
    if not os.path.exists(PDF_LINKS_FILE):
        print(f"PDF links file not found: {PDF_LINKS_FILE}. Run extract_pdf_links.py first.")
        return

    with open(PDF_LINKS_FILE, encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    session = requests.Session()
    session.headers.update(HEADERS)

    total = len(links)
    ok = 0
    failed = 0
    for i, path in enumerate(links, 1):
        url = path if path.startswith("http") else urljoin(BASE_URL + "/", path.lstrip("/"))
        filename = safe_filename(os.path.basename(path.split("?")[0]))
        out_path = unique_path(PDF_ROOT, filename)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print(f"[{i}/{total}] skip (exists): {os.path.basename(out_path)}")
            ok += 1
            continue

        print(f"[{i}/{total}] downloading: {os.path.basename(out_path)}", end=" ")
        try:
            resp = session.get(url, verify=False, timeout=60, stream=True)
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            size = os.path.getsize(out_path)
            print(f"OK ({size} bytes)")
            ok += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed += 1
            try:
                if os.path.exists(out_path):
                    os.remove(out_path)
            except OSError:
                pass
        time.sleep(0.5)

    print(f"\nDone. Success: {ok}, Failed: {failed}, Total: {total}")
    print(f"Saved to: {PDF_ROOT}")


if __name__ == "__main__":
    main()
