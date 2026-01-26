"""
PHASE 1: Goal Clarifier Node
Interactive 5-turn dialogue to clarify learning goals, assess skills, and gather preferences.
"""
from src.core.state import AppState, Phase
from src.agents.goal_clarifier import GoalClarifierAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)


def goal_clarifier_node(state: AppState) -> AppState:
    """
    PHASE 1: Goal Clarification - 5-turn interactive dialogue
    
    Conducts multi-turn conversation with user to:
    - Clarify learning goal
    - Assess current skill level
    - Understand learning preferences
    - Identify constraints and challenges
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with conversation history and completion flag
    """
    logger.info("→ [PHASE 1] goal_clarifier_node: Starting goal clarification")
    
    try:
        agent = GoalClarifierAgent()
        
        # Run 5-turn conversation loop
        for turn in range(5):
            logger.debug(f"  Turn {turn + 1}/5")
            
            # Call agent to get next response/question
            state = agent.clarify_goal(state)
            
            # Check if clarification is complete
            if state.get("discovery_complete", False):
                logger.info(f"  ✓ Clarification complete after {turn + 1} turns")
                break
        
        # Ensure discovery_complete flag is set
        if not state.get("discovery_complete"):
            state["discovery_complete"] = True
            logger.info("  ✓ Clarification complete (max turns reached)")
        
        state["current_phase"] = Phase.DISCOVERY
        state["current_node"] = "goal_clarifier_node"
        
        logger.info(f"  ✓ goal_clarifier_node complete")
        logger.debug(f"    Conversation turns: {len(state.get('conversation_history', []))}")
        
        return state
        
    except Exception as e:
        logger.error(f"✗ goal_clarifier_node failed: {str(e)}", exc_info=True)
        state["error"] = f"Goal clarification failed: {str(e)}"
        state["error_node"] = "goal_clarifier_node"
        return state
