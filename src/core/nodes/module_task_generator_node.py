"""
PHASE 3: Module Task Generator Node
Creates tasks aligned to each module's topics and learning objectives.
"""
import json
from typing import Dict, Any, List
from src.core.state import AppState, Phase
from src.llm.config import get_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)


def module_task_generator_node(state: AppState) -> AppState:
    """
    PHASE 3: Generate tasks for the current module
    
    For the current module:
    - Extract learning objectives from topics
    - Create task types: exercise, quiz, project, reflection
    - Align tasks to available resources
    - Set success criteria and estimated time
    
    This runs after module_curator_node for the same module.
    
    Args:
        state: Current application state with module_resources
        
    Returns:
        Updated state with module_tasks for current module
    """
    logger.info("→ [PHASE 3] module_task_generator_node: Generating module tasks")
    
    try:
        abstract_roadmap = state.get("abstract_roadmap")
        module_resources = state.get("module_resources", {})
        current_module_id = state.get("current_module")
        user_profile = state.get("user_profile", {})
        target_weeks = state.get("target_weeks")
        daily_minutes = user_profile.get("daily_minutes", 30)
        
        if not abstract_roadmap:
            raise ValueError("abstract_roadmap required for task generation")
        if not current_module_id:
            raise ValueError("current_module required for task generation")
        
        modules = abstract_roadmap.get("structure", {}).get("modules", [])
        current_module = next((m for m in modules if m["id"] == current_module_id), None)
        
        if not current_module:
            raise ValueError(f"Module {current_module_id} not found")
        
        logger.info(f"  Generating tasks for: {current_module['title']}")
        
        # Calculate time budget for this module based on timeline
        module_weeks = current_module.get("estimated_weeks", 1)
        module_days = module_weeks * 7
        module_total_minutes = module_days * daily_minutes
        module_total_hours = module_total_minutes / 60
        
        # Build prompt for task generation with time constraints
        system_prompt = f"""You are an expert instructional designer creating learning tasks.

TIME BUDGET CONSTRAINT:
- This module has {module_total_minutes} total minutes ({module_total_hours:.1f} hours) of learning time
- User studies {daily_minutes} minutes per day
- Each task should fit within a single study session ({daily_minutes} mins max per task)
- Total estimated_minutes across all tasks should NOT exceed {module_total_minutes}

Generate tasks as JSON array:
[
    {{
        "id": "task_1_1",
        "title": "Task title",
        "description": "What student does",
        "task_type": "exercise|quiz|project|reflection",
        "difficulty": 0.3,
        "estimated_minutes": 20,
        "learning_objectives": ["objective 1", "objective 2"],
        "success_criteria": "What success looks like",
        "hints": ["hint 1", "hint 2"]
    }}
]

Generate 3-5 tasks per module covering all topics and learning objectives.
Keep estimated_minutes realistic (15-{min(60, daily_minutes)} minutes per task)."""
        
        # Prepare topics info
        topics_info = []
        for topic in current_module.get("topics", []):
            topics_info.append({
                "title": topic.get("title"),
                "objectives": topic.get("learning_objectives", []),
                "subtopics": topic.get("subtopics", [])
            })
        
        # Get resources for this module
        module_res = module_resources.get(current_module_id, [])
        resource_titles = [r.get("title") for r in module_res[:5]]  # Top 5 resources
        
        user_prompt = f"""Create tasks for module: {current_module['title']}

TIME BUDGET: {module_total_minutes} total minutes ({module_total_hours:.1f} hours)
Daily study time: {daily_minutes} minutes

Topics:
{json.dumps(topics_info, indent=2)}

Module difficulty: {current_module.get('difficulty', 0.5)}
User level: {user_profile.get('level', 'beginner')}
Available resources: {', '.join(resource_titles)}

Generate 3-5 tasks that FIT within the time budget. Return JSON array only."""
        
        # Call LLM
        llm = get_llm(temperature=0.4)
        
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        response_text = response.content if hasattr(response, "content") else str(response)
        
        # Parse tasks
        try:
            json_start = response_text.find("[")
            json_end = response_text.rfind("]") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                tasks = json.loads(json_str)
            else:
                tasks = _create_default_tasks(current_module)
                logger.warning("Could not parse tasks JSON, using default")
        
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}, using default tasks")
            tasks = _create_default_tasks(current_module)
        
        # Ensure task IDs are properly formatted
        for i, task in enumerate(tasks):
            if "id" not in task:
                task["id"] = f"{current_module_id}_task_{i+1}"
        
        # Store in state
        if "module_tasks" not in state:
            state["module_tasks"] = {}
        
        state["module_tasks"][current_module_id] = tasks
        state["current_node"] = "module_task_generator_node"
        state["current_phase"] = Phase.CONTENT_POPULATION
        
        logger.info(f"  ✓ module_task_generator_node complete")
        logger.debug(f"    Tasks created: {len(tasks)}")
        
        return state
        
    except Exception as e:
        logger.error(f"✗ module_task_generator_node failed: {str(e)}", exc_info=True)
        state["error"] = f"Task generation failed: {str(e)}"
        state["error_node"] = "module_task_generator_node"
        return state


def _create_default_tasks(module: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create default tasks if LLM generation fails."""
    module_id = module["id"]
    module_diff = module.get("difficulty", 0.5)
    
    topics = module.get("topics", [])
    topic_titles = [t.get("title", "Topic") for t in topics[:2]]
    
    return [
        {
            "id": f"{module_id}_task_1",
            "title": f"Learn {topic_titles[0] if topic_titles else 'core concepts'}",
            "description": f"Study the topic and take notes on key points",
            "task_type": "exercise",
            "difficulty": max(0.1, module_diff - 0.2),
            "estimated_minutes": 30,
            "learning_objectives": ["Understand core concepts"],
            "success_criteria": "Complete and submit notes",
            "hints": ["Focus on definitions", "Create a mind map"]
        },
        {
            "id": f"{module_id}_task_2",
            "title": "Practice exercises",
            "description": "Complete guided practice problems",
            "task_type": "exercise",
            "difficulty": module_diff,
            "estimated_minutes": 45,
            "learning_objectives": ["Apply concepts", "Build fluency"],
            "success_criteria": "80% correct on attempts",
            "hints": ["Start with easier examples", "Use provided solutions as guidance"]
        },
        {
            "id": f"{module_id}_task_3",
            "title": "Module quiz",
            "description": "Assess understanding with a short quiz",
            "task_type": "quiz",
            "difficulty": module_diff,
            "estimated_minutes": 15,
            "learning_objectives": ["Demonstrate mastery"],
            "success_criteria": "Score 80% or higher",
            "hints": ["Review key concepts", "Check your work before submitting"]
        }
    ]
