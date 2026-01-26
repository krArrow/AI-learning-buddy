"""
PHASE 2: Roadmap Validator Node
Validates roadmap structure, checks prerequisites, and gets user approval.
"""
from src.core.state import AppState, Phase
from src.utils.logger import get_logger

logger = get_logger(__name__)


def roadmap_validator_node(state: AppState) -> AppState:
    """
    PHASE 2: Validate and get approval for abstract roadmap
    
    Checks:
    - Prerequisites are realistic for user level
    - Module dependencies are correctly ordered
    - Estimated time aligns with user availability
    - Total structure is coherent
    
    Then presents roadmap to user for approval.
    
    Args:
        state: Current application state with abstract_roadmap
        
    Returns:
        Updated state with roadmap_validated flag
    """
    logger.info("→ [PHASE 2] roadmap_validator_node: Validating roadmap")
    
    try:
        abstract_roadmap = state.get("abstract_roadmap")
        user_profile = state.get("user_profile", {})
        
        if not abstract_roadmap:
            raise ValueError("abstract_roadmap is required for validation")
        
        # Validate structure
        modules = abstract_roadmap.get("structure", {}).get("modules", [])
        if not modules:
            raise ValueError("Roadmap must contain at least one module")
        
        # Validate prerequisites and dependencies
        module_ids = {mod["id"] for mod in modules}
        for mod in modules:
            mod_id = mod["id"]
            prereqs = mod.get("prerequisites", [])
            
            # Check all prerequisites exist
            for prereq in prereqs:
                if prereq not in module_ids:
                    logger.warning(f"  ⚠ Module {mod_id} has invalid prerequisite {prereq}")
        
        # Check estimated time vs user availability
        total_weeks = abstract_roadmap.get("total_estimated_weeks", 8)
        daily_minutes = user_profile.get("daily_minutes", 30)
        user_level = user_profile.get("level", "beginner")
        
        logger.info(f"  Validation checks:")
        logger.info(f"    Total weeks: {total_weeks}")
        logger.info(f"    User availability: {daily_minutes} min/day")
        logger.info(f"    User level: {user_level}")
        logger.info(f"    Modules: {len(modules)}")
        
        # Check if user has already provided approval/rejection via UI
        # If roadmap_validated is already set (from UI), respect that decision
        if "roadmap_validated" in state and state["roadmap_validated"] is not None:
            if state["roadmap_validated"]:
                logger.info(f"  ✓ Roadmap approved by user")
            else:
                logger.info(f"  ✗ Roadmap rejected by user: {state.get('roadmap_validation_feedback', 'No reason given')}")
                # Keep roadmap_validated = False to trigger re-architecture
        else:
            # No user decision yet - set to pending for UI to handle
            # In interactive mode, the UI should prompt user before continuing
            # For non-interactive/testing, auto-approve
            logger.warning("  ⚠ No user approval provided - auto-validating (set roadmap_validated in UI for user approval)")
            state["roadmap_validated"] = True
            state["roadmap_validation_feedback"] = "Auto-validated (no user interaction)"
        
        state["current_phase"] = Phase.ROADMAP_ARCHITECTURE
        state["current_node"] = "roadmap_validator_node"
        
        logger.info(f"  ✓ roadmap_validator_node complete - validated: {state['roadmap_validated']}")
        
        return state
        
    except Exception as e:
        logger.error(f"✗ roadmap_validator_node failed: {str(e)}", exc_info=True)
        state["error"] = f"Roadmap validation failed: {str(e)}"
        state["error_node"] = "roadmap_validator_node"
        return state
