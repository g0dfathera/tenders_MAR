#!/usr/bin/env python3
import os
import sys
import time
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://tenders.procurement.gov.ge"
BASE_CONTROLLER = f"{BASE_URL}/engine/controller.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": f"{BASE_URL}/",
}

COOKIE_VALUE = input("Paste your PHPSESSID cookie value: ").strip()
if not COOKIE_VALUE:
    print(" No cookie provided. Exiting.")
    sys.exit(1)


def check_cookie_valid(session):
    r = session.get(BASE_URL + "/", headers=HEADERS, timeout=15)
    if r.status_code == 200 and ("logout" in r.text.lower() or "გამოსვლა" in r.text.lower()):
        return True
    return False


def fetch_tweets_page(session, page):
    params = {"action": "tweets", "page": page}
    r = session.get(BASE_CONTROLLER, params=params, headers=HEADERS, timeout=15)
    return r.text if r.status_code == 200 else None


def extract_mrs_items(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for tr in soup.select("tr.togglebox"):
        id_attr = tr.get("id")
        if not id_attr or ":" not in id_attr:
            continue

        # look for span with id="mrs:<something>"
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
        s.cookies.set("PHPSESSID", COOKIE_VALUE, domain="tenders.procurement.gov.ge")

        print(" Checking cookie validity...")
        if not check_cookie_valid(s):
            print(" Cookie seems invalid or expired.")
            sys.exit(1)
        print(" Cookie valid, continuing...\n")

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
                    print(f" Marked MRS tw_id={tw_id} as read")
                else:
                    print(f" Failed to mark MRS tw_id={tw_id}")
            page += 1
            time.sleep(0.3)

        print(f"\n Done. Total MRS marked as read: {total}")


if __name__ == "__main__":
    main()
