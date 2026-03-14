"""A2A (Agent-to-Agent) protocol adapter for agent orchestration."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class A2AMessage(BaseModel):
    """A2A protocol message structure."""

    message_id: str
    sender: str
    receiver: Optional[str] = None
    action: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class A2AAdapter:
    """Adapter for A2A protocol messaging and orchestration."""

    def __init__(self) -> None:
        self.message_queue: List[A2AMessage] = []

    def emit_event(self, action: str, payload: Dict[str, Any], sender: str = "marketing-agent") -> A2AMessage:
        """Emit an A2A event message."""
        message = A2AMessage(
            message_id=f"msg_{datetime.utcnow().timestamp()}",
            sender=sender,
            action=action,
            payload=payload,
        )
        self.message_queue.append(message)
        return message

    def register_action(self, action: str, handler: callable) -> None:
        """Register an action handler for A2A messages."""
        # Placeholder for action registry
        pass

    def get_pending_messages(self, receiver: Optional[str] = None) -> List[A2AMessage]:
        """Retrieve pending messages, optionally filtered by receiver."""
        if receiver:
            return [msg for msg in self.message_queue if msg.receiver == receiver]
        return self.message_queue

