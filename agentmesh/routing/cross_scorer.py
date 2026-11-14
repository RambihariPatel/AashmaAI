from typing import Tuple, Dict
from agentmesh.models.agent import Agent, AgentDomain
from agentmesh.models.post import Post, PostIntent


class ContextualCrossScorer:
    """
    Stage 3: Contextual Cross-Scorer.
    Evaluates business actionability and cross-industry synergy.
    Answers: Can this notified agent take a meaningful business action on this post?
    Produces a contextual synergy score [0.0, 1.0] and an explainability rationale.
    """

    # Domain synergy matrix: (author_domain, recipient_domain) -> base synergy
    DOMAIN_SYNERGIES: Dict[Tuple[AgentDomain, AgentDomain], float] = {
        # Food Delivery synergies
        (AgentDomain.FOOD_DELIVERY, AgentDomain.FINTECH_PAYMENTS): 0.95,
        (AgentDomain.FOOD_DELIVERY, AgentDomain.BANKING_CREDIT): 0.90,
        (AgentDomain.FOOD_DELIVERY, AgentDomain.ECOMMERCE): 0.50,
        (AgentDomain.FOOD_DELIVERY, AgentDomain.AUTOMOTIVE_FLEET): 0.15,

        # Ecommerce synergies
        (AgentDomain.ECOMMERCE, AgentDomain.BANKING_CREDIT): 0.95,
        (AgentDomain.ECOMMERCE, AgentDomain.FINTECH_PAYMENTS): 0.95,
        (AgentDomain.ECOMMERCE, AgentDomain.TRAVEL_LOGISTICS): 0.85,
        (AgentDomain.ECOMMERCE, AgentDomain.AUTOMOTIVE_FLEET): 0.40,

        # Automotive / Fleet synergies
        (AgentDomain.AUTOMOTIVE_FLEET, AgentDomain.TRAVEL_LOGISTICS): 0.90,
        (AgentDomain.AUTOMOTIVE_FLEET, AgentDomain.BANKING_CREDIT): 0.85,  # Vehicle financing
        (AgentDomain.AUTOMOTIVE_FLEET, AgentDomain.FOOD_DELIVERY): 0.20,
        (AgentDomain.AUTOMOTIVE_FLEET, AgentDomain.FINTECH_PAYMENTS): 0.35,

        # Fintech & Banking synergies
        (AgentDomain.FINTECH_PAYMENTS, AgentDomain.FOOD_DELIVERY): 0.85,
        (AgentDomain.FINTECH_PAYMENTS, AgentDomain.ECOMMERCE): 0.85,
        (AgentDomain.BANKING_CREDIT, AgentDomain.ECOMMERCE): 0.85,
    }

    def evaluate(self, post: Post, author_domain: AgentDomain, recipient: Agent) -> Tuple[float, str]:
        """
        Calculates actionable business synergy score and generates an explanation.
        """
        # 1. Base Domain Synergy
        synergy_key = (author_domain, recipient.domain)
        base_synergy = self.DOMAIN_SYNERGIES.get(synergy_key, 0.40)

        # 2. Intent Modifiers
        intent_multiplier = 1.0
        reason_fragments = []

        if post.intent == PostIntent.OFFER:
            if recipient.domain in [AgentDomain.FINTECH_PAYMENTS, AgentDomain.BANKING_CREDIT]:
                intent_multiplier = 1.15
                reason_fragments.append("Consumer promotional offer matches checkout payment/card rewards synergy")
            elif recipient.domain == AgentDomain.AUTOMOTIVE_FLEET:
                intent_multiplier = 0.60
                reason_fragments.append("Consumer discount has low relevance to vehicle manufacturing and fleet sales")
            else:
                reason_fragments.append("General promotional tie-in")

        elif post.intent == PostIntent.PARTNERSHIP_PROPOSAL:
            if recipient.domain in [AgentDomain.TRAVEL_LOGISTICS, AgentDomain.AUTOMOTIVE_FLEET]:
                intent_multiplier = 1.20
                reason_fragments.append("B2B partnership request aligns with operational logistics integration")
            else:
                intent_multiplier = 1.0

        # 3. Keyword / Topic synergy checks
        post_words = set(f"{post.content} {' '.join(post.tags)}".lower().split())
        agent_topics = set(t.lower() for t in recipient.subscription.topics)
        shared = post_words.intersection(agent_topics)

        if shared:
            keyword_bonus = min(0.20, 0.05 * len(shared))
            reason_fragments.append(f"Direct subscription tag overlap: {', '.join(list(shared)[:3])}")
        else:
            keyword_bonus = 0.0

        final_score = min(1.0, max(0.0, (base_synergy * intent_multiplier) + keyword_bonus))

        # Build clean reasoning string
        if not reason_fragments:
            reason = f"Cross-domain collaboration between {author_domain.value} and {recipient.domain.value}"
        else:
            reason = " | ".join(reason_fragments)

        return round(final_score, 3), reason
