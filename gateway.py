"""
MCP Gateway — scope-enforcing tool invocation layer.

Every sub-agent in MCP-Swarm is issued a short-lived, task-scoped capability
token by the Supervisor Agent (Sec. IV-B of the paper). The gateway is the
single choke point through which all MCP Tool invocations pass; it enforces
least privilege by checking the requesting agent's granted scope against the
tool being invoked, and it refuses to honor a capability token outside the
task context it was minted for (non-transitive delegation — see
"Authorization Propagation in Multi-Agent AI Systems", Tallam, 2026).

This is a synthetic, seed-free, deterministic reference implementation used
to produce reproducible security-regression evidence for the paper. It is
NOT a production access-control system.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import time

# Per-role least-privilege scope table. Each sub-agent role is granted only
# the tools it needs to do its job; nothing else.
SCOPE_TABLE: Dict[str, Set[str]] = {
    "supervisor": {"council.invoke", "memory.read", "memory.write", "doc.dispatch"},
    "council_model": {"council.respond"},
    "document_intelligence": {"doc.parse", "memory.write"},
    "memory_agent": {"memory.read", "memory.write", "memory.expire"},
    "external_tool_agent": {"api.invoke_readonly"},
}

# Tools considered high-risk / irreversible; invoking these always requires
# the "supervisor" role regardless of what the scope table says, mirroring
# a break-glass / human-oversight boundary triggered over SSE.
HIGH_RISK_TOOLS: Set[str] = {"memory.expire_all", "api.invoke_writeback"}


@dataclass
class CapabilityToken:
    agent_role: str
    task_id: str
    issued_at: float = field(default_factory=time.time)
    ttl_seconds: float = 30.0

    def expired(self, now: float) -> bool:
        return (now - self.issued_at) > self.ttl_seconds


@dataclass
class AuditEntry:
    agent_role: str
    tool: str
    task_id: str
    allowed: bool
    reason: str


class MCPGateway:
    def __init__(self):
        self.audit_log: List[AuditEntry] = []

    def enforce(self, token: CapabilityToken, tool: str, invoked_task_id: str,
                now: Optional[float] = None) -> AuditEntry:
        now = time.time() if now is None else now

        # 1. Token expiry (bounded blast radius in time)
        if token.expired(now):
            entry = AuditEntry(token.agent_role, tool, invoked_task_id, False,
                                "token_expired")
            self.audit_log.append(entry)
            return entry

        # 2. Non-transitive delegation: a token minted for task A cannot be
        #    reused to authorize an action under task B (authorization
        #    propagation control).
        if token.task_id != invoked_task_id:
            entry = AuditEntry(token.agent_role, tool, invoked_task_id, False,
                                "task_scope_mismatch")
            self.audit_log.append(entry)
            return entry

        # 3. High-risk tools require supervisor role irrespective of scope.
        if tool in HIGH_RISK_TOOLS and token.agent_role != "supervisor":
            entry = AuditEntry(token.agent_role, tool, invoked_task_id, False,
                                "high_risk_requires_supervisor")
            self.audit_log.append(entry)
            return entry

        # 4. Least-privilege scope check.
        allowed_tools = SCOPE_TABLE.get(token.agent_role, set())
        if tool not in allowed_tools:
            entry = AuditEntry(token.agent_role, tool, invoked_task_id, False,
                                "out_of_scope")
            self.audit_log.append(entry)
            return entry

        entry = AuditEntry(token.agent_role, tool, invoked_task_id, True, "ok")
        self.audit_log.append(entry)
        return entry


class UngatedBaseline:
    """
    Represents a naive MCP integration with no gateway enforcement: every
    tool call from every agent is allowed unconditionally, regardless of
    scope, task binding, or token expiry. This models the class of
    undefended MCP client/server integrations documented in MCPSecBench
    (Yang et al., 2025), which reports current client-side protections
    across major MCP platforms succeed at blocking attacks less than 30% of
    the time. Used only as a comparison baseline so that the gateway's
    effect can be measured relative to something, not only shown to be
    internally consistent.
    """
    def __init__(self):
        self.audit_log: List[AuditEntry] = []

    def enforce(self, token: CapabilityToken, tool: str, invoked_task_id: str,
                now: Optional[float] = None) -> AuditEntry:
        entry = AuditEntry(token.agent_role, tool, invoked_task_id, True,
                            "ungated_baseline_allow_all")
        self.audit_log.append(entry)
        return entry
