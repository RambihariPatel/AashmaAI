from fastapi import APIRouter
from typing import Dict, Any
from pydantic import BaseModel
from agentmesh.models.metrics import SystemMetrics
from agentmesh.models.notification import FeedbackEvent
from agentmesh.storage.memory_store import storage

router = APIRouter(prefix="/api/v1", tags=["Metrics & Feedback"])


class FeedbackReportRequest(BaseModel):
    notification_id: str
    post_id: str
    recipient_agent_id: str
    author_agent_id: str
    action: str  # "commented", "ignored", "reported_irrelevant"
    reward: float  # +1.0, 0.0, -1.0


@router.get("/metrics", response_model=SystemMetrics)
def get_metrics():
    """Returns platform operational metrics and conversion rate."""
    return storage.get_metrics()


@router.get("/affinity")
def get_affinity_matrix() -> Dict[str, Dict[str, float]]:
    """Returns the learned agent-to-agent affinity scores."""
    result = {}
    for author_id, recipients in storage.affinity_matrix.items():
        result[author_id] = dict(recipients)
    return result


@router.post("/feedback")
def submit_feedback(req: FeedbackReportRequest):
    """Submits manual or external feedback on notification quality to tune future routing."""
    event = FeedbackEvent(
        notification_id=req.notification_id,
        post_id=req.post_id,
        recipient_agent_id=req.recipient_agent_id,
        author_agent_id=req.author_agent_id,
        action=req.action,
        reward=req.reward
    )
    storage.record_feedback(event)
    return {
        "status": "success",
        "updated_affinity": storage.get_affinity(req.author_agent_id, req.recipient_agent_id)
    }
