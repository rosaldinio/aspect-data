#!/usr/bin/env python3
"""
Minimal Telegram bot that listens for /update and triggers the GitHub Actions
update workflow via the GitHub API. Run this locally or as a long-running
process — but for a zero-server setup, use the GitHub Actions bot_listener
workflow instead, which polls on a schedule.

Usage (local, for testing):
    TELEGRAM_TOKEN=xxx TELEGRAM_CHAT_ID=yyy GITHUB_TOKEN=zzz \
    GITHUB_REPO=rosaldinio/aspect-data python3 scripts/telegram_bot.py
"""

import json
import os
import time
import urllib.request

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ.get("GITHUB_REPO", "rosaldinio/aspect-data")
UPDATE_WORKFLOW = "update_scenarios.yml"

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def get_updates(offset: int) -> list:
    url = f"{BASE_URL}/getUpdates?timeout=30&offset={offset}"
    with urllib.request.urlopen(url, timeout=35) as r:
        data = json.loads(r.read())
    return data.get("result", [])


def send_message(text: str) -> None:
    url = f"{BASE_URL}/sendMessage"
    body = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)


def trigger_github_workflow() -> bool:
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
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"GitHub trigger failed: {e}")
        return False


def main() -> None:
    print("Telegram bot started. Listening for /update...")
    offset = 0
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                from_id = str(msg.get("chat", {}).get("id", ""))

                if from_id != CHAT_ID:
                    continue  # ignore messages from other chats

                if text.strip() == "/update":
                    send_message("⏳ Update wird gestartet... GitHub Action läuft.")
                    ok = trigger_github_workflow()
                    if ok:
                        send_message("✅ GitHub Action gestartet! Du bekommst eine Nachricht wenn fertig.")
                    else:
                        send_message("❌ Fehler beim Starten der GitHub Action. Prüfe den GITHUB_TOKEN.")
                elif text.strip() == "/status":
                    send_message("🤖 Aspect Maintenance Bot ist aktiv und wartet auf /update.")
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
