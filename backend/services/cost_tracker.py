"""
Cost Tracking Service for LLM Usage

Tracks token usage and costs to prevent exceeding OpenRouter free tier limits.
Provides warnings and hard limits for production cost control.

OpenRouter Free Tier: ~200K tokens/day
Safety Limits: 150K tokens/day (75%)
"""
import logging
from datetime import datetime, date
from typing import Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UsageStats:
    """Statistics for token usage."""
    total_tokens: int = 0
    total_calls: int = 0
    daily_tokens: Dict[date, int] = field(default_factory=dict)
    daily_calls: Dict[date, int] = field(default_factory=dict)


class CostTracker:
    """
    Track and enforce LLM usage limits.
    
    Monitors token usage and prevents exceeding free tier limits.
    """
    
    # OpenRouter free tier limit (approximate)
    DAILY_TOKEN_LIMIT = 200000
    
    # Warning thresholds
    WARNING_THRESHOLD_75 = int(DAILY_TOKEN_LIMIT * 0.75)  # 150K
    WARNING_THRESHOLD_90 = int(DAILY_TOKEN_LIMIT * 0.90)  # 180K
    WARNING_THRESHOLD_95 = int(DAILY_TOKEN_LIMIT * 0.95)  # 190K
    
    def __init__(self):
        """Initialize cost tracker."""
        self.stats = UsageStats()
        logger.info(f"CostTracker initialized (daily limit: {self.DAILY_TOKEN_LIMIT:,} tokens)")
    
    def record_usage(self, tokens: int, model: str = "unknown") -> None:
        """
        Record token usage for a call.
        
        Args:
            tokens: Number of tokens used
            model: Model name (for future per-model tracking)
        """
        self.stats.total_tokens += tokens
        self.stats.total_calls += 1
        
        # Track daily usage
        today = datetime.now().date()
        
        if today not in self.stats.daily_tokens:
            self.stats.daily_tokens[today] = 0
            self.stats.daily_calls[today] = 0
        
        self.stats.daily_tokens[today] += tokens
        self.stats.daily_calls[today] += 1
        
        # Log usage
        daily_usage = self.stats.daily_tokens[today]
        percentage = (daily_usage / self.DAILY_TOKEN_LIMIT) * 100
        
        logger.info(
            f"Token usage: +{tokens} (daily: {daily_usage:,}/{self.DAILY_TOKEN_LIMIT:,} = {percentage:.1f}%)"
        )
        
        # Emit warnings at thresholds
        if daily_usage >= self.WARNING_THRESHOLD_95 and daily_usage - tokens < self.WARNING_THRESHOLD_95:
            logger.warning("⚠️  95% of daily token limit reached!")
        elif daily_usage >= self.WARNING_THRESHOLD_90 and daily_usage - tokens < self.WARNING_THRESHOLD_90:
            logger.warning("⚠️  90% of daily token limit reached")
        elif daily_usage >= self.WARNING_THRESHOLD_75 and daily_usage - tokens < self.WARNING_THRESHOLD_75:
            logger.info("ℹ️  75% of daily token limit reached")
    
    def check_limit(self) -> bool:
        """
        Check if within daily token limit.
        
        Returns:
            True if within limit, False if limit exceeded
        """
        today = datetime.now().date()
        daily_usage = self.stats.daily_tokens.get(today, 0)
        
        return daily_usage < self.DAILY_TOKEN_LIMIT
    
    def get_remaining_tokens(self) -> int:
        """
        Get remaining tokens for today.
        
        Returns:
            Number of tokens remaining in daily limit
        """
        today = datetime.now().date()
        daily_usage = self.stats.daily_tokens.get(today, 0)
        
        return max(0, self.DAILY_TOKEN_LIMIT - daily_usage)
    
    def get_usage_stats(self) -> Dict:
        """
        Get current usage statistics.
        
        Returns:
            Dictionary with usage stats
        """
        today = datetime.now().date()
        daily_usage = self.stats.daily_tokens.get(today, 0)
        daily_calls = self.stats.daily_calls.get(today, 0)
        
        return {
            "total_tokens": self.stats.total_tokens,
            "total_calls": self.stats.total_calls,
            "daily_tokens": daily_usage,
            "daily_calls": daily_calls,
            "daily_limit": self.DAILY_TOKEN_LIMIT,
            "remaining_tokens": self.get_remaining_tokens(),
            "percentage_used": (daily_usage / self.DAILY_TOKEN_LIMIT) * 100,
            "within_limit": self.check_limit()
        }
    
    def reset_daily_stats(self, target_date: Optional[date] = None) -> None:
        """
        Reset statistics for a specific date (for testing).
        
        Args:
            target_date: Date to reset (defaults to today)
        """
        target = target_date or datetime.now().date()
        
        if target in self.stats.daily_tokens:
            del self.stats.daily_tokens[target]
        if target in self.stats.daily_calls:
            del self.stats.daily_calls[target]
        
        logger.info(f"Reset daily stats for {target}")


# Singleton instance
_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """
    Get or create the singleton cost tracker instance.
    
    Returns:
        CostTracker: The singleton instance
    """
    global _cost_tracker
    
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    
    return _cost_tracker
