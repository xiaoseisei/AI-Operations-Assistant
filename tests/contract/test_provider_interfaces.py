from ai_ops.domain.interfaces import EmailProvider, LLMProvider


class FakeEmailProvider:
    def fetch_message(self, message_id: str) -> dict:
        return {"message_id": message_id}


class FakeLLMProvider:
    def generate(self, prompt: str) -> str:
        return prompt


def test_provider_interfaces_are_provider_neutral():
    email: EmailProvider = FakeEmailProvider()
    llm: LLMProvider = FakeLLMProvider()

    assert email.fetch_message("msg-demo") == {"message_id": "msg-demo"}
    assert llm.generate("prompt-demo") == "prompt-demo"
