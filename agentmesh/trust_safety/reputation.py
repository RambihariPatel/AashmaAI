from agentmesh.models.agent import Agent, VerificationStatus


class ReputationManager:
    """
    Maintains trust scores across agents.
    Reputation determines routing priority and notification delivery caps.
    """

    SUSPENSION_THRESHOLD = 40.0
    PROBATION_THRESHOLD = 65.0

    @staticmethod
    def adjust_reputation(agent: Agent, delta: float, reason: str = "") -> Agent:
        new_score = round(max(0.0, min(100.0, agent.reputation_score + delta)), 2)
        agent.reputation_score = new_score

        if new_score < ReputationManager.SUSPENSION_THRESHOLD:
            agent.verification_status = VerificationStatus.SUSPENDED
            agent.is_active = False
        elif new_score < ReputationManager.PROBATION_THRESHOLD:
            # Lower notification limits on probation
            agent.subscription.hourly_notification_budget = max(5, agent.subscription.hourly_notification_budget // 2)

        return agent
