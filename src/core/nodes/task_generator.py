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
        
        # Attach resources from state with smart matching
        resources = state.get("resources", [])
        if resources:
            logger.debug(f"[{node_name}] Attaching {len(resources)} resources to {len(tasks)} tasks")
            
            for i, task in enumerate(tasks):
                task_text = task.get("task", "").lower()
                task_resources = []
                
                # Strategy: Match resources to task content intelligently
                # 1. Score each resource by relevance to this task
                scored_resources = []
                for resource in resources:
                    relevance_score = 0.0
                    
                    # Check if resource title/description matches task keywords
                    resource_title = resource.get("title", "").lower()
                    resource_desc = resource.get("description", "").lower()
                    resource_text = f"{resource_title} {resource_desc}"
                    
                    # Extract key words from task (ignoring common words)
                    task_words = set(word for word in task_text.split() 
                                   if len(word) > 3 and word not in ["with", "this", "that", "from", "your", "the", "and"])
                    
                    # Count word matches
                    matches = sum(1 for word in task_words if word in resource_text)
                    relevance_score = matches / max(len(task_words), 1)
                    
                    # Consider difficulty match (early tasks should have easier resources)
                    task_difficulty = task.get("difficulty", 0.5)
                    resource_difficulty = resource.get("difficulty", 0.5)
                    difficulty_diff = abs(task_difficulty - resource_difficulty)
                    difficulty_score = 1.0 - difficulty_diff
                    
                    # Combined score (70% relevance, 30% difficulty match)
                    combined_score = 0.7 * relevance_score + 0.3 * difficulty_score
                    
                    scored_resources.append({
                        "resource": resource,
                        "score": combined_score
                    })
                
                # Sort by score and take top 2-3
                scored_resources.sort(key=lambda x: x["score"], reverse=True)
                
                # Take top resources, but ensure variety by not taking same resource for all tasks
                num_resources = min(2, len(resources))
                for j in range(num_resources):
                    # Use round-robin with scoring to ensure variety
                    idx = (i + j) % len(scored_resources)
                    task_resources.append(scored_resources[idx]["resource"])
                
                task["resources"] = task_resources
                logger.debug(
                    f"[{node_name}] Task {i+1} ('{task_text[:40]}...'): "
                    f"Attached {len(task_resources)} resources with avg score "
                    f"{sum(sr['score'] for sr in scored_resources[:num_resources])/max(num_resources,1):.2f}"
                )
        else:
            logger.warning(f"[{node_name}] No resources found in state to attach to tasks")
            for task in tasks:
                task["resources"] = []
        
        # Validate tasks
        is_valid, error = validate_tasks(tasks)
        if not is_valid:
            raise ValueError(f"Invalid tasks structure: {error}")
        
        # Validate time estimates against daily_minutes budget
        for task in tasks:
            task_minutes = task.get("estimated_minutes", 30)
            if task_minutes > daily_minutes:
                logger.warning(
                    f"[{node_name}] Task {task['day']} exceeds daily budget "
                    f"({task_minutes} > {daily_minutes}). Adjusting to {daily_minutes}."
                )
                task["estimated_minutes"] = daily_minutes
            elif task_minutes < 10:
                logger.warning(
                    f"[{node_name}] Task {task['day']} has very low time estimate "
                    f"({task_minutes} min). Adjusting to minimum 10 minutes."
                )
                task["estimated_minutes"] = 10
        
        logger.info(f"[{node_name}] Generated {len(tasks)} tasks with resources and validated time estimates")
        
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
