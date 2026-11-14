from typing import Optional, List
from agentmesh.models.agent import Agent
from agentmesh.models.notification import Notification, FeedbackEvent
from agentmesh.models.comment import Comment, CommentCreateRequest
from agentmesh.agents.mock_llm import LLMEngine
from agentmesh.storage.memory_store import StorageEngine


class AutonomousAgentWorker:
    """
    Autonomous runtime for an agent participating in AgentMesh.
    Handles:
    - Receiving notifications
    - Evaluating whether to engage
    - Calling LLM to draft high-synergy comments
    - Submitting comments to the platform
    - Reporting feedback to close the learning loop
    """

    def __init__(self, agent: Agent, llm: Optional[LLMEngine] = None):
        self.agent = agent
        self.llm = llm or LLMEngine()

    def should_engage(self, notification: Notification) -> bool:
        """Decides whether this agent will engage with a received notification."""
        if not self.agent.is_active:
            return False

        # Threshold check
        if notification.relevance_score < self.agent.subscription.min_relevance_threshold:
            return False

        return True

    def draft_response(self, notification: Notification) -> Optional[CommentCreateRequest]:
        """Uses LLM to construct a brand-aligned response comment."""
        if not self.should_engage(notification):
            return None

        comment_text = self.llm.generate_response(
            company_name=self.agent.company_name,
            handle=self.agent.handle,
            domain=self.agent.domain.value,
            personality_prompt=self.agent.description,
            post_content=notification.post_content,
            post_author=notification.author_handle,
            routing_reason=notification.routing_reason
        )

        return CommentCreateRequest(
            content=comment_text,
            intent="synergy_co_promo",
            metadata={
                "in_response_to_notif": notification.notification_id,
                "relevance_score": notification.relevance_score
            }
        )

    def process_notification(
        self,
        notification: Notification,
        storage: StorageEngine
    ) -> Optional[Comment]:
        """
        Receives a notification, decides whether to respond, creates a comment,
        and posts feedback to improve future routing.
        """
        if self.should_engage(notification):
            comment_req = self.draft_response(notification)
            if comment_req:
                comment = Comment(
                    post_id=notification.post_id,
                    author_agent_id=self.agent.agent_id,
                    author_handle=self.agent.handle,
                    author_company=self.agent.company_name,
                    content=comment_req.content,
                    intent=comment_req.intent,
                    metadata=comment_req.metadata
                )
                storage.add_comment(comment)

                # Positive feedback event
                storage.record_feedback(FeedbackEvent(
                    notification_id=notification.notification_id,
                    post_id=notification.post_id,
                    recipient_agent_id=self.agent.agent_id,
                    author_agent_id=notification.author_agent_id,
                    action="commented",
                    reward=1.0
                ))
                return comment

        # If rejected/ignored
        storage.record_feedback(FeedbackEvent(
            notification_id=notification.notification_id,
            post_id=notification.post_id,
            recipient_agent_id=self.agent.agent_id,
            author_agent_id=notification.author_agent_id,
            action="ignored",
            reward=0.0
        ))
        return None
