"""
PHASE 2: Curriculum Architect Node
Creates hierarchical Modules → Topics → Subtopics structure (NO content yet)
"""
from src.core.state import AppState, Phase
from src.agents.curriculum_architect import CurriculumArchitect
from src.utils.logger import get_logger

logger = get_logger(__name__)


def curriculum_architect_node(state: AppState) -> AppState:
    """
    PHASE 2: Create hierarchical curriculum structure
    
    Builds the abstract roadmap with:
    - Modules (main learning blocks)
    - Topics and subtopics
    - Prerequisites and dependencies
    - Estimated weeks per module
    - Learning objectives
    
    NO learning resources or tasks added at this stage.
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with abstract_roadmap
    """
    logger.info("→ [PHASE 2] curriculum_architect_node: Creating curriculum structure")
    
    try:
        # Validate prerequisites from Phase 1
        if not state.get("discovery_complete"):
            raise ValueError("Phase 1 (Discovery) must be complete before architecture")
        
        goal_text = state.get("goal_text", "")
        domain_analysis = state.get("domain_analysis", {})
        user_profile = state.get("user_profile", {})
        goal_analysis = state.get("goal_analysis")
        target_completion_days = state.get("target_completion_days")
        target_weeks = state.get("target_weeks")
        
        if not goal_text:
            raise ValueError("goal_text required for architecture")
        if not domain_analysis:
            raise ValueError("domain_analysis required for architecture")
        
        # Create curriculum with timeline constraints
        architect = CurriculumArchitect()
        abstract_roadmap = architect.architect(
            goal_text=goal_text,
            domain_analysis=domain_analysis,
            user_profile=user_profile,
            goal_analysis=goal_analysis,
            target_weeks=target_weeks,
            target_completion_days=target_completion_days
        )
        
        # Initialize module curation status
        modules = abstract_roadmap.get("structure", {}).get("modules", [])
        module_status = {mod["id"]: "pending" for mod in modules}
        
        state["abstract_roadmap"] = abstract_roadmap
        state["module_curation_status"] = module_status
        state["current_phase"] = Phase.ROADMAP_ARCHITECTURE
        state["current_node"] = "curriculum_architect_node"
        
        logger.info(f"  ✓ curriculum_architect_node complete")
        logger.debug(f"    Modules created: {len(modules)}")
        logger.debug(f"    Total estimated weeks: {abstract_roadmap.get('total_estimated_weeks')}")
        
        return state
        
    except Exception as e:
        logger.error(f"✗ curriculum_architect_node failed: {str(e)}", exc_info=True)
        state["error"] = f"Curriculum architecture failed: {str(e)}"
        state["error_node"] = "curriculum_architect_node"
        return state
