"""
LangGraph State Definition - 4-Phase Learning Workflow
Defines the complete application state that flows through the graph.
"""
from typing import TypedDict, Optional, Any, List, Dict
from datetime import datetime
from enum import Enum


class Phase(str, Enum):
    """Workflow phase tracking"""
    DISCOVERY = "discovery"
    ROADMAP_ARCHITECTURE = "roadmap_architecture"
    CONTENT_POPULATION = "content_population"
    ADAPTIVE_EXECUTION = "adaptive_execution"


class AppState(TypedDict, total=False):
    """
    4-Phase Learning Workflow State

    Flow: Discovery → Roadmap Architecture → Content Population → Adaptive Execution

    Each phase builds on the previous, with clear state transitions and outputs.
    """

    # ============== PHASE 1: DISCOVERY ==============
    current_phase: str  # Phase enum value

    # User goal & profile
    goal_text: str
    """User's learning goal (e.g., "Learn Python for data science")"""

    goal_analysis: Optional[Dict[str, Any]]
    """LLM analysis of goal: {"domain": "...", "complexity": 0.7, "learning_area": "..."}"""

    # Skill assessment results
    user_profile: Optional[Dict[str, Any]]
    """
    Comprehensive user profile:
    {
        "level": "beginner|intermediate|advanced",
        "learning_style": "visual|kinesthetic|auditory|reading_writing",
        "pace": "slow|medium|fast",
        "daily_minutes": 30-480,
        "preferences": {...},
        "identified_skills": ["Python basics", "Statistics"],
        "learning_challenges": ["Limited time", "Math phobia"],
        "preferred_resources": ["videos", "interactive"]
    }
    """

    # Domain analysis
    domain_analysis: Optional[Dict[str, Any]]
    """
    Domain structure analysis:
    {
        "prerequisites": ["basic programming", "algebra"],
        "dependencies": {"advanced-python": ["basic-python"]},
        "complexity_estimate": 0.7,  # 0-1 scale
        "estimated_weeks": 12,
        "core_competencies": ["variables", "loops", "functions"],
        "learning_path_options": [...]
    }
    """

    # Discovery conversation history
    conversation_history: List[Dict[str, str]]
    """List of conversation turns: [{"role": "user|assistant", "content": "..."}, ...]"""

    discovery_complete: bool
    """Flag: Phase 1 (Discovery) is complete"""

    # ============== PHASE 2: ROADMAP ARCHITECTURE ==============
    abstract_roadmap: Optional[Dict[str, Any]]
    """
    Hierarchical curriculum structure (NO content yet):
    {
        "structure": {
            "modules": [
                {
                    "id": "mod_1",
                    "title": "Python Fundamentals",
                    "description": "Core language features",
                    "estimated_weeks": 2,
                    "difficulty": 0.3,
                    "topics": [
                        {
                            "id": "topic_1_1",
                            "title": "Variables & Types",
                            "subtopics": ["int/float", "strings", "booleans"],
                            "learning_objectives": ["Understand type system", "Use variables effectively"]
                        }
                    ],
                    "prerequisites": [],
                    "dependencies_before": [],
                    "dependencies_after": ["mod_2"]
                }
            ]
        },
        "milestones": [
            {"week": 2, "checkpoint": "Quiz on fundamentals", "success_criteria": "80%"}
        ],
        "total_estimated_weeks": 12
    }
    """

    roadmap_validated: bool
    """Flag: User approved the abstract roadmap"""

    roadmap_validation_feedback: Optional[str]
    """User feedback on roadmap (if rejected)"""

    # ============== PHASE 3: CONTENT POPULATION ==============
    module_resources: Dict[str, List[Dict[str, Any]]]
    """
    Per-module curated resources:
    {
        "mod_1": [
            {
                "id": "res_1",
                "title": "Python Variables Tutorial",
                "url": "https://...",
                "type": "video|article|interactive|exercise",
                "difficulty": 0.2,  # 0-1 scale
                "duration_minutes": 15,
                "source": "youtube|course|blog|official",
                "relevance_score": 0.95,
                "description": "Comprehensive guide to variables",
                "metadata": {...}
            }
        ]
    }
    """

    module_tasks: Dict[str, List[Dict[str, Any]]]
    """
    Per-module generated tasks:
    {
        "mod_1": [
            {
                "id": "task_1_1",
                "title": "Create variables exercise",
                "description": "Write a program using variables",
                "task_type": "exercise|quiz|project|reflection",
                "difficulty": 0.3,
                "estimated_minutes": 20,
                "learning_objectives": ["practice variable assignment", "understand scope"],
                "resources_used": ["res_1"],
                "success_criteria": "Submit working code",
                "hints": ["Start with integers...", "Remember type conversion..."]
            }
        ]
    }
    """

    module_curation_status: Dict[str, str]
    """Status of each module: {"mod_1": "completed", "mod_2": "in_progress", "mod_3": "pending"}"""

    content_population_progress: float
    """Percentage of modules with content: 0.0 to 1.0"""

    populated_roadmap: Optional[Dict[str, Any]]
    """Complete roadmap: abstract structure + resources + tasks merged"""

    # ============== PHASE 4: ADAPTIVE EXECUTION ==============
    # Progress tracking
    completed_tasks: List[str]
    """List of completed task IDs: ["task_1_1", "task_1_2", ...]"""

    task_completion_details: Dict[str, Dict[str, Any]]
    """
    Detailed completion info:
    {
        "task_1_1": {
            "completed_at": "2025-01-26T10:30:00Z",
            "time_spent_minutes": 25,
            "difficulty_reported": 0.4,  # User's perceived difficulty
            "performance_score": 0.95,  # 0-1 based on test/submission
            "feedback": "Was easier than expected",
            "revision_count": 1
        }
    }
    """

    current_module: Optional[str]
    """Which module is user currently working on: "mod_1", etc."""

    current_task_index: int
    """Index position in current module's task list"""

    # Performance metrics
    performance_metrics: Dict[str, Any]
    """
    Real-time performance analysis:
    {
        "avg_time_vs_estimate": 1.2,  # 20% over time estimate
        "avg_difficulty_vs_estimate": 0.6,  # User finds easier than estimated
        "completion_velocity": 0.8,  # tasks per week
        "consistency_score": 0.75,  # 0-1
        "struggling_modules": ["mod_3"],
        "struggling_topics": ["recursion", "generators"],
        "strength_areas": ["loops", "dictionaries"],
        "days_to_completion": 35,
        "pacing_warning": False
    }
    """

    # Adaptation detection
    struggles_detected: bool
    """Flag: User is struggling with content"""

    struggle_topic: Optional[str]
    """Specific topic user is struggling with"""

    struggle_severity: float
    """0-1: How severe the struggle is"""

    adaptation_required: bool
    """Flag: Learning plan needs adjustment"""

    # Adaptive decisions
    pacing_adjustment: Optional[float]
    """Pacing multiplier: 0.8 = slow down, 1.2 = speed up"""

    recommended_actions: List[str]
    """Recommended interventions: ["add prerequisite module", "slow down", "add practice"]"""

    re_curation_triggered: bool
    """Flag: Need to re-curate struggling module"""

    struggling_module_id: Optional[str]
    """Which module needs re-curation: "mod_3", etc."""

    replanning_threshold: float
    """Trigger re-planning if struggle_severity > threshold (default: 0.7)"""

    # ============== TIMELINE & SCHEDULING ==============
    target_completion_days: Optional[int]
    """User's target timeline to complete the learning goal (in days)"""
    
    target_weeks: Optional[int]
    """Calculated target weeks (target_completion_days // 7)"""
    
    target_display: Optional[str]
    """Human-readable target display (e.g., '2 Weeks', '30 Days')"""

    # ============== METADATA & CONTROL ==============
    user_id: Optional[int]
    """Database user ID (None until saved)"""

    session_id: str
    """UUID for tracking this workflow execution"""

    start_time: datetime
    """Workflow start timestamp"""

    # Execution tracking
    error: Optional[str]
    """Error message if any node failed"""

    error_node: Optional[str]
    """Which node threw the error"""

    current_node: str
    """Name of currently executing node (for tracking)"""

    metadata: Dict[str, Any]
    """
    Execution metadata:
    {
        "node_execution_times": {"goal_clarifier_node": 45.2, "domain_analyzer_node": 12.1},
        "api_calls": 23,
        "token_count": 5000,
        "graph_version": "3.0",
        "timestamp": "2025-01-26T10:30:00Z",
        "phase_transitions": [
            {"phase": "discovery", "timestamp": "...", "duration_seconds": 180}
        ]
    }
    """


