"""
Roadmap Generator Node - Creates structured learning roadmap with LLM.
"""
import json
import time
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.state import AppState
from src.llm.config import invoke_llm
from src.tools.validators import validate_roadmap
from src.database import db_manager, RoadmapCRUD
from src.utils.logger import get_logger

logger = get_logger(__name__)


ROADMAP_GENERATION_PROMPT = """You are an expert learning path designer. Create a personalized learning roadmap.

Given:
- Goal: {goal_text}
- Level: {level}
- Daily time: {daily_minutes} minutes
- Learning style: {learning_style}
- Pace: {pace}

Create a roadmap with 4-5 modules that:
- Progressively builds skills
- Matches the user's pace and time availability
- Adapts to their learning style
- Includes clear objectives

Return ONLY valid JSON in this exact format:
{{
    "modules": [
        {{
            "id": 1,
            "title": "Module Title",
            "description": "What this module covers",
            "estimated_weeks": 2,
            "topics": ["topic1", "topic2", "topic3"]
        }}
    ],
    "total_weeks": 10,
    "milestones": [
        {{"week": 2, "milestone": "Complete basics"}},
        {{"week": 5, "milestone": "Build first project"}}
    ]
}}

No preamble, just JSON."""


def roadmap_generator_node(state: AppState) -> AppState:
    """
    Generate a structured learning roadmap based on goal and preferences.
    
    This node:
    - Uses LLM to create personalized roadmap
    - Breaks goal into 4-5 progressive modules
    - Estimates timelines
    - Stores roadmap in database
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with roadmap populated
    """
    start_time = time.time()
    node_name = "roadmap_generator"
    state["current_node"] = node_name
    
    logger.info(f"[{node_name}] Starting roadmap generation")
    
    try:
        # Extract parameters
        goal_text = state.get("goal_text", "")
        level = state.get("level", "beginner")
        daily_minutes = state.get("daily_minutes", 30)
        learning_style = state.get("learning_style", "visual")
        pace = state.get("pace", "medium")
        
        logger.info(
            f"[{node_name}] Generating roadmap for: {goal_text[:50]}... "
            f"(level={level}, style={learning_style}, pace={pace})"
        )
        
        # Prepare prompt
        prompt = ROADMAP_GENERATION_PROMPT.format(
            goal_text=goal_text,
            level=level,
            daily_minutes=daily_minutes,
            learning_style=learning_style,
            pace=pace
        )
        
        messages = [
            SystemMessage(content="You are a learning path expert. Return only valid JSON."),
            HumanMessage(content=prompt)
        ]
        
        # Generate roadmap with LLM
        logger.debug(f"[{node_name}] Invoking LLM for roadmap generation")
        response = invoke_llm(messages, temperature=0.7, max_tokens=2000)
        response_text = response.content
        
        # Parse JSON
        roadmap = _extract_json(response_text)
        
        if not roadmap:
            raise ValueError("Failed to parse roadmap JSON from LLM response")
        
        # Validate roadmap structure
        is_valid, error = validate_roadmap(roadmap)
        if not is_valid:
            raise ValueError(f"Invalid roadmap structure: {error}")
        
        logger.info(
            f"[{node_name}] Generated roadmap with {len(roadmap['modules'])} modules, "
            f"{roadmap['total_weeks']} weeks"
        )
        
        # Store in database if goal_id exists
        if state.get("goal_id"):
            try:
                with db_manager.get_session_context() as session:
                    RoadmapCRUD.create(
                        session=session,
                        goal_id=state["goal_id"],
                        roadmap_json=json.dumps(roadmap),
                        modules_count=len(roadmap["modules"]),
                        estimated_weeks=roadmap["total_weeks"]
                    )
                    logger.info(f"[{node_name}] Roadmap stored in database")
            except Exception as db_error:
                logger.warning(f"[{node_name}] Failed to store roadmap in DB: {db_error}")
        
        # Update state
        state["roadmap"] = roadmap
        
        # Track execution time
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        logger.info(f"[{node_name}] Roadmap generation complete in {elapsed:.2f}s")
        
        return state
        
    except Exception as e:
        logger.error(f"[{node_name}] Error generating roadmap: {e}", exc_info=True)
        state["error"] = f"Roadmap generation failed: {str(e)}"
        
        # Use fallback roadmap
        state["roadmap"] = _create_fallback_roadmap(state)
        
        # Track execution time
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        return state


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response."""
    try:
        # Find JSON in text
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx]
            return json.loads(json_str)
        
        return None
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {e}")
        return None


def _create_fallback_roadmap(state: AppState) -> Dict[str, Any]:
    """Create a simple fallback roadmap if LLM fails."""
    logger.warning("Creating fallback roadmap")
    
    return {
        "modules": [
            {
                "id": 1,
                "title": "Fundamentals",
                "description": "Core concepts and basics",
                "estimated_weeks": 2,
                "topics": ["Introduction", "Basic Concepts", "Practice"]
            },
            {
                "id": 2,
                "title": "Intermediate Skills",
                "description": "Building on the basics",
                "estimated_weeks": 3,
                "topics": ["Advanced Topics", "Real Projects", "Best Practices"]
            }
        ],
        "total_weeks": 5,
        "milestones": [
            {"week": 2, "milestone": "Complete fundamentals"},
            {"week": 5, "milestone": "Build first project"}
        ]
    }