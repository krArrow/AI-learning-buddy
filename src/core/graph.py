"""
LangGraph Graph Definition - Orchestrates the learning workflow.
Defines the complete state graph with all nodes and edges.
"""
from typing import Optional
from langgraph.graph import StateGraph, END

from src.core.state import AppState
from src.core.nodes import NODE_REGISTRY
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GraphBuildError(Exception):
    """Custom exception for graph building failures."""
    pass


def build_graph() -> StateGraph:
    """
    Build and compile the complete learning workflow graph.
    
    The graph flow:
    1. START → goal_analyzer
    2. goal_analyzer → resource_retriever
    3. resource_retriever → roadmap_generator
    4. roadmap_generator → task_generator
    5. task_generator → finalize
    6. finalize → END
    
    Future enhancements (Day 3+):
    - Conditional routing based on performance
    - Loop back for adaptations
    - Error handling branches
    
    Returns:
        Compiled StateGraph ready for execution
        
    Raises:
        GraphBuildError: If graph compilation fails
        
    Example:
        >>> graph = build_graph()
        >>> result = graph.invoke(initial_state)
    """
    logger.info("Building LangGraph workflow...")
    
    try:
        # Create the state graph
        workflow = StateGraph(AppState)
        logger.debug("StateGraph created")
        
        # Add all nodes from registry
        for node_name, node_func in NODE_REGISTRY.items():
            workflow.add_node(node_name, node_func)
            logger.debug(f"Added node: {node_name}")
        
        # Define the workflow edges (linear for now, will add conditions in Day 3)
        workflow.set_entry_point("goal_analyzer")
        logger.debug("Set entry point: goal_analyzer")
        
        # Main workflow path
        workflow.add_edge("goal_analyzer", "resource_retriever")
        workflow.add_edge("resource_retriever", "roadmap_generator")
        workflow.add_edge("roadmap_generator", "task_generator")
        workflow.add_edge("task_generator", "finalize")
        workflow.add_edge("finalize", END)
        
        logger.debug("All edges added successfully")
        
        # Compile the graph
        logger.info("Compiling graph...")
        compiled_graph = workflow.compile()
        
        logger.info("✓ Graph compiled successfully")
        logger.info(f"  Nodes: {len(NODE_REGISTRY)}")
        logger.info(f"  Entry: goal_analyzer")
        logger.info(f"  Exit: finalize → END")
        
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
        
        # TODO: Add more sophisticated validation
        # - Check all nodes are reachable
        # - Check no dangling edges
        # - Check entry/exit points are valid
        
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
    Execute the complete workflow with the given initial state.
    
    Args:
        initial_state: Starting state with user goal information
        
    Returns:
        Final state after workflow completion
        
    Raises:
        Exception: If workflow execution fails
        
    Example:
        >>> from src.core.state import create_initial_state
        >>> state = create_initial_state(
        ...     goal_text="Learn Python",
        ...     level="beginner",
        ...     daily_minutes=30
        ... )
        >>> final_state = execute_workflow(state)
        >>> print(final_state['goal_id'])
    """
    logger.info("=" * 60)
    logger.info("EXECUTING WORKFLOW")
    logger.info("=" * 60)
    logger.info(f"Goal: {initial_state.get('goal_text', 'N/A')}")
    logger.info(f"Level: {initial_state.get('level', 'N/A')}")
    logger.info(f"Daily Minutes: {initial_state.get('daily_minutes', 'N/A')}")
    logger.info("=" * 60)
    
    try:
        # Get compiled graph
        graph = get_graph()
        
        # Execute workflow
        logger.info("Starting workflow execution...")
        final_state = graph.invoke(initial_state)
        
        # Log completion
        logger.info("=" * 60)
        logger.info("WORKFLOW COMPLETED")
        logger.info("=" * 60)
        
        if "error" in final_state and final_state["error"]:
            logger.error(f"Workflow completed with error: {final_state['error']}")
        else:
            logger.info("✓ Workflow completed successfully")
            
            # Log key outputs
            if "goal_id" in final_state:
                logger.info(f"  Goal ID: {final_state['goal_id']}")
            if "tasks" in final_state:
                logger.info(f"  Tasks Generated: {len(final_state['tasks'])}")
            if "metadata" in final_state:
                if "total_execution_time" in final_state["metadata"]:
                    logger.info(
                        f"  Total Time: {final_state['metadata']['total_execution_time']:.2f}s"
                    )
        
        logger.info("=" * 60)
        
        return final_state
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("WORKFLOW FAILED")
        logger.error("=" * 60)
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error("=" * 60)
        raise