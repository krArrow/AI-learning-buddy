"""
PHASE 1: Domain Analyzer Node
Analyzes the learning domain to extract prerequisites, dependencies, and complexity.
"""
import json
from src.core.state import AppState
from src.llm.config import get_llm, invoke_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)


def domain_analyzer_node(state: AppState) -> AppState:
    """
    PHASE 1: Domain Analysis - Extract domain structure
    
    Uses LLM to analyze:
    - Prerequisites and foundational knowledge needed
    - Topic dependencies and learning order
    - Complexity estimate
    - Core competencies to master
    
    Args:
        state: Current application state with goal_analysis
        
    Returns:
        Updated state with domain_analysis
    """
    logger.info("→ [PHASE 1] domain_analyzer_node: Analyzing domain structure")
    
    try:
        goal_text = state.get("goal_text", "")
        goal_analysis = state.get("goal_analysis", {})
        user_profile = state.get("user_profile", {})
        target_completion_days = state.get("target_completion_days")
        target_weeks = state.get("target_weeks")
        
        if not goal_text:
            raise ValueError("goal_text is required for domain analysis")
        
        # Calculate available learning hours for timeline constraint
        daily_minutes = user_profile.get('daily_minutes', 30)
        if target_completion_days:
            total_available_hours = (daily_minutes * target_completion_days) / 60
            timeline_constraint = f"""
IMPORTANT TIMELINE CONSTRAINT:
- User wants to complete in: {target_completion_days} days ({target_weeks} weeks)
- Daily study time: {daily_minutes} minutes
- Total available learning hours: {total_available_hours:.0f} hours
- You MUST fit the curriculum within this timeline
- Adjust complexity and scope to match available time"""
        else:
            timeline_constraint = ""
        
        # Prepare prompt for LLM
        system_prompt = """You are an expert curriculum designer analyzing learning domains.
        
        Given a learning goal, analyze and return a JSON object with:
        {
            "prerequisites": ["skill1", "skill2"],
            "dependencies": {"advanced_topic": ["basic_topic1", "basic_topic2"]},
            "complexity_estimate": 0.5,  # 0-1 scale
            "estimated_weeks": 12,
            "core_competencies": ["competency1", "competency2"],
            "learning_path_options": ["path1", "path2"]
        }
        
        CRITICAL: If a timeline constraint is provided, your estimated_weeks MUST fit within that timeline.
        Adjust the scope and depth of learning to match the available time.
        Be specific and realistic based on the learning goal."""
        
        user_prompt = f"""Analyze this learning goal: "{goal_text}"
        
Current level: {user_profile.get('level', 'beginner')}
Daily study time: {daily_minutes} minutes
Learning style: {user_profile.get('learning_style', 'visual')}
{timeline_constraint}

Provide domain analysis as JSON. Make sure estimated_weeks respects the user's timeline."""
        
        # Call LLM
        llm = get_llm(temperature=0.3)  # Lower temp for structured analysis
        
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        # Parse response
        response_text = response.content if hasattr(response, "content") else str(response)
        
        # Extract JSON from response
        try:
            # Try to find JSON in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                domain_analysis = json.loads(json_str)
            else:
                # Fallback structure
                domain_analysis = {
                    "prerequisites": [],
                    "dependencies": {},
                    "complexity_estimate": 0.5,
                    "estimated_weeks": 8,
                    "core_competencies": [],
                    "learning_path_options": []
                }
                logger.warning("Could not parse domain analysis JSON, using fallback")
        
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}, using fallback structure")
            domain_analysis = {
                "prerequisites": [],
                "dependencies": {},
                "complexity_estimate": 0.5,
                "estimated_weeks": 8,
                "core_competencies": [],
                "learning_path_options": []
            }
        
        state["domain_analysis"] = domain_analysis
        state["current_node"] = "domain_analyzer_node"
        
        logger.info(f"  ✓ domain_analyzer_node complete")
        logger.debug(f"    Prerequisites: {domain_analysis.get('prerequisites', [])}")
        logger.debug(f"    Estimated weeks: {domain_analysis.get('estimated_weeks', '?')}")
        
        return state
        
    except Exception as e:
        logger.error(f"✗ domain_analyzer_node failed: {str(e)}", exc_info=True)
        state["error"] = f"Domain analysis failed: {str(e)}"
        state["error_node"] = "domain_analyzer_node"
        return state