# ============== VALIDATORS ==============
VALID_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_LEARNING_STYLES = {"visual", "kinesthetic", "auditory", "reading_writing"}
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
    if "user_profile" in state and state["user_profile"]:
        profile = state["user_profile"]
        if "level" in profile:
            level = profile["level"].lower() if isinstance(profile["level"], str) else profile["level"]
            if level not in VALID_LEVELS:
                return False, f"level must be one of {VALID_LEVELS}, got '{level}'"

    # Validate daily_minutes
    if "user_profile" in state and state["user_profile"]:
        profile = state["user_profile"]
        if "daily_minutes" in profile:
            daily_minutes = profile["daily_minutes"]
            if not isinstance(daily_minutes, int):
                return False, f"daily_minutes must be an integer, got {type(daily_minutes)}"
            if daily_minutes < MIN_DAILY_MINUTES or daily_minutes > MAX_DAILY_MINUTES:
                return False, f"daily_minutes must be between {MIN_DAILY_MINUTES} and {MAX_DAILY_MINUTES}"

    # Validate performance_metrics values
    if "performance_metrics" in state and state["performance_metrics"]:
        metrics = state["performance_metrics"]
        if "consistency_score" in metrics:
            score = metrics["consistency_score"]
            if not isinstance(score, (int, float)) or score < 0.0 or score > 1.0:
                return False, f"consistency_score must be 0.0-1.0, got {score}"

    return True, None


