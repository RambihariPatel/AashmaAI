import pytest
from agentmesh.storage.memory_store import StorageEngine
from agentmesh.models.notification import FeedbackEvent, Notification


def test_feedback_loop_boosts_affinity():
    storage = StorageEngine()
    author_id = "agent_swiggy"
    recipient_id = "agent_phonepe"

    initial_affinity = storage.get_affinity(author_id, recipient_id)
    assert initial_affinity == 0.50

    # Record notification
    notif = Notification(
        post_id="post_1",
        author_agent_id=author_id,
        author_handle="@swiggy_deals",
        author_company="Swiggy",
        recipient_agent_id=recipient_id,
        post_content="Diwali 5% off",
        post_intent="offer",
        relevance_score=0.75,
        routing_reason="High payment synergy"
    )
    storage.record_notification(notif)

    # Positive engagement: comment posted (+1.0 reward)
    event = FeedbackEvent(
        notification_id=notif.notification_id,
        post_id="post_1",
        recipient_agent_id=recipient_id,
        author_agent_id=author_id,
        action="commented",
        reward=1.0
    )
    storage.record_feedback(event)

    updated_affinity = storage.get_affinity(author_id, recipient_id)
    assert updated_affinity > initial_affinity
    assert updated_affinity == 0.625


def test_feedback_loop_penalizes_spam():
    storage = StorageEngine()
    author_id = "agent_spammer"
    recipient_id = "agent_phonepe"

    event = FeedbackEvent(
        notification_id="notif_spam",
        post_id="post_spam",
        recipient_agent_id=recipient_id,
        author_agent_id=author_id,
        action="marked_irrelevant",
        reward=-1.0
    )
    storage.record_feedback(event)

    updated_affinity = storage.get_affinity(author_id, recipient_id)
    assert updated_affinity < 0.50
