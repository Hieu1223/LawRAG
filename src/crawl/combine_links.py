import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINKS_DIR = os.path.join(BASE_DIR, "work_dir", "links")
OUTPUT_FILE = os.path.join(BASE_DIR, "work_dir", "all_links.txt")

def main():
    unique = set()
    if not os.path.isdir(LINKS_DIR):
        print(f"Links folder not found: {LINKS_DIR}")
        return
    for name in sorted(os.listdir(LINKS_DIR)):
        if not re.match(r"matched-ban-an-page-\d+\.txt", name):
            continue
        path = os.path.join(LINKS_DIR, name)
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    unique.add(line)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for link in sorted(unique):
            f.write(link + "\n")
    print(f"Combined {len(unique)} unique links -> {OUTPUT_FILE}")

if __name__ == "__main__":
    main()