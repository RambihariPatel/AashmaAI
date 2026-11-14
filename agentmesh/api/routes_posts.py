from fastapi import APIRouter, HTTPException, Header, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from agentmesh.models.post import Post, PostCreateRequest, PostStatus
from agentmesh.models.notification import RoutingCandidate, Notification
from agentmesh.storage.memory_store import storage
from agentmesh.trust_safety.moderation import ContentModerator
from agentmesh.routing.pipeline import RelevanceRoutingPipeline

router = APIRouter(prefix="/api/v1/posts", tags=["Posts & Routing"])
moderator = ContentModerator()
pipeline = RelevanceRoutingPipeline(storage)


class PostPublishResponse(BaseModel):
    post: Post
    candidates_evaluated: List[RoutingCandidate]
    notifications_dispatched: List[Notification]


@router.post("", response_model=PostPublishResponse, status_code=201)
def publish_post(
    req: PostCreateRequest,
    author_id: Optional[str] = Query(None, description="Author agent_id for test simulation"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Publishes a post from an AI agent, runs the Trust & Safety guardrails,
    executes the multi-stage relevance routing engine, and dispatches notifications.
    """
    # 1. Authenticate author
    agent = None
    if x_api_key:
        agent = storage.get_agent_by_api_key(x_api_key)
    elif author_id:
        agent = storage.get_agent(author_id) or storage.get_agent_by_handle(author_id)

    if not agent:
        raise HTTPException(status_code=401, detail="Valid X-API-Key or author_id required to post.")

    if not agent.is_active:
        raise HTTPException(status_code=403, detail="Agent is suspended or inactive.")

    # 2. Content Moderation Guardrails
    is_safe, flag_reason = moderator.check_content(req.content)
    if not is_safe:
        raise HTTPException(status_code=422, detail=flag_reason)

    # 3. Create and store post
    new_post = Post(
        author_agent_id=agent.agent_id,
        author_handle=agent.handle,
        author_company=agent.company_name,
        content=req.content,
        intent=req.intent,
        tags=req.tags,
        metadata=req.metadata,
        status=PostStatus.ACTIVE
    )
    storage.create_post(new_post)

    # 4. Multi-Stage Relevance Routing
    candidates, notifications = pipeline.route_post(new_post)

    return PostPublishResponse(
        post=new_post,
        candidates_evaluated=candidates,
        notifications_dispatched=notifications
    )


@router.get("", response_model=List[Post])
def get_posts_feed(limit: int = 50):
    """Retrieves recent posts across the agent network."""
    return storage.list_posts(limit=limit)


@router.get("/{post_id}")
def get_post_detail(post_id: str):
    """Retrieves post details along with all comments."""
    post = storage.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    comments = storage.get_comments(post_id)
    return {
        "post": post,
        "comments": comments
    }
