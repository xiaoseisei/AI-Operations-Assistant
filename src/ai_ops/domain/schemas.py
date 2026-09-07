"""Versioned domain and event schemas for the first persistence baseline."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Tenant(StrictSchema):
    internal_id: UUID
    provider_id: str | None = None
    name: str
    status: Literal["active", "paused", "suspended"] = "active"
    created_at: datetime


class Mailbox(StrictSchema):
    internal_id: UUID
    tenant_id: UUID
    provider_id: str
    address: str
    status: Literal["active", "reauth_required", "disabled"] = "active"


class Thread(StrictSchema):
    internal_id: UUID
    tenant_id: UUID
    mailbox_id: UUID
    provider_id: str
    status: Literal["open", "closed", "paused"] = "open"
    last_inbound_at: datetime | None = None


class Message(StrictSchema):
    internal_id: UUID
    tenant_id: UUID
    thread_id: UUID
    provider_id: str
    event_id: str
    direction: Literal["inbound", "outbound"]
    body_ref: str
    received_at: datetime


class Draft(StrictSchema):
    internal_id: UUID
    tenant_id: UUID
    thread_id: UUID
    run_id: UUID
    body: str
    draft_hash: str = Field(min_length=8)
    status: Literal["draft", "pending_approval", "approved", "rejected"] = "draft"


class Approval(StrictSchema):
    internal_id: UUID
    tenant_id: UUID
    draft_id: UUID
    decision: Literal["approve", "edit", "reject", "reassign"]
    actor_id: str
    approved_hash: str
    decided_at: datetime


class FollowUp(StrictSchema):
    internal_id: UUID
    tenant_id: UUID
    thread_id: UUID
    status: Literal["scheduled", "invalidated", "cancelled", "sent"]
    scheduled_at: datetime
    invalidation_reason: str | None = None


class ProfileFact(StrictSchema):
    internal_id: UUID
    tenant_id: UUID
    subject_key: str
    fact_type: Literal["fact", "inference", "hypothesis"]
    value: str
    source_message_id: UUID
    evidence_span: str
    confidence: float = Field(ge=0, le=1)
    observed_at: datetime


class KnowledgeDocument(StrictSchema):
    internal_id: UUID
    tenant_id: UUID | None = None
    document_id: str
    version: str
    title: str
    blob_ref: str
    status: Literal["staging", "active", "archived"]


class AgentRun(StrictSchema):
    internal_id: UUID
    tenant_id: UUID
    thread_id: UUID
    schema_version: int = Field(ge=1)
    route: str
    status: Literal["running", "pending_approval", "completed", "failed", "quarantined"]
    started_at: datetime
    finished_at: datetime | None = None


class EventEnvelope(StrictSchema):
    event_id: str = Field(min_length=1)
    provider_event_id: str | None = None
    provider_id: str
    tenant_id: UUID
    thread_id: UUID | None = None
    schema_version: int = Field(ge=1)
    event_type: str
    occurred_at: datetime
    payload: dict[str, Any]
