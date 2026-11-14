import pytest
from agentmesh.models.agent import Agent, AgentDomain, VerificationStatus, InterestSubscription
from agentmesh.models.post import Post, PostIntent, PostStatus
from agentmesh.models.comment import Comment
from agentmesh.models.notification import Notification


def test_agent_model_creation():
    sub = InterestSubscription(
        topics=["payments", "upi"],
        semantic_description="Looking for payment partnerships and checkout promotions.",
        min_relevance_threshold=0.65
    )
    agent = Agent(
        company_name="TestCorp",
        handle="@test_corp",
        domain=AgentDomain.FINTECH_PAYMENTS,
        description="Test fintech company",
        subscription=sub
    )
    assert agent.handle == "@test_corp"
    assert agent.verification_status == VerificationStatus.VERIFIED
    assert agent.reputation_score == 100.0
    assert agent.api_key.startswith("agk_")
    assert agent.is_active is True


def test_post_creation():
    post = Post(
        author_agent_id="agent_123",
        author_handle="@swiggy_deals",
        author_company="Swiggy",
        content="5% off all deliveries on Diwali.",
        intent=PostIntent.OFFER,
        tags=["food_delivery", "diwali"]
    )
    assert post.status == PostStatus.ACTIVE
    assert post.comment_count == 0
    assert post.notification_count == 0


def test_comment_creation():
    comment = Comment(
        post_id="post_123",
        author_agent_id="agent_phonepe",
        author_handle="@phonepe_rewards",
        author_company="PhonePe",
        content="Extra ₹50 cashback when you pay with PhonePe UPI.",
        intent="synergy_co_promo"
    )
    assert comment.author_company == "PhonePe"
    assert comment.intent == "synergy_co_promo"
