"""
Difficulty Scorer Tool - Dynamically scores task difficulty based on user performance.
"""
from typing import List, Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


def score_difficulty(
    task_description: str,
    user_level: str = "beginner",
    user_completion_rate: float = 0.0,
    user_average_time: Optional[int] = None,
    estimated_time: Optional[int] = None,
    task_history: Optional[List[Dict[str, Any]]] = None
) -> float:
    """
    Score task difficulty on a scale from 0.0 to 1.0.
    
    Combines:
    1. Base difficulty from task description analysis
    2. User performance adjustments
    3. Historical data patterns
    
    Args:
        task_description: Description of the task
        user_level: User's current level (beginner/intermediate/advanced)
        user_completion_rate: Overall task completion rate (0.0-1.0)
        user_average_time: Average time user takes on tasks (minutes)
        estimated_time: Estimated time for this task (minutes)
        task_history: List of previous task performance
        
    Returns:
        Difficulty score from 0.0 (easiest) to 1.0 (hardest)
        
    Example:
        >>> score = score_difficulty(
        ...     "Build a REST API with authentication",
        ...     user_level="intermediate",
        ...     user_completion_rate=0.85
        ... )
        >>> print(f"Difficulty: {score:.2f}")
        Difficulty: 0.65
    """
    logger.debug(f"Scoring difficulty for task: {task_description[:50]}...")
    
    # Step 1: Base difficulty from task description
    base_difficulty = _analyze_task_complexity(task_description)
    logger.debug(f"Base difficulty: {base_difficulty:.2f}")
    
    # Step 2: Adjust for user level
    level_adjustment = _get_level_adjustment(user_level)
    adjusted_difficulty = base_difficulty * level_adjustment
    logger.debug(f"Level-adjusted difficulty: {adjusted_difficulty:.2f}")
    
    # Step 3: Adjust based on user performance
    if user_completion_rate > 0:
        performance_adjustment = _calculate_performance_adjustment(
            user_completion_rate,
            user_average_time,
            estimated_time
        )
        adjusted_difficulty *= performance_adjustment
        logger.debug(f"Performance-adjusted difficulty: {adjusted_difficulty:.2f}")
    
    # Step 4: Consider historical patterns
    if task_history:
        history_adjustment = _analyze_task_history(task_history)
        adjusted_difficulty *= history_adjustment
        logger.debug(f"History-adjusted difficulty: {adjusted_difficulty:.2f}")
    
    # Clamp to valid range
    final_score = max(0.0, min(1.0, adjusted_difficulty))
    
    logger.info(f"Final difficulty score: {final_score:.2f}")
    return final_score


def _analyze_task_complexity(task_description: str) -> float:
    """
    Analyze task complexity from description.
    
    Looks for complexity indicators:
    - Keywords (advanced, complex, integrate, build, etc.)
    - Technical terms
    - Multiple components
    - Length and detail
    
    Args:
        task_description: Task description text
        
    Returns:
        Base difficulty score (0.0-1.0)
    """
    desc_lower = task_description.lower()
    score = 0.3  # Base score
    
    # Beginner indicators (decrease difficulty)
    beginner_keywords = [
        "introduction", "basics", "getting started", "hello world",
        "simple", "first", "learn", "tutorial", "beginner"
    ]
    for keyword in beginner_keywords:
        if keyword in desc_lower:
            score -= 0.1
    
    # Intermediate indicators
    intermediate_keywords = [
        "implement", "create", "build", "design", "develop",
        "practice", "exercise", "project"
    ]
    for keyword in intermediate_keywords:
        if keyword in desc_lower:
            score += 0.1
    
    # Advanced indicators (increase difficulty)
    advanced_keywords = [
        "advanced", "complex", "integrate", "optimize", "architect",
        "production", "scale", "performance", "security", "deploy"
    ]
    for keyword in advanced_keywords:
        if keyword in desc_lower:
            score += 0.2
    
    # Multiple components indicator
    component_keywords = ["and", "with", "using", "integrate", "combine"]
    component_count = sum(1 for kw in component_keywords if kw in desc_lower)
    if component_count >= 2:
        score += 0.1
    
    # Length indicator (longer = potentially more complex)
    if len(task_description) > 100:
        score += 0.1
    
    return max(0.1, min(0.9, score))


def _get_level_adjustment(user_level: str) -> float:
    """
    Get difficulty multiplier based on user level.
    
    Args:
        user_level: User's skill level
        
    Returns:
        Adjustment multiplier
    """
    adjustments = {
        "beginner": 1.2,      # Tasks seem harder for beginners
        "intermediate": 1.0,   # Baseline
        "advanced": 0.8,       # Tasks seem easier for advanced users
    }
    
    return adjustments.get(user_level.lower(), 1.0)


