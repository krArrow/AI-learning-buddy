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
    """Get roadmap for a goal with proper error handling. Supports both old and new structures."""
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
                
                # Handle new 4-phase flow structure (populated_roadmap)
                if "structure" in roadmap_data:
                    # New structure: populated_roadmap with structure.modules
                    modules = roadmap_data.get("structure", {}).get("modules", [])
                else:
                    # Old structure: direct modules list
                    modules = roadmap_data.get("modules", [])
                
                if not isinstance(modules, list):
                    logger.warning(f"Modules in roadmap is not a list, got {type(modules)}")
                    modules = []
                
                return {
                    "id": roadmap.id,
                    "modules": modules,
                    "modules_count": roadmap.modules_count or len(modules),
                    "estimated_weeks": roadmap.estimated_weeks or roadmap_data.get("total_weeks", roadmap_data.get("total_estimated_weeks", "N/A")),
                    "total_weeks": roadmap_data.get("total_weeks") or roadmap_data.get("total_estimated_weeks"),
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
        tasks = get_tasks_for_goal(goal_id)
        
        if not tasks:
            return {
                "completion_rate": 0.0,
                "tasks_completed": 0,
                "tasks_total": 0,
                "average_completion_time": 0,
                "min_completion_time": 0,
                "max_completion_time": 0,
                "consistency_score": 0,
                "average_difficulty": 5.0,
                "difficulty_match": "unknown"
            }
        
        # Calculate metrics from actual tasks
        completed_tasks = [t for t in tasks if t.get("is_completed")]
        total_tasks = len(tasks)
        completed_count = len(completed_tasks)
        
        # Completion rate
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Time metrics (using estimated_minutes as proxy for actual time)
        if completed_tasks:
            times = [t.get("estimated_minutes", 30) for t in completed_tasks]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
        else:
            avg_time = 0
            min_time = 0
            max_time = 0
        
        # Difficulty metrics
        all_difficulties = [t.get("difficulty_score", 5) for t in tasks]
        avg_difficulty = sum(all_difficulties) / len(all_difficulties) if all_difficulties else 5.0
        
        # Determine difficulty match
        if avg_difficulty < 4:
            difficulty_match = "too_easy"
        elif avg_difficulty > 7:
            difficulty_match = "too_hard"
        else:
            difficulty_match = "appropriate"
        
        # Consistency score (based on completion pattern)
        # Simple heuristic: completed_count / total_tasks
        consistency_score = completion_rate / 100.0 if total_tasks > 0 else 0.0
        
        return {
            "completion_rate": completion_rate,
            "tasks_completed": completed_count,
            "tasks_total": total_tasks,
            "average_completion_time": avg_time,
            "min_completion_time": min_time,
            "max_completion_time": max_time,
            "consistency_score": consistency_score,
            "average_difficulty": avg_difficulty,
            "difficulty_match": difficulty_match
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}", exc_info=True)
        return {
            "completion_rate": 0.0,
            "tasks_completed": 0,
            "tasks_total": 0,
            "average_completion_time": 0,
            "min_completion_time": 0,
            "max_completion_time": 0,
            "consistency_score": 0,
            "average_difficulty": 5.0,
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
            # Get the full roadmap structure
            modules = roadmap.get("modules", [])
            
            # Determine structure type and store appropriately
            if modules and "resources" in modules[0]:
                # New 4-phase structure with populated_roadmap
                state["populated_roadmap"] = {
                    "structure": {"modules": modules},
                    "milestones": roadmap.get("milestones", []),
                    "total_estimated_weeks": roadmap.get("total_weeks") or roadmap.get("estimated_weeks"),
                    "content_status": "populated"
                }
            
            # Also keep backward compatible field
            state["abstract_roadmap"] = {
                "structure": {"modules": modules},
                "total_estimated_weeks": roadmap.get("total_weeks") or roadmap.get("estimated_weeks")
            }
        
        if tasks:
            state["completed_tasks"] = [t["id"] for t in tasks if t["is_completed"]]
            
            # Build task_completion_details from tasks
            task_details = {}
            for task in tasks:
                if task["is_completed"] and task["completed_at"]:
                    task_details[task["id"]] = {
                        "completed_at": task["completed_at"].isoformat() if hasattr(task["completed_at"], "isoformat") else str(task["completed_at"]),
                        "time_spent_minutes": task.get("estimated_minutes", 30),
                        "difficulty_reported": 0.5,
                        "performance_score": 0.85,
                        "feedback": "Completed",
                        "revision_count": 1
                    }
            
            state["task_completion_details"] = task_details
        
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
    """Run performance analysis and adaptation workflow using 4-phase nodes"""
    try:
        logger.info("Running adaptation loop (4-phase)...")
        
        # Import 4-phase nodes
        from src.core.nodes.progress_tracker_node import progress_tracker_node
        from src.core.nodes.adaptive_controller_node import adaptive_controller_node
        from src.core.nodes.replanning_trigger_node import replanning_trigger_node
        from src.core.nodes.module_curator_node import module_curator_node
        from src.core.nodes.module_task_generator_node import module_task_generator_node
        from src.core.nodes.content_aggregator_node import content_aggregator_node
        
        # Phase 4: Track progress
        state = progress_tracker_node(state)
        
        # Phase 4: Analyze for adaptations
        state = adaptive_controller_node(state)
        
        # Phase 4: Check if replanning needed
        state = replanning_trigger_node(state)
        
        # If re-curation triggered, re-curate the struggling module
        if state.get("re_curation_triggered") and state.get("struggling_module_id"):
            logger.info(f"Re-curating module: {state['struggling_module_id']}")
            
            # Mark module for re-curation
            module_status = state.get("module_curation_status", {})
            module_status[state["struggling_module_id"]] = "pending"
            state["module_curation_status"] = module_status
            state["current_module"] = state["struggling_module_id"]
            
            # Re-curate and regenerate tasks
            state = module_curator_node(state)
            state = module_task_generator_node(state)
            state = content_aggregator_node(state)
            
            # Reset trigger
            state["re_curation_triggered"] = False
        
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

def save_graph_output_to_db(state: AppState) -> int:
    """
    Save the graph execution results to database.
    
    Saves:
    - LearningGoal (if new)
    - Roadmap from populated_roadmap
    - Tasks from module_tasks
    
    Args:
        state: Final state from graph execution
        
    Returns:
        goal_id: The created or updated goal ID
        
    Raises:
        ValueError: If required state fields are missing
    """
    try:
        if not state.get("goal_text"):
            raise ValueError("goal_text required in state")
        
        with DatabaseManager.get_session_context() as session:
            # 1. Create or get learning goal
            goal_id = state.get("goal_id")
            
            if not goal_id:
                # Create new goal
                goal = LearningGoalCRUD.create(
                    session=session,
                    goal_text=state.get("original_goal_text") or state.get("goal_text"),
                    level=state.get("user_profile", {}).get("level", "beginner"),
                    daily_minutes=state.get("user_profile", {}).get("daily_minutes", 30),
                    learning_style=state.get("user_profile", {}).get("learning_style", "visual"),
                    pace=state.get("user_profile", {}).get("pace", "medium"),
                    preferences=state.get("user_profile", {}).get("preferences", {}),
                    target_completion_days=state.get("target_completion_days"),
                    target_display_text=state.get("target_display")
                )
                goal_id = goal.id
                logger.info(f"Created new goal: {goal_id}")
            else:
                goal = LearningGoalCRUD.get_by_id(session, goal_id)
                logger.info(f"Using existing goal: {goal_id}")
            
            # 2. Save roadmap from populated_roadmap
            populated_roadmap = state.get("populated_roadmap")
            
            if populated_roadmap:
                modules = populated_roadmap.get("structure", {}).get("modules", [])
                modules_count = len(modules)
                total_weeks = populated_roadmap.get("total_estimated_weeks", 8)
                
                # Create roadmap record
                roadmap = RoadmapCRUD.create(
                    session=session,
                    goal_id=goal_id,
                    roadmap_json=populated_roadmap,
                    modules_count=modules_count,
                    estimated_weeks=total_weeks
                )
                logger.info(f"Created roadmap: {roadmap.id} with {modules_count} modules")
            
            # 3. Save tasks from module_tasks
            module_tasks = state.get("module_tasks", {})
            day_number = 1
            
            for module_id, tasks in module_tasks.items():
                for task in tasks:
                    TaskCRUD.create(
                        session=session,
                        goal_id=goal_id,
                        day_number=day_number,
                        task_text=task.get("title", "Task"),
                        why_text=task.get("description", ""),
                        estimated_minutes=task.get("estimated_minutes", 30),
                        difficulty_score=task.get("difficulty", 0.5),
                        resources_json=task.get("resources_used", [])
                    )
                    day_number += 1
            
            logger.info(f"Saved {day_number - 1} tasks for goal {goal_id}")
            
            return goal_id
    
    except Exception as e:
        logger.error(f"Error saving graph output to database: {e}", exc_info=True)
        raise


def convert_module_tasks_to_display_format(state: AppState) -> List[Dict[str, Any]]:
    """
    Convert module_tasks structure to flat, displayable format.
    
    Transforms:
        {mod_1: [{id, title, description}], mod_2: [{...}]}
    To:
        [{module_id, module_title, day, task_id, title, description, ...}, ...]
    
    Args:
        state: Application state with module_tasks and abstract_roadmap
        
    Returns:
        List of task dictionaries with module context
    """
    try:
        module_tasks = state.get("module_tasks", {})
        abstract_roadmap = state.get("abstract_roadmap", {})
        populated_roadmap = state.get("populated_roadmap", {})
        
        # Get module info
        modules = {}
        
        # Try populated_roadmap first (has resources)
        if populated_roadmap:
            for mod in populated_roadmap.get("structure", {}).get("modules", []):
                modules[mod["id"]] = mod
        
        # Fall back to abstract_roadmap
        if not modules and abstract_roadmap:
            for mod in abstract_roadmap.get("structure", {}).get("modules", []):
                modules[mod["id"]] = mod
        
        # Convert to flat list
        result = []
        day_number = 1
        
        for module_id in sorted(module_tasks.keys()):
            tasks = module_tasks[module_id]
            module_info = modules.get(module_id, {})
            
            for task in tasks:
                result.append({
                    "module_id": module_id,
                    "module_title": module_info.get("title", "Module"),
                    "day_number": day_number,
                    "task_id": task.get("id"),
                    "task_title": task.get("title", "Task"),
                    "task_description": task.get("description", ""),
                    "task_type": task.get("task_type", "exercise"),
                    "difficulty": task.get("difficulty", 0.5),
                    "estimated_minutes": task.get("estimated_minutes", 30),
                    "learning_objectives": task.get("learning_objectives", []),
                    "success_criteria": task.get("success_criteria", ""),
                    "hints": task.get("hints", [])
                })
                day_number += 1
        
        return result
    
    except Exception as e:
        logger.error(f"Error converting module tasks: {e}")
        return []


def get_current_module_tasks(state: AppState) -> List[Dict[str, Any]]:
    """
    Get tasks for the currently active module.
    
    Args:
        state: Application state with current_module and module_tasks
        
    Returns:
        List of tasks for the current module
    """
    try:
        current_module = state.get("current_module")
        module_tasks = state.get("module_tasks", {})
        
        if not current_module:
            return []
        
        tasks = module_tasks.get(current_module, [])
        return tasks
    
    except Exception as e:
        logger.error(f"Error getting current module tasks: {e}")
        return []


def update_task_completion_in_state(
    state: AppState,
    task_id: str,
    time_spent_minutes: int,
    difficulty_reported: float,
    performance_score: float = 0.85
) -> AppState:
    """
    Update state when user completes a task.
    
    Updates:
    - completed_tasks list
    - task_completion_details dictionary
    - Recalculates performance_metrics
    
    Args:
        state: Current application state
        task_id: ID of completed task
        time_spent_minutes: How long task took
        difficulty_reported: User's perceived difficulty (0-1)
        performance_score: User's performance (0-1)
        
    Returns:
        Updated state
    """
    try:
        # Add to completed tasks
        completed = state.get("completed_tasks", [])
        if task_id not in completed:
            completed.append(task_id)
            state["completed_tasks"] = completed
        
        # Record completion details
        task_details = state.get("task_completion_details", {})
        task_details[task_id] = {
            "completed_at": datetime.utcnow().isoformat(),
            "time_spent_minutes": time_spent_minutes,
            "difficulty_reported": difficulty_reported,
            "performance_score": performance_score,
            "feedback": "Task completed",
            "revision_count": 1
        }
        state["task_completion_details"] = task_details
        
        # Recalculate metrics
        state = _recalculate_performance_metrics(state)
        
        logger.info(f"Task {task_id} marked complete in state")
        return state
    
    except Exception as e:
        logger.error(f"Error updating task completion: {e}")
        return state


def _recalculate_performance_metrics(state: AppState) -> AppState:
    """Recalculate performance metrics from task_completion_details."""
    try:
        task_details = state.get("task_completion_details", {})
        
        if not task_details:
            state["performance_metrics"] = {}
            return state
        
        # Calculate metrics
        times = [d.get("time_spent_minutes", 0) for d in task_details.values()]
        difficulties = [d.get("difficulty_reported", 0.5) for d in task_details.values()]
        performances = [d.get("performance_score", 0.8) for d in task_details.values()]
        
        metrics = {
            "total_time_spent_minutes": sum(times),
            "avg_time_per_task": sum(times) / len(times) if times else 0,
            "avg_difficulty_reported": sum(difficulties) / len(difficulties) if difficulties else 0.5,
            "avg_performance_score": sum(performances) / len(performances) if performances else 0.8,
            "completion_velocity": len(task_details) / max(1, sum(times) / 60),  # tasks per hour
            "consistency_score": min(1.0, sum(performances) / len(performances) if performances else 0.8),
            "tasks_completed": len(task_details)
        }
        
        state["performance_metrics"] = metrics
        
        return state
    
    except Exception as e:
        logger.error(f"Error recalculating metrics: {e}")
        return state