def create_initial_state(
    goal_text: str,
    level: str = "beginner",
    daily_minutes: int = 30,
    learning_style: Optional[str] = "visual",
    pace: Optional[str] = "medium",
    preferences: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    target_completion_days: Optional[int] = None,
) -> AppState:
    """
    Create an initial state for Phase 1: Discovery.
    
    Can be called two ways:
    1. Minimal (new 4-phase flow):
       create_initial_state(goal_text="Learn Python")
       → User goes through discovery phases
    
    2. With context (backward compatible):
       create_initial_state(
           goal_text="Learn Python",
           level="beginner",
           daily_minutes=60,
           learning_style="visual",
           target_completion_days=30
       )
       → Pre-populates user_profile with timeline, skips some discovery
    
    Args:
        goal_text: The user's learning goal (required, 10-500 chars)
        level: Skill level (default: beginner)
        daily_minutes: Daily study time (default: 30)
        learning_style: Learning style (default: visual)
        pace: Learning pace (default: medium)
        preferences: Additional preferences (default: empty dict)
        user_id: Optional database user ID
        session_id: Optional session UUID (will be generated if not provided)
        target_completion_days: User's target timeline in days (e.g., 30 days, 90 days)

    Returns:
        Initial AppState ready for graph execution

    Raises:
        ValueError: If any validation fails

    Example:
        >>> # Minimal
        >>> state = create_initial_state(goal_text="Learn Python for data science")
        
        >>> # With context and timeline
        >>> state = create_initial_state(
        ...     goal_text="Learn Python for data science",
        ...     level="intermediate",
        ...     daily_minutes=60,
        ...     target_completion_days=30
        ... )
    """
    import uuid

    if session_id is None:
        session_id = str(uuid.uuid4())

    # Pre-populate user_profile if provided
    user_profile = {
        "level": level.lower() if level else "beginner",
        "daily_minutes": daily_minutes,
        "learning_style": learning_style.lower() if learning_style else "visual",
        "pace": pace.lower() if pace else "medium",
        "preferences": preferences or {},
        "target_completion_days": target_completion_days,  # User's timeline goal
    }
    
    # Calculate target weeks for curriculum planning
    target_weeks = None
    if target_completion_days:
        target_weeks = max(1, target_completion_days // 7)

    state: AppState = {
        "current_phase": Phase.DISCOVERY,
        "goal_text": goal_text,
        "goal_analysis": None,
        "user_profile": user_profile,
        "domain_analysis": None,
        "conversation_history": [],
        "discovery_complete": False,
        "abstract_roadmap": None,
        "roadmap_validated": None,  # None = pending user decision, True/False = decided
        "roadmap_validation_feedback": None,
        "module_resources": {},
        "module_tasks": {},
        "module_curation_status": {},
        "content_population_progress": 0.0,
        "populated_roadmap": None,
        "completed_tasks": [],
        "task_completion_details": {},
        "current_module": None,
        "current_task_index": 0,
        "performance_metrics": {},
        "struggles_detected": False,
        "struggle_topic": None,
        "struggle_severity": 0.0,
        "adaptation_required": False,
        "pacing_adjustment": None,
        "recommended_actions": [],
        "re_curation_triggered": False,
        "struggling_module_id": None,
        "replanning_threshold": 0.7,
        "user_id": user_id,
        "session_id": session_id,
        "start_time": datetime.utcnow(),
        "target_completion_days": target_completion_days,  # Top-level for easy access
        "target_weeks": target_weeks,  # Convenience field for curriculum planning
        "error": None,
        "error_node": None,
        "current_node": "start",
        "metadata": {
            "node_execution_times": {},
            "api_calls": 0,
            "token_count": 0,
            "graph_version": "3.0",
            "timestamp": datetime.utcnow().isoformat(),
            "phase_transitions": [],
        },
    }

    # Validate the state
    is_valid, error = validate_state(state)
    if not is_valid:
        raise ValueError(f"Invalid initial state: {error}")

    return state

