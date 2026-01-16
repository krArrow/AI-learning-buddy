"""
UI Utilities - Helper functions for Streamlit UI
Day 5: Supporting functions for all UI pages
"""

from typing import Optional, Dict, List, Any
import streamlit as st
from datetime import datetime, date, timedelta
import json

from src.core.state import AppState, create_initial_state
from src.database.db import DatabaseManager
from src.database.crud import (
    LearningGoalCRUD, RoadmapCRUD, TaskCRUD, 
    ProgressCRUD, ConversationCRUD, AssessmentCRUD
)
from src.database.models import Task
from src.memory.learning_memory import LearningMemoryManager, get_learning_memory
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_active_goal() -> Optional[Dict[str, Any]]:
    """Get the currently active learning goal"""
    try:
        if st.session_state.active_goal_id:
            with DatabaseManager.get_session_context() as session:
                goal = LearningGoalCRUD.get_by_id(session, st.session_state.active_goal_id)
                if goal:
                    return {
                        "id": goal.id,
                        "goal_text": goal.goal_text,
                        "level": goal.level,
                        "daily_minutes": goal.daily_minutes,
                        "learning_style": goal.learning_style,
                        "pace": goal.pace,
                        "created_at": goal.created_at
                    }
        return None
    except Exception as e:
        logger.error(f"Error getting active goal: {e}")
        return None


def get_latest_goal() -> Optional[Dict[str, Any]]:
    """Get the most recently created goal"""
    try:
        with DatabaseManager.get_session_context() as session:
            goals = LearningGoalCRUD.get_all(session)
            if goals:
                latest = max(goals, key=lambda g: g.created_at)
                return {
                    "id": latest.id,
                    "goal_text": latest.goal_text,
                    "level": latest.level,
                    "daily_minutes": latest.daily_minutes,
                    "learning_style": latest.learning_style,
                    "pace": latest.pace,
                    "created_at": latest.created_at
                }
        return None
    except Exception as e:
        logger.error(f"Error getting latest goal: {e}")
        return None


def get_roadmap(goal_id: int) -> Optional[Dict[str, Any]]:
    """Get roadmap for a goal with proper error handling"""
    try:
        with DatabaseManager.get_session_context() as session:
            roadmap = RoadmapCRUD.get_by_goal_id(session, goal_id)
            if roadmap:
                # Parse roadmap JSON safely
                roadmap_data = roadmap.roadmap_json
                if isinstance(roadmap_data, str):
                    try:
                        roadmap_data = json.loads(roadmap_data)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to parse roadmap JSON for goal {goal_id}: {e}")
                        roadmap_data = {}
                
                # Ensure roadmap_data is a dict
                if not isinstance(roadmap_data, dict):
                    logger.warning(f"Roadmap data is not a dict, got {type(roadmap_data)}")
                    roadmap_data = {}
                
                # Extract modules from the roadmap data
                modules = roadmap_data.get("modules", [])
                if not isinstance(modules, list):
                    logger.warning(f"Modules in roadmap is not a list, got {type(modules)}")
                    modules = []
                
                return {
                    "id": roadmap.id,
                    "modules": modules,
                    "modules_count": roadmap.modules_count or len(modules),
                    "estimated_weeks": roadmap.estimated_weeks or roadmap_data.get("total_weeks", "N/A"),
                    "total_weeks": roadmap_data.get("total_weeks"),
                    "milestones": roadmap_data.get("milestones", []),
                    "created_at": roadmap.created_at
                }
        return None
    except Exception as e:
        logger.error(f"Error getting roadmap for goal {goal_id}: {e}", exc_info=True)
        return None


def get_tasks_for_goal(goal_id: int) -> List[Dict[str, Any]]:
    """Get all tasks for a goal with proper error handling"""
    try:
        with DatabaseManager.get_session_context() as session:
            tasks = TaskCRUD.get_by_goal_id(session, goal_id)
            result = []
            
            for task in tasks:
                try:
                    # Parse resources JSON safely
                    resources = task.resources_json
                    if isinstance(resources, str):
                        try:
                            resources = json.loads(resources)
                        except (json.JSONDecodeError, ValueError):
                            resources = []
                    elif resources is None:
                        resources = []
                    
                    # Ensure resources is a list
                    if not isinstance(resources, list):
                        resources = []
                    
                    result.append({
                        "id": task.id,
                        "day_number": task.day_number,
                        "task_text": task.task_text,
                        "why_text": task.why_text,
                        "resources": resources,
                        "difficulty_score": task.difficulty_score or 5,
                        "estimated_minutes": task.estimated_minutes or 30,
                        "is_completed": task.is_completed or False,
                        "completed_at": task.completed_at,
                        "created_at": task.created_at
                    })
                except Exception as task_error:
                    logger.warning(f"Error processing task {task.id}: {task_error}")
                    continue
            
            return result
    except Exception as e:
        logger.error(f"Error getting tasks for goal {goal_id}: {e}")
        return []


