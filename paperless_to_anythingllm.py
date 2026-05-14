#!/usr/bin/env python3
import os
import json
import requests

def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env

_env = load_env(os.path.expanduser("~/privat/dokumente/.env"))

PAPERLESS_URL = "http://127.0.0.1:8010"
PAPERLESS_TOKEN = _env["PAPERLESS_TOKEN"]
ANYTHINGLLM_URL = "http://127.0.0.1:3002"
ANYTHINGLLM_TOKEN = _env["ANYTHINGLLM_TOKEN"]
WORKSPACE_SLUG = "my-workspace"
STATE_FILE = os.path.expanduser("~/synced_ids.json")

def load_synced_ids():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()

def save_synced_ids(ids):
    with open(STATE_FILE, "w") as f:
        json.dump(list(ids), f)

def get_paperless_documents():
    headers = {"Authorization": f"Token {PAPERLESS_TOKEN}"}
    docs = []
    url = f"{PAPERLESS_URL}/api/documents/?page_size=100"
    while url:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        docs.extend(data["results"])
        url = data["next"]
    return docs

def download_pdf(doc_id):
    headers = {"Authorization": f"Token {PAPERLESS_TOKEN}"}
    r = requests.get(f"{PAPERLESS_URL}/api/documents/{doc_id}/download/", headers=headers)
    r.raise_for_status()
    return r.content

def upload_to_anythingllm(pdf_bytes, filename):
    headers = {"Authorization": f"Bearer {ANYTHINGLLM_TOKEN}"}
    files = {"file": (filename, pdf_bytes, "application/pdf")}
    r = requests.post(f"{ANYTHINGLLM_URL}/api/v1/document/upload", headers=headers, files=files)
    r.raise_for_status()
    return r.json()

def add_to_workspace(doc_location):
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"adds": [doc_location]}
    r = requests.post(
        f"{ANYTHINGLLM_URL}/api/v1/workspace/{WORKSPACE_SLUG}/update-embeddings",
        headers=headers,
        json=payload,
    )
    r.raise_for_status()

def main():
    synced_ids = load_synced_ids()
    docs = get_paperless_documents()
    new_count = 0

    for doc in docs:
        doc_id = doc["id"]
        if doc_id in synced_ids:
            continue

        title = doc["title"]
        filename = f"paperless_{doc_id}_{title}.pdf"
        print(f"Synchronisiere: {title}")

        pdf_bytes = download_pdf(doc_id)
        result = upload_to_anythingllm(pdf_bytes, filename)

        location = result.get("documents", [{}])[0].get("location")
        if location:
            add_to_workspace(location)
            synced_ids.add(doc_id)
            new_count += 1
            print(f"  OK: {title}")
        else:
            print(f"  Fehler: kein location in Antwort: {result}")

    save_synced_ids(synced_ids)
    print(f"\nFertig. {new_count} neue Dokumente synchronisiert.")

if __name__ == "__main__":
    main()
