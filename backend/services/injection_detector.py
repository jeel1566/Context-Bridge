"""
Prompt Injection Detection Service

Detects and blocks prompt injection attacks before they reach the LLM,
providing defense-in-depth security for AI applications.

Attack Categories Detected:
- Role manipulation ("you are now...", "forget previous instructions")
- Instruction override ("disregard rules", "bypass restrictions")
- Delimiter/escape attacks ("</system>", "===END===")
- Encoding tricks (Base64, hex, Unicode obfuscation)
- Jailbreak attempts ("DAN mode", "developer mode")
- Prompt leaking ("show me your system prompt")
- Context poisoning ("[System Message]:", "<|im_start|>")
"""
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Comprehensive injection attack patterns by category
INJECTION_PATTERNS = {
    "role_manipulation": {
        "patterns": [
            r'ignore\s+(?:previous|all|your|the)\s+(?:instructions?|rules?|prompts?)',
            r'forget\s+(?:everything|all|previous|your)',
            r'you\s+are\s+now\s+(?:a|an|the)',
            r'new\s+role\s*:',
            r'act\s+as\s+(?:a|an|if)',
            r'pretend\s+(?:you|to)\s+(?:are|be)',
            r'system\s*:\s*you\s+are',
            r'sudo\s+mode',
            r'admin\s+mode',
        ],
        "confidence": "high",
        "threat_level": "critical"
    },
    
    "instruction_override": {
        "patterns": [
            r'disregard\s+(?:all|your|the|any)\s+(?:rules?|guidelines?|instructions?)',
            r'bypass\s+(?:restrictions?|safety|security)',
            r'override\s+(?:your|the)\s+(?:programming|instructions?|rules?)',
            r'your\s+new\s+(?:instructions?|role|purpose)',
            r'stop\s+(?:being|following)',
            r'no\s+(?:longer|more)\s+(?:follow|obey)',
        ],
        "confidence": "high",
        "threat_level": "critical"
    },
    
    "delimiter_escape": {
        "patterns": [
            r'<\s*/?\s*system\s*>',
            r'<!-+\s*end\s+instructions?\s*-+>',
            r'={3,}(?:END|STOP|OVERRIDE)={3,}',
            r'\{\{(?:system_end|override|admin)\}\}',
            r'\[\[(?:OVERRIDE|ADMIN|SYSTEM)\]\]',
            r'```\s*(?:end|stop|system)',
        ],
        "confidence": "high",
        "threat_level": "high"
    },
    
    "encoding_obfuscation": {
        "patterns": [
            r'(?:base64|b64decode|atob)\s*\(',
            r'\\x[0-9a-fA-F]{2}',  # Hex encoding
            r'&#\d+;',  # HTML entities
            r'\\u[0-9a-fA-F]{4}',  # Unicode escape
            r'%[0-9a-fA-F]{2}',  # URL encoding
            r'&\#x[0-9a-fA-F]+;',  # Hex HTML entities
        ],
        "confidence": "medium",
        "threat_level": "high"
    },
    
    "jailbreak": {
        "patterns": [
            r'\bDAN\s+mode\b',  # Do Anything Now
            r'developer\s+mode',
            r'god\s+mode',
            r'unrestricted\s+mode',
            r'jailbreak\s+(?:activated|mode)',
            r'evil\s+(?:mode|AI)',
            r'no\s+rules\s+mode',
            r'uncensored\s+(?:mode|version)',
        ],
        "confidence": "high",
        "threat_level": "critical"
    },
    
    "prompt_leaking": {
        "patterns": [
            r'show\s+(?:me\s+)?your\s+(?:system\s+)?(?:prompt|instructions?)',
            r'what\s+(?:are|is)\s+your\s+(?:system\s+)?(?:prompt|instructions?)',
            r'repeat\s+the\s+(?:text|instructions?)\s+above',
            r'output\s+your\s+(?:prompt|instructions?|rules?)',
            r'print\s+(?:system\s+)?(?:prompt|instructions?)',
            r'reveal\s+your\s+(?:instructions?|prompt)',
        ],
        "confidence": "high",
        "threat_level": "medium"
    },
    
    "context_poisoning": {
        "patterns": [
            r'\[(?:System|SYSTEM)\s+(?:Message|Instruction)\s*\]',
            r'\[INST\]',  # LLaMA format
            r'<\|im_start\|>',  # ChatML format
            r'(?:Human|Assistant)\s*:',  # Claude format
            r'<\|endoftext\|>',  # GPT format
            r'USER\s*:',
            r'ASSISTANT\s*:',
        ],
        "confidence": "high",
        "threat_level": "high"
    },
    
    # Additional attack types (Issue #12)
    "sql_injection": {
        "patterns": [
            r"(?i)\b(?:union|select|insert|update|delete|drop)\s+.+\s+(?:from|into|table|where)",
            r"';?\s*(?:--|#|/\*)",
            r"\bor\s+1\s*=\s*1\b",
            r"\band\s+1\s*=\s*0\b",
        ],
        "confidence": "medium",
        "threat_level": "high"
    },
    
    "xss_attempt": {
        "patterns": [
            r"<script[^>]*>",
            r"javascript\s*:",
            r"on(?:load|error|click|mouse\w+)\s*=",
            r"<iframe[^>]*>",
        ],
        "confidence": "medium",
        "threat_level": "medium"
    },
}


