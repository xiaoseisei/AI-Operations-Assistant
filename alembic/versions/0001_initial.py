"""initial domain tables"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_tenant_id", sa.String(255), unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "mailboxes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("provider_mailbox_id", sa.String(255), nullable=False),
        sa.Column("address", sa.String(320), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
    )
    op.create_index("ix_mailboxes_tenant_id", "mailboxes", ["tenant_id"])
    op.create_table(
        "inbox_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("provider_event_id", sa.String(255), nullable=False),
        sa.Column("thread_id", sa.String(64)),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "provider_event_id", name="uq_inbox_event"),
    )
    op.create_index("ix_inbox_records_tenant_id", "inbox_records", ["tenant_id"])
    op.create_table(
        "threads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("provider_thread_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("last_inbound_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id", "provider_thread_id", name="uq_thread_provider"),
    )
    op.create_index("ix_threads_tenant_id", "threads", ["tenant_id"])
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("thread_id", sa.String(64), nullable=False),
        sa.Column("provider_message_id", sa.String(255), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("body_ref", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "provider_message_id", name="uq_message_provider"),
    )
    op.create_index("ix_messages_tenant_id", "messages", ["tenant_id"])
    op.create_index("ix_messages_thread_id", "messages", ["thread_id"])
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("thread_id", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_runs_tenant_id", "agent_runs", ["tenant_id"])
    op.create_index("ix_agent_runs_thread_id", "agent_runs", ["thread_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("event_ref", sa.String(255), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_ref", sa.Text()),
    )
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])
    op.create_table(
        "drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("thread_id", sa.String(64), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("body_ref", sa.Text(), nullable=False),
        sa.Column("draft_hash", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_drafts_tenant_id", "drafts", ["tenant_id"])
    op.create_index("ix_drafts_thread_id", "drafts", ["thread_id"])
    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("draft_id", sa.String(64), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("approved_hash", sa.String(128), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_approvals_tenant_id", "approvals", ["tenant_id"])
    op.create_index("ix_approvals_draft_id", "approvals", ["draft_id"])
    op.create_table(
        "follow_ups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("thread_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invalidation_reason", sa.Text()),
    )
    op.create_index("ix_follow_ups_tenant_id", "follow_ups", ["tenant_id"])
    op.create_index("ix_follow_ups_thread_id", "follow_ups", ["thread_id"])
    op.create_table(
        "profile_facts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("subject_key", sa.String(255), nullable=False),
        sa.Column("fact_type", sa.String(32), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("source_message_id", sa.String(64), nullable=False),
        sa.Column("evidence_span", sa.Text(), nullable=False),
        sa.Column("confidence", sa.String(32), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_profile_facts_tenant_id", "profile_facts", ["tenant_id"])
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64)),
        sa.Column("document_id", sa.String(255), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("blob_ref", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
    )
    op.create_index("ix_knowledge_documents_tenant_id", "knowledge_documents", ["tenant_id"])
    op.create_table(
        "send_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("thread_id", sa.String(64), nullable=False),
        sa.Column("draft_hash", sa.String(128), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("provider_message_id", sa.String(255)),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_send_attempts_tenant_id", "send_attempts", ["tenant_id"])
    op.create_index("ix_send_attempts_thread_id", "send_attempts", ["thread_id"])


def downgrade() -> None:
    op.drop_index("ix_send_attempts_thread_id", table_name="send_attempts")
    op.drop_index("ix_send_attempts_tenant_id", table_name="send_attempts")
    op.drop_table("send_attempts")
    op.drop_index("ix_knowledge_documents_tenant_id", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
    op.drop_index("ix_profile_facts_tenant_id", table_name="profile_facts")
    op.drop_table("profile_facts")
    op.drop_index("ix_follow_ups_thread_id", table_name="follow_ups")
    op.drop_index("ix_follow_ups_tenant_id", table_name="follow_ups")
    op.drop_table("follow_ups")
    op.drop_index("ix_approvals_draft_id", table_name="approvals")
    op.drop_index("ix_approvals_tenant_id", table_name="approvals")
    op.drop_table("approvals")
    op.drop_index("ix_drafts_thread_id", table_name="drafts")
    op.drop_index("ix_drafts_tenant_id", table_name="drafts")
    op.drop_table("drafts")
    op.drop_index("ix_audit_events_tenant_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_agent_runs_thread_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_tenant_id", table_name="agent_runs")
    op.drop_table("agent_runs")
    op.drop_index("ix_messages_thread_id", table_name="messages")
    op.drop_index("ix_messages_tenant_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_threads_tenant_id", table_name="threads")
    op.drop_table("threads")
    op.drop_index("ix_inbox_records_tenant_id", table_name="inbox_records")
    op.drop_table("inbox_records")
    op.drop_index("ix_mailboxes_tenant_id", table_name="mailboxes")
    op.drop_table("mailboxes")
    op.drop_table("tenants")
