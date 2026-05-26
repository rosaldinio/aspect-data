#!/usr/bin/env python3
"""
Fetches scenario data from marvelcdb.com and compares it with the current
scenarios.json in the repo. Sends a Telegram notification if new content
is found. Used by the GitHub Actions monitor workflow.
"""

import json
import os
import sys
import urllib.request
import urllib.parse

MARVELCDB_PACKS_URL = "https://marvelcdb.com/api/public/packs/"
SCENARIOS_PATH = "data/scenarios.json"

# Scenario packs are identified by their type_code in marvelcdb.
# These pack codes belong to villain/scenario boxes — we derive scenario
# names from the pack name since marvelcdb doesn't expose scenario lists.
# The mapping below covers all known scenario packs and is extended
# automatically when new packs appear (names come from the API).
KNOWN_SCENARIO_PACK_TYPES = {"villain", "campaign"}


def send_telegram(token: str, chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)


def fetch_json(url: str) -> list | dict:
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def load_current_scenarios() -> list[dict]:
    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_known_pack_names(scenarios: list[dict]) -> set[str]:
    return {s["pack"] for s in scenarios}


def find_new_packs(api_packs: list[dict], known_names: set[str]) -> list[dict]:
    new_packs = []
    for pack in api_packs:
        if pack.get("pack_type_code") not in KNOWN_SCENARIO_PACK_TYPES:
            continue
        name = pack.get("name", "")
        if name and name not in known_names:
            new_packs.append(pack)
    return new_packs


def main() -> None:
    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_TOKEN and TELEGRAM_CHAT_ID must be set.")
        sys.exit(1)

    print("Fetching packs from marvelcdb...")
    api_packs = fetch_json(MARVELCDB_PACKS_URL)
    print(f"  {len(api_packs)} packs received from API")

    current = load_current_scenarios()
    known_names = get_known_pack_names(current)
    print(f"  {len(known_names)} packs currently in scenarios.json")

    new_packs = find_new_packs(api_packs, known_names)

    if not new_packs:
        print("No new scenario packs found. All up to date.")
        sys.exit(0)

    names = "\n".join(f"  • {p['name']}" for p in new_packs)
    message = (
        f"⚠️ <b>Aspect – Neue Marvel Champions Packs entdeckt!</b>\n\n"
        f"{len(new_packs)} neues Pack(s) auf marvelcdb.com:\n{names}\n\n"
        f"Schreibe /update an den Bot um scenarios.json automatisch zu aktualisieren."
    )

    print(f"Found {len(new_packs)} new pack(s): {[p['name'] for p in new_packs]}")
    send_telegram(token, chat_id, message)
    print("Telegram notification sent.")

    # Signal to the workflow that new content was found
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"new_packs_found=true\n")
            f.write(f"new_pack_count={len(new_packs)}\n")


if __name__ == "__main__":
    main()
