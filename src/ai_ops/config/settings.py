from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",
        case_sensitive=False,
        hide_input_in_errors=True,
    )

    app_env: Literal["local", "test", "staging", "production"] = "local"
    app_mode: Literal["offline", "real"] = "offline"
    auto_send: bool = False
    email_adapter: Literal["mock", "gmail"] = "mock"
    llm_adapter: Literal["mock", "real"] = "mock"
    sqlite_path: str = ".runtime/app.sqlite3"

    gmail_client_id: SecretStr | None = None
    gmail_client_secret: SecretStr | None = None
    gmail_refresh_token: SecretStr | None = None
    feishu_app_id: SecretStr | None = None
    feishu_app_secret: SecretStr | None = None
    llm_api_key: SecretStr | None = None

    @field_validator("auto_send", mode="before")
    @classmethod
    def parse_boolean(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in {"true", "false"}:
            return value.lower() == "true"
        raise ValueError("AUTO_SEND must be exactly true or false")

    @model_validator(mode="after")
    def validate_runtime_boundary(self) -> "Settings":
        if self.auto_send:
            raise ValueError(
                "AUTO_SEND=true is disabled until the outbound safety gate is approved"
            )

        if self.app_mode == "offline":
            if self.email_adapter != "mock" or self.llm_adapter != "mock":
                raise ValueError(
                    "APP_MODE=offline requires EMAIL_ADAPTER=mock and LLM_ADAPTER=mock"
                )
            return self

        if self.email_adapter != "gmail" or self.llm_adapter != "real":
            raise ValueError("APP_MODE=real requires EMAIL_ADAPTER=gmail and LLM_ADAPTER=real")

        required = {
            "GMAIL_CLIENT_ID": self.gmail_client_id,
            "GMAIL_CLIENT_SECRET": self.gmail_client_secret,
            "GMAIL_REFRESH_TOKEN": self.gmail_refresh_token,
            "FEISHU_APP_ID": self.feishu_app_id,
            "FEISHU_APP_SECRET": self.feishu_app_secret,
            "LLM_API_KEY": self.llm_api_key,
        }
        missing = [
            name
            for name, value in required.items()
            if value is None or not value.get_secret_value()
        ]
        if missing:
            raise ValueError(
                "APP_MODE=real requires configured production secrets: " + ", ".join(missing)
            )
        return self


def load_settings() -> Settings:
    """Load and validate settings; invalid production configuration fails closed."""

    return Settings()
