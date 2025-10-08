import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://tenders.procurement.gov.ge/engine/controller.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": "YOUR_COOKIE_HERE",   # Replace this with your cookie
}

def get_tweets_page(page):
    params = {"action": "tweets", "page": page}
    r = requests.get(BASE_URL, params=params, headers=HEADERS)
    if r.status_code == 200:
        return r.text
    print(f"[!] Failed to load page {page}, status={r.status_code}")
    return None


def extract_mrs_tweets(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr.togglebox")
    mrs_items = []
    for tr in rows:
        id_attr = tr.get("id")
        if not id_attr or ":" not in id_attr:
            continue
        tw_id, tw_code = id_attr.split(":", 1)

        if "id=\"mrs:" in str(tr):
            mrs_items.append((tw_id, tw_code))
    return mrs_items


def mark_as_read(tw_id, tw_code):
    params = {
        "action": "toggle_tweet",
        "tw_id": tw_id,
        "tw_code": tw_code,
    }
    r = requests.get(BASE_URL, params=params, headers=HEADERS)
    if r.status_code == 200:
        print(f"  [+] Marked tw_id={tw_id} as read")
    else:
        print(f"  [!] Failed to mark tw_id={tw_id} (HTTP {r.status_code})")
    time.sleep(0.2)


def main():
    page = 1
    total_marked = 0

    while True:
        print(f"\n[+] Fetching notifications page {page}")
        html = get_tweets_page(page)
        if not html:
            break

        mrs_items = extract_mrs_tweets(html)
        if not mrs_items:
            print("[✓] No MRS notifications found — stopping.")
            break

        print(f"  Found {len(mrs_items)} MRS notifications on this page.")
        for tw_id, tw_code in mrs_items:
            mark_as_read(tw_id, tw_code)
            total_marked += 1

        page += 1
        time.sleep(0.5)

    print(f"\n[✓] Done. Total marked as read: {total_marked}")


if __name__ == "__main__":
    main()
