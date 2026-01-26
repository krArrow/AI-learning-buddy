"""
Goal Enrichment and ETA Calculation Utilities
"""
from typing import Dict, Any, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)


def enrich_goal_text(state: Dict[str, Any]) -> str:
    """
    Enrich goal text with clarified preferences for better resource matching.
    
    This creates a detailed, context-rich goal description that includes:
    - Original goal text
    - Learning style preference
    - Pace preference
    - Any specific preferences from clarification
    
    Args:
        state: Application state with goal information
        
    Returns:
        Enriched goal text with full context
        
    Example:
        >>> state = {
        ...     "goal_text": "Learn Spanish",
        ...     "learning_style": "visual",
        ...     "pace": "medium",
        ...     "level": "beginner",
        ...     "preferences": {"focus": "conversation", "interest": "travel"}
        ... }
        >>> enriched = enrich_goal_text(state)
        >>> print(enriched)
        "Learn Spanish (Beginner level, visual learning style, medium pace). 
         Focus on conversation for travel purposes."
    """
    logger.info("[GoalEnrichment] Enriching goal text with user preferences")
    
    # Get base goal text
    goal_text = state.get("goal_text", "").strip()
    
    if not goal_text:
        logger.warning("[GoalEnrichment] No goal_text found in state")
        return ""
    
    # Start with original goal
    enriched_parts = [goal_text]
    
    # Add level
    level = state.get("level")
    if level:
        enriched_parts.append(f"{level.title()} level")
    
    # Add learning style
    learning_style = state.get("learning_style")
    if learning_style and learning_style not in ["not_sure", "none"]:
        style_display = learning_style.replace("_", "/").replace("-", " ").title()
        enriched_parts.append(f"{style_display} learning style")
    
    # Add pace
    pace = state.get("pace")
    if pace and pace not in ["not_sure", "none"]:
        enriched_parts.append(f"{pace} pace")
    
    # Combine main parts
    main_description = goal_text
    if len(enriched_parts) > 1:
        main_description += " (" + ", ".join(enriched_parts[1:]) + ")"
    
    # Add specific preferences
    preferences = state.get("preferences", {})
    preference_details = []
    
    if isinstance(preferences, dict):
        for key, value in preferences.items():
            if value and isinstance(value, str) and len(value.strip()) > 0:
                # Format key nicely
                key_display = key.replace("_", " ").title()
                preference_details.append(f"{key_display}: {value}")
    
    # Combine all parts
    if preference_details:
        enriched_goal = main_description + ". " + ". ".join(preference_details) + "."
    else:
        enriched_goal = main_description + "."
    
    logger.info(f"[GoalEnrichment] Original: {goal_text[:50]}...")
    logger.info(f"[GoalEnrichment] Enriched: {enriched_goal[:100]}...")
    
    return enriched_goal


def calculate_eta(
    estimated_total_hours: float,
    daily_minutes: int,
    efficiency_factor: float = 0.8
) -> Dict[str, Any]:
    """
    Calculate Estimated Time to Achieve (ETA) a learning goal.
    
    Args:
        estimated_total_hours: Total estimated hours to complete the goal
        daily_minutes: Minutes user can dedicate per day
        efficiency_factor: Adjustment for real-world efficiency (default 0.8 = 80%)
        
    Returns:
        Dictionary with ETA breakdown:
        {
            "total_hours": float,
            "daily_minutes": int,
            "total_days": int,
            "total_weeks": int,
            "total_months": int,
            "completion_date_days": int,
            "efficiency_adjusted": bool,
            "display_text": str
        }
        
    Example:
        >>> eta = calculate_eta(estimated_total_hours=120, daily_minutes=60)
        >>> print(eta["display_text"])
        "Approximately 4 months"
    """
    logger.info(f"[ETA] Calculating ETA: {estimated_total_hours}h total, {daily_minutes}min/day")
    
    # Validate inputs
    if estimated_total_hours <= 0:
        logger.warning(f"[ETA] Invalid total hours: {estimated_total_hours}")
        return _create_eta_result(0, 0, 0, 0, 0, "Unable to estimate")
    
    if daily_minutes <= 0:
        logger.warning(f"[ETA] Invalid daily minutes: {daily_minutes}")
        return _create_eta_result(estimated_total_hours, daily_minutes, 0, 0, 0, "Unable to estimate")
    
    # Apply efficiency factor (account for breaks, review time, etc.)
    adjusted_hours = estimated_total_hours / efficiency_factor
    
    # Convert daily minutes to hours
    daily_hours = daily_minutes / 60.0
    
    # Calculate total days needed
    total_days = adjusted_hours / daily_hours
    
    # Round up to ensure we don't underestimate
    import math
    total_days = math.ceil(total_days)
    
    # Calculate weeks and months
    total_weeks = math.ceil(total_days / 7)
    total_months = math.ceil(total_days / 30)
    
    # Create display text
    display_text = _format_eta_display(total_days, total_weeks, total_months)
    
    logger.info(f"[ETA] Result: {total_days} days, {total_weeks} weeks, {total_months} months")
    logger.info(f"[ETA] Display: {display_text}")
    
    return _create_eta_result(
        adjusted_hours,
        daily_minutes,
        total_days,
        total_weeks,
        total_months,
        display_text
    )


