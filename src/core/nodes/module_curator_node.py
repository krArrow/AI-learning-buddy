"""
PHASE 3: Module Curator Node
Per-module resource curation via RAG + web search (NOT all-at-once).
Runs once per module in a loop to build module_resources.
"""
import json
from typing import Dict, Any, List
from src.core.state import AppState, Phase
from src.tools.course_search import course_search
from src.llm.config import get_llm
from src.utils.logger import get_logger

# RAG integration
try:
    from src.memory.vector_store import VectorStore
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = get_logger(__name__)

# Lazy-initialized vector store singleton
_vector_store = None

def _get_vector_store() -> "VectorStore":
    """Get or create the vector store singleton."""
    global _vector_store
    if _vector_store is None and RAG_AVAILABLE:
        try:
            _vector_store = VectorStore()
            logger.info("  RAG: VectorStore initialized")
        except Exception as e:
            logger.warning(f"  RAG: Failed to initialize VectorStore: {e}")
    return _vector_store


def module_curator_node(state: AppState) -> AppState:
    """
    PHASE 3: Curate resources for a single module
    
    For the current module:
    - Extract topic requirements
    - Search for relevant resources (RAG, web, APIs)
    - Rank by relevance and difficulty match
    - Store module_resources[module_id]
    
    This runs ONCE per module, not all-at-once, to enable:
    - Adaptive resource selection
    - Progressive curation
    - User feedback between modules
    
    Args:
        state: Current application state
        
    Returns:
        Updated state with module_resources for current module
    """
    logger.info("→ [PHASE 3] module_curator_node: Curating module resources")
    
    try:
        abstract_roadmap = state.get("abstract_roadmap")
        module_status = state.get("module_curation_status", {})
        user_profile = state.get("user_profile", {})
        
        if not abstract_roadmap:
            raise ValueError("abstract_roadmap required for curation")
        
        modules = abstract_roadmap.get("structure", {}).get("modules", [])
        
        # Find next module to curate
        current_module_id = None
        for mod in modules:
            mod_id = mod["id"]
            if module_status.get(mod_id) == "pending":
                current_module_id = mod_id
                break
        
        if not current_module_id:
            logger.info("  ✓ All modules already curated")
            state["content_population_progress"] = 1.0
            state["current_node"] = "module_curator_node"
            return state
        
        # Get module details
        current_module = next((m for m in modules if m["id"] == current_module_id), None)
        if not current_module:
            raise ValueError(f"Module {current_module_id} not found")
        
        logger.info(f"  Curating module: {current_module['title']} ({current_module_id})")
        
        # Extract topics and subtopics - OPTIMIZED to reduce API calls
        # Instead of searching for every subtopic, we create consolidated queries
        topics = current_module.get("topics", [])
        search_queries = []
        
        # Strategy: Create 1-2 queries per topic instead of 1 per subtopic
        # This reduces API calls from 7+ per module to 2-4 per module
        for topic in topics:
            topic_title = topic.get("title", "")
            subtopics = topic.get("subtopics", [])
            
            # Primary topic query (includes module context)
            search_queries.append(f"{current_module['title']} {topic_title}")
            
            # Combine subtopics into one query if there are many
            # This is more efficient than searching each subtopic separately
            if len(subtopics) > 2:
                # Just use top 2-3 subtopics for a more focused search
                key_subtopics = " ".join(subtopics[:3])
                search_queries.append(f"{topic_title} {key_subtopics}")
            elif subtopics:
                # If only 1-2 subtopics, include them in one query
                search_queries.append(f"{topic_title} {' '.join(subtopics)}")
        
        # Limit total queries per module to prevent excessive API usage
        MAX_QUERIES_PER_MODULE = 4
        if len(search_queries) > MAX_QUERIES_PER_MODULE:
            logger.info(f"    Limiting queries from {len(search_queries)} to {MAX_QUERIES_PER_MODULE}")
            search_queries = search_queries[:MAX_QUERIES_PER_MODULE]
        
        # Search for resources per query - BOTH web search AND RAG
        all_resources: List[Dict[str, Any]] = []
        user_level = user_profile.get("level", "beginner")
        learning_style = user_profile.get("learning_style", "visual")
        
        # === WEB SEARCH ===
        logger.info(f"    [Web Search] Searching {len(search_queries)} queries...")
        for query in search_queries:
            logger.debug(f"    Searching: {query}")
            try:
                resources = course_search(
                    query=query,
                    learning_style=learning_style,
                    level=user_level,
                    max_results=5
                )
                for r in resources:
                    r["source"] = "web_search"
                all_resources.extend(resources)
            except Exception as e:
                logger.warning(f"    Search failed for '{query}': {e}")
        
        logger.info(f"    [Web Search] Found {len(all_resources)} resources")
        
        # === RAG SEARCH ===
        if RAG_AVAILABLE:
            vector_store = _get_vector_store()
            if vector_store:
                logger.info(f"    [RAG] Searching vector store...")
                try:
                    # Build combined query for semantic search
                    combined_query = f"{current_module['title']} " + " ".join(
                        t.get("title", "") for t in topics
                    )
                    rag_results = vector_store.search(
                        query=combined_query,
                        k=10,
                        learning_style=learning_style
                    )
                    for r in rag_results:
                        r["source"] = "rag"
                    all_resources.extend(rag_results)
                    logger.info(f"    [RAG] Found {len(rag_results)} resources from vector store")
                except Exception as e:
                    logger.warning(f"    [RAG] Search failed: {e}")
        else:
            logger.debug("    [RAG] VectorStore not available, skipping RAG search")
        
        # Deduplicate and rank
        seen_urls = set()
        unique_resources = []
        
        for res in all_resources:
            url = res.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                # Adjust relevance based on user level match
                difficulty = res.get("difficulty", 0.5)
                level_multiplier = 1.0
                if user_level == "beginner" and difficulty < 0.4:
                    level_multiplier = 1.1
                elif user_level == "advanced" and difficulty > 0.6:
                    level_multiplier = 1.1
                
                res["relevance_score"] = min(1.0, res.get("relevance_score", 0.7) * level_multiplier)
                unique_resources.append(res)
        
        # Sort by relevance
        unique_resources.sort(key=lambda x: x.get("relevance_score", 0.5), reverse=True)
        
        # Keep top 15 resources per module
        curated_resources = unique_resources[:15]
        
        # Store in state
        if "module_resources" not in state:
            state["module_resources"] = {}
        
        state["module_resources"][current_module_id] = curated_resources
        state["module_curation_status"][current_module_id] = "completed"
        
        # Update progress
        completed = sum(1 for s in module_status.values() if s == "completed")
        total = len(modules)
        state["content_population_progress"] = min(1.0, (completed + 1) / total)
        
        state["current_module"] = current_module_id
        state["current_node"] = "module_curator_node"
        state["current_phase"] = Phase.CONTENT_POPULATION
        
        logger.info(f"  ✓ module_curator_node complete for {current_module_id}")
        logger.debug(f"    Resources found: {len(curated_resources)}")
        logger.debug(f"    Progress: {state['content_population_progress']:.0%}")
        
        return state
        
    except Exception as e:
        logger.error(f"✗ module_curator_node failed: {str(e)}", exc_info=True)
        state["error"] = f"Module curation failed: {str(e)}"
        state["error_node"] = "module_curator_node"
        return state
