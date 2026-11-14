from typing import Dict
from pydantic import BaseModel, Field


class SystemMetrics(BaseModel):
    total_agents: int = 0
    total_posts: int = 0
    total_notifications_sent: int = 0
    total_comments: int = 0
    conversion_rate_pct: float = Field(default=0.0, description="Percentage of notifications converted to comments")
    spam_blocked_count: int = 0
    avg_relevance_score: float = 0.0
    domain_post_counts: Dict[str, int] = Field(default_factory=dict)
