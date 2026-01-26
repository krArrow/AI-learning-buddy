"""
PHASE 4: Adaptive Controller Node
Detects struggles, analyzes performance, and recommends adaptations.
"""
from src.core.state import AppState, Phase
from src.agents.adaptive_controller import AdaptiveController
from src.utils.logger import get_logger

logger = get_logger(__name__)


def adaptive_controller_node(state: AppState) -> AppState:
    """
    PHASE 4: Analyze performance and trigger adaptations
    
    Called periodically or after task completion to:
    - Detect if user is struggling
    - Recommend pacing adjustments
    - Suggest interventions
    - Set re-curation trigger if needed
    
    Args:
        state: Current application state with performance metrics
        
    Returns:
        Updated state with adaptation recommendations
    """
    logger.info("→ [PHASE 4] adaptive_controller_node: Analyzing for adaptations")
    
    try:
        performance_metrics = state.get("performance_metrics", {})
        user_profile = state.get("user_profile", {})
        populated_roadmap = state.get("populated_roadmap")
        
        # Run adaptation analysis
        controller = AdaptiveController()
        adaptation = controller.analyze(
            performance_metrics=performance_metrics,
            user_profile=user_profile,
            populated_roadmap=populated_roadmap
        )
        
        # Update state with adaptation results
        state["struggles_detected"] = adaptation.get("struggles_detected", False)
        state["struggle_severity"] = adaptation.get("struggle_severity", 0.0)
        state["struggle_topic"] = None  # Could be set if specific topic identified
        state["adaptation_required"] = adaptation.get("adaptation_required", False)
        state["pacing_adjustment"] = adaptation.get("pacing_adjustment", 1.0)
        state["recommended_actions"] = adaptation.get("recommended_actions", [])
        
        # Determine if re-curation needed
        threshold = state.get("replanning_threshold", 0.7)
        if state["struggle_severity"] > threshold:
            state["re_curation_triggered"] = True
            # Could identify which module to re-curate
            # For now, just set flag
            logger.info(f"  ⚠ Re-curation triggered (severity: {state['struggle_severity']:.1f})")
        
        state["current_node"] = "adaptive_controller_node"
        state["current_phase"] = Phase.ADAPTIVE_EXECUTION
        
        logger.info(f"  ✓ adaptive_controller_node complete")
        logger.debug(f"    Struggles detected: {state['struggles_detected']}")
        logger.debug(f"    Recommended actions: {state['recommended_actions']}")
        
        return state
        
    except Exception as e:
        logger.error(f"✗ adaptive_controller_node failed: {str(e)}", exc_info=True)
        state["error"] = f"Adaptive control failed: {str(e)}"
        state["error_node"] = "adaptive_controller_node"
        return state
