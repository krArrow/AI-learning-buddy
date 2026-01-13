"""
Performance Analyzer Node - Analyzes user learning progress and performance.
"""
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.core.state import AppState
from src.database import db_manager, TaskCRUD, ProgressCRUD
from src.utils.logger import get_logger

logger = get_logger(__name__)


def performance_analyzer_node(state: AppState) -> AppState:
    """
    Analyze user's learning performance and progress.
    
    This node:
    - Queries completed tasks from database
    - Calculates completion rate
    - Computes average completion time
    - Determines consistency score
    - Identifies struggling areas
    - Updates state with metrics
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with performance_metrics populated
    """
    start_time = time.time()
    node_name = "performance_analyzer"
    state["current_node"] = node_name
    
    logger.info(f"[{node_name}] Starting performance analysis")
    
    try:
        goal_id = state.get("goal_id")
        if not goal_id:
            logger.warning(f"[{node_name}] No goal_id, skipping analysis")
            state["completion_rate"] = 0.0
            state["performance_metrics"] = {}
            return state
        
        # Query tasks from database
        with db_manager.get_session_context() as session:
            all_tasks = TaskCRUD.get_by_goal_id(session, goal_id)
            completed_tasks = [t for t in all_tasks if t.is_completed]
            incomplete_tasks = [t for t in all_tasks if not t.is_completed]
            
            logger.info(
                f"[{node_name}] Found {len(completed_tasks)}/{len(all_tasks)} tasks completed"
            )
            
            # Calculate metrics
            metrics = _calculate_metrics(all_tasks, completed_tasks, incomplete_tasks)
            
            # Update state
            state["completion_rate"] = metrics["completion_rate"]
            state["performance_metrics"] = metrics
            
            logger.info(
                f"[{node_name}] Completion rate: {metrics['completion_rate']:.2%}, "
                f"Avg time: {metrics.get('average_completion_time', 0):.1f} min"
            )
        
        # Track execution time
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        logger.info(f"[{node_name}] Performance analysis complete in {elapsed:.2f}s")
        
        return state
        
    except Exception as e:
        logger.error(f"[{node_name}] Error analyzing performance: {e}", exc_info=True)
        state["error"] = f"Performance analysis failed: {str(e)}"
        state["completion_rate"] = 0.0
        state["performance_metrics"] = {}
        
        # Track execution time
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        return state


def _calculate_metrics(all_tasks: List, completed_tasks: List, incomplete_tasks: List) -> Dict[str, Any]:
    """
    Calculate performance metrics from task data.
    
    Args:
        all_tasks: All tasks for the goal
        completed_tasks: Completed tasks
        incomplete_tasks: Incomplete tasks
        
    Returns:
        Dictionary of metrics
    """
    metrics = {}
    
    # Completion rate
    total_count = len(all_tasks)
    completed_count = len(completed_tasks)
    
    metrics["completion_rate"] = completed_count / total_count if total_count > 0 else 0.0
    metrics["tasks_total"] = total_count
    metrics["tasks_completed"] = completed_count
    metrics["tasks_remaining"] = len(incomplete_tasks)
    
    # Average completion time
    completion_times = [
        t.completion_time_minutes
        for t in completed_tasks
        if t.completion_time_minutes is not None
    ]
    
    if completion_times:
        metrics["average_completion_time"] = sum(completion_times) / len(completion_times)
        metrics["min_completion_time"] = min(completion_times)
        metrics["max_completion_time"] = max(completion_times)
    else:
        metrics["average_completion_time"] = 0.0
        metrics["min_completion_time"] = 0.0
        metrics["max_completion_time"] = 0.0
    
    # Consistency score (based on completion times variance)
    if len(completion_times) >= 2:
        mean_time = metrics["average_completion_time"]
        variance = sum((t - mean_time) ** 2 for t in completion_times) / len(completion_times)
        std_dev = variance ** 0.5
        # Consistency score: lower std_dev = more consistent = higher score
        metrics["consistency_score"] = max(0.0, 1.0 - (std_dev / mean_time)) if mean_time > 0 else 0.5
    else:
        metrics["consistency_score"] = 0.5  # Neutral score
    
    # Difficulty match
    if completed_tasks:
        avg_difficulty = sum(t.difficulty_score for t in completed_tasks) / len(completed_tasks)
        metrics["average_difficulty"] = avg_difficulty
        
        # Are tasks too easy or too hard?
        if metrics["completion_rate"] > 0.9 and avg_difficulty < 0.4:
            metrics["difficulty_match"] = "too_easy"
        elif metrics["completion_rate"] < 0.5 and avg_difficulty > 0.6:
            metrics["difficulty_match"] = "too_hard"
        else:
            metrics["difficulty_match"] = "appropriate"
    else:
        metrics["average_difficulty"] = 0.5
        metrics["difficulty_match"] = "unknown"
    
    # Struggling topics (incomplete tasks)
    struggling_topics = []
    for task in incomplete_tasks:
        if task.day_number <= completed_count:  # Should have been done by now
            struggling_topics.append(task.task_text[:50])
    
    metrics["struggling_topics"] = struggling_topics[:5]  # Top 5
    
    logger.debug(f"Calculated metrics: {metrics}")
    
    return metrics