import random
from typing import Dict, Any, Tuple
from agentmesh.models.agent import Agent


class AdaptiveBanditRanker:
    """
    Stage 4: Blends multi-stage signals into a final decision.
    Implements:
    - Multi-signal weighted composite scoring
    - Dynamic congestion thresholding (prevents inbox overload)
    - Epsilon-greedy exploration for partnership discovery
    - Feedback updates via Exponentially Weighted Moving Average (EWMA)
    """

    def __init__(
        self,
        weight_tag: float = 0.15,
        weight_semantic: float = 0.35,
        weight_contextual: float = 0.35,
        weight_affinity: float = 0.15,
        epsilon: float = 0.05
    ):
        self.w_tag = weight_tag
        self.w_sem = weight_semantic
        self.w_ctx = weight_contextual
        self.w_aff = weight_affinity
        self.epsilon = epsilon

    def compute_composite_score(
        self,
        tag_score: float,
        semantic_score: float,
        contextual_score: float,
        historical_affinity: float
    ) -> float:
        composite = (
            self.w_tag * tag_score +
            self.w_sem * semantic_score +
            self.w_ctx * contextual_score +
            self.w_aff * historical_affinity
        )
        return round(max(0.0, min(1.0, composite)), 3)

    def decide_notification(
        self,
        agent: Agent,
        composite_score: float,
        current_hourly_count: int,
        allow_exploration: bool = True
    ) -> Tuple[bool, str]:
        """
        Applies dynamic thresholding and epsilon-greedy exploration.
        Returns (should_notify: bool, explanation: str).
        """
        base_threshold = agent.subscription.min_relevance_threshold

        # Dynamic congestion tax: if agent is receiving high volume, raise the bar
        congestion_penalty = 0.0
        budget = agent.subscription.hourly_notification_budget
        load_factor = current_hourly_count / max(1, budget)
        if load_factor > 0.70:
            congestion_penalty = 0.10
        elif load_factor > 0.90:
            congestion_penalty = 0.20

        effective_threshold = min(0.95, base_threshold + congestion_penalty)

        if composite_score >= effective_threshold:
            return True, f"Passed threshold ({composite_score:.2f} >= {effective_threshold:.2f})"

        # Epsilon-greedy exploration: test near-boundary matches to break echo chambers
        if allow_exploration and composite_score >= 0.50 and random.random() < self.epsilon:
            return True, f"Exploration dispatch (Bandit epsilon probe at {composite_score:.2f})"

        return False, f"Below relevance threshold ({composite_score:.2f} < {effective_threshold:.2f})"
