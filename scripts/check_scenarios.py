#!/usr/bin/env python3
"""
Fetches the pack list from marvelcdb.com and compares it with the pack codes
we've already seen (data/known_packs.json). Sends a Telegram notification if
a genuinely new pack appears. Used by the GitHub Actions monitor workflow.
"""

import json
import os
import sys
import urllib.request
import urllib.parse

MARVELCDB_PACKS_URL = "https://marvelcdb.com/api/public/packs/"
KNOWN_PACKS_PATH = "data/known_packs.json"


def send_telegram(token: str, chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)


def fetch_json(url: str) -> list | dict:
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def load_known_pack_codes() -> set[str]:
    if not os.path.exists(KNOWN_PACKS_PATH):
        return set()
    with open(KNOWN_PACKS_PATH, encoding="utf-8") as f:
        return set(json.load(f))


def save_known_pack_codes(codes: set[str]) -> None:
    with open(KNOWN_PACKS_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(codes), f, indent=2)
        f.write("\n")


def find_new_packs(api_packs: list[dict], known_codes: set[str]) -> list[dict]:
    return [p for p in api_packs if p.get("code") not in known_codes]


def main() -> None:
    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_TOKEN and TELEGRAM_CHAT_ID must be set.")
        sys.exit(1)

    print("Fetching packs from marvelcdb...")
    api_packs = fetch_json(MARVELCDB_PACKS_URL)
    print(f"  {len(api_packs)} packs received from API")

    known_codes = load_known_pack_codes()
    print(f"  {len(known_codes)} pack codes already known")

    new_packs = find_new_packs(api_packs, known_codes)

    github_output = os.environ.get("GITHUB_OUTPUT", "")

    if not new_packs:
        print("No new packs found. All up to date.")
        sys.exit(0)

    names = "\n".join(f"  • {p['name']} ({p['code']})" for p in new_packs)
    message = (
        f"⚠️ <b>Aspect – Neue Marvel Champions Packs entdeckt!</b>\n\n"
        f"{len(new_packs)} neues Pack(s) auf marvelcdb.com:\n{names}\n\n"
        f"Falls Szenario-/Kampagnendaten nötig sind: Schreibe /update an den Bot."
    )

    print(f"Found {len(new_packs)} new pack(s): {[p['code'] for p in new_packs]}")
    send_telegram(token, chat_id, message)
    print("Telegram notification sent.")

    save_known_pack_codes(known_codes | {p["code"] for p in api_packs})

    if github_output:
        with open(github_output, "a") as f:
            f.write("state_changed=true\n")
            f.write(f"new_pack_count={len(new_packs)}\n")


if __name__ == "__main__":
    main()
