#!/usr/bin/env python3
import os
import sys
import json
import re
import requests
from pathlib import Path

ENV_FILE = Path.home() / "privat" / "dokumente" / ".env"
ANYTHINGLLM_URL = "http://localhost:3002"
WORKSPACE = "my-workspace"


def load_env():
    if not ENV_FILE.exists():
        print(f"Fehler: {ENV_FILE} nicht gefunden", file=sys.stderr)
        sys.exit(1)
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def chat_stream(message: str, token: str):
    url = f"{ANYTHINGLLM_URL}/api/v1/workspace/{WORKSPACE}/stream-chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"message": message, "mode": "chat"}

    with requests.post(url, headers=headers, json=payload, stream=True, timeout=120) as resp:
        if resp.status_code != 200:
            print(f"Fehler {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)

        sources = []
        full_text = ""
        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8")
            if line.startswith("data:"):
                line = line[5:].strip()
            if line in ("", "[DONE]"):
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            token_text = data.get("textResponse", "")
            if token_text:
                full_text += token_text

            if data.get("close"):
                sources = data.get("sources", [])
                break

        full_text = re.sub(r"<think>.*?</think>", "", full_text, flags=re.DOTALL).strip()
        print(full_text)
        print()
        if sources:
            print("\nQuellen:")
            seen = set()
            for s in sources:
                title = s.get("title") or s.get("metadata", {}).get("title", "unbekannt")
                if title not in seen:
                    seen.add(title)
                    print(f"  - {title}")


def interactive(token: str):
    print("Chat mit deinen Dokumenten (Ctrl+C zum Beenden)\n")
    while True:
        try:
            message = input("Du: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not message:
            continue
        print("LLM: ", end="", flush=True)
        chat_stream(message, token)
        print()


def main():
    load_env()
    token = os.environ.get("ANYTHINGLLM_TOKEN")
    if not token:
        print("Fehler: ANYTHINGLLM_TOKEN nicht gesetzt", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        print("LLM: ", end="", flush=True)
        chat_stream(message, token)
    else:
        interactive(token)


if __name__ == "__main__":
    main()
