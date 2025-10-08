#!/usr/bin/env python3
import sys
import time
import re
import requests
from bs4 import BeautifulSoup

USERNAME = "username" # replace with actual username
PASSWORD = "password" # replace with actual password
LOGIN_URL = "https://tenders.procurement.gov.ge/login.php"
BASE_CONTROLLER = "https://tenders.procurement.gov.ge/engine/controller.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://tenders.procurement.gov.ge/login.php",
    "Origin": "https://tenders.procurement.gov.ge",
}

def login(session, username, password):
    payload = {"lang": "ge", "user": username, "pass": password}
    r = session.post(LOGIN_URL, data=payload, headers=HEADERS, allow_redirects=False, timeout=15)
    if r.status_code in (301, 302):
        loc = r.headers.get("Location", "")
        if loc == "/":
            session.get("https://tenders.procurement.gov.ge/", headers=HEADERS, timeout=15)
            return True
    try:
        r2 = session.get("https://tenders.procurement.gov.ge/", headers=HEADERS, timeout=15)
        if r2.status_code == 200 and ("logout" in r2.text.lower() or "გამოსვლა" in r2.text.lower()):
            return True
    except Exception:
        pass
    return False

def fetch_tweets_page(session, page):
    params = {"action": "tweets", "page": page}
    r = session.get(BASE_CONTROLLER, params=params, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return None
    return r.text

def extract_mrs_items(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for tr in soup.select("tr.togglebox"):
        id_attr = tr.get("id")
        if not id_attr or ":" not in id_attr:
            continue
        mrs_span = tr.find("span", id=re.compile(r"^mrs:"))
        if mrs_span:
            tw_id, tw_code = id_attr.split(":", 1)
            results.append((tw_id, tw_code))
    return results

def mark_as_read(session, tw_id, tw_code):
    params = {"action": "toggle_tweet", "tw_id": tw_id, "tw_code": tw_code}
    r = session.get(BASE_CONTROLLER, params=params, headers=HEADERS, timeout=15)
    return r.status_code == 200

def main():
    with requests.Session() as s:
        s.headers.update(HEADERS)
        if not login(s, USERNAME, PASSWORD):
            print("Login failed.")
            sys.exit(1)
        page = 1
        total = 0
        while True:
            html = fetch_tweets_page(s, page)
            if not html:
                break
            items = extract_mrs_items(html)
            if not items:
                break
            for tw_id, tw_code in items:
                if mark_as_read(s, tw_id, tw_code):
                    total += 1
                    print(f"Marked tw_id={tw_id} as read")
                else:
                    print(f"Failed to mark tw_id={tw_id}")
                time.sleep(0.2)
            page += 1
            time.sleep(0.5)
        print(f"Done. Total marked: {total}")

if __name__ == "__main__":
    main()
