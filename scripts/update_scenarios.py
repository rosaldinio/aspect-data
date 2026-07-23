#!/usr/bin/env python3
"""
Fetches the latest scenario/campaign packs from marvelcdb.com and adds a
placeholder entry per new pack to scenarios.json. The GitHub Actions update
workflow commits and pushes the result.

marvelcdb's public API cannot give us real per-scenario names automatically:
- The /packs/ endpoint has no pack_type_code field (confirmed empirically —
  0 of 61 packs have it), so pack "type" can't be read from the API at all.
- /api/public/cards/?pack_code=X ignores the pack_code filter entirely and
  returns the whole card database regardless of the parameter.
- The public cards API exposes no type_code == "villain" cards whatsoever
  (0 of 2086 cards across the whole database) — villain/main-scheme identity
  cards simply aren't in the public dataset.
So every new pack gets ONE placeholder entry named after the pack. A human
must split multi-scenario campaign boxes into their real scenario names
afterward (this is what happened for GMW previously — see project history).

Which pack codes need a scenario entry at all is a judgment call marvelcdb's
API can't answer (hero packs normally don't have their own villain; campaign
boxes and standalone scenario packs do) — mirrors the app's own
pack-categories.ts classification. Keep in sync if that list changes.
"""

import json
import os
import sys
import urllib.request

MARVELCDB_PACKS_URL = "https://marvelcdb.com/api/public/packs/"
SCENARIOS_PATH = "data/scenarios.json"

# Mirrors CAMPAIGN_BOX_CODES + SCENARIO_PACK_CODES in
# temp_init/src/features/collection/data/pack-categories.ts, plus 'core'.
SCENARIO_RELEVANT_CODES = {
    "core",
    "trors", "gmw", "mts", "sm", "mut_gen", "next_evol", "aoa", "aos", "cw", "fne",
    "gob", "twc", "ron", "toafk", "hood", "mojo", "tt", "synthezoid",
}


def send_telegram(token: str, chat_id: str, message: str) -> None:
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram notification failed: {e}")


def fetch_json(url: str) -> list | dict:
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def get_scenario_names_for_pack(pack_code: str) -> list[str]:
    """
    Fetches villain/encounter cards for a pack and returns unique scenario names.
    Falls back to an empty list if no villain cards found — caller will use pack name.
    """
    try:
        cards = fetch_json(f"{MARVELCDB_CARDS_URL}?pack_code={pack_code}")
        names = []
        seen = set()
        for card in cards:
            if card.get("type_code") == "villain":
                name = card.get("name", "").strip()
                if name and name not in seen:
                    seen.add(name)
                    names.append(name)
        return names
    except Exception:
        return []


def load_current_scenarios() -> list[dict]:
    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_scenarios(scenarios: list[dict]) -> None:
    # Pretty-print with consistent column alignment
    lines = ["["]
    for i, s in enumerate(scenarios):
        pack = s["pack"]
        name = s["name"]
        sort = s["sort"]
        comma = "," if i < len(scenarios) - 1 else ""
        lines.append(f'  {{ "pack": "{pack}",  "name": "{name}",  "sort": {sort} }}{comma}')
    lines.append("]")
    with open(SCENARIOS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    print("Fetching packs from marvelcdb...")
    api_packs = fetch_json(MARVELCDB_PACKS_URL)
    print(f"  {len(api_packs)} packs received")

    current = load_current_scenarios()
    known_pack_names = {s["pack"] for s in current}
    next_sort = max(s["sort"] for s in current) + 1

    new_entries: list[dict] = []

    for pack in api_packs:
        if pack.get("pack_type_code") not in KNOWN_SCENARIO_PACK_TYPES:
            continue
        pack_name = pack.get("name", "").strip()
        if not pack_name or pack_name in known_pack_names:
            continue

        pack_code = pack.get("code", "")
        print(f"  New pack found: {pack_name} ({pack_code}) — fetching scenarios...")

        scenario_names = get_scenario_names_for_pack(pack_code)

        if scenario_names:
            for scenario_name in scenario_names:
                new_entries.append({"pack": pack_name, "name": scenario_name, "sort": next_sort})
                next_sort += 1
        else:
            # Fallback: use pack name as single scenario name
            new_entries.append({"pack": pack_name, "name": pack_name, "sort": next_sort})
            next_sort += 1

        known_pack_names.add(pack_name)

    if not new_entries:
        print("No new scenarios found. scenarios.json is up to date.")
        send_telegram(token, chat_id, "✅ <b>Aspect Wartung</b>\n\nKeine neuen Szenarien gefunden. scenarios.json ist aktuell.")
        sys.exit(0)

    updated = current + new_entries
    save_scenarios(updated)

    names_list = "\n".join(f"  • {e['pack']}: {e['name']}" for e in new_entries)
    summary = (
        f"✅ <b>Aspect – scenarios.json aktualisiert!</b>\n\n"
        f"{len(new_entries)} neue Szenarien hinzugefügt:\n{names_list}\n\n"
        f"Commit wurde gepusht. Die App lädt die neuen Daten beim nächsten Sync."
    )
    print(f"\nAdded {len(new_entries)} new scenario(s):")
    for e in new_entries:
        print(f"  {e['pack']}: {e['name']} (sort {e['sort']})")

    send_telegram(token, chat_id, summary)
    print("\nTelegram notification sent. scenarios.json updated.")

    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"changes_made=true\n")
            f.write(f"new_count={len(new_entries)}\n")


if __name__ == "__main__":
    main()
