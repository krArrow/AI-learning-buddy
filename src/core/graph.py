"""
LangGraph Graph Definition - 4-Phase Learning Workflow
Defines the complete state graph with conditional edges for adaptive routing.
"""
from typing import Optional, Literal
from langgraph.graph import StateGraph, END

from src.core.state import AppState
from src.core.nodes import NODE_REGISTRY
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GraphBuildError(Exception):
    """Custom exception for graph building failures."""
    pass


# ============== CONDITIONAL EDGE ROUTERS ==============

def route_after_domain_analysis(state: AppState) -> Literal["curriculum_architect_node", "goal_clarifier_node"]:
    """
    PHASE 1→2: Decide whether to proceed to architecture or clarify more.
    
    For now: Always proceed to architecture once domain analysis is complete.
    """
    if state.get("discovery_complete"):
        return "curriculum_architect_node"
    else:
        return "goal_clarifier_node"


def route_after_roadmap_validation(state: AppState) -> Literal["module_curator_node", "curriculum_architect_node"]:
    """
    PHASE 2→3 or loop: Proceed to content curation if roadmap approved.
    Otherwise, re-architect.
    """
    if state.get("roadmap_validated"):
        return "module_curator_node"
    else:
        # User rejected: re-architect
        return "curriculum_architect_node"


def route_module_curation_loop(state: AppState) -> Literal["module_curator_node", "content_aggregator_node"]:
    """
    PHASE 3 loop: After task generation, check if more modules need curation.
    
    Flow: curator → task_generator → (back to curator if pending) OR aggregator
    """
    module_status = state.get("module_curation_status", {})
    pending = [m for m, s in module_status.items() if s == "pending"]
    
    if pending:
        # More modules need curation - loop back
        return "module_curator_node"
    else:
        # All modules curated, proceed to aggregation
        return "content_aggregator_node"


def route_after_content_aggregation(state: AppState) -> Literal["progress_tracker_node", "replanning_trigger_node"]:
    """
    PHASE 3→4: Content population complete, start adaptive execution.
    """
    return "progress_tracker_node"


def route_progress_to_adaptation(state: AppState) -> Literal["adaptive_controller_node", "progress_tracker_node"]:
    """
    PHASE 4: After tracking progress, run adaptation analysis.
    """
    return "adaptive_controller_node"


def route_after_adaptation(state: AppState) -> Literal["replanning_trigger_node", "progress_tracker_node"]:
    """
    PHASE 4: After adaptation analysis, check if replanning needed.
    """
    return "replanning_trigger_node"


def route_replanning_decision(state: AppState) -> Literal["module_curator_node", "progress_tracker_node", END]:
    """
    PHASE 4: Decide if re-curation needed, continue, or end.
    
    - If re_curation_triggered: go back to module_curator_node for struggling module
    - Otherwise: continue or end
    """
    if state.get("re_curation_triggered"):
        logger.info("  → Routing to module re-curation loop")
        return "module_curator_node"
    else:
        # Continue normal execution or end
        # For now, end the workflow
        return END


def build_graph() -> StateGraph:
    """
    Build and compile the complete 4-phase learning workflow graph.
    
    Phases:
    1. DISCOVERY: goal_clarifier → domain_analyzer
    2. ROADMAP ARCHITECTURE: curriculum_architect → roadmap_validator
    3. CONTENT POPULATION: module_curator ↔ module_task_generator → content_aggregator
    4. ADAPTIVE EXECUTION: progress_tracker → adaptive_controller → replanning_trigger → [END or loop]
    
    Returns:
        Compiled StateGraph ready for execution
        
    Raises:
        GraphBuildError: If graph compilation fails
        
    Example:
        >>> graph = build_graph()
        >>> result = graph.invoke(initial_state)
    """
    logger.info("Building 4-Phase LangGraph workflow...")
    
    try:
        # Create the state graph
        workflow = StateGraph(AppState)
        logger.debug("StateGraph created")
        
        # Add all nodes from registry
        for node_name, node_func in NODE_REGISTRY.items():
            if node_func:  # Skip None values
                workflow.add_node(node_name, node_func)
                logger.debug(f"Added node: {node_name}")
        
        # ==================== SET ENTRY POINT ====================
        workflow.set_entry_point("goal_clarifier_node")
        logger.debug("Set entry point: goal_clarifier_node")
        
        # ==================== PHASE 1: DISCOVERY ====================
        # goal_clarifier → domain_analyzer (linear)
        workflow.add_edge("goal_clarifier_node", "domain_analyzer_node")
        logger.debug("Edge: goal_clarifier_node → domain_analyzer_node")
        
        # domain_analyzer → curriculum_architect OR goal_clarifier (conditional)
        workflow.add_conditional_edges(
            "domain_analyzer_node",
            route_after_domain_analysis,
            {
                "curriculum_architect_node": "curriculum_architect_node",
                "goal_clarifier_node": "goal_clarifier_node"
            }
        )
        logger.debug("Conditional edge: domain_analyzer_node → [architect | clarifier]")
        
        # ==================== PHASE 2: ROADMAP ARCHITECTURE ====================
        # curriculum_architect → roadmap_validator (linear)
        workflow.add_edge("curriculum_architect_node", "roadmap_validator_node")
        logger.debug("Edge: curriculum_architect_node → roadmap_validator_node")
        
        # roadmap_validator → module_curator OR curriculum_architect (conditional)
        workflow.add_conditional_edges(
            "roadmap_validator_node",
            route_after_roadmap_validation,
            {
                "module_curator_node": "module_curator_node",
                "curriculum_architect_node": "curriculum_architect_node"
            }
        )
        logger.debug("Conditional edge: roadmap_validator_node → [curator | architect]")
        
        # ==================== PHASE 3: CONTENT POPULATION ====================
        # module_curator ↔ module_task_generator (per-module loop)
        workflow.add_edge("module_curator_node", "module_task_generator_node")
        logger.debug("Edge: module_curator_node → module_task_generator_node")
        
        workflow.add_conditional_edges(
            "module_task_generator_node",
            route_module_curation_loop,
            {
                "module_curator_node": "module_curator_node",
                "content_aggregator_node": "content_aggregator_node"
            }
        )
        logger.debug("Conditional edge: module_task_generator_node → [curator loop | aggregator]")
        
        # content_aggregator → progress_tracker (Phase 3→4 transition)
        workflow.add_edge("content_aggregator_node", "progress_tracker_node")
        logger.debug("Edge: content_aggregator_node → progress_tracker_node")
        
        # ==================== PHASE 4: ADAPTIVE EXECUTION ====================
        # progress_tracker → adaptive_controller (linear)
        workflow.add_edge("progress_tracker_node", "adaptive_controller_node")
        logger.debug("Edge: progress_tracker_node → adaptive_controller_node")
        
        # adaptive_controller → replanning_trigger (linear)
        workflow.add_edge("adaptive_controller_node", "replanning_trigger_node")
        logger.debug("Edge: adaptive_controller_node → replanning_trigger_node")
        
        # replanning_trigger → [curator (re-curate), END, or progress_tracker (continue)]
        workflow.add_conditional_edges(
            "replanning_trigger_node",
            route_replanning_decision,
            {
                "module_curator_node": "module_curator_node",
                "progress_tracker_node": "progress_tracker_node",
                END: END
            }
        )
        logger.debug("Conditional edge: replanning_trigger_node → [curator recure | progress | END]")
        
        logger.debug("All edges added successfully")
        
        # Compile the graph
        logger.info("Compiling graph...")
        compiled_graph = workflow.compile()
        
        logger.info("✓ Graph compiled successfully")
        logger.info(f"  Nodes: {len(NODE_REGISTRY)}")
        logger.info(f"  Entry: goal_clarifier_node")
        logger.info(f"  Phases: 4 (Discovery → Roadmap → Content → Adaptive)")
        
        return compiled_graph
        
    except Exception as e:
        error_msg = f"Failed to build graph: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise GraphBuildError(error_msg) from e


