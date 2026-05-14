# document-system

Local document system running on a VirtualBox VM (Ubuntu). Everything runs locally — no cloud access, no external services.

## Stack

- **Paperless-ngx** — document archive with OCR → http://localhost:8010
- **AnythingLLM** — AI chat over your own documents → http://localhost:3002
- **Ollama** — local LLM, no cloud model

## Requirements

- Docker + Docker Compose
- Ollama with the required models (`gemma4:e4b`, `nomic-embed-text:latest`)
- Python 3 with `requests` (`pip install requests`)
- `~/privat/.env` with API keys (see below)

## Starting

```bash
cd ~/privat/dokumente
docker compose up -d
```

## Configuration

`~/privat/.env` (template: `.env.example`):
```
PAPERLESS_TOKEN=         # API token from Paperless under Settings → API Token
ANYTHINGLLM_TOKEN=       # API token from AnythingLLM under Settings
PAPERLESS_DBPASS=        # Any secure password for the Postgres database
PAPERLESS_SECRET_KEY=    # Long random string, e.g.: python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Scripts

### `paperless_ki.py` (located in `~/privat/`)
Analyses new documents (without tags) using Ollama and automatically sets title, tags, correspondent and document type. Runs a Paperless export as backup at the end.

```bash
python3 ~/privat/paperless_ki.py
```

Model used: `qwen2.5:14b-ctx32k` (configurable via `ANALYSIS_MODEL` in the script).

### `paperless_to_anythingllm.py`
Syncs new documents from Paperless into the AnythingLLM workspace.

```bash
python3 ~/paperless_to_anythingllm.py
```

Already synced document IDs are stored in `~/synced_ids.json`.

### `chat.py`
Chat with your own documents via AnythingLLM.

```bash
# Interactive mode
chat

# Single question
chat What does my latest invoice say?
```

The `chat` alias must be added to `~/.bashrc`:
```bash
alias chat='~/chat.py'
```
