"""
Task Generator Node - Creates daily learning tasks with LLM.
"""
import json
import time
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.state import AppState
from src.llm.config import invoke_llm
from src.tools.validators import validate_tasks
from src.tools.difficulty_scorer import score_difficulty
from src.database import db_manager, TaskCRUD
from src.utils.logger import get_logger

logger = get_logger(__name__)


TASK_GENERATION_PROMPT = """You are an expert learning task designer. Create 7 daily learning tasks.

Given:
- Module: {module_title}
- Topics: {topics}
- Level: {level}
- Daily time: {daily_minutes} minutes
- Learning style: {learning_style}

Create 7 progressive daily tasks that:
- Build on each other logically
- Match the daily time limit
- Suit the learning style
- Include clear "why" explanations
- Are actionable and specific

Return ONLY valid JSON array:
[
    {{
        "day": 1,
        "task": "Specific task description",
        "why": "Why this task is important",
        "estimated_minutes": 30,
        "difficulty": 0.3,
        "resources": []
    }}
]

No preamble, just the JSON array."""


def task_generator_node(state: AppState) -> AppState:
    """
    Generate daily learning tasks from roadmap.
    
    This node:
    - Takes first module from roadmap
    - Generates 7 daily tasks using LLM
    - Scores difficulty for each task
    - Attaches resources from state
    - Stores tasks in database
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with tasks list populated
    """
    start_time = time.time()
    node_name = "task_generator"
    state["current_node"] = node_name
    
    logger.info(f"[{node_name}] Starting task generation")
    
    try:
        # Extract parameters
        roadmap = state.get("roadmap")
        if not roadmap or not roadmap.get("modules"):
            raise ValueError("No roadmap available for task generation")
        
        # Use first module
        first_module = roadmap["modules"][0]
        module_title = first_module["title"]
        topics = first_module["topics"]
        
        level = state.get("level", "beginner")
        daily_minutes = state.get("daily_minutes", 30)
        learning_style = state.get("learning_style", "visual")
        
        logger.info(
            f"[{node_name}] Generating tasks for module: {module_title} "
            f"(topics: {len(topics)})"
        )
        
        # Prepare prompt
        prompt = TASK_GENERATION_PROMPT.format(
            module_title=module_title,
            topics=", ".join(topics),
            level=level,
            daily_minutes=daily_minutes,
            learning_style=learning_style
        )
        
        messages = [
            SystemMessage(content="You are a task design expert. Return only valid JSON array."),
            HumanMessage(content=prompt)
        ]
        
        # Generate tasks with LLM
        logger.debug(f"[{node_name}] Invoking LLM for task generation")
        response = invoke_llm(messages, temperature=0.8, max_tokens=2000)
        response_text = response.content
        
        # Parse JSON
        tasks = _extract_json_array(response_text)
        
        if not tasks:
            raise ValueError("Failed to parse tasks JSON from LLM response")
        
        # Score difficulty for each task
        for task in tasks:
            if "difficulty" not in task or task["difficulty"] == 0:
                difficulty = score_difficulty(
                    task["task"],
                    user_level=level
                )
                task["difficulty"] = difficulty
        
        # Attach resources from state
        resources = state.get("resources", [])
        if resources:
            logger.debug(f"[{node_name}] Attaching {len(resources)} resources to {len(tasks)} tasks")
            for i, task in enumerate(tasks):
                # Distribute resources across tasks (rotate them)
                # This ensures different resources for different days
                resource_start = (i * 2) % len(resources)
                task_resources = []
                
                # Get 2-3 resources, cycling through the list
                for j in range(2):
                    resource_idx = (resource_start + j) % len(resources)
                    task_resources.append(resources[resource_idx])
                
                task["resources"] = task_resources
                logger.debug(f"[{node_name}] Task {i+1}: Attached {len(task_resources)} resources")
        else:
            logger.warning(f"[{node_name}] No resources found in state to attach to tasks")
            for task in tasks:
                task["resources"] = []
        
        # Validate tasks
        is_valid, error = validate_tasks(tasks)
        if not is_valid:
            raise ValueError(f"Invalid tasks structure: {error}")
        
        logger.info(f"[{node_name}] Generated {len(tasks)} tasks with resources")
        
        # Store in database if goal_id exists
        if state.get("goal_id"):
            try:
                with db_manager.get_session_context() as session:
                    for task in tasks:
                        task_resources = task.get("resources", [])
                        logger.debug(f"[{node_name}] Storing task '{task['task'][:50]}...' with {len(task_resources)} resources")
                        TaskCRUD.create(
                            session=session,
                            goal_id=state["goal_id"],
                            day_number=task["day"],
                            task_text=task["task"],
                            why_text=task.get("why", ""),
                            estimated_minutes=task["estimated_minutes"],
                            resources_json=task_resources,
                            difficulty_score=task["difficulty"]
                        )
                    logger.info(f"[{node_name}] Tasks stored in database")
            except Exception as db_error:
                logger.warning(f"[{node_name}] Failed to store tasks in DB: {db_error}")
        
        # Update state
        state["tasks"] = tasks
        
        # Track execution time
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        logger.info(f"[{node_name}] Task generation complete in {elapsed:.2f}s")
        
        return state
        
    except Exception as e:
        logger.error(f"[{node_name}] Error generating tasks: {e}", exc_info=True)
        state["error"] = f"Task generation failed: {str(e)}"
        
        # Use fallback tasks
        state["tasks"] = _create_fallback_tasks(state)
        
        # Track execution time
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        return state


def _extract_json_array(text: str) -> List[Dict[str, Any]]:
    """Extract JSON array from LLM response."""
    try:
        # Find JSON array in text
        start_idx = text.find("[")
        end_idx = text.rfind("]") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx]
            return json.loads(json_str)
        
        return None
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {e}")
        return None


def _create_fallback_tasks(state: AppState) -> List[Dict[str, Any]]:
    """Create simple fallback tasks if LLM fails."""
    logger.warning("Creating fallback tasks")
    
    daily_minutes = state.get("daily_minutes", 30)
    
    return [
        {
            "day": 1,
            "task": "Get familiar with the basics and setup environment",
            "why": "Building a strong foundation is essential",
            "resources": [],
            "estimated_minutes": daily_minutes,
            "difficulty": 0.2
        },
        {
            "day": 2,
            "task": "Practice fundamental concepts",
            "why": "Hands-on practice reinforces learning",
            "resources": [],
            "estimated_minutes": daily_minutes,
            "difficulty": 0.3
        },
        {
            "day": 3,
            "task": "Build your first small project",
            "why": "Applying knowledge helps retention",
            "resources": [],
            "estimated_minutes": daily_minutes,
            "difficulty": 0.5
        }
    ]