def _create_eta_result(
    total_hours: float,
    daily_minutes: int,
    total_days: int,
    total_weeks: int,
    total_months: int,
    display_text: str
) -> Dict[str, Any]:
    """Helper to create ETA result dictionary"""
    return {
        "total_hours": total_hours,
        "daily_minutes": daily_minutes,
        "total_days": total_days,
        "total_weeks": total_weeks,
        "total_months": total_months,
        "completion_date_days": total_days,
        "efficiency_adjusted": True,
        "display_text": display_text
    }


def _format_eta_display(total_days: int, total_weeks: int, total_months: int) -> str:
    """Format ETA for display"""
    
    if total_days < 7:
        # Less than a week
        if total_days == 1:
            return "1 day"
        return f"{total_days} days"
    
    elif total_weeks < 5:
        # Less than a month, show in weeks
        if total_weeks == 1:
            return "1 week"
        return f"{total_weeks} weeks"
    
    elif total_months < 12:
        # Less than a year, show in months
        if total_months == 1:
            return "1 month"
        
        # Also show weeks for 2-3 months
        if total_months <= 3:
            return f"{total_months} months ({total_weeks} weeks)"
        
        return f"{total_months} months"
    
    else:
        # A year or more
        years = total_months // 12
        remaining_months = total_months % 12
        
        if years == 1:
            if remaining_months == 0:
                return "1 year"
            return f"1 year, {remaining_months} months"
        
        if remaining_months == 0:
            return f"{years} years"
        
        return f"{years} years, {remaining_months} months"


def estimate_goal_hours(goal_text: str, level: str = "beginner") -> float:
    """
    Estimate total hours needed for a learning goal.
    
    This is a heuristic-based estimation. In production, this could use
    ML models or historical data.
    
    Args:
        goal_text: The learning goal description
        level: User's current level
        
    Returns:
        Estimated total hours needed
    """
    logger.info(f"[HourEstimation] Estimating hours for: {goal_text[:50]}...")
    
    # Base hours by level
    base_hours = {
        "beginner": 100,
        "intermediate": 60,
        "advanced": 40
    }
    
    level_hours = base_hours.get(level.lower(), 100)
    
    # Adjust based on keywords in goal
    goal_lower = goal_text.lower()
    
    # Complex topics need more time
    complex_keywords = ["machine learning", "deep learning", "ai", "data science", 
                       "full stack", "advanced", "expert", "master"]
    if any(keyword in goal_lower for keyword in complex_keywords):
        level_hours *= 1.5
    
    # Language learning typically takes longer
    language_keywords = ["language", "spanish", "french", "german", "chinese", 
                        "japanese", "fluent", "conversation"]
    if any(keyword in goal_lower for keyword in language_keywords):
        level_hours *= 1.3
    
    # Quick skills need less time
    quick_keywords = ["basics", "introduction", "fundamentals", "quick", "crash course"]
    if any(keyword in goal_lower for keyword in quick_keywords):
        level_hours *= 0.7
    
    # Round to reasonable number
    import math
    estimated_hours = math.ceil(level_hours / 10) * 10  # Round to nearest 10
    
    logger.info(f"[HourEstimation] Estimated: {estimated_hours} hours")
    
    return estimated_hours


__all__ = [
    "enrich_goal_text",
    "calculate_eta",
    "estimate_goal_hours"
]
