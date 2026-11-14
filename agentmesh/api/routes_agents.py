from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from agentmesh.models.agent import Agent, AgentRegistrationRequest, InterestSubscription
from agentmesh.storage.memory_store import storage

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


@router.post("/register", response_model=Agent, status_code=201)
def register_agent(req: AgentRegistrationRequest):
    """Registers a new company AI agent and sets up its declarative and semantic interest profile."""
    # Check handle uniqueness
    if storage.get_agent_by_handle(req.handle):
        raise HTTPException(status_code=400, detail=f"Handle '{req.handle}' is already registered.")

    new_agent = Agent(
        company_name=req.company_name,
        handle=req.handle,
        domain=req.domain,
        description=req.description,
        webhook_url=req.webhook_url,
        subscription=req.subscription
    )
    storage.register_agent(new_agent)
    return new_agent


@router.get("", response_model=List[Agent])
def list_agents():
    """Lists all registered AI agents on the network."""
    return storage.list_agents()


@router.get("/{agent_id}", response_model=Agent)
def get_agent(agent_id: str):
    """Retrieves an agent profile by agent_id or handle."""
    agent = storage.get_agent(agent_id) or storage.get_agent_by_handle(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return agent


@router.put("/{agent_id}/subscription", response_model=Agent)
def update_subscription(agent_id: str, subscription: InterestSubscription):
    """Updates what an agent cares about (topics, semantic manifesto, filters)."""
    agent = storage.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    agent.subscription = subscription
    # Re-register to update inverted index
    storage.register_agent(agent)
    return agent


@router.get("/{agent_id}/inbox")
def get_agent_inbox(agent_id: str):
    """Fetches notifications delivered to an agent's inbox."""
    agent = storage.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return storage.get_notifications_for_agent(agent_id)
