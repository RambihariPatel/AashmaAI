import hmac
import hashlib
import json
from typing import Dict, Any, Tuple


class SecurityManager:
    """Handles agent API authentication and HMAC-SHA256 webhook signatures."""

    @staticmethod
    def sign_payload(payload: Dict[str, Any], secret: str) -> str:
        """Computes HMAC-SHA256 signature for outgoing webhook notifications."""
        serialized = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), serialized, hashlib.sha256).hexdigest()
        return f"sha256={signature}"

    @staticmethod
    def verify_signature(payload: Dict[str, Any], secret: str, header_signature: str) -> bool:
        """Verifies HMAC-SHA256 header against the payload."""
        if not header_signature or not header_signature.startswith("sha256="):
            return False
        expected_sig = SecurityManager.sign_payload(payload, secret)
        return hmac.compare_digest(expected_sig, header_signature)

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validates format of agent API key."""
        return api_key.startswith("agk_") and len(api_key) >= 30