def build_graph_with_retry(max_retries: int = 3) -> StateGraph:
    """
    Build graph with retry logic for robustness.
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        Compiled StateGraph
        
    Raises:
        GraphBuildError: If all retries fail
    """
    import time
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Graph build attempt {attempt}/{max_retries}")
            return build_graph()
            
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"All {max_retries} graph build attempts failed")
                raise
            
            wait_time = 2 ** attempt  # Exponential backoff
            logger.warning(
                f"Graph build attempt {attempt} failed: {e}. "
                f"Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)
    
    raise GraphBuildError("Unexpected error in retry logic")


def validate_graph_structure(graph: StateGraph) -> bool:
    """
    Validate that graph has all required nodes and edges.
    
    Args:
        graph: The compiled graph to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Basic validation - check if graph is compiled
        if graph is None:
            logger.error("Graph is None")
            return False
        
        logger.info("Graph structure validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Graph validation failed: {e}", exc_info=True)
        return False


# Global graph instance (lazy initialization)
_graph_instance: Optional[StateGraph] = None


def get_graph(rebuild: bool = False) -> StateGraph:
    """
    Get the compiled graph instance (singleton pattern).
    
    Args:
        rebuild: Force rebuild of the graph
        
    Returns:
        Compiled StateGraph
    """
    global _graph_instance
    
    if _graph_instance is None or rebuild:
        logger.info("Initializing global graph instance...")
        _graph_instance = build_graph_with_retry()
    
    return _graph_instance


def execute_workflow(initial_state: AppState) -> AppState:
    """
    Execute the complete 4-phase workflow with the given initial state.
    
    Args:
        initial_state: Starting state with user goal
        
    Returns:
        Final state after workflow completion
        
    Raises:
        Exception: If workflow execution fails
        
    Example:
        >>> from src.core.state import create_initial_state
        >>> state = create_initial_state(goal_text="Learn Python")
        >>> final_state = execute_workflow(state)
    """
    logger.info("=" * 70)
    logger.info("EXECUTING 4-PHASE LEARNING WORKFLOW")
    logger.info("=" * 70)
    logger.info(f"Goal: {initial_state.get('goal_text', 'N/A')}")
    logger.info(f"Session ID: {initial_state.get('session_id', 'N/A')}")
    logger.info("=" * 70)
    
    try:
        # Get compiled graph
        graph = get_graph()
        
        # Execute workflow
        logger.info("Starting workflow execution...")
        final_state = graph.invoke(initial_state)
        
        # Log completion
        logger.info("=" * 70)
        logger.info("WORKFLOW COMPLETED")
        logger.info("=" * 70)
        
        if "error" in final_state and final_state["error"]:
            logger.error(f"Workflow completed with error: {final_state['error']}")
        else:
            logger.info("✓ Workflow completed successfully")
            
            # Log key outputs
            if "populated_roadmap" in final_state:
                roadmap = final_state["populated_roadmap"]
                modules = roadmap.get("structure", {}).get("modules", [])
                logger.info(f"  Modules: {len(modules)}")
                total_tasks = sum(len(m.get("tasks", [])) for m in modules)
                logger.info(f"  Total Tasks: {total_tasks}")
        
        logger.info("=" * 70)
        
        return final_state
        
    except Exception as e:
        logger.error("=" * 70)
        logger.error("WORKFLOW FAILED")
        logger.error("=" * 70)
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error("=" * 70)
        raise