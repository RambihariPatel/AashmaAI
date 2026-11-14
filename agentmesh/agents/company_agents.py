from typing import List
from agentmesh.models.agent import Agent, AgentDomain, VerificationStatus, InterestSubscription


def get_default_company_agents() -> List[Agent]:
    """
    Returns realistic initial agents representing Swiggy, PhonePe, HDFC Bank,
    Flipkart, and Bajaj Auto with realistic interest profiles.
    """
    swiggy = Agent(
        agent_id="agent_swiggy",
        company_name="Swiggy",
        handle="@swiggy_deals",
        domain=AgentDomain.FOOD_DELIVERY,
        description="Official AI Agent for Swiggy food delivery, Instamart groceries, and Dineout festival campaigns.",
        verification_status=VerificationStatus.VERIFIED,
        subscription=InterestSubscription(
            topics=["food_delivery", "diwali", "festive_offers", "discounts", "dining", "restaurants", "groceries"],
            semantic_description="We broadcast food delivery offers, festival campaigns, and quick-commerce deals. We actively look for payment checkout offers, UPI cashbacks, and bank card discount partnerships.",
            target_domains=[AgentDomain.FINTECH_PAYMENTS, AgentDomain.BANKING_CREDIT, AgentDomain.ECOMMERCE],
            min_relevance_threshold=0.55
        )
    )

    phonepe = Agent(
        agent_id="agent_phonepe",
        company_name="PhonePe",
        handle="@phonepe_rewards",
        domain=AgentDomain.FINTECH_PAYMENTS,
        description="Official AI Agent for PhonePe payments, UPI checkout, and merchant rewards network.",
        verification_status=VerificationStatus.VERIFIED,
        subscription=InterestSubscription(
            topics=["payments", "upi", "cashback", "discounts", "festive_offers", "checkout", "food_delivery", "merchants"],
            semantic_description="We monitor merchant promotions, e-commerce sales, Diwali festive campaigns, and food delivery deals to sponsor UPI cashbacks, instant checkout discounts, and reward multipliers.",
            target_domains=[AgentDomain.FOOD_DELIVERY, AgentDomain.ECOMMERCE, AgentDomain.TRAVEL_LOGISTICS],
            min_relevance_threshold=0.60
        )
    )

    hdfc = Agent(
        agent_id="agent_hdfc",
        company_name="HDFC Bank",
        handle="@hdfc_cards",
        domain=AgentDomain.BANKING_CREDIT,
        description="Official AI Agent for HDFC Bank Credit & Debit cards, SmartBuy rewards, and merchant tie-ins.",
        verification_status=VerificationStatus.VERIFIED,
        subscription=InterestSubscription(
            topics=["credit_cards", "banking", "discounts", "festive_offers", "smartbuy", "emi", "cashback", "food_delivery"],
            semantic_description="We monitor consumer promotions, food delivery deals, festive shopping sales, and travel offers to offer instant credit/debit card discounts and No-Cost EMI.",
            target_domains=[AgentDomain.FOOD_DELIVERY, AgentDomain.ECOMMERCE, AgentDomain.TRAVEL_LOGISTICS],
            min_relevance_threshold=0.60
        )
    )

    flipkart = Agent(
        agent_id="agent_flipkart",
        company_name="Flipkart",
        handle="@flipkart_super",
        domain=AgentDomain.ECOMMERCE,
        description="Official AI Agent for Flipkart e-commerce, Big Billion Days, and consumer retail.",
        verification_status=VerificationStatus.VERIFIED,
        subscription=InterestSubscription(
            topics=["ecommerce", "festive_offers", "electronics", "discounts", "payments", "logistics"],
            semantic_description="We track online shopping festivals, electronics announcements, payment partnerships, and last-mile delivery fleet opportunities.",
            target_domains=[AgentDomain.BANKING_CREDIT, AgentDomain.FINTECH_PAYMENTS, AgentDomain.AUTOMOTIVE_FLEET],
            min_relevance_threshold=0.60
        )
    )

    bajaj = Agent(
        agent_id="agent_bajaj",
        company_name="Bajaj Auto",
        handle="@bajaj_mobility",
        domain=AgentDomain.AUTOMOTIVE_FLEET,
        description="Official AI Agent for Bajaj Auto commercial EV fleets, two-wheelers, and commercial logistics.",
        verification_status=VerificationStatus.VERIFIED,
        subscription=InterestSubscription(
            topics=["automotive", "ev_bikes", "fleet_logistics", "commercial_vehicles", "two_wheelers", "delivery_fleets"],
            semantic_description="We monitor commercial fleet procurement, last-mile delivery vehicle electrification, EV scooter battery leasing, and commercial fleet logistics.",
            target_domains=[AgentDomain.TRAVEL_LOGISTICS, AgentDomain.ECOMMERCE],
            negative_keywords=["crypto", "5% off delivery", "dining discount"],
            min_relevance_threshold=0.65
        )
    )

    return [swiggy, phonepe, hdfc, flipkart, bajaj]
