import pytest
from agentmesh.storage.memory_store import StorageEngine
from agentmesh.agents.company_agents import get_default_company_agents
from agentmesh.models.post import Post, PostIntent
from agentmesh.routing.pipeline import RelevanceRoutingPipeline


@pytest.fixture
def test_env():
    storage = StorageEngine()
    for agent in get_default_company_agents():
        storage.register_agent(agent)
    pipeline = RelevanceRoutingPipeline(storage)
    return storage, pipeline


def test_swiggy_diwali_routing_accuracy(test_env):
    storage, pipeline = test_env
    swiggy = storage.get_agent_by_handle("@swiggy_deals")

    post = Post(
        author_agent_id=swiggy.agent_id,
        author_handle=swiggy.handle,
        author_company=swiggy.company_name,
        content="5% off all deliveries on Diwali.",
        intent=PostIntent.OFFER,
        tags=["food_delivery", "diwali", "discounts"]
    )
    storage.create_post(post)

    candidates, notifications = pipeline.route_post(post)
    notified_handles = [n.author_handle if n.author_handle != "@swiggy_deals" else storage.get_agent(n.recipient_agent_id).handle for n in notifications]

    # Verify Swiggy itself is not notified
    assert "@swiggy_deals" not in notified_handles

    # Verify PhonePe and HDFC are notified
    assert "@phonepe_rewards" in notified_handles
    assert "@hdfc_cards" in notified_handles

    # Verify Bajaj Auto is NOT notified (spam prevention)
    assert "@bajaj_mobility" not in notified_handles


def test_self_notification_prevention(test_env):
    storage, pipeline = test_env
    phonepe = storage.get_agent_by_handle("@phonepe_rewards")

    post = Post(
        author_agent_id=phonepe.agent_id,
        author_handle=phonepe.handle,
        author_company=phonepe.company_name,
        content="UPI flat cashback weekend for all shopping apps.",
        intent=PostIntent.OFFER,
        tags=["payments", "upi", "cashback"]
    )
    storage.create_post(post)

    candidates, notifications = pipeline.route_post(post)
    recipient_ids = [n.recipient_agent_id for n in notifications]
    assert phonepe.agent_id not in recipient_ids
