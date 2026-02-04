"""
Personality Profile Service

Applies personality-specific formatting and tone to context text
for different target audiences.

Profiles:
- senior-dev: Concise, technical, code-first
- beginner: Friendly, patient, step-by-step
- academic: Formal, precise, comprehensive
- business: Professional, ROI-focused
- creative: Conversational, storytelling
"""
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Personality profile definitions
PROFILES = {
    "senior-dev": {
        "name": "Senior Developer",
        "tone": "concise and technical",
        "format": "code-first with minimal explanations",
        "style": "assumes deep technical knowledge",
        "instructions": [
            "Use technical terminology without explanation",
            "Prioritize code examples over prose",
            "Be direct and concise",
            "Focus on implementation details and edge cases",
            "Skip basic concepts"
        ]
    },
    
    "beginner": {
        "name": "Beginner/Learning",
        "tone": "friendly and patient",
        "format": "step-by-step with context",
        "style": "explains concepts from first principles",
        "instructions": [
            "Define technical terms when first used",
            "Provide context and background",
            "Use analogies and examples",
            "Break down complex concepts into simple steps",
            "Encourage and be supportive"
        ]
    },
    
    "academic": {
        "name": "Academic/Research",
        "tone": "formal and precise",
        "format": "detailed with citations and references",
        "style": "comprehensive and thorough",
        "instructions": [
            "Use formal academic language",
            "Provide detailed explanations",
            "Reference relevant research or documentation",
            "Be comprehensive and thorough",
            "Use precise terminology"
        ]
    },
    
    "business": {
        "name": "Business Professional",
        "tone": "professional and value-focused",
        "format": "executive summary with key takeaways",
        "style": "focuses on ROI and business impact",
        "instructions": [
            "Lead with business value and ROI",
            "Use metrics and KPIs where relevant",
            "Keep technical details minimal",
            "Focus on outcomes and benefits",
            "Be professional and concise"
        ]
    },
    
    "creative": {
        "name": "Creative/Storyteller",
        "tone": "conversational and engaging",
        "format": "narrative-driven with examples",
        "style": "uses storytelling and metaphors",
        "instructions": [
            "Use conversational language",
            "Tell stories and use real-world examples",
            "Make concepts relatable",
            "Be engaging and memorable",
            "Use metaphors and analogies"
        ]
    }
}


class PersonalityProfileService:
    """
    Service for applying personality profiles to context text.
    """
    
    def __init__(self):
        """Initialize personality profile service."""
        logger.info(f"Initializing PersonalityProfileService with {len(PROFILES)} profiles")
        self.profiles = PROFILES
    
    def get_profile(self, profile_name: str) -> Dict:
        """
        Get personality profile by name.
        
        Args:
            profile_name: Name of the profile (e.g., "senior-dev")
            
        Returns:
            Profile dictionary or default profile if not found
        """
        return self.profiles.get(profile_name, self.profiles["senior-dev"])
    
    def list_profiles(self) -> list:
        """
        List all available personality profiles.
        
        Returns:
            List of profile names
        """
        return list(self.profiles.keys())
    
    def get_instructions(self, profile_name: str) -> str:
        """
        Get formatting instructions for a personality profile.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Formatted instructions string for LLM
        """
        profile = self.get_profile(profile_name)
        
        instructions = f"""
PERSONALITY PROFILE: {profile['name']}

Tone: {profile['tone']}
Format: {profile['format']}
Style: {profile['style']}

Specific Instructions:
"""
        for i, instruction in enumerate(profile['instructions'], 1):
            instructions += f"{i}. {instruction}\n"
        
        return instructions.strip()
    
    def apply_metadata(self, profile_name: str) -> Dict:
        """
        Get profile metadata for context processing result.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Metadata dictionary
        """
        profile = self.get_profile(profile_name)
        
        return {
            "personality_profile": profile_name,
            "profile_name": profile["name"],
            "tone": profile["tone"],
            "format": profile["format"]
        }


# Singleton instance
_profile_service: PersonalityProfileService | None = None


def get_personality_service() -> PersonalityProfileService:
    """
    Get or create the singleton personality profile service.
    
    Returns:
        PersonalityProfileService: The singleton instance
    """
    global _profile_service
    
    if _profile_service is None:
        _profile_service = PersonalityProfileService()
    
    return _profile_service
