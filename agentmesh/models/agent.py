from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid
import secrets


class AgentDomain(str, Enum):
    FOOD_DELIVERY = "food_delivery"
    FINTECH_PAYMENTS = "fintech_payments"
    BANKING_CREDIT = "banking_credit"
    ECOMMERCE = "ecommerce"
    AUTOMOTIVE_FLEET = "automotive_fleet"
    HEALTHCARE = "healthcare"
    TRAVEL_LOGISTICS = "travel_logistics"
    GENERAL = "general"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class InterestSubscription(BaseModel):
    """
    Declarative and semantic specification of what an agent cares about.
    Used by the multi-stage routing engine for fast candidate retrieval
    and semantic vector matching.
    """
    topics: List[str] = Field(
        default_factory=list,
        description="Explicit keywords/tags the agent monitors (e.g., 'festivals', 'discounts', 'upi', 'co-brand')"
    )
    semantic_description: str = Field(
        ...,
        description="Natural language description of what partnership, offer, or market intelligence triggers this agent."
    )
    target_domains: List[AgentDomain] = Field(
        default_factory=list,
        description="Domains the agent actively wants to collaborate with. If empty, considers all."
    )
    negative_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that immediately disqualify a post for this agent."
    )
    blocked_agent_ids: List[str] = Field(
        default_factory=list,
        description="Agents whose posts should never trigger notifications."
    )
    min_relevance_threshold: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum composite relevance score needed to dispatch a notification."
    )
    hourly_notification_budget: int = Field(
        default=50,
        ge=1,
        description="Maximum notifications allowed per hour to prevent LLM overload."
    )


class AgentRegistrationRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=100)
    handle: str = Field(..., pattern=r"^@[A-Za-z0-9_]{3,30}$")
    domain: AgentDomain
    description: str = Field(..., max_length=500)
    webhook_url: Optional[str] = None
    subscription: InterestSubscription


class Agent(BaseModel):
    agent_id: str = Field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:10]}")
    company_name: str
    handle: str
    domain: AgentDomain
    description: str
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    webhook_url: Optional[str] = None
    webhook_secret: str = Field(default_factory=lambda: secrets.token_hex(16))
    api_key: str = Field(default_factory=lambda: f"agk_{secrets.token_urlsafe(24)}")
    reputation_score: float = Field(default=100.0, ge=0.0, le=100.0)
    subscription: InterestSubscription
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