def get_current_task(goal_id: int) -> Optional[Dict[str, Any]]:
    """Get the first incomplete task"""
    tasks = get_tasks_for_goal(goal_id)
    for task in tasks:
        if not task["is_completed"]:
            return task
    return None


def get_completed_tasks_count(goal_id: int) -> int:
    """Get count of completed tasks"""
    tasks = get_tasks_for_goal(goal_id)
    return sum(1 for task in tasks if task["is_completed"])


def get_completion_rate(goal_id: int) -> float:
    """Calculate completion rate as percentage"""
    tasks = get_tasks_for_goal(goal_id)
    if not tasks:
        return 0.0
    completed = sum(1 for task in tasks if task["is_completed"])
    return (completed / len(tasks)) * 100


def mark_task_complete(task_id: int) -> bool:
    """Mark a task as completed"""
    try:
        with DatabaseManager.get_session_context() as session:
            TaskCRUD.mark_completed(session, task_id)
            
            # Update progress record
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                goal_id = task.goal_id
                
                # Get all tasks for this goal
                all_tasks = TaskCRUD.get_by_goal_id(session, goal_id)
                total = len(all_tasks)
                completed = sum(1 for t in all_tasks if t.is_completed)
                completion_pct = (completed / total * 100) if total > 0 else 0
                
                # Create or update progress record for today
                today = date.today()
                ProgressCRUD.create_or_update(
                    session,
                    goal_id=goal_id,
                    progress_date=today,
                    tasks_completed=completed,
                    tasks_total=total
                )
            
            logger.info(f"Task {task_id} marked as completed")
            return True
    except Exception as e:
        logger.error(f"Error marking task complete: {e}")
        return False


def get_performance_metrics(goal_id: int) -> Dict[str, Any]:
    """Get performance metrics for a goal"""
    try:
        memory_manager = LearningMemoryManager()
        metrics = memory_manager.get_performance_summary(goal_id)
        return metrics
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return {
            "completion_rate": 0.0,
            "tasks_completed": 0,
            "tasks_total": 0,
            "average_completion_time": 0,
            "consistency_score": 0,
            "difficulty_match": "unknown"
        }


