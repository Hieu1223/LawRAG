import os
import base64
import json
import time
import requests

WORK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "work_dir")
PDF_DIR = os.path.join(WORK_DIR, "pdf")
OCR_DIR = os.path.join(WORK_DIR, "ocr_res")
KEYS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "env", "nim.txt")

NIM_ENDPOINT = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-parse"

os.makedirs(OCR_DIR, exist_ok=True)

def load_keys():
    with open(KEYS_FILE, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def ocr_pdf(path, key):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"input": [{"type": "pdf", "url": f"data:application/pdf;base64,{b64}"}]}
    resp = requests.post(NIM_ENDPOINT, headers=headers, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()

def main():
    keys = load_keys()
    ki = 0
    for name in sorted(os.listdir(PDF_DIR)):
        if not name.lower().endswith(".pdf"):
            continue
        src = os.path.join(PDF_DIR, name)
        out = os.path.join(OCR_DIR, os.path.splitext(name)[0] + ".txt")
        if os.path.exists(out):
            print(f"skip {name}")
            continue
        for attempt in range(len(keys)):
            key = keys[ki % len(keys)]
            try:
                result = ocr_pdf(src, key)
                text = json.dumps(result, ensure_ascii=False, indent=2)
                # try to extract text field if present
                if isinstance(result, dict):
                    for k in ("text", "content", "result"):
                        if k in result and isinstance(result[k], str):
                            text = result[k]
                            break
                with open(out, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"OK {name}")
                break
            except Exception as e:
                print(f"key fail {name}: {e}")
                ki += 1
                time.sleep(2)
        else:
            print(f"FAILED {name}")

if __name__ == "__main__":
    main()