import pytest
from pydantic import ValidationError

from ai_ops.config import Settings


def test_offline_mock_defaults_require_no_secrets():
    settings = Settings(_env_file=None)

    assert settings.app_mode == "offline"
    assert settings.email_adapter == "mock"
    assert settings.llm_adapter == "mock"
    assert settings.auto_send is False


def test_false_is_parsed_as_false(monkeypatch):
    monkeypatch.setenv("AUTO_SEND", "false")

    assert Settings(_env_file=None).auto_send is False


@pytest.mark.parametrize("value", ["0", "no", "off", "yes", "random", ""])
def test_ambiguous_boolean_is_rejected(monkeypatch, value):
    monkeypatch.setenv("AUTO_SEND", value)

    with pytest.raises(ValidationError, match="AUTO_SEND"):
        Settings(_env_file=None)


def test_offline_mode_rejects_real_adapter(monkeypatch):
    monkeypatch.setenv("EMAIL_ADAPTER", "gmail")

    with pytest.raises(ValidationError, match="APP_MODE=offline"):
        Settings(_env_file=None)


def test_real_mode_requires_all_secrets(monkeypatch):
    monkeypatch.setenv("APP_MODE", "real")
    monkeypatch.setenv("EMAIL_ADAPTER", "gmail")
    monkeypatch.setenv("LLM_ADAPTER", "real")

    with pytest.raises(ValidationError, match="GMAIL_CLIENT_ID"):
        Settings(_env_file=None)


def test_real_mode_accepts_configured_secrets(monkeypatch):
    values = {
        "APP_MODE": "real",
        "EMAIL_ADAPTER": "gmail",
        "LLM_ADAPTER": "real",
        "GMAIL_CLIENT_ID": "client-demo",
        "GMAIL_CLIENT_SECRET": "secret-demo",
        "GMAIL_REFRESH_TOKEN": "refresh-demo",
        "FEISHU_APP_ID": "app-demo",
        "FEISHU_APP_SECRET": "feishu-secret-demo",
        "LLM_API_KEY": "llm-key-demo",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)

    assert settings.gmail_client_secret.get_secret_value() == "secret-demo"
    assert str(settings.gmail_client_secret) == "**********"


def test_auto_send_is_rejected_until_safety_gate(monkeypatch):
    monkeypatch.setenv("AUTO_SEND", "true")

    with pytest.raises(ValidationError, match="AUTO_SEND=true"):
        Settings(_env_file=None)


def test_validation_errors_do_not_echo_secret_values(monkeypatch):
    monkeypatch.setenv("APP_MODE", "real")
    monkeypatch.setenv("EMAIL_ADAPTER", "gmail")
    monkeypatch.setenv("LLM_ADAPTER", "real")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "secret-client-demo")

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    assert "secret-client-demo" not in str(error.value)
