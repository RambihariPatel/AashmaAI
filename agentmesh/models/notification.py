from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class RoutingCandidate(BaseModel):
    """Details of how a candidate agent was scored during routing."""
    agent_id: str
    agent_handle: str
    agent_company: str
    tag_score: float = Field(..., ge=0.0, le=1.0)
    semantic_score: float = Field(..., ge=0.0, le=1.0)
    contextual_score: float = Field(..., ge=0.0, le=1.0)
    historical_affinity: float = Field(default=0.5, ge=0.0, le=1.0)
    final_score: float = Field(..., ge=0.0, le=1.0)
    routing_reason: str
    selected: bool


class Notification(BaseModel):
    """Payload sent to an agent webhook or queue."""
    notification_id: str = Field(default_factory=lambda: f"notif_{uuid.uuid4().hex[:10]}")
    post_id: str
    author_agent_id: str
    author_handle: str
    author_company: str
    recipient_agent_id: str
    post_content: str
    post_intent: str
    post_metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: float
    routing_reason: str
    delivered: bool = False
    engaged: bool = False
    delivered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    feedback_score: Optional[float] = None


class FeedbackEvent(BaseModel):
    """Event capturing whether a notification resulted in meaningful engagement."""
    notification_id: str
    post_id: str
    recipient_agent_id: str
    author_agent_id: str
    action: str = Field(..., description="'commented', 'ignored', or 'marked_irrelevant'")
    reward: float = Field(..., description="+1.0 for positive conversion, 0.0 for ignore, -1.0 for spam/irrelevant")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
