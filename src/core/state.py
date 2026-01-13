"""
LangGraph State Definition for AI Learning Buddy.
Defines the complete application state that flows through the graph.
"""
from typing import TypedDict, Optional, Any, List, Dict
from datetime import datetime


class AppState(TypedDict, total=False):
    """
    Complete application state for the learning workflow.
    
    This state is passed through all nodes in the LangGraph and maintains
    all information about the user's learning journey, preferences, and
    generated content.
    """
    
    # ==================== Core Goal Information ====================
    goal_id: Optional[int]
    """Database ID of the stored learning goal (None until goal is saved)"""
    
    goal_text: str
    """User's learning goal description (e.g., "Learn Python for data science")"""
    
    level: str
    """User's current skill level: 'beginner', 'intermediate', or 'advanced'"""
    
    daily_minutes: int
    """Available study time per day in minutes (range: 10-480)"""
    
    learning_style: str
    """Preferred learning style: 'visual', 'kinesthetic', 'auditory', or 'reading'"""
    
    pace: str
    """Preferred learning pace: 'slow', 'medium', or 'fast'"""
    
    preferences: Dict[str, Any]
    """Additional custom preferences as a flexible dictionary"""
    
    # ==================== Conversation Context ====================
    conversation_history: List[Dict[str, str]]
    """
    List of conversation turns with structure:
    [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    
    clarification_complete: bool
    """Whether goal clarification conversation is complete"""
    
    # ==================== Retrieved/Generated Data ====================
    resources: List[Dict[str, Any]]
    """
    Retrieved learning resources from RAG/search with structure:
    [{"title": str, "url": str, "type": str, "difficulty": float, "description": str}]
    """
    
    roadmap: Optional[Dict[str, Any]]
    """
    Generated learning roadmap with structure:
    {
        "modules": [
            {
                "id": int,
                "title": str,
                "description": str,
                "estimated_weeks": int,
                "topics": List[str]
            }
        ],
        "total_weeks": int,
        "milestones": List[Dict]
    }
    """
    
    tasks: List[Dict[str, Any]]
    """
    Generated daily tasks with structure:
    [
        {
            "day": int,
            "task": str,
            "why": str,
            "resources": List[str],
            "estimated_minutes": int,
            "difficulty": float
        }
    ]
    """
    
    # ==================== Analysis Results ====================
    completion_rate: float
    """Current task completion rate (0.0 to 1.0)"""
    
    gaps_identified: List[str]
    """List of identified knowledge gaps from assessments"""
    
    adaptations_needed: bool
    """Flag indicating whether the learning plan needs adaptation"""
    
    performance_metrics: Dict[str, Any]
    """
    Performance analysis results:
    {
        "average_completion_time": float,
        "difficulty_match": float,
        "consistency_score": float,
        "struggling_topics": List[str]
    }
    """
    
    # ==================== Execution Tracking ====================
    error: Optional[str]
    """Error message if any node failed (None if no errors)"""
    
    current_node: str
    """Name of the currently executing node (for tracking)"""
    
    metadata: Dict[str, Any]
    """
    Execution metadata:
    {
        "start_time": datetime,
        "end_time": datetime,
        "node_execution_times": Dict[str, float],
        "retry_count": int,
        "graph_version": str
    }
    """


# State field validators
VALID_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_LEARNING_STYLES = {"visual", "kinesthetic", "auditory", "reading"}
VALID_PACES = {"slow", "medium", "fast"}
MIN_DAILY_MINUTES = 10
MAX_DAILY_MINUTES = 480  # 8 hours


def validate_state(state: AppState) -> tuple[bool, Optional[str]]:
    """
    Validate state fields have correct values.
    
    Args:
        state: The application state to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> is_valid, error = validate_state(state)
        >>> if not is_valid:
        ...     raise ValueError(error)
    """
    # Validate goal_text
    if "goal_text" in state:
        goal_text = state["goal_text"]
        if not goal_text or len(goal_text.strip()) == 0:
            return False, "goal_text cannot be empty"
        if len(goal_text) < 10:
            return False, "goal_text must be at least 10 characters"
        if len(goal_text) > 500:
            return False, "goal_text must be at most 500 characters"
    
    # Validate level
    if "level" in state:
        level = state["level"].lower()
        if level not in VALID_LEVELS:
            return False, f"level must be one of {VALID_LEVELS}, got '{level}'"
    
    # Validate daily_minutes
    if "daily_minutes" in state:
        daily_minutes = state["daily_minutes"]
        if not isinstance(daily_minutes, int):
            return False, f"daily_minutes must be an integer, got {type(daily_minutes)}"
        if daily_minutes < MIN_DAILY_MINUTES or daily_minutes > MAX_DAILY_MINUTES:
            return False, f"daily_minutes must be between {MIN_DAILY_MINUTES} and {MAX_DAILY_MINUTES}"
    
    # Validate learning_style
    if "learning_style" in state:
        if state["learning_style"] is not None:
            style = state["learning_style"].lower()
            if style not in VALID_LEARNING_STYLES:
                return False, f"learning_style must be one of {VALID_LEARNING_STYLES}, got '{style}'"
    
    # Validate pace
    if "pace" in state:
        if state["pace"] is not None:
            pace = state["pace"].lower()
            if pace not in VALID_PACES:
                return False, f"pace must be one of {VALID_PACES}, got '{pace}'"
    
    # Validate completion_rate
    if "completion_rate" in state:
        rate = state["completion_rate"]
        if not isinstance(rate, (int, float)):
            return False, f"completion_rate must be numeric, got {type(rate)}"
        if rate < 0.0 or rate > 1.0:
            return False, f"completion_rate must be between 0.0 and 1.0, got {rate}"
    
    return True, None


def create_initial_state(
    goal_text: str,
    level: str = "beginner",
    daily_minutes: int = 30,
    learning_style: Optional[str] = "visual",
    pace: Optional[str] = "medium",
    preferences: Optional[Dict[str, Any]] = None
) -> AppState:
    """
    Create an initial state with default values.
    
    Args:
        goal_text: The user's learning goal
        level: Skill level (default: beginner)
        daily_minutes: Daily study time (default: 30)
        learning_style: Learning style (default: visual)
        pace: Learning pace (default: medium)
        preferences: Additional preferences (default: empty dict)
        
    Returns:
        Initial AppState ready for graph execution
        
    Raises:
        ValueError: If any validation fails
        
    Example:
        >>> state = create_initial_state(
        ...     goal_text="Learn Python",
        ...     level="beginner",
        ...     daily_minutes=60
        ... )
    """
    state: AppState = {
        "goal_id": None,
        "goal_text": goal_text,
        "level": level.lower() if level else "beginner",
        "daily_minutes": daily_minutes,
        "learning_style": learning_style.lower() if learning_style else "visual",
        "pace": pace.lower() if pace else "medium",
        "preferences": preferences or {},
        "conversation_history": [],
        "clarification_complete": False,
        "resources": [],
        "roadmap": None,
        "tasks": [],
        "completion_rate": 0.0,
        "gaps_identified": [],
        "adaptations_needed": False,
        "performance_metrics": {},
        "error": None,
        "current_node": "start",
        "metadata": {
            "start_time": datetime.utcnow().isoformat(),
            "node_execution_times": {},
            "retry_count": 0,
            "graph_version": "2.0.0"
        }
    }
    
    # Validate the state
    is_valid, error = validate_state(state)
    if not is_valid:
        raise ValueError(f"Invalid initial state: {error}")
    
    return state