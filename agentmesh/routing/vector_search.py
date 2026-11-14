import re
import math
from typing import List, Dict, Optional
import numpy as np


class HybridSemanticEmbedder:
    """
    Computes semantic vector representations of posts and agent interest profiles.
    Uses sub-word and term-frequency hashing with domain concept expansion
    and cosine similarity for high-throughput, zero-external-dependency execution.
    Can also be swapped with dense transformer embeddings (e.g. OpenAI/Ollama/SentenceTransformers).
    """

    DIMENSION = 128

    # Semantic concept clusters that bridge cross-domain vocabularies
    CONCEPT_SYNONYMS: Dict[str, List[str]] = {
        "payment": ["upi", "card", "wallet", "checkout", "cashback", "settlement", "pay", "transaction", "hdfc", "phonepe"],
        "discount": ["offer", "5%", "10%", "sale", "cashback", "deals", "promo", "voucher", "diwali", "festive"],
        "food_delivery": ["swiggy", "zomato", "restaurant", "meals", "delivery", "orders", "dining", "groceries"],
        "banking": ["credit_cards", "debit", "emi", "smartbuy", "hdfc", "loan", "financing", "interest"],
        "automotive": ["bajaj", "bike", "fleet", "ev", "scooter", "vehicle", "two-wheeler", "logistics_fleet"],
        "ecommerce": ["flipkart", "amazon", "electronics", "cart", "products", "shopping"],
    }

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\b[A-Za-z0-9_%₹$]+\b", text.lower())
        tokens = []
        for word in words:
            tokens.append(word)
            # Lightweight suffix normalization (stemming common plurals/gerunds)
            stemmed = word
            if word.endswith("ies"):
                stemmed = word[:-3] + "y"
                tokens.append(stemmed)
                tokens.append(word[:-3])
            elif word.endswith("es") and len(word) > 4:
                tokens.append(word[:-2])
            elif word.endswith("s") and not word.endswith("ss") and len(word) > 3:
                tokens.append(word[:-1])

            # Expand with conceptual synonyms
            for concept, synonyms in self.CONCEPT_SYNONYMS.items():
                if word in synonyms or stemmed in synonyms or word == concept or stemmed == concept:
                    tokens.append(concept)
                    tokens.extend(synonyms[:3])
        return tokens

    def embed_text(self, text: str) -> List[float]:
        tokens = self._tokenize(text)
        vec = np.zeros(self.DIMENSION, dtype=np.float32)

        if not tokens:
            return vec.tolist()

        for token in tokens:
            # Deterministic hash bucket
            h = hash(token) % self.DIMENSION
            weight = 1.0
            # Higher weight for specific monetary/percentage/offer signals
            if "%" in token or "₹" in token or "$" in token or token in ["diwali", "festive", "cashback"]:
                weight = 2.0
            vec[h] += weight

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2:
            return 0.0
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        dot = float(np.dot(a, b))
        # Clip to [0.0, 1.0]
        return max(0.0, min(1.0, dot))
