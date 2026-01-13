"""
Knowledge Gap Detector Node - Identifies learning gaps from assessments and progress.
"""
import time
from typing import List

from src.core.state import AppState
from src.database import db_manager, AssessmentCRUD, TaskCRUD
from src.utils.logger import get_logger

logger = get_logger(__name__)


def knowledge_gap_detector_node(state: AppState) -> AppState:
    """
    Detect knowledge gaps through assessment analysis.
    
    This node:
    - Analyzes failed assessments
    - Identifies skipped tasks
    - Detects rushed completions
    - Finds incomplete modules
    - Sets adaptation flags
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with gaps_identified and adaptations_needed
    """
    start_time = time.time()
    node_name = "knowledge_gap_detector"
    state["current_node"] = node_name
    
    logger.info(f"[{node_name}] Starting knowledge gap detection")
    
    try:
        goal_id = state.get("goal_id")
        if not goal_id:
            logger.warning(f"[{node_name}] No goal_id, skipping gap detection")
            state["gaps_identified"] = []
            state["adaptations_needed"] = False
            return state
        
        gaps = []
        
        # Analyze assessments
        with db_manager.get_session_context() as session:
            assessments = AssessmentCRUD.get_by_goal_id(session, goal_id)
            
            for assessment in assessments:
                if assessment.is_correct is False:
                    gap = assessment.gap_identified
                    if gap and gap not in gaps:
                        gaps.append(gap)
                        logger.debug(f"[{node_name}] Gap identified from assessment: {gap}")
            
            # Analyze skipped tasks
            all_tasks = TaskCRUD.get_by_goal_id(session, goal_id)
            incomplete_tasks = TaskCRUD.get_incomplete_tasks(session, goal_id)
            
            completion_rate = state.get("completion_rate", 1.0)
            
            # If many tasks are skipped, that's a gap
            if len(incomplete_tasks) > len(all_tasks) * 0.3:  # >30% incomplete
                gaps.append("task_completion_issues")
                logger.debug(f"[{node_name}] Gap: Many tasks incomplete")
            
            # Analyze rushed completions (completed too quickly)
            rushed_count = 0
            for task in all_tasks:
                if task.is_completed and task.completion_time_minutes:
                    if task.estimated_minutes and task.completion_time_minutes < task.estimated_minutes * 0.5:
                        rushed_count += 1
            
            if rushed_count > len(all_tasks) * 0.2:  # >20% rushed
                gaps.append("rushed_learning")
                logger.debug(f"[{node_name}] Gap: Many tasks rushed")
        
        # Check performance metrics for additional gaps
        performance_metrics = state.get("performance_metrics", {})
        
        if performance_metrics.get("difficulty_match") == "too_hard":
            gaps.append("difficulty_too_high")
            logger.debug(f"[{node_name}] Gap: Difficulty too high")
        
        if performance_metrics.get("consistency_score", 1.0) < 0.5:
            gaps.append("inconsistent_practice")
            logger.debug(f"[{node_name}] Gap: Inconsistent practice")
        
        # Add struggling topics from performance analysis
        struggling_topics = performance_metrics.get("struggling_topics", [])
        for topic in struggling_topics[:3]:  # Top 3
            gaps.append(f"struggling_with:{topic}")
        
        # Update state
        state["gaps_identified"] = gaps
        state["adaptations_needed"] = len(gaps) >= 2  # Adapt if 2+ gaps
        
        logger.info(
            f"[{node_name}] Detected {len(gaps)} gaps. "
            f"Adaptations needed: {state['adaptations_needed']}"
        )
        
        if gaps:
            logger.info(f"[{node_name}] Gaps: {', '.join(gaps[:5])}")
        
        # Track execution time
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        logger.info(f"[{node_name}] Gap detection complete in {elapsed:.2f}s")
        
        return state
        
    except Exception as e:
        logger.error(f"[{node_name}] Error detecting gaps: {e}", exc_info=True)
        state["error"] = f"Gap detection failed: {str(e)}"
        state["gaps_identified"] = []
        state["adaptations_needed"] = False
        
        # Track execution time
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        return state