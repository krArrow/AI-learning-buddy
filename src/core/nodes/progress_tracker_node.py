"""
PHASE 4: Progress Tracker Node
Logs completion, time spent, and difficulty feedback for tasks.
"""
from datetime import datetime
from typing import Dict, Any
from src.core.state import AppState, Phase
from src.utils.logger import get_logger

logger = get_logger(__name__)


def progress_tracker_node(state: AppState) -> AppState:
    """
    PHASE 4: Track task completion and performance
    
    Records:
    - Completed task ID
    - Time spent vs estimate
    - User's perceived difficulty
    - Performance score (if available)
    - User feedback
    
    Updates:
    - completed_tasks list
    - task_completion_details
    - performance_metrics
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with completion tracking
    """
    logger.info("→ [PHASE 4] progress_tracker_node: Tracking progress")
    
    try:
        populated_roadmap = state.get("populated_roadmap")
        current_module = state.get("current_module")
        current_task_index = state.get("current_task_index", 0)
        
        if not populated_roadmap:
            logger.info("  ⓘ No populated_roadmap yet, skipping progress tracking")
            state["current_node"] = "progress_tracker_node"
            state["current_phase"] = Phase.ADAPTIVE_EXECUTION
            return state
        
        # Get current task
        modules = populated_roadmap.get("structure", {}).get("modules", [])
        
        if not current_module:
            # Initialize to first module
            if modules:
                current_module = modules[0]["id"]
                state["current_module"] = current_module
            else:
                logger.warning("  ⚠ No modules available for tracking")
                state["current_node"] = "progress_tracker_node"
                return state
        
        # Find current module
        current_mod = next((m for m in modules if m["id"] == current_module), None)
        if not current_mod:
            logger.warning(f"  ⚠ Module {current_module} not found")
            state["current_node"] = "progress_tracker_node"
            return state
        
        tasks = current_mod.get("tasks", [])
        if current_task_index >= len(tasks):
            logger.info(f"  ✓ All tasks completed for module {current_module}")
            # Move to next module
            next_mod_idx = next((i for i, m in enumerate(modules) if m["id"] == current_module)) + 1
            if next_mod_idx < len(modules):
                state["current_module"] = modules[next_mod_idx]["id"]
                state["current_task_index"] = 0
            state["current_node"] = "progress_tracker_node"
            state["current_phase"] = Phase.ADAPTIVE_EXECUTION
            return state
        
        current_task = tasks[current_task_index]
        task_id = current_task.get("id")
        
        # Simulate task completion (in real app, this comes from user)
        # For now, record the task as completed
        if task_id not in state.get("completed_tasks", []):
            completed_tasks = state.get("completed_tasks", [])
            completed_tasks.append(task_id)
            state["completed_tasks"] = completed_tasks
            
            # Record completion details (simulated)
            estimated_mins = current_task.get("estimated_minutes", 20)
            actual_mins = int(estimated_mins * 1.1)  # Simulate 10% over estimate
            
            completion_detail = {
                "completed_at": datetime.utcnow().isoformat(),
                "time_spent_minutes": actual_mins,
                "difficulty_reported": current_task.get("difficulty", 0.5),
                "performance_score": 0.85,
                "feedback": "Task completed",
                "revision_count": 1
            }
            
            task_details = state.get("task_completion_details", {})
            task_details[task_id] = completion_detail
            state["task_completion_details"] = task_details
            
            logger.info(f"  ✓ Task completed: {task_id}")
            logger.debug(f"    Time: {actual_mins} min (est: {estimated_mins} min)")
        
        # Update performance metrics
        _update_performance_metrics(state)
        
        # Advance to next task
        state["current_task_index"] = current_task_index + 1
        
        state["current_node"] = "progress_tracker_node"
        state["current_phase"] = Phase.ADAPTIVE_EXECUTION
        
        logger.info(f"  ✓ progress_tracker_node complete")
        logger.debug(f"    Tasks completed: {len(state.get('completed_tasks', []))}")
        
        return state
        
    except Exception as e:
        logger.error(f"✗ progress_tracker_node failed: {str(e)}", exc_info=True)
        state["error"] = f"Progress tracking failed: {str(e)}"
        state["error_node"] = "progress_tracker_node"
        return state


def _update_performance_metrics(state: AppState) -> None:
    """Calculate and update performance metrics."""
    completed_details = state.get("task_completion_details", {})
    
    if not completed_details:
        return
    
    # Calculate metrics
    total_time_spent = sum(d.get("time_spent_minutes", 0) for d in completed_details.values())
    total_estimated = 0  # Would calculate from populated_roadmap
    avg_difficulty = sum(d.get("difficulty_reported", 0.5) for d in completed_details.values()) / len(completed_details)
    avg_performance = sum(d.get("performance_score", 0.8) for d in completed_details.values()) / len(completed_details)
    
    # Create/update metrics
    metrics = state.get("performance_metrics", {})
    metrics["total_time_spent_minutes"] = total_time_spent
    metrics["avg_difficulty_reported"] = avg_difficulty
    metrics["avg_performance_score"] = avg_performance
    metrics["completion_velocity"] = len(completed_details) / max(1, total_time_spent / 60)  # tasks per hour
    metrics["consistency_score"] = min(1.0, avg_performance)
    
    state["performance_metrics"] = metrics
