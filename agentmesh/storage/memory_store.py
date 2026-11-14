import threading
from typing import Dict, List, Optional, Set
from collections import defaultdict
from agentmesh.models.agent import Agent, AgentDomain
from agentmesh.models.post import Post
from agentmesh.models.comment import Comment
from agentmesh.models.notification import Notification, FeedbackEvent
from agentmesh.models.metrics import SystemMetrics


class StorageEngine:
    """
    Thread-safe repository for agents, posts, comments, notifications,
    inverted index for O(1) candidate lookup, and the adaptive affinity matrix.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.agents: Dict[str, Agent] = {}
        self.agents_by_handle: Dict[str, str] = {}
        self.agents_by_api_key: Dict[str, str] = {}

        self.posts: Dict[str, Post] = {}
        self.comments_by_post: Dict[str, List[Comment]] = defaultdict(list)
        self.notifications: Dict[str, Notification] = {}
        self.agent_inboxes: Dict[str, List[Notification]] = defaultdict(list)
        self.feedback_events: List[FeedbackEvent] = []

        # Inverted index for candidate retrieval (Stage 1)
        self.topic_index: Dict[str, Set[str]] = defaultdict(set)
        self.domain_index: Dict[str, Set[str]] = defaultdict(set)

        # Pairwise affinity matrix: (author_agent_id, recipient_agent_id) -> score in [0.0, 1.0]
        # Initialized to neutral 0.50
        self.affinity_matrix: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(lambda: 0.50))

        # Hourly notification tracking for rate-limiting
        self.notification_timestamps: Dict[str, List[float]] = defaultdict(list)

    def register_agent(self, agent: Agent) -> Agent:
        with self._lock:
            self.agents[agent.agent_id] = agent
            self.agents_by_handle[agent.handle.lower()] = agent.agent_id
            self.agents_by_api_key[agent.api_key] = agent.agent_id

            # Update inverted indices
            self.domain_index[agent.domain.value].add(agent.agent_id)
            for topic in agent.subscription.topics:
                self.topic_index[topic.lower()].add(agent.agent_id)

            return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        with self._lock:
            return self.agents.get(agent_id)

    def get_agent_by_handle(self, handle: str) -> Optional[Agent]:
        with self._lock:
            agent_id = self.agents_by_handle.get(handle.lower())
            return self.agents.get(agent_id) if agent_id else None

    def get_agent_by_api_key(self, api_key: str) -> Optional[Agent]:
        with self._lock:
            agent_id = self.agents_by_api_key.get(api_key)
            return self.agents.get(agent_id) if agent_id else None

    def list_agents(self) -> List[Agent]:
        with self._lock:
            return list(self.agents.values())

    def create_post(self, post: Post) -> Post:
        with self._lock:
            self.posts[post.post_id] = post
            return post

    def get_post(self, post_id: str) -> Optional[Post]:
        with self._lock:
            return self.posts.get(post_id)

    def list_posts(self, limit: int = 50) -> List[Post]:
        with self._lock:
            sorted_posts = sorted(self.posts.values(), key=lambda p: p.created_at, reverse=True)
            return sorted_posts[:limit]

    def add_comment(self, comment: Comment) -> Comment:
        with self._lock:
            self.comments_by_post[comment.post_id].append(comment)
            if comment.post_id in self.posts:
                self.posts[comment.post_id].comment_count += 1
            return comment

    def get_comments(self, post_id: str) -> List[Comment]:
        with self._lock:
            return list(self.comments_by_post.get(post_id, []))

    def record_notification(self, notification: Notification) -> Notification:
        with self._lock:
            self.notifications[notification.notification_id] = notification
            self.agent_inboxes[notification.recipient_agent_id].append(notification)
            if notification.post_id in self.posts:
                self.posts[notification.post_id].notification_count += 1
            return notification

    def get_notifications_for_agent(self, agent_id: str) -> List[Notification]:
        with self._lock:
            return list(self.agent_inboxes.get(agent_id, []))

    def record_feedback(self, event: FeedbackEvent) -> None:
        with self._lock:
            self.feedback_events.append(event)
            # Find and update corresponding notification
            if event.notification_id in self.notifications:
                notif = self.notifications[event.notification_id]
                notif.engaged = (event.action == "commented")
                notif.feedback_score = event.reward

            # Update EWMA affinity matrix:
            # new_affinity = alpha * reward_normalized + (1 - alpha) * current_affinity
            # reward ranges from -1.0 to 1.0 -> map to [0.0, 1.0] where 1.0 is +1, 0.5 is 0, 0.0 is -1
            target_norm = (event.reward + 1.0) / 2.0
            alpha = 0.25  # Learning rate
            curr = self.affinity_matrix[event.author_agent_id][event.recipient_agent_id]
            updated = (alpha * target_norm) + ((1.0 - alpha) * curr)
            self.affinity_matrix[event.author_agent_id][event.recipient_agent_id] = round(max(0.0, min(1.0, updated)), 4)

    def get_affinity(self, author_id: str, recipient_id: str) -> float:
        with self._lock:
            return self.affinity_matrix[author_id][recipient_id]

    def get_metrics(self) -> SystemMetrics:
        with self._lock:
            total_notifs = len(self.notifications)
            engaged_notifs = sum(1 for n in self.notifications.values() if n.engaged)
            conversion = (engaged_notifs / total_notifs * 100.0) if total_notifs > 0 else 0.0

            domain_counts = defaultdict(int)
            for p in self.posts.values():
                author = self.agents.get(p.author_agent_id)
                if author:
                    domain_counts[author.domain.value] += 1

            avg_score = 0.0
            if total_notifs > 0:
                avg_score = sum(n.relevance_score for n in self.notifications.values()) / total_notifs

            return SystemMetrics(
                total_agents=len(self.agents),
                total_posts=len(self.posts),
                total_notifications_sent=total_notifs,
                total_comments=sum(len(c) for c in self.comments_by_post.values()),
                conversion_rate_pct=round(conversion, 2),
                spam_blocked_count=0,
                avg_relevance_score=round(avg_score, 3),
                domain_post_counts=dict(domain_counts)
            )


# Global singleton instance for application use
storage = StorageEngine()
