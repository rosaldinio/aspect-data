#!/usr/bin/env python3
"""
Tracks the marvelcdb "known" card count for packs we're watching (see
WATCHED_PACKS) and sends a Telegram notification whenever it changes.

Note: marvelcdb's "known"/"total" pack fields do NOT reach parity even for
packs that have been 100% released and known for years (e.g. Captain America:
35/56, Ms. Marvel: 34/56) — so "known == total" is not a usable "fully
spoiled" signal. This script instead reports progress deltas so a human can
judge completeness (e.g. by checking the pack's page on marvelcdb.com).
"""

import json
import os
import sys
import urllib.request

MARVELCDB_PACKS_URL = "https://marvelcdb.com/api/public/packs/"
PROGRESS_PATH = "data/spoiler_progress.json"

# Pack codes we actively want progress updates for. Remove a code once its
# expansion is fully spoiled and its scenario/campaign data has been entered.
WATCHED_PACKS = {"fne"}


def send_telegram(token: str, chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)


def fetch_json(url: str) -> list | dict:
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def load_progress() -> dict[str, int]:
    if not os.path.exists(PROGRESS_PATH):
        return {}
    with open(PROGRESS_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_progress(progress: dict[str, int]) -> None:
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)
        f.write("\n")


def main() -> None:
    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_TOKEN and TELEGRAM_CHAT_ID must be set.")
        sys.exit(1)

    print("Checking spoiler progress on marvelcdb...")
    api_packs = fetch_json(MARVELCDB_PACKS_URL)
    by_code = {p["code"]: p for p in api_packs if p.get("code") in WATCHED_PACKS}

    progress = load_progress()
    changed = False

    for code, pack in by_code.items():
        known = pack.get("known", 0)
        total = pack.get("total", 0)
        previous = progress.get(code)

        if previous is None:
            # First time watching this pack – record baseline, no notification.
            progress[code] = known
            changed = True
            print(f"  {code}: baseline set at {known} (total {total})")
            continue

        if known != previous:
            delta = known - previous
            sign = "+" if delta > 0 else ""
            message = (
                f"📈 <b>Aspect – Spoiler-Fortschritt: {pack['name']}</b>\n\n"
                f"{known} bekannt (total lt. marvelcdb: {total}), {sign}{delta} seit letztem Check.\n\n"
                f"Prüfe https://marvelcdb.com/set/{code} um zu sehen ob genug bekannt ist."
            )
            send_telegram(token, chat_id, message)
            print(f"  {code}: {previous} -> {known} ({sign}{delta}), notified")
            progress[code] = known
            changed = True
        else:
            print(f"  {code}: unchanged at {known}")

    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if changed:
        save_progress(progress)
        if github_output:
            with open(github_output, "a") as f:
                f.write("state_changed=true\n")


if __name__ == "__main__":
    main()
