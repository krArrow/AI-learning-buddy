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
        logger.info("="*80)
        logger.info("[ContentCuratorAgent] 🎯 STARTING RESOURCE CURATION")
        logger.info("="*80)
        
        try:
            goal_text = state.get("goal_text", "")
            learning_style = state.get("learning_style", "visual")
            level = state.get("level", "beginner")
            
            logger.info(f"[ContentCuratorAgent] Goal Text: '{goal_text}'")
            logger.info(f"[ContentCuratorAgent] Learning Style: {learning_style}")
            logger.info(f"[ContentCuratorAgent] Skill Level: {level}")
            logger.info(f"[ContentCuratorAgent] Requested Max Resources: {max_resources}")
            logger.info("-"*80)
            
            # Step 1: Use course_search tool to find resources
            logger.info("[ContentCuratorAgent] 📚 STEP 1: Fetching resources from internet sources...")
            raw_resources = course_search(
                query=goal_text,
                learning_style=learning_style,
                level=level,
                max_results=max_resources * 2  # Get more, then filter
            )
            
            logger.info(f"[ContentCuratorAgent] ✓ Received {len(raw_resources)} raw resources from search")
            logger.info("-"*80)
            
            # Step 2: Validate and filter resources
            logger.info("[ContentCuratorAgent] 🔍 STEP 2: Validating resource quality...")
            valid_resources = []
            invalid_count = 0
            
            for idx, resource in enumerate(raw_resources, 1):
                is_valid, error = validate_resource(resource)
                if is_valid:
                    valid_resources.append(resource)
                    logger.debug(f"[ContentCuratorAgent]   ✓ Resource {idx} valid: {resource.get('title', 'Unknown')[:50]}")
                else:
                    invalid_count += 1
                    logger.warning(f"[ContentCuratorAgent]   ✗ Resource {idx} invalid: {error}")
            
            logger.info(f"[ContentCuratorAgent] ✓ Validation complete: {len(valid_resources)} valid, {invalid_count} invalid")
            logger.info("-"*80)
            
            # Step 3: Rank and select top resources
            logger.info("[ContentCuratorAgent] 📊 STEP 3: Ranking and selecting top resources...")
            # Already sorted by combined_score in course_search
            top_resources = valid_resources[:max_resources]
            
            # Update state
            state["resources"] = top_resources
            
            logger.info(f"[ContentCuratorAgent] ✓ Selected top {len(top_resources)} resources")
            logger.info("="*80)
            logger.info("[ContentCuratorAgent] 📋 FINAL CURATED RESOURCES:")
            logger.info("="*80)
            
            # Log all selected resources with detailed information
            for i, resource in enumerate(top_resources, 1):
                logger.info(f"[ContentCuratorAgent] #{i}. {resource['title']}")
                logger.info(f"     Platform: {resource.get('platform', 'N/A')} | Type: {resource.get('type', 'unknown')}")
                logger.info(f"     URL: {resource.get('url', 'N/A')}")
                logger.info(f"     Difficulty: {resource.get('difficulty', 0):.2f} | Hours: {resource.get('estimated_hours', 'N/A')}")
                logger.info(f"     Scores - Relevance: {resource.get('relevance_score', 0):.2f}, "
                           f"Style Match: {resource.get('learning_style_match', 0):.2f}, "
                           f"Combined: {resource.get('combined_score', 0):.2f}")
                logger.info(f"     Description: {resource.get('description', 'N/A')}")
                logger.info("-" * 80)
            
            logger.info("="*80)
            logger.info(f"[ContentCuratorAgent] ✅ CURATION COMPLETE - {len(top_resources)} resources curated for '{goal_text}'")
            logger.info("="*80)
            
            return state
            
        except Exception as e:
            logger.error("="*80)
            logger.error(f"[ContentCuratorAgent] ❌ ERROR during curation: {e}")
            logger.error("="*80)
            logger.error(f"[ContentCuratorAgent] Exception details:", exc_info=True)
            state["error"] = f"Resource curation failed: {str(e)}"
            # Return empty resources on error
            state["resources"] = []
            return state


__all__ = ["ContentCuratorAgent"]
