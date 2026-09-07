from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai_ops.domain.schemas import EventEnvelope, Message, Tenant, export_json_schemas


def test_domain_schema_accepts_valid_message():
    message = Message(
        internal_id=uuid4(), tenant_id=uuid4(), thread_id=uuid4(), provider_id="gmail-mock",
        event_id="event-demo-001", direction="inbound", body_ref="blob://demo/message-001",
        received_at=datetime.now(UTC),
    )
    assert message.provider_id == "gmail-mock"


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        Tenant(
            internal_id=uuid4(),
            name="Demo Tenant",
            created_at=datetime.now(UTC),
            unexpected="reject-me",
        )


def test_required_fields_are_rejected():
    with pytest.raises(ValidationError):
        Message.model_validate({"provider_id": "gmail-mock"})


def test_event_schema_version_is_positive():
    with pytest.raises(ValidationError):
        EventEnvelope(
            event_id="event-demo-002",
            provider_id="gmail-mock",
            tenant_id=uuid4(),
            schema_version=-1,
            event_type="message.received",
            occurred_at=datetime.now(UTC),
            payload={},
        )


def test_unmappable_event_can_be_quarantined_by_route():
    event = EventEnvelope(
        event_id="event-demo-003",
        provider_id="unknown-provider",
        tenant_id=uuid4(),
        schema_version=1,
        event_type="unknown.event",
        occurred_at=datetime.now(UTC),
        payload={"quarantine_reason": "unsupported provider"},
    )
    assert event.payload["quarantine_reason"]


def test_legacy_event_version_is_explicitly_identified():
    event = EventEnvelope(
        event_id="event-demo-legacy",
        provider_id="gmail-mock",
        tenant_id=uuid4(),
        schema_version=0,
        event_type="message.received",
        occurred_at=datetime.now(UTC),
        payload={"legacy": True},
    )

    assert event.is_legacy is True


def test_domain_json_schemas_are_exported(tmp_path):
    export_json_schemas(str(tmp_path))

    schema = (tmp_path / "event-envelope.v1.json").read_text(encoding="utf-8")
    assert '"$schema": "https://json-schema.org/draft/2020-12/schema"' in schema
    assert '"schema_version"' in schema
