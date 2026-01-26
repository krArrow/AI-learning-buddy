"""
PHASE 4: Replanning Trigger Node
Decides whether to regenerate/re-curate modules based on adaptation signals.
"""
from src.core.state import AppState, Phase
from src.utils.logger import get_logger

logger = get_logger(__name__)


def replanning_trigger_node(state: AppState) -> AppState:
    """
    PHASE 4: Decide if re-planning/re-curation is needed
    
    Checks:
    - re_curation_triggered flag
    - struggle_severity vs threshold
    - adaptation_required flag
    
    Decides:
    - Re-curate struggling module (loop back to module_curator_node)
    - Adjust overall pacing
    - Continue normal execution
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with re-curation decision
    """
    logger.info("→ [PHASE 4] replanning_trigger_node: Evaluating re-planning need")
    
    try:
        re_curation_triggered = state.get("re_curation_triggered", False)
        struggle_severity = state.get("struggle_severity", 0.0)
        threshold = state.get("replanning_threshold", 0.7)
        current_module = state.get("current_module")
        
        # Decide action
        needs_replanning = re_curation_triggered or (struggle_severity > threshold)
        
        if needs_replanning and current_module:
            logger.info(f"  ⚠ Replanning triggered for module: {current_module}")
            
            # Mark module for re-curation
            module_status = state.get("module_curation_status", {})
            module_status[current_module] = "pending_recuration"
            state["module_curation_status"] = module_status
            
            state["struggling_module_id"] = current_module
            state["re_curation_triggered"] = True
            
            logger.info(f"    Module marked for re-curation")
            logger.debug(f"    Struggle severity: {struggle_severity:.1f}/{threshold}")
        
        else:
            logger.info(f"  ✓ No replanning needed, continuing execution")
            state["re_curation_triggered"] = False
        
        state["current_node"] = "replanning_trigger_node"
        state["current_phase"] = Phase.ADAPTIVE_EXECUTION
        
        logger.info(f"  ✓ replanning_trigger_node complete")
        
        return state
        
    except Exception as e:
        logger.error(f"✗ replanning_trigger_node failed: {str(e)}", exc_info=True)
        state["error"] = f"Replanning trigger failed: {str(e)}"
        state["error_node"] = "replanning_trigger_node"
        return state
