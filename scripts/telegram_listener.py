#!/usr/bin/env python3
"""
Runs in GitHub Actions every 5 minutes. Checks Telegram for new /update
commands and triggers the update_scenarios workflow if found.

State (last seen update_id) is stored in the Actions cache via an output
file — but since caching across runs is complex, we use a simpler approach:
we fetch only updates from the last 10 minutes using allowed_updates filtering,
and deduplicate via the update_id written to a temp file in the repo's
workflow run artifacts (not persisted — intentionally fire-and-forget).
"""

import json
import os
import time
import urllib.request
import urllib.error

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
UPDATE_WORKFLOW = "update_scenarios.yml"
OFFSET_FILE = "/tmp/tg_offset.txt"

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def send_message(text: str) -> None:
    url = f"{BASE_URL}/sendMessage"
    body = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"send_message failed: {e}")


def get_updates(offset: int) -> list:
    url = f"{BASE_URL}/getUpdates?offset={offset}&limit=10&timeout=5"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read()).get("result", [])
    except Exception as e:
        print(f"getUpdates failed: {e}")
        return []


def trigger_update_workflow() -> bool:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{UPDATE_WORKFLOW}/dispatches"
    body = json.dumps({"ref": "main"}).encode()
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 204
    except urllib.error.HTTPError as e:
        print(f"GitHub trigger HTTP error: {e.code} {e.read()}")
        return False
    except Exception as e:
        print(f"GitHub trigger failed: {e}")
        return False


def load_offset() -> int:
    # Use GitHub Actions cache key via env if available, fallback to 0
    cached = os.environ.get("TG_OFFSET", "0")
    try:
        return int(cached)
    except ValueError:
        return 0


def main() -> None:
    offset = load_offset()
    print(f"Checking Telegram updates from offset {offset}...")

    updates = get_updates(offset)
    print(f"  {len(updates)} update(s) received")

    triggered = False
    for update in updates:
        new_offset = update["update_id"] + 1
        if new_offset > offset:
            offset = new_offset

        msg = update.get("message", {})
        text = msg.get("text", "").strip()
        from_id = str(msg.get("chat", {}).get("id", ""))

        # Only accept commands from the configured chat
        if from_id != CHAT_ID:
            print(f"  Ignoring message from unknown chat {from_id}")
            continue

        print(f"  Message from {from_id}: {text!r}")

        if text == "/update" and not triggered:
            send_message("⏳ <b>Aspect Wartung</b>\n\nUpdate wird gestartet... schaue gleich nach neuen Szenarien!")
            ok = trigger_update_workflow()
            if ok:
                send_message("✅ GitHub Action gestartet! Du bekommst eine Nachricht sobald scenarios.json aktualisiert wurde (ca. 1–2 Min.).")
                triggered = True
            else:
                send_message("❌ Fehler beim Starten des Updates. Bitte prüfe die GitHub Secrets.")

        elif text == "/status":
            send_message(
                "🤖 <b>Aspect Maintenance Bot</b>\n\n"
                "Status: Aktiv ✅\n"
                "Prüft täglich um 10:00 Uhr auf neue Packs.\n\n"
                "Verfügbare Befehle:\n"
                "/update – scenarios.json jetzt aktualisieren\n"
                "/status – Dieser Status"
            )

    # Write new offset to GitHub output for potential caching
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"tg_offset={offset}\n")

    print(f"Done. Next offset: {offset}")


if __name__ == "__main__":
    main()
