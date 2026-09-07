"""Validate configuration without printing secret values."""

from __future__ import annotations

import sys

from ai_ops.config import load_settings


def main() -> int:
    try:
        settings = load_settings()
    except Exception as error:  # noqa: BLE001 - CLI returns a safe concise error.
        print(f"CONFIG_CHECK_FAIL {error}", file=sys.stderr)
        return 1

    print(
        "CONFIG_CHECK_PASS "
        f"app_env={settings.app_env} "
        f"app_mode={settings.app_mode} "
        f"email_adapter={settings.email_adapter} "
        f"llm_adapter={settings.llm_adapter} "
        f"auto_send={str(settings.auto_send).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
