"""
PHASE 3: Content Aggregator Node
Merges abstract roadmap + per-module resources + per-module tasks into final populated roadmap.
"""
from src.core.state import AppState, Phase
from src.utils.logger import get_logger

logger = get_logger(__name__)


def content_aggregator_node(state: AppState) -> AppState:
    """
    PHASE 3: Aggregate all content into final populated roadmap
    
    Takes:
    - abstract_roadmap (structure)
    - module_resources (curated per module)
    - module_tasks (generated per module)
    
    Produces:
    - populated_roadmap (complete: structure + content)
    
    This is the OUTPUT of Phase 3 - fully populated, ready for Phase 4 execution.
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with populated_roadmap
    """
    logger.info("→ [PHASE 3] content_aggregator_node: Aggregating content")
    
    try:
        abstract_roadmap = state.get("abstract_roadmap")
        module_resources = state.get("module_resources", {})
        module_tasks = state.get("module_tasks", {})
        
        if not abstract_roadmap:
            raise ValueError("abstract_roadmap required for aggregation")
        
        # Start with abstract roadmap
        populated_roadmap = {
            "structure": {},
            "milestones": abstract_roadmap.get("milestones", []),
            "total_estimated_weeks": abstract_roadmap.get("total_estimated_weeks", 8),
            "content_status": "populated"
        }
        
        # Enrich modules with content
        modules = abstract_roadmap.get("structure", {}).get("modules", [])
        enriched_modules = []
        
        for module in modules:
            module_id = module["id"]
            enriched = module.copy()
            
            # Add resources
            enriched["resources"] = module_resources.get(module_id, [])
            
            # Add tasks
            enriched["tasks"] = module_tasks.get(module_id, [])
            
            # Add status
            enriched["content_status"] = "ready"
            
            enriched_modules.append(enriched)
        
        populated_roadmap["structure"]["modules"] = enriched_modules
        
        # Store in state
        state["populated_roadmap"] = populated_roadmap
        state["content_population_progress"] = 1.0
        state["current_phase"] = Phase.CONTENT_POPULATION
        state["current_node"] = "content_aggregator_node"
        
        logger.info(f"  ✓ content_aggregator_node complete")
        logger.debug(f"    Modules: {len(enriched_modules)}")
        logger.debug(f"    Total resources: {sum(len(m.get('resources', [])) for m in enriched_modules)}")
        logger.debug(f"    Total tasks: {sum(len(m.get('tasks', [])) for m in enriched_modules)}")
        
        return state
        
    except Exception as e:
        logger.error(f"✗ content_aggregator_node failed: {str(e)}", exc_info=True)
        state["error"] = f"Content aggregation failed: {str(e)}"
        state["error_node"] = "content_aggregator_node"
        return state
