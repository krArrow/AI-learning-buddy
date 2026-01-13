"""
Content Curator Agent - Curates and ranks learning resources.
"""
import json
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.state import AppState
from src.llm.config import invoke_llm
from src.llm.prompts import CONTENT_CURATOR_SYSTEM_PROMPT
from src.tools.course_search import course_search
from src.tools.validators import validate_resource
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ContentCuratorAgent:
    """
    Agent that curates high-quality learning resources.
    
    Combines:
    - LLM-generated search queries
    - Tool-based resource search
    - Relevance scoring
    - Learning style matching
    """
    
    def __init__(self, temperature: float = 0.5):
        """
        Initialize content curator agent.
        
        Args:
            temperature: LLM temperature (lower for more consistent curation)
        """
        self.system_prompt = CONTENT_CURATOR_SYSTEM_PROMPT
        self.temperature = temperature
        logger.info("ContentCuratorAgent initialized")
    
    def curate_resources(
        self,
        state: AppState,
        max_resources: int = 10
    ) -> AppState:
        """
        Curate learning resources based on goal and preferences.
        
        Args:
            state: Current application state
            max_resources: Maximum number of resources to return
            
        Returns:
            Updated state with curated resources
        """
        logger.info("[ContentCuratorAgent] Starting resource curation")
        
        try:
            goal_text = state.get("goal_text", "")
            learning_style = state.get("learning_style", "visual")
            level = state.get("level", "beginner")
            
            logger.info(
                f"[ContentCuratorAgent] Curating for: {goal_text[:50]}... "
                f"(style={learning_style}, level={level})"
            )
            
            # Step 1: Use course_search tool to find resources
            logger.debug("[ContentCuratorAgent] Searching for resources")
            raw_resources = course_search(
                query=goal_text,
                learning_style=learning_style,
                level=level,
                max_results=max_resources * 2  # Get more, then filter
            )
            
            logger.info(f"[ContentCuratorAgent] Found {len(raw_resources)} raw resources")
            
            # Step 2: Validate and filter resources
            valid_resources = []
            for resource in raw_resources:
                is_valid, error = validate_resource(resource)
                if is_valid:
                    valid_resources.append(resource)
                else:
                    logger.warning(f"[ContentCuratorAgent] Invalid resource: {error}")
            
            logger.info(f"[ContentCuratorAgent] {len(valid_resources)} valid resources")
            
            # Step 3: Rank and select top resources
            # Already sorted by combined_score in course_search
            top_resources = valid_resources[:max_resources]
            
            # Update state
            state["resources"] = top_resources
            
            logger.info(f"[ContentCuratorAgent] Curation complete: {len(top_resources)} resources")
            
            # Log top 3 resources
            for i, resource in enumerate(top_resources[:3], 1):
                logger.debug(
                    f"  {i}. {resource['title']} "
                    f"({resource['type']}, score={resource.get('combined_score', 0):.2f})"
                )
            
            return state
            
        except Exception as e:
            logger.error(f"[ContentCuratorAgent] Error during curation: {e}", exc_info=True)
            state["error"] = f"Resource curation failed: {str(e)}"
            # Return empty resources on error
            state["resources"] = []
            return state


__all__ = ["ContentCuratorAgent"]