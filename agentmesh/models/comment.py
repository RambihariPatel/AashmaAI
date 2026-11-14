from typing import Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=2, max_length=1500, description="The comment text drafted by the agent.")
    intent: str = Field(default="synergy_response", description="Business intent of the response (e.g. cashback_offer, co_promo, counter_offer).")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Structured parameters of the proposed offer or reply.")


class Comment(BaseModel):
    comment_id: str = Field(default_factory=lambda: f"cmt_{uuid.uuid4().hex[:10]}")
    post_id: str
    author_agent_id: str
    author_handle: str
    author_company: str
    content: str
    intent: str = "synergy_response"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
