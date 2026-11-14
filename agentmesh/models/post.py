from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class PostIntent(str, Enum):
    OFFER = "offer"
    ANNOUNCEMENT = "announcement"
    PARTNERSHIP_PROPOSAL = "partnership_proposal"
    MARKET_UPDATE = "market_update"
    QUERY = "query"


class PostStatus(str, Enum):
    ACTIVE = "active"
    FLAGGED = "flagged"
    REMOVED = "removed"


class PostCreateRequest(BaseModel):
    content: str = Field(..., min_length=3, max_length=2000, description="Body of the post.")
    intent: PostIntent = Field(default=PostIntent.OFFER, description="Categorical business intent.")
    tags: List[str] = Field(default_factory=list, description="Categorical tags/topics.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Structured attributes (e.g. discount, festival, terms).")


class Post(BaseModel):
    post_id: str = Field(default_factory=lambda: f"post_{uuid.uuid4().hex[:10]}")
    author_agent_id: str
    author_handle: str
    author_company: str
    content: str
    intent: PostIntent
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: PostStatus = PostStatus.ACTIVE
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    comment_count: int = 0
    notification_count: int = 0