def _calculate_performance_adjustment(
    completion_rate: float,
    avg_time: Optional[int],
    estimated_time: Optional[int]
) -> float:
    """
    Calculate difficulty adjustment based on performance.
    
    Logic:
    - High completion rate (>80%) → tasks are easier → reduce difficulty
    - Low completion rate (<50%) → tasks are harder → increase difficulty
    - Taking much longer than estimated → increase difficulty
    - Finishing much faster → reduce difficulty
    
    Args:
        completion_rate: Task completion rate
        avg_time: Average completion time
        estimated_time: Estimated time
        
    Returns:
        Adjustment multiplier
    """
    adjustment = 1.0
    
    # Completion rate adjustment
    if completion_rate > 0.8:
        # User is excelling - reduce perceived difficulty
        adjustment *= 0.85
    elif completion_rate < 0.5:
        # User is struggling - increase perceived difficulty
        adjustment *= 1.15
    
    # Time-based adjustment
    if avg_time and estimated_time and estimated_time > 0:
        time_ratio = avg_time / estimated_time
        
        if time_ratio > 1.5:
            # Taking much longer - tasks are harder
            adjustment *= 1.1
        elif time_ratio < 0.7:
            # Finishing much faster - tasks are easier
            adjustment *= 0.9
    
    return adjustment


def _analyze_task_history(task_history: List[Dict[str, Any]]) -> float:
    """
    Analyze historical task performance for patterns.
    
    Args:
        task_history: List of completed tasks with performance data
        
    Returns:
        Adjustment multiplier
    """
    if not task_history or len(task_history) < 3:
        return 1.0  # Not enough data
    
    # Calculate recent trend
    recent_tasks = task_history[-5:]  # Last 5 tasks
    completed_count = sum(1 for task in recent_tasks if task.get("is_completed", False))
    recent_completion_rate = completed_count / len(recent_tasks)
    
    # Trend-based adjustment
    if recent_completion_rate > 0.8:
        # Strong recent performance - reduce difficulty
        return 0.9
    elif recent_completion_rate < 0.4:
        # Poor recent performance - increase difficulty
        return 1.1
    
    return 1.0


def recommend_difficulty_range(
    user_level: str,
    completion_rate: float,
    assessment_scores: Optional[List[float]] = None
) -> tuple[float, float]:
    """
    Recommend optimal difficulty range for user.
    
    Args:
        user_level: User's skill level
        completion_rate: Current completion rate
        assessment_scores: Recent assessment scores
        
    Returns:
        Tuple of (min_difficulty, max_difficulty)
        
    Example:
        >>> min_diff, max_diff = recommend_difficulty_range("intermediate", 0.75)
        >>> print(f"Recommended range: {min_diff:.2f} - {max_diff:.2f}")
        Recommended range: 0.40 - 0.70
    """
    # Base ranges by level
    level_ranges = {
        "beginner": (0.1, 0.4),
        "intermediate": (0.3, 0.7),
        "advanced": (0.6, 0.9),
    }
    
    min_diff, max_diff = level_ranges.get(user_level.lower(), (0.3, 0.7))
    
    # Adjust based on completion rate
    if completion_rate > 0.8:
        # User is doing well - increase range
        min_diff += 0.1
        max_diff += 0.1
    elif completion_rate < 0.5:
        # User struggling - decrease range
        min_diff -= 0.1
        max_diff -= 0.1
    
    # Adjust based on assessment scores
    if assessment_scores and len(assessment_scores) >= 3:
        avg_score = sum(assessment_scores) / len(assessment_scores)
        if avg_score > 0.8:
            min_diff += 0.1
            max_diff += 0.1
        elif avg_score < 0.5:
            min_diff -= 0.1
            max_diff -= 0.1
    
    # Clamp to valid range
    min_diff = max(0.0, min(0.8, min_diff))
    max_diff = max(min_diff + 0.1, min(1.0, max_diff))
    
    logger.info(
        f"Recommended difficulty range for {user_level}: "
        f"{min_diff:.2f} - {max_diff:.2f}"
    )
    
    return (min_diff, max_diff)


def classify_difficulty(score: float) -> str:
    """
    Convert numeric difficulty score to text label.
    
    Args:
        score: Difficulty score (0.0-1.0)
        
    Returns:
        Text label (Very Easy, Easy, Medium, Hard, Very Hard)
    """
    if score < 0.2:
        return "Very Easy"
    elif score < 0.4:
        return "Easy"
    elif score < 0.6:
        return "Medium"
    elif score < 0.8:
        return "Hard"
    else:
        return "Very Hard"


__all__ = [
    "score_difficulty",
    "recommend_difficulty_range",
    "classify_difficulty",
]