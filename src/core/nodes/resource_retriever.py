"""
Resource Retriever Node - Fetches learning resources using Content Curator Agent.
"""
import time
from src.core.state import AppState
from src.agents.content_curator import ContentCuratorAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)


def resource_retriever_node(state: AppState) -> AppState:
    """
    Retrieve relevant learning resources for the goal.
    
    This node:
    - Initializes ContentCuratorAgent
    - Curates resources based on goal and learning style
    - Validates and ranks resources
    - Updates state with top resources
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with resources list populated
    """
    start_time = time.time()
    node_name = "resource_retriever"
    state["current_node"] = node_name
    
    logger.info(f"[{node_name}] Starting resource retrieval")
    logger.debug(f"[{node_name}] Goal: {state.get('goal_text', 'N/A')[:50]}...")
    logger.debug(f"[{node_name}] Learning style: {state.get('learning_style', 'N/A')}")
    
    try:
        # Initialize Content Curator Agent
        curator = ContentCuratorAgent(temperature=0.5)
        
        # Curate resources
        state = curator.curate_resources(state, max_resources=10)
        
        # Log results
        resources_count = len(state.get("resources", []))
        logger.info(f"[{node_name}] Retrieved {resources_count} resources")
        
        # Track execution time
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        logger.info(f"[{node_name}] Execution complete in {elapsed:.2f}s")
        
        return state
        
    except Exception as e:
        logger.error(f"[{node_name}] Error during resource retrieval: {e}", exc_info=True)
        state["error"] = f"Resource retrieval failed: {str(e)}"
        state["resources"] = []
        
        # Track execution time even on error
        elapsed = time.time() - start_time
        if "metadata" not in state:
            state["metadata"] = {}
        if "node_execution_times" not in state["metadata"]:
            state["metadata"]["node_execution_times"] = {}
        state["metadata"]["node_execution_times"][node_name] = elapsed
        
        return state