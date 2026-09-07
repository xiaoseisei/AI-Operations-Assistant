# Test Fixtures

Fixtures must use synthetic `.test` identities, fake tenant/thread IDs, and redacted content. Never store customer email, contracts, tokens, cookies, API keys, or binary attachments here. Keep unit fixtures deterministic and place connector payloads under `tests/contract/` only when their provider schema is intentionally being tested.
