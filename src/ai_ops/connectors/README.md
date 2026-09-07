# Connector Boundary

External Gmail, Feishu, and LLM SDK calls belong under this boundary. Application, Graph, and Agent layers consume provider-neutral protocols from `ai_ops.domain.interfaces`; they must not import vendor SDKs directly.

Mock and real implementations must satisfy the same contract tests. Replacing an email or model provider should require adding or changing a connector implementation, not changing the domain interfaces or domain models.
