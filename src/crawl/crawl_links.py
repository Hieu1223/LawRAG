import re
import time
import os
import json
import requests
from bs4 import BeautifulSoup

WORK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "work_dir")
LINKS_DIR = os.path.join(WORK_DIR, "links")
PAYLOADS_DIR = os.path.join(WORK_DIR, "payloads")
os.makedirs(LINKS_DIR, exist_ok=True)
os.makedirs(PAYLOADS_DIR, exist_ok=True)

URL = "https://congbobanan.toaan.gov.vn/0tat1cvn/ban-an-quyet-dinh"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Base payload template
BASE_PAYLOAD = {
    "ctl00$ScriptManager": "ctl00$Content_home_Public$ctl00$Ajax_Manager_Updata|ctl00$Content_home_Public$ctl00$DropPages",
    "__EVENTTARGET": "ctl00$Content_home_Public$ctl00$DropPages",
    "__EVENTARGUMENT": "",
    "__LASTFOCUS": "",
    "__VIEWSTATEGENERATOR": "CA0B0334",
    "ctl00$Feedback_Home$hdnProcess": "FALSE",
    "ctl00$Content_home_Public$ctl00$txtKeyword_top": "",
    "ctl00$Content_home_Public$ctl00$Drop_Levels_top": "",
    "ctl00$Content_home_Public$ctl00$Ra_Drop_Courts_top": "",
    "ctl00$Content_home_Public$ctl00$Drop_LEVEL_JUDGMENT_SEARCH_top": "",
    "ctl00$Content_home_Public$ctl00$Drop_STATUS_JUDGMENT_SEARCH_top": "",
    "ctl00$Content_home_Public$ctl00$Drop_CASES_STYLES_SEARCH_top": "0",
    "ctl00$Content_home_Public$ctl00$Ra_Case_shows_search_top": "",
    "ctl00$Content_home_Public$ctl00$Rad_DATE_FROM_top": "",
    "ctl00$Content_home_Public$ctl00$MaskedEditExtender1_ClientState": "",
    "ctl00$Content_home_Public$ctl00$Rad_DATE_TO_top": "",
    "ctl00$Content_home_Public$ctl00$MaskedEditExtender4_ClientState": "",
    "ctl00$Content_home_Public$ctl00$txtKeyword": "",
    "ctl00$Content_home_Public$ctl00$Drop_Levels": "",
    "ctl00$Content_home_Public$ctl00$Ra_Drop_Courts": "",
    "ctl00$Content_home_Public$ctl00$Drop_LEVEL_JUDGMENT_SEARCH": "",
    "ctl00$Content_home_Public$ctl00$Drop_STATUS_JUDGMENT_SEARCH": "",
    "ctl00$Content_home_Public$ctl00$Drop_CASES_STYLES_SEARCH": "0",
    "ctl00$Content_home_Public$ctl00$Ra_Case_shows_search": "",
    "ctl00$Content_home_Public$ctl00$Rad_DATE_FROM": "",
    "ctl00$Content_home_Public$ctl00$MaskedEditExtender2_ClientState": "",
    "ctl00$Content_home_Public$ctl00$Rad_DATE_TO": "",
    "ctl00$Content_home_Public$ctl00$MaskedEditExtender3_ClientState": "",
    "ctl00$Content_home_Public$ctl00$Hi_id_pub": ""
}

def get_hidden_value(html, field_name):
    """Extract __VIEWSTATE or __EVENTVALIDATION from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("input", {"name": field_name})
    return tag["value"] if tag else ""

def _last_completed_page():
    if not os.path.isdir(PAYLOADS_DIR):
        return 0
    nums = []
    for name in os.listdir(PAYLOADS_DIR):
        m = re.match(r"page-(\d+)\.json", name)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) if nums else 0

def main(max_pages=1, resume=True):
    session = requests.Session()
    session.headers.update(HEADERS)

    start_page = 1
    view_state = ""
    event_validation = ""

    if resume:
        last = _last_completed_page()
        if last > 0:
            last_file = os.path.join(PAYLOADS_DIR, f"page-{last}.json")
            with open(last_file, encoding="utf-8") as f:
                data = json.load(f)
            view_state = data.get("next_view_state", "")
            event_validation = data.get("next_event_validation", "")
            start_page = last + 1
            print(f"[resume] Resuming from page {start_page} (last completed: {last})")

    if not view_state:
        print("[1/3] Fetching initial page to get ViewState...")
        response = session.get(URL, verify=False)
        response.raise_for_status()
        view_state = get_hidden_value(response.text, "__VIEWSTATE")
        event_validation = get_hidden_value(response.text, "__EVENTVALIDATION")

    if not view_state:
        print("ERROR: Could not find __VIEWSTATE. Site may have changed or blocked the request.")
        return

    print(f"[2/3] Starting sequential crawl for {max_pages} pages...")
    unique_links = set()

    # load previously collected links if resuming
    if resume and start_page > 1:
        for p in range(1, start_page):
            lf = os.path.join(LINKS_DIR, f"matched-ban-an-page-{p}.txt")
            if os.path.exists(lf):
                with open(lf, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            unique_links.add(line)

    for page in range(start_page, start_page + max_pages):
        print(f"--> Requesting Page {page}...", end=" ")
        
        # Build fresh payload for this specific page
        payload = BASE_PAYLOAD.copy()
        payload["__VIEWSTATE"] = view_state
        payload["__EVENTVALIDATION"] = event_validation
        payload["ctl00$Content_home_Public$ctl00$DropPages"] = str(page)

        # POST request
        resp = session.post(URL, data=payload,verify=False)
        
        if resp.status_code != 200:
            print(f"FAILED (Status {resp.status_code})")
            break

        html = resp.text
        
        # Extract links matching /<alphanumeric>/chi-tiet-ban-an
        matches = re.findall(r'(/[a-zA-Z0-9]+/chi-tiet-ban-an/?)"?', html)
        new_links = set(matches)
        unique_links.update(new_links)
        print(f"Found {len(new_links)} new links. Total unique: {len(unique_links)}")

        # CRITICAL: Extract the NEW ViewState and EventValidation for the NEXT page
        new_view_state = get_hidden_value(html, "__VIEWSTATE")
        new_event_validation = get_hidden_value(html, "__EVENTVALIDATION")
        
        if new_view_state:
            view_state = new_view_state
            event_validation = new_event_validation
        else:
            print("[!] Warning: Could not extract new ViewState. Pagination may stop here.")
            break
        # Save only the links found on THIS page
        list_file = os.path.join(LINKS_DIR, f"matched-ban-an-page-{page}.txt")
        with open(list_file, "w", encoding="utf-8") as f:
            for link in sorted(new_links):
                f.write(link + "\n")

        # Save the request payload + next ViewState/EventValidation for resume
        payload_file = os.path.join(PAYLOADS_DIR, f"page-{page}.json")
        with open(payload_file, "w", encoding="utf-8") as f:
            json.dump({"payload": payload, "next_view_state": new_view_state, "next_event_validation": new_event_validation}, f, ensure_ascii=False, indent=2)
        # Be polite, avoid instant IP bans
        time.sleep(1.5)
            
if __name__ == "__main__":
    # Change max_pages to whatever you need (0 or remove limit for all pages)
    main(max_pages=5000)