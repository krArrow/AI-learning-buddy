"""
Goal Analysis Node - Validates and stores user learning goals.
This is the entry point of the learning workflow.
"""
from typing import Dict, Any
import time

from src.core.state import AppState, validate_state
from src.database import db_manager, LearningGoalCRUD
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GoalAnalysisError(Exception):
    """Custom exception for goal analysis failures."""
    pass


def goal_analysis_node(state: AppState) -> AppState:
    """
    Analyze and validate user learning goal.
    
    This node:
    1. Validates all goal-related fields in the state
    2. Normalizes values (lowercase, trim whitespace)
    3. Stores the goal in the database
    4. Updates state with the goal_id
    
    Args:
        state: Current application state containing goal information
        
    Returns:
        Updated state with goal_id set and validation complete
        
    Raises:
        GoalAnalysisError: If goal validation or storage fails
        
    Example:
        >>> state = create_initial_state(
        ...     goal_text="Learn Python",
        ...     level="beginner",
        ...     daily_minutes=30
        ... )
        >>> updated_state = goal_analysis_node(state)
        >>> assert updated_state['goal_id'] is not None
    """
    start_time = time.time()
    node_name = "goal_analyzer"
    
    # Update current node in state
    state["current_node"] = node_name
    logger.info(f"[{node_name}] Starting goal analysis")
    
    try:
        # Step 1: Validate state fields
        logger.debug(f"[{node_name}] Validating state fields")
        is_valid, error_msg = validate_state(state)
        if not is_valid:
            raise GoalAnalysisError(f"State validation failed: {error_msg}")
        
        # Step 2: Extract and validate goal_text
        goal_text = state.get("goal_text", "").strip()
        if not goal_text:
            raise GoalAnalysisError("goal_text is required and cannot be empty")
        
        if len(goal_text) < 10:
            raise GoalAnalysisError(
                f"goal_text must be at least 10 characters, got {len(goal_text)}"
            )
        
        if len(goal_text) > 500:
            raise GoalAnalysisError(
                f"goal_text must be at most 500 characters, got {len(goal_text)}"
            )
        
        logger.info(f"[{node_name}] Goal text validated: '{goal_text[:50]}...'")
        
        # Step 3: Normalize and validate level
        level = state.get("level", "beginner").lower().strip()
        valid_levels = {"beginner", "intermediate", "advanced"}
        if level not in valid_levels:
            raise GoalAnalysisError(
                f"level must be one of {valid_levels}, got '{level}'"
            )
        state["level"] = level
        logger.debug(f"[{node_name}] Level: {level}")
        
        # Step 4: Validate daily_minutes
        daily_minutes = state.get("daily_minutes", 30)
        if not isinstance(daily_minutes, int):
            try:
                daily_minutes = int(daily_minutes)
                state["daily_minutes"] = daily_minutes
            except (ValueError, TypeError):
                raise GoalAnalysisError(
                    f"daily_minutes must be an integer, got {type(daily_minutes)}"
                )
        
        if daily_minutes < 10 or daily_minutes > 480:
            raise GoalAnalysisError(
                f"daily_minutes must be between 10 and 480, got {daily_minutes}"
            )
        logger.debug(f"[{node_name}] Daily minutes: {daily_minutes}")
        
        # Step 5: Normalize learning_style
        learning_style = state.get("learning_style", "visual").lower().strip()
        valid_styles = {"visual", "kinesthetic", "auditory", "reading"}
        if learning_style not in valid_styles:
            logger.warning(
                f"[{node_name}] Invalid learning_style '{learning_style}', defaulting to 'visual'"
            )
            learning_style = "visual"
        state["learning_style"] = learning_style
        logger.debug(f"[{node_name}] Learning style: {learning_style}")
        
        # Step 6: Normalize pace
        pace = state.get("pace", "medium").lower().strip()
        valid_paces = {"slow", "medium", "fast"}
        if pace not in valid_paces:
            logger.warning(
                f"[{node_name}] Invalid pace '{pace}', defaulting to 'medium'"
            )
            pace = "medium"
        state["pace"] = pace
        logger.debug(f"[{node_name}] Pace: {pace}")
        
        # Step 7: Get preferences
        preferences = state.get("preferences", {})
        if not isinstance(preferences, dict):
            logger.warning(f"[{node_name}] preferences is not a dict, resetting to empty dict")
            preferences = {}
            state["preferences"] = preferences
        
        # Step 8: Store goal in database
        logger.info(f"[{node_name}] Storing goal in database")
        
        try:
            with db_manager.get_session_context() as session:
                goal = LearningGoalCRUD.create(
                    session=session,
                    goal_text=goal_text,
                    level=level,
                    daily_minutes=daily_minutes,
                    learning_style=learning_style,
                    pace=pace,
                    preferences=preferences
                )
                
                # Update state with goal_id
                state["goal_id"] = goal.id
                logger.info(f"[{node_name}] Goal stored successfully with ID: {goal.id}")
                
        except Exception as db_error:
            logger.error(f"[{node_name}] Database error: {db_error}", exc_info=True)
            raise GoalAnalysisError(f"Failed to store goal in database: {db_error}")
        
        # Step 9: Update metadata
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        # Clear any previous errors
        state["error"] = None
        
        logger.info(
            f"[{node_name}] Goal analysis complete in {elapsed:.2f}s. "
            f"Goal ID: {state['goal_id']}"
        )
        
        return state
        
    except GoalAnalysisError as e:
        # Handle validation errors
        error_msg = str(e)
        logger.error(f"[{node_name}] Goal analysis failed: {error_msg}")
        state["error"] = error_msg
        state["current_node"] = f"{node_name}_failed"
        
        # Track execution time even on failure
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        raise
        
    except Exception as e:
        # Handle unexpected errors
        error_msg = f"Unexpected error in goal analysis: {str(e)}"
        logger.error(f"[{node_name}] {error_msg}", exc_info=True)
        state["error"] = error_msg
        state["current_node"] = f"{node_name}_error"
        
        # Track execution time
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        raise GoalAnalysisError(error_msg) from e


def validate_goal_requirements(state: AppState) -> bool:
    """
    Check if state has all required fields for goal analysis.
    
    Args:
        state: Application state to check
        
    Returns:
        True if all required fields are present
    """
    required_fields = ["goal_text", "level", "daily_minutes"]
    
    for field in required_fields:
        if field not in state:
            logger.warning(f"Missing required field for goal analysis: {field}")
            return False
    
    return True