class InjectionDetector:
    """
    High-performance prompt injection detection service.
    
    Pre-compiles all regex patterns for fast detection.
    Provides both detailed analysis and quick safety checks.
    """
    
    def __init__(self):
        """Initialize the injection detector with pre-compiled patterns."""
        logger.info("Initializing InjectionDetector with comprehensive attack patterns")
        
        # Pre-compile all patterns for performance
        self._compiled: Dict[str, Dict] = {}
        for category, data in INJECTION_PATTERNS.items():
            self._compiled[category] = {
                "patterns": [
                    re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    for pattern in data["patterns"]
                ],
                "confidence": data["confidence"],
                "threat_level": data["threat_level"]
            }
        
        logger.info(f"Compiled {len(self._compiled)} injection pattern categories")
    
    def detect(self, text: str) -> Dict:
        """
        Detect prompt injection attempts in text.
        
        Args:
            text: The user input to analyze
            
        Returns:
            Detection result with details:
            {
                "injection_detected": bool,
                "confidence": "high" | "medium" | "low",
                "attack_types": ["role_manipulation", ...],
                "matches": [{"category": "...", "pattern": "...", "position": (start, end)}],
                "threat_level": "critical" | "high" | "medium" | "low",
                "safe": bool
            }
        """
        matches = []
        attack_types = set()
        max_confidence = "low"
        max_threat = "low"
        
        # Scan for all patterns
        for category, compiled_data in self._compiled.items():
            for pattern in compiled_data["patterns"]:
                for match in pattern.finditer(text):
                    matches.append({
                        "category": category,
                        "pattern": pattern.pattern,
                        "matched_text": match.group(0),
                        "position": match.span()
                    })
                    attack_types.add(category)
                    
                    # Track highest confidence/threat
                    if compiled_data["confidence"] == "high":
                        max_confidence = "high"
                    elif max_confidence == "low" and compiled_data["confidence"] == "medium":
                        max_confidence = "medium"
                    
                    threat = compiled_data["threat_level"]
                    if threat == "critical":
                        max_threat = "critical"
                    elif max_threat in ["low", "medium"] and threat == "high":
                        max_threat = "high"
                    elif max_threat == "low" and threat == "medium":
                        max_threat = "medium"
        
        injection_detected = len(matches) > 0
        
        if injection_detected:
            logger.warning(
                f"Injection detected! Types: {list(attack_types)}, "
                f"Matches: {len(matches)}, Threat: {max_threat}"
            )
        
        return {
            "injection_detected": injection_detected,
            "confidence": max_confidence,
            "attack_types": list(attack_types),
            "matches": matches,
            "threat_level": max_threat,
            "safe": not injection_detected
        }
    
    def is_safe(self, text: str) -> bool:
        """
        Quick boolean check if text is safe (no injection detected).
        
        Args:
            text: The user input to check
            
        Returns:
            True if safe, False if injection detected
        """
        # Optimized for early exit on first match
        for category, compiled_data in self._compiled.items():
            for pattern in compiled_data["patterns"]:
                if pattern.search(text):
                    return False
        
        return True
    
    def get_threat_level(self, detection_result: Dict) -> str:
        """
        Get threat level from detection result.
        
        Args:
            detection_result: Result from detect() method
            
        Returns:
            Threat level: "critical", "high", "medium", or "low"
        """
        return detection_result.get("threat_level", "low")


# Singleton instance for reuse
_detector_instance: InjectionDetector | None = None


def get_injection_detector() -> InjectionDetector:
    """
    Get or create the singleton injection detector instance.
    
    Returns:
        InjectionDetector: The singleton detector instance
    """
    global _detector_instance
    
    if _detector_instance is None:
        _detector_instance = InjectionDetector()
    
    return _detector_instance
