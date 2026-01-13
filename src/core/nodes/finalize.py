"""
Finalize Node - LangGraph Node

Handles graceful completion of the learning workflow.
- Adds final timestamps
- Generates summary statistics
- Stores workflow summary in database
- Prepares state for UI consumption
- Logs workflow completion

Author: AI Learning Platform Team
"""

import logging
from datetime import datetime
from typing import Optional
from src.core.state import AppState
from src.database.crud import create_progress_record
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def finalize_node(state: AppState) -> AppState:
    """
    Finalize the learning workflow and prepare output state.
    
    This node:
    - Adds completion timestamps
    - Generates workflow summary statistics
    - Stores progress snapshot in database
    - Prepares state for UI consumption
    - Logs workflow metrics
    
    Args:
        state: Current application state from previous nodes
        
    Returns:
        Updated state with finalization metadata and timestamps
        
    Raises:
        ValueError: If critical state fields are missing
        Exception: If database operations fail
        
    Example:
        >>> state = AppState(goal_id=1, tasks=[...], completion_rate=0.75)
        >>> final_state = finalize_node(state)
        >>> assert final_state.metadata["workflow_status"] == "completed"
    """
    logger.info(f"Starting finalize node for goal_id={state.get('goal_id')}")
    
    try:
        # Validate critical state fields
        _validate_state(state)
        
        # Calculate workflow metrics
        metadata = _calculate_metadata(state)
        
        # Store progress record in database
        _store_progress(state, metadata)
        
        # Prepare final state
        state["workflow_status"] = "completed"
        state["finalized_at"] = datetime.utcnow().isoformat()
        state["metadata"] = metadata
        
        logger.info(
            f"Finalize node completed successfully. "
            f"Goal: {state.get('goal_id')}, "
            f"Tasks: {len(state.get('tasks', []))}, "
            f"Completion: {state.get('completion_rate', 0):.2%}"
        )
        
        return state
        
    except ValueError as e:
        logger.error(f"Validation error in finalize node: {str(e)}")
        state["error"] = f"Finalization validation failed: {str(e)}"
        state["workflow_status"] = "failed"
        return state
        
    except Exception as e:
        logger.error(f"Unexpected error in finalize node: {str(e)}", exc_info=True)
        state["error"] = f"Finalization failed: {str(e)}"
        state["workflow_status"] = "error"
        return state


def _validate_state(state: AppState) -> None:
    """
    Validate that state contains required fields for finalization.
    
    Args:
        state: State to validate
        
    Raises:
        ValueError: If required fields are missing
    """
    required_fields = ["goal_id", "goal_text", "tasks"]
    missing_fields = [field for field in required_fields if field not in state or state[field] is None]
    
    if missing_fields:
        raise ValueError(f"Missing required fields for finalization: {missing_fields}")
    
    # Validate goal_id is valid
    if not isinstance(state["goal_id"], int) or state["goal_id"] <= 0:
        raise ValueError(f"Invalid goal_id: {state['goal_id']}")
    
    logger.debug("State validation passed")


def _calculate_metadata(state: AppState) -> dict:
    """
    Calculate workflow summary statistics and metadata.
    
    Includes:
    - Total workflow duration
    - Task metrics (count, completion rate)
    - Resource metrics (count, types)
    - Node execution information
    - Timestamp information
    
    Args:
        state: Current application state
        
    Returns:
        Dictionary with metadata and statistics
    """
    metadata = {}
    
    # Timestamps
    metadata["finalized_at"] = datetime.utcnow().isoformat()
    if "created_at" in state:
        try:
            workflow_duration = (datetime.utcnow() - datetime.fromisoformat(state["created_at"])).total_seconds()
            metadata["workflow_duration_seconds"] = workflow_duration
            metadata["workflow_duration_minutes"] = round(workflow_duration / 60, 2)
        except (ValueError, TypeError):
            logger.warning("Could not calculate workflow duration due to invalid timestamp")
    
    # Task metrics
    tasks = state.get("tasks", [])
    metadata["total_tasks_generated"] = len(tasks)
    metadata["tasks_completed"] = sum(1 for task in tasks if task.get("is_completed", False))
    metadata["tasks_skipped"] = sum(1 for task in tasks if task.get("is_skipped", False))
    metadata["tasks_pending"] = len(tasks) - metadata["tasks_completed"] - metadata["tasks_skipped"]
    
    # Completion metrics
    completion_rate = state.get("completion_rate", 0.0)
    metadata["completion_rate"] = completion_rate
    metadata["completion_percentage"] = f"{completion_rate * 100:.1f}%"
    
    # Resource metrics
    resources = state.get("resources", [])
    metadata["total_resources_retrieved"] = len(resources)
    if resources:
        resource_types = {}
        for resource in resources:
            resource_type = resource.get("type", "unknown")
            resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
        metadata["resources_by_type"] = resource_types
    
    # Roadmap metrics
    roadmap = state.get("roadmap")
    if roadmap:
        metadata["modules_in_roadmap"] = len(roadmap.get("modules", []))
        metadata["estimated_weeks"] = roadmap.get("total_weeks", 0)
    
    # Gaps and adaptations
    metadata["gaps_identified"] = len(state.get("gaps_identified", []))
    metadata["adaptations_needed"] = state.get("adaptations_needed", False)
    
    # State fields present
    metadata["state_fields_populated"] = [
        field for field in [
            "goal_id", "goal_text", "level", "learning_style", 
            "roadmap", "tasks", "resources"
        ]
        if field in state and state[field]
    ]
    
    logger.debug(f"Calculated metadata: {metadata}")
    return metadata


def _store_progress(state: AppState, metadata: dict) -> None:
    """
    Store progress snapshot in database.
    
    Creates a progress record with:
    - Current completion rate
    - Task counts
    - Metadata summary
    
    Args:
        state: Current application state
        metadata: Calculated metadata
        
    Raises:
        Exception: If database operation fails
    """
    try:
        goal_id = state["goal_id"]
        completion_rate = state.get("completion_rate", 0.0)
        tasks_completed = metadata.get("tasks_completed", 0)
        tasks_total = metadata.get("total_tasks_generated", 0)
        
        # Store progress record
        progress_record = create_progress_record(
            goal_id=goal_id,
            completion_percentage=completion_rate * 100,
            tasks_completed=tasks_completed,
            tasks_total=tasks_total,
            notes=f"Workflow finalized. Metadata: {metadata}"
        )
        
        logger.info(f"Stored progress record: {progress_record.id if hasattr(progress_record, 'id') else 'unknown'}")
        
    except Exception as e:
        logger.error(f"Failed to store progress record: {str(e)}")
        raise


def get_workflow_summary(state: AppState) -> dict:
    """
    Get a human-readable summary of the workflow.
    
    Useful for UI display and logging.
    
    Args:
        state: Finalized application state
        
    Returns:
        Dictionary with summary information
    """
    metadata = state.get("metadata", {})
    
    summary = {
        "status": state.get("workflow_status", "unknown"),
        "goal": state.get("goal_text", "Unknown"),
        "level": state.get("level", "Unknown"),
        "total_tasks": metadata.get("total_tasks_generated", 0),
        "completed_tasks": metadata.get("tasks_completed", 0),
        "completion_rate": f"{metadata.get('completion_percentage', '0%')}",
        "resources_found": metadata.get("total_resources_retrieved", 0),
        "modules": metadata.get("modules_in_roadmap", 0),
        "duration_minutes": metadata.get("workflow_duration_minutes", "N/A"),
    }
    
    return summary
