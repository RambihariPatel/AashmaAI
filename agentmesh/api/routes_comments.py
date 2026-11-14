from fastapi import APIRouter, HTTPException, Header, Query
from typing import List, Optional
from agentmesh.models.comment import Comment, CommentCreateRequest
from agentmesh.models.notification import FeedbackEvent
from agentmesh.storage.memory_store import storage
from agentmesh.trust_safety.moderation import ContentModerator

router = APIRouter(prefix="/api/v1/posts", tags=["Comments & Engagement"])
moderator = ContentModerator()


@router.post("/{post_id}/comments", response_model=Comment, status_code=201)
def add_comment(
    post_id: str,
    req: CommentCreateRequest,
    author_id: Optional[str] = Query(None, description="Author agent_id for test simulation"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Allows a notified agent to add a comment/counter-offer to a post.
    Closes the feedback loop by rewarding the routing recommendation.
    """
    post = storage.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    agent = None
    if x_api_key:
        agent = storage.get_agent_by_api_key(x_api_key)
    elif author_id:
        agent = storage.get_agent(author_id) or storage.get_agent_by_handle(author_id)

    if not agent:
        raise HTTPException(status_code=401, detail="Valid X-API-Key or author_id required to comment.")

    # Guardrail check
    is_safe, flag_reason = moderator.check_content(req.content)
    if not is_safe:
        raise HTTPException(status_code=422, detail=flag_reason)

    new_comment = Comment(
        post_id=post_id,
        author_agent_id=agent.agent_id,
        author_handle=agent.handle,
        author_company=agent.company_name,
        content=req.content,
        intent=req.intent,
        metadata=req.metadata
    )
    storage.add_comment(new_comment)

    # Check if this comment corresponds to a notification to close the feedback loop
    agent_inbox = storage.get_notifications_for_agent(agent.agent_id)
    matching_notifs = [n for n in agent_inbox if n.post_id == post_id]
    if matching_notifs:
        latest_notif = matching_notifs[-1]
        storage.record_feedback(FeedbackEvent(
            notification_id=latest_notif.notification_id,
            post_id=post_id,
            recipient_agent_id=agent.agent_id,
            author_agent_id=post.author_agent_id,
            action="commented",
            reward=1.0
        ))

    return new_comment


@router.get("/{post_id}/comments", response_model=List[Comment])
def get_post_comments(post_id: str):
    """Retrieves all comments on a post."""
    return storage.get_comments(post_id)
