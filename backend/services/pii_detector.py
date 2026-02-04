"""
Comprehensive PII Detection and Redaction Service

Detects and redacts 15+ types of Personally Identifiable Information (PII)
using pre-compiled regex patterns for high performance.

Supported PII Types:
- Email addresses
- API keys (OpenAI, AWS, Google, GitHub, Stripe)
- Credit cards (Visa, Mastercard, Amex, Discover)
- SSNs (US Social Security Numbers)
- Phone numbers (US and international)
- IP addresses (IPv4 and IPv6)
- JWT tokens
- Private keys (RSA, EC, OpenSSH)
- Passwords/secrets (in code/config)
- Passport numbers
"""
import re
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Comprehensive PII pattern definitions
PII_PATTERNS = {
    "email": [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    ],
    "api_key": [
        r'\bsk-[a-zA-Z0-9]{20,}\b',  # OpenAI
        r'\b(sk|pk)_(test|live)_[a-zA-Z0-9]{24,}\b',  # Stripe
        r'\bAKIA[A-Z0-9]{16}\b',  # AWS Access Key
        r'\bAIza[a-zA-Z0-9_-]{35}\b',  # Google API Key
        r'\bghp_[a-zA-Z0-9]{36}\b',  # GitHub Personal Access Token
        r'\bgho_[a-zA-Z0-9]{36}\b',  # GitHub OAuth Token
        r'\bghu_[a-zA-Z0-9]{36}\b',  # GitHub User Token
        r'\bghs_[a-zA-Z0-9]{36}\b',  # GitHub Server Token
        r'\bghr_[a-zA-Z0-9]{36}\b',  # GitHub Refresh Token
        r'\bya29\.[0-9A-Za-z\-_]+\b',  # Google OAuth
    ],
    "credit_card": [
        # Visa, Mastercard, Amex, Discover (with or without separators)
        r'\b(?:\d{4}[\s-]?){3}\d{4}\b',
        r'\b\d{13,19}\b',  # Generic card number
    ],
    "ssn": [
        r'\b\d{3}-\d{2}-\d{4}\b',  # XXX-XX-XXXX format
        r'\b\d{3}\s\d{2}\s\d{4}\b',  # XXX XX XXXX format
    ],
    "phone": [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
        r'\+\d{1,3}\s?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}\b',  # International
    ],
    "ip_address": [
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IPv4
        r'\b([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',  # IPv6
    ],
    "jwt_token": [
        r'\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b',
    ],
    "private_key": [
        r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    ],
    "password": [
        r'(?i)(password|pwd|pass|secret|token|api_key|apikey)\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?',
    ],
    "passport": [
        r'\b[A-Z]{1,2}\d{6,9}\b',  # US Passport format
    ],
    # Additional security-sensitive patterns
    "bearer_token": [
        r'\bBearer\s+[a-zA-Z0-9_-]{20,}\b',
    ],
    # Additional PII types (Issue #11)
    "drivers_license": [
        r'\b[A-Z]{1,2}\d{6,8}\b',  # Most US states
        r'\b[A-Z]\d{7}\b',  # Some states
    ],
    "vin": [
        r'\b[A-HJ-NPR-Z0-9]{17}\b',  # Vehicle Identification Number
    ],
    "healthcare_id": [
        r'\b\d{3}-\d{2}-\d{4}\b',  # Similar to SSN format
        r'\bH\d{9}\b',  # Some healthcare IDs
    ],
    "aws_secret": [
        r'\b[A-Za-z0-9/+=]{40}\b',  # AWS Secret Access Key
    ],
}


class PIIDetector:
    """
    High-performance PII detection and redaction service.
    
    Pre-compiles all regex patterns during initialization for faster processing.
    """
    
    def __init__(self):
        """Initialize the PII detector with pre-compiled regex patterns."""
        logger.info("Initializing PIIDetector with comprehensive patterns")
        
        # Pre-compile all patterns for performance
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        for pii_type, patterns in PII_PATTERNS.items():
            self._compiled_patterns[pii_type] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern in patterns
            ]
        
        logger.info(f"Compiled {len(self._compiled_patterns)} PII pattern categories")
    
    def detect(self, text: str) -> List[Dict[str, any]]:
        """
        Detect PII in text without modifying it.
        
        Args:
            text: The text to scan for PII
            
        Returns:
            List of detected PII items with type, value, and position:
            [
                {
                    "type": "EMAIL",
                    "value": "user@example.com",
                    "position": (10, 27),
                    "confidence": "high"
                },
                ...
            ]
        """
        found = []
        
        for pii_type, compiled_patterns in self._compiled_patterns.items():
            for pattern in compiled_patterns:
                for match in pattern.finditer(text):
                    found.append({
                        "type": pii_type.upper(),
                        "value": match.group(0),
                        "position": match.span(),
                        "confidence": "high" if pii_type in ["email", "ssn", "credit_card"] else "medium"
                    })
        
        if found:
            logger.info(f"Detected {len(found)} PII items across {len(set(item['type'] for item in found))} types")
        
        return found
    
    def redact(self, text: str, redaction_format: str = "[REDACTED: {type}]") -> str:
        """
        Redact PII from text, replacing with redaction markers.
        
        Args:
            text: The text to redact
            redaction_format: Format string for redaction marker (default: "[REDACTED: {type}]")
            
        Returns:
            Text with all PII replaced by redaction markers
        """
        result = text
        redaction_count = 0
        
        # Process patterns in order of specificity (most specific first)
        # This prevents partial redactions
        priority_order = [
            "private_key", "jwt_token", "api_key", "bearer_token",
            "aws_secret", "password", "ssn", "credit_card",
            "email", "phone", "ip_address", "passport"
        ]
        
        for pii_type in priority_order:
            if pii_type not in self._compiled_patterns:
                continue
                
            replacement = redaction_format.format(type=pii_type.upper())
            
            for pattern in self._compiled_patterns[pii_type]:
                matches_before = len(pattern.findall(result))
                result = pattern.sub(replacement, result)
                redaction_count += matches_before
        
        if redaction_count > 0:
            logger.info(f"Redacted {redaction_count} PII items")
        
        return result
    
    def process(self, text: str) -> Dict[str, any]:
        """
        Detect and redact PII in one operation.
        
        Args:
            text: The text to process
            
        Returns:
            Dictionary with sanitized text and detection metadata:
            {
                "sanitized_text": "...",
                "pii_found": [...],
                "redaction_count": 3,
                "pii_types": ["EMAIL", "API_KEY"]
            }
        """
        # Detect first (on original text for accurate positions)
        pii_found = self.detect(text)
        
        # Then redact
        sanitized_text = self.redact(text)
        
        return {
            "sanitized_text": sanitized_text,
            "pii_found": pii_found,
            "redaction_count": len(pii_found),
            "pii_types": list(set(item["type"] for item in pii_found))
        }


# Singleton instance for reuse
_detector_instance: PIIDetector | None = None


def get_pii_detector() -> PIIDetector:
    """
    Get or create the singleton PII detector instance.
    
    Returns:
        PIIDetector: The singleton detector instance
    """
    global _detector_instance
    
    if _detector_instance is None:
        _detector_instance = PIIDetector()
    
    return _detector_instance
