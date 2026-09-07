# Offline Demo Runbook

This runbook exercises synthetic fixtures only. It never calls Gmail, Feishu, an external LLM, or a production database, and it cannot send a real email.

## Prerequisites

```powershell
uv sync --locked --dev
$env:APP_MODE = 'offline'
$env:EMAIL_ADAPTER = 'mock'
$env:LLM_ADAPTER = 'mock'
$env:AUTO_SEND = 'false'
```

## Run

```powershell
uv run python scripts/config_check.py
uv run python scripts/run_demo.py --fixture fixtures
uv run pytest -q
```

Expected output includes `CONFIG_CHECK_PASS`, `DEMO_PASS mode=offline database=sqlite adapter=mock`, and a green test suite. The fixture set covers FAQ, address query, high-risk contract/refund, multi-intent, empty body, HTML, safe attachment metadata, Prompt Injection, provider timeout, duplicate event, and follow-up cancellation.

## Reset and evidence

The demo does not require a pre-existing database. If a future runner creates `.runtime/app.sqlite3`, delete only that ignored file before rerunning so the scenario starts from empty state. Expected terminal states are in `fixtures/expected/expected-results.json`; all IDs and content are synthetic. Record command output and environment mode in the delivery report, never customer data or credentials.
