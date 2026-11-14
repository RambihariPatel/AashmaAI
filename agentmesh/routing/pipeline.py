from typing import List, Tuple
from agentmesh.models.agent import Agent, AgentDomain
from agentmesh.models.post import Post
from agentmesh.models.notification import Notification, RoutingCandidate
from agentmesh.storage.memory_store import StorageEngine
from agentmesh.routing.candidate_gen import CandidateGenerator
from agentmesh.routing.vector_search import HybridSemanticEmbedder
from agentmesh.routing.cross_scorer import ContextualCrossScorer
from agentmesh.routing.bandit_feedback import AdaptiveBanditRanker
from agentmesh.trust_safety.verification import SecurityManager


class RelevanceRoutingPipeline:
    """
    End-to-End Multi-Stage Relevance Engine for AgentMesh.
    Orchestrates candidate generation, semantic embedding, contextual cross-scoring,
    and adaptive bandit thresholding.
    """

    def __init__(self, storage: StorageEngine):
        self.storage = storage
        self.candidate_gen = CandidateGenerator(storage)
        self.embedder = HybridSemanticEmbedder()
        self.cross_scorer = ContextualCrossScorer()
        self.bandit_ranker = AdaptiveBanditRanker()

    def route_post(self, post: Post) -> Tuple[List[RoutingCandidate], List[Notification]]:
        """
        Processes a newly published post, runs through the 4-stage pipeline,
        and generates notifications for relevant agents.
        """
        # Ensure post has embedding
        post_full_text = f"{post.content} {' '.join(post.tags)} {post.intent.value}"
        if not post.embedding:
            post.embedding = self.embedder.embed_text(post_full_text)

        author = self.storage.get_agent(post.author_agent_id)
        author_domain = author.domain if author else AgentDomain.GENERAL

        # Stage 0 & 1: Candidate Generation & Hard Filters
        candidates = self.candidate_gen.filter_and_retrieve_candidates(post)

        evaluated_candidates: List[RoutingCandidate] = []
        notifications_to_send: List[Notification] = []

        for candidate_agent in candidates:
            # 1. Tag overlap score
            post_tags = set(t.lower() for t in post.tags)
            agent_topics = set(t.lower() for t in candidate_agent.subscription.topics)
            if post_tags and agent_topics:
                intersection = len(post_tags.intersection(agent_topics))
                tag_score = round(intersection / len(post_tags), 3)
            else:
                tag_score = 0.0

            # 2. Semantic vector similarity
            agent_profile_text = (
                f"{candidate_agent.description} "
                f"{' '.join(candidate_agent.subscription.topics)} "
                f"{candidate_agent.subscription.semantic_description}"
            )
            agent_embedding = self.embedder.embed_text(agent_profile_text)
            semantic_score = round(self.embedder.cosine_similarity(post.embedding, agent_embedding), 3)

            # 3. Contextual cross-domain synergy
            contextual_score, synergy_reason = self.cross_scorer.evaluate(
                post=post,
                author_domain=author_domain,
                recipient=candidate_agent
            )

            # 4. Historical affinity from feedback matrix
            affinity = self.storage.get_affinity(post.author_agent_id, candidate_agent.agent_id)

            # 5. Composite score calculation
            composite_score = self.bandit_ranker.compute_composite_score(
                tag_score=tag_score,
                semantic_score=semantic_score,
                contextual_score=contextual_score,
                historical_affinity=affinity
            )

            # 6. Dynamic thresholding decision
            hourly_count = len(self.storage.agent_inboxes.get(candidate_agent.agent_id, []))
            should_notify, decision_reason = self.bandit_ranker.decide_notification(
                agent=candidate_agent,
                composite_score=composite_score,
                current_hourly_count=hourly_count
            )

            full_reason = f"{synergy_reason} | Decision: {decision_reason}"

            routing_record = RoutingCandidate(
                agent_id=candidate_agent.agent_id,
                agent_handle=candidate_agent.handle,
                agent_company=candidate_agent.company_name,
                tag_score=tag_score,
                semantic_score=semantic_score,
                contextual_score=contextual_score,
                historical_affinity=affinity,
                final_score=composite_score,
                routing_reason=full_reason,
                selected=should_notify
            )
            evaluated_candidates.append(routing_record)

            if should_notify:
                notif = Notification(
                    post_id=post.post_id,
                    author_agent_id=post.author_agent_id,
                    author_handle=post.author_handle,
                    author_company=post.author_company,
                    recipient_agent_id=candidate_agent.agent_id,
                    post_content=post.content,
                    post_intent=post.intent.value,
                    post_metadata=post.metadata,
                    relevance_score=composite_score,
                    routing_reason=full_reason,
                    delivered=True
                )
                self.storage.record_notification(notif)
                notifications_to_send.append(notif)

        # Sort evaluated candidates by final_score descending
        evaluated_candidates.sort(key=lambda c: c.final_score, reverse=True)
        return evaluated_candidates, notifications_to_send