def get_progress_history(goal_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """Get progress history for the last N days"""
    try:
        with DatabaseManager.get_session_context() as session:
            progress_records = ProgressCRUD.get_by_goal_id(session, goal_id)
            
            # Get last N days
            cutoff_date = date.today() - timedelta(days=days)
            recent = [
                {
                    "date": p.date.strftime("%Y-%m-%d"),
                    "completion_percentage": p.completion_percentage,
                    "tasks_completed": p.tasks_completed,
                    "tasks_total": p.tasks_total
                }
                for p in progress_records
                if p.date >= cutoff_date
            ]
            
            # Sort by date
            recent.sort(key=lambda x: x["date"])
            return recent
    except Exception as e:
        logger.error(f"Error getting progress history: {e}")
        return []


def get_learning_gaps(goal_id: int) -> List[str]:
    """Get identified learning gaps"""
    try:
        with DatabaseManager.get_session_context() as session:
            assessments = AssessmentCRUD.get_by_goal_id(session, goal_id)
            
            gaps = []
            for assessment in assessments:
                if not assessment.is_correct and assessment.gap_identified:
                    gaps.append(assessment.gap_identified)
            
            return list(set(gaps))  # Remove duplicates
    except Exception as e:
        logger.error(f"Error getting learning gaps: {e}")
        return []


def get_current_state() -> AppState:
    """Build current AppState from session and database"""
    try:
        goal = get_active_goal()
        if not goal:
            # Return empty state
            return create_initial_state(
                goal_text="",
                level="beginner",
                daily_minutes=30
            )
        
        # Build state from database
        roadmap = get_roadmap(goal["id"])
        tasks = get_tasks_for_goal(goal["id"])
        metrics = get_performance_metrics(goal["id"])
        
        state = create_initial_state(
            goal_text=goal["goal_text"],
            level=goal["level"],
            daily_minutes=goal["daily_minutes"],
            learning_style=goal.get("learning_style", "visual"),
            pace=goal.get("pace", "medium")
        )
        
        # Update with current data
        state["goal_id"] = goal["id"]
        
        if roadmap:
            state["roadmap"] = roadmap["modules"]
        
        if tasks:
            state["tasks"] = tasks
        
        state["completion_rate"] = metrics.get("completion_rate", 0.0) / 100
        state["performance_metrics"] = metrics
        
        return state
    
    except Exception as e:
        logger.error(f"Error building current state: {e}")
        return create_initial_state("", "beginner", 30)


def run_graph_execution(state: AppState) -> AppState:
    """Execute the compiled graph with current state"""
    try:
        if not st.session_state.graph:
            raise ValueError("Graph not initialized")
        
        logger.info("Executing graph...")
        result = st.session_state.graph.invoke(state)
        logger.info("Graph execution completed")
        
        return result
    
    except Exception as e:
        logger.error(f"Error executing graph: {e}")
        st.error(f"Graph execution failed: {e}")
        return state


def run_adaptation_loop(state: AppState) -> AppState:
    """Run performance analysis and adaptation workflow"""
    try:
        logger.info("Running adaptation loop...")
        
        # Import nodes
        from src.core.nodes.performance_analyzer import performance_analyzer_node
        from src.core.nodes.knowledge_gap_detector import knowledge_gap_detector_node
        from src.core.nodes.task_generator import task_generator_node
        
        # Analyze performance
        state = performance_analyzer_node(state)
        
        # Detect gaps
        state = knowledge_gap_detector_node(state)
        
        # Generate new tasks if needed
        if state.get("adaptations_needed", False):
            state = task_generator_node(state)
        
        logger.info("Adaptation loop completed")
        return state
    
    except Exception as e:
        logger.error(f"Error in adaptation loop: {e}")
        st.error(f"Adaptation failed: {e}")
        return state


def predict_completion_date(goal_id: int) -> str:
    """Predict when the goal will be completed"""
    try:
        tasks = get_tasks_for_goal(goal_id)
        if not tasks:
            return "Unknown"
        
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t["is_completed"])
        
        if completed_tasks == 0:
            return "Not enough data"
        
        # Calculate average tasks per day
        progress_history = get_progress_history(goal_id, days=14)
        if len(progress_history) < 2:
            return "Not enough data"
        
        # Simple prediction based on recent velocity
        recent_days = len(progress_history)
        tasks_per_day = completed_tasks / recent_days
        
        if tasks_per_day == 0:
            return "Unable to predict"
        
        remaining_tasks = total_tasks - completed_tasks
        days_remaining = int(remaining_tasks / tasks_per_day)
        
        completion_date = date.today() + timedelta(days=days_remaining)
        return completion_date.strftime("%B %d, %Y")
    
    except Exception as e:
        logger.error(f"Error predicting completion: {e}")
        return "Unable to predict"


def format_duration(minutes: int) -> str:
    """Format minutes into human-readable duration"""
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours} hr"
    return f"{hours} hr {mins} min"


def get_resource_emoji(resource_type: str) -> str:
    """Get emoji for resource type"""
    emojis = {
        "video": "🎥",
        "article": "📄",
        "course": "📚",
        "documentation": "📖",
        "tutorial": "🎓",
        "book": "📕",
        "tool": "🔧",
        "interactive": "💻"
    }
    return emojis.get(resource_type.lower(), "📌")


def verify_resources_match_goal(goal_text: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verify that resources match the learning goal.
    For debugging purposes to ensure resource matching is working correctly.
    
    Args:
        goal_text: The learning goal text
        resources: List of resources retrieved
        
    Returns:
        Dictionary with verification results
    """
    if not resources:
        return {
            "valid": False,
            "reason": "No resources found",
            "resource_count": 0,
            "goal_text": goal_text[:100]
        }
    
    goal_lower = goal_text.lower()
    
    # Check for matching keywords
    resource_types = [r.get("type", "unknown") for r in resources]
    resource_titles = [r.get("title", "Unknown") for r in resources]
    resource_descriptions = [r.get("description", "") for r in resources]
    
    # Verify resources are relevant
    matches = []
    for i, resource in enumerate(resources):
        title_lower = resource.get("title", "").lower()
        desc_lower = resource.get("description", "").lower()
        
        # Check if resource relates to goal
        goal_keywords = goal_lower.split()
        resource_text = f"{title_lower} {desc_lower}".lower()
        
        keyword_matches = sum(1 for kw in goal_keywords if len(kw) > 2 and kw in resource_text)
        matches.append(keyword_matches > 0)
    
    matching_resources = sum(matches)
    match_percentage = (matching_resources / len(resources) * 100) if resources else 0
    
    result = {
        "valid": match_percentage >= 50,  # At least 50% of resources should match
        "match_percentage": match_percentage,
        "resource_count": len(resources),
        "matching_resources": matching_resources,
        "goal_text": goal_text[:100],
        "resource_types": resource_types,
        "top_resources": [
            f"{r.get('title', 'Unknown')} ({r.get('type', 'unknown')})"
            for r in resources[:3]
        ]
    }
    
    logger.info(f"Resource verification: {result}")
    
    return result