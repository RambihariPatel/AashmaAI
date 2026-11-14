from typing import List, Set
from agentmesh.models.agent import Agent, VerificationStatus
from agentmesh.models.post import Post
from agentmesh.storage.memory_store import StorageEngine


class CandidateGenerator:
    """
    Stage 0 & 1: Fast candidate retrieval and hard-filtering.
    Scales to thousands of agents by utilizing inverted indices and
    eliminating incompatible agents in O(1) ~ O(K) before expensive scoring.
    """

    def __init__(self, storage: StorageEngine):
        self.storage = storage

    def filter_and_retrieve_candidates(self, post: Post) -> List[Agent]:
        """
        Retrieves eligible candidate agents for a post using fast indexing
        and applies safety/domain/negative keyword hard filters.
        """
        author = self.storage.get_agent(post.author_agent_id)
        author_domain = author.domain if author else None

        # 1. Retrieve candidates via inverted topic index and domain index
        matched_agent_ids: Set[str] = set()

        # Tag overlap candidates
        for tag in post.tags:
            matched_agent_ids.update(self.storage.topic_index.get(tag.lower(), set()))

        # If few candidates found via tags, include domain-based candidates
        # Also always consider active agents with general interest
        for agent in self.storage.list_agents():
            # If agent has empty topics (broad observer) or general target
            if not agent.subscription.topics or not matched_agent_ids:
                matched_agent_ids.add(agent.agent_id)
            else:
                # Add agents whose target domains match author domain
                if author_domain and author_domain in agent.subscription.target_domains:
                    matched_agent_ids.add(agent.agent_id)

        candidates: List[Agent] = []
        post_text_lower = f"{post.content} {' '.join(post.tags)}".lower()

        for agent_id in matched_agent_ids:
            # Stage 0: Hard Filters
            if agent_id == post.author_agent_id:
                continue  # Never notify author

            agent = self.storage.get_agent(agent_id)
            if not agent or not agent.is_active:
                continue

            if agent.verification_status != VerificationStatus.VERIFIED:
                continue

            # Check if agent blocked author
            if post.author_agent_id in agent.subscription.blocked_agent_ids:
                continue

            # Check negative keywords
            has_negative = any(neg.lower() in post_text_lower for neg in agent.subscription.negative_keywords if neg)
            if has_negative:
                continue

            # Check domain restrictions (allow if direct tag/topic overlap exists)
            has_tag_match = any(tag.lower() in [t.lower() for t in agent.subscription.topics] for tag in post.tags)
            if agent.subscription.target_domains and not has_tag_match:
                if author_domain and author_domain not in agent.subscription.target_domains:
                    continue

            # Check hourly notification budget
            timestamps = self.storage.notification_timestamps.get(agent_id, [])
            # Keep budget check lightweight
            if len(timestamps) >= agent.subscription.hourly_notification_budget:
                continue

            candidates.append(agent)

        return candidates
