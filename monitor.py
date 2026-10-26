#!/usr/bin/env python3
"""Watch a Shopify collection and push ntfy alerts for new (and restocked) products."""
import json
import os
import sys
import time
import urllib.request

STORE = "https://www.autmog.com"
COLLECTION = "currently-available"
STATE_FILE = os.environ.get("STATE_FILE", "seen.json")
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")
NTFY_TOKEN = os.environ.get("NTFY_TOKEN", "")  # only needed for protected topics
NOTIFY_RESTOCK = os.environ.get("NOTIFY_RESTOCK", "true").lower() == "true"
CHECK_EVERY = int(os.environ.get("CHECK_EVERY", "60"))  # seconds between checks
RUN_FOR = int(os.environ.get("RUN_FOR", "0"))  # keep checking this many seconds (0 = once)
UA = "Mozilla/5.0 (product-watch; personal use)"


def fetch_products():
    products, page = [], 1
    while True:
        url = f"{STORE}/collections/{COLLECTION}/products.json?limit=250&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.load(r).get("products", [])
        if not batch:
            return products
        products.extend(batch)
        page += 1


def summarize(p):
    variants = p.get("variants") or [{}]
    images = p.get("images") or []
    return {
        "title": p["title"],
        "url": f"{STORE}/products/{p['handle']}",
        "price": variants[0].get("price", "?"),
        "available": any(v.get("available") for v in variants),
        "image": images[0]["src"] if images else "",
    }


def notify(title, message, click="", image="", tags="pen", priority="high"):
    headers = {"Title": title, "Tags": tags, "Priority": priority}
    if click:
        headers["Click"] = click
    if image:
        headers["Attach"] = image
    if NTFY_TOKEN:
        headers["Authorization"] = f"Bearer {NTFY_TOKEN}"
    req = urllib.request.Request(
        f"{NTFY_SERVER}/{NTFY_TOPIC}", data=message.encode("utf-8"),
        headers=headers, method="POST",
    )
    urllib.request.urlopen(req, timeout=30).read()


def check():
    current = {str(p["id"]): summarize(p) for p in fetch_products()}
    if not current:
        print("Got 0 products - not touching saved state.")
        return

    try:
        with open(STATE_FILE) as f:
            seen = json.load(f)
    except FileNotFoundError:
        seen = None

    if seen is None:
        notify("Autmog watcher is running",
               f"Tracking {len(current)} products. You'll be pinged when new ones appear.",
               click=f"{STORE}/collections/{COLLECTION}", priority="low", tags="eyes")
    else:
        for pid, p in current.items():
            price = f"${p['price']}"
            if pid not in seen:
                status = "In stock" if p["available"] else "Sold out"
                notify("New Autmog product", f"{p['title']}\n{price} - {status}",
                       click=p["url"], image=p["image"], tags="new,pen")
                print("NEW:", p["title"])
            elif NOTIFY_RESTOCK and p["available"] and not seen[pid].get("available"):
                notify("Autmog item available", f"{p['title']}\n{price}",
                       click=p["url"], image=p["image"], tags="white_check_mark,pen",
                       priority="urgent")
                print("AVAILABLE:", p["title"])

    with open(STATE_FILE, "w") as f:
        json.dump({k: {"title": v["title"], "available": v["available"]}
                   for k, v in current.items()}, f, indent=1, sort_keys=True)
    print(f"Checked {len(current)} products.")


def main():
    if not NTFY_TOPIC:
        sys.exit("Set the NTFY_TOPIC environment variable / secret.")
    deadline = time.time() + RUN_FOR
    while True:
        try:
            check()
        except Exception as e:  # a hiccup shouldn't kill the whole run
            print("Check failed:", e)
        if time.time() + CHECK_EVERY > deadline:
            break
        time.sleep(CHECK_EVERY)


if __name__ == "__main__":
    main()
