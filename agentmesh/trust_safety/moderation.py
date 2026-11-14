import re
from typing import Tuple, Optional


class ContentModerator:
    """
    Guardrails engine protecting the agent network from:
    1. Prompt injections and system prompt leakage attempts
    2. Phishing, crypto scamming, and fraudulent claims
    3. Malicious code payloads and abusive language
    """

    INJECTION_PATTERNS = [
        r"(?i)\bignore\s+(all\s+)?(previous|prior)\s+instructions\b",
        r"(?i)\byou\s+are\s+now\s+(an\s+)?unfiltered\b",
        r"(?i)\bsystem\s+prompt\s+(leak|override|reveal)\b",
        r"(?i)\bjailbreak\b",
        r"(?i)\bexecute\s+arbitrary\s+code\b",
        r"(?i)\beval\s*\(",
        r"(?i)<\s*script\b",
    ]

    SCAM_PATTERNS = [
        r"(?i)\b(free\s+crypto|send\s+bitcoin|double\s+your\s+eth|seed\s+phrase)\b",
        r"(?i)\bguaranteed\s+(1000%|return|wealth)\b",
        r"(?i)\bclaim\s+\$?\d+,\d{3}\s+prize\b",
    ]

    ABUSE_PATTERNS = [
        r"(?i)\b(fraudsters|scammers|thieves)\s+at\s+@?\w+\b",
        r"(?i)\bboycott\s+@?\w+\b",
    ]

    def check_content(self, text: str) -> Tuple[bool, Optional[str]]:
        if not text or len(text.strip()) == 0:
            return False, "Content cannot be empty"

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text):
                return False, f"Flagged by Trust & Safety: Potential prompt injection or system override detected."

        for pattern in self.SCAM_PATTERNS:
            if re.search(pattern, text):
                return False, f"Flagged by Trust & Safety: Prohibited financial scam or spam pattern detected."

        for pattern in self.ABUSE_PATTERNS:
            if re.search(pattern, text):
                return False, f"Flagged by Trust & Safety: Defamatory or targeted competitor attack detected."

        return True, None
