"""
Goal Clarifier Agent - Interactive multi-turn conversation to clarify learning goals.
"""
import json
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.core.state import AppState
from src.llm.config import get_llm, invoke_llm
from src.llm.prompts import GOAL_CLARIFIER_SYSTEM_PROMPT
from src.database import db_manager, ConversationCRUD
from src.utils.logger import get_logger
from src.utils.goal_enrichment import enrich_goal_text

logger = get_logger(__name__)


class GoalClarifierAgent:
    """
    Agent that clarifies user learning goals through conversation.
    
    Conducts multi-turn dialogue to extract:
    - Learning style preference
    - Preferred pace
    - Additional preferences and constraints
    """
    
    def __init__(self, temperature: float = 0.7):
        """
        Initialize the goal clarifier agent.
        
        Args:
            temperature: LLM temperature for responses
        """
        self.llm = get_llm(temperature=temperature)
        self.system_prompt = GOAL_CLARIFIER_SYSTEM_PROMPT
        self.max_turns = 5
        logger.info("GoalClarifierAgent initialized")
    
    def clarify_goal(
        self,
        state: AppState,
        user_message: Optional[str] = None
    ) -> AppState:
        """
        Clarify learning goal through conversation.
        
        This method can be called multiple times to continue the conversation.
        Set user_message to None to start a new conversation.
        
        Args:
            state: Current application state
            user_message: User's response (None to start conversation)
            
        Returns:
            Updated state with clarification progress
        """
        logger.info("[GoalClarifierAgent] Starting goal clarification")
        
        # Get or initialize conversation history
        conversation = state.get("conversation_history", [])
        
        try:
            # If starting conversation, add initial context with ALL form data
            if len(conversation) == 0:
                logger.info("[GoalClarifierAgent] Starting new conversation")
                
                # Get user profile
                user_profile = state.get("user_profile", {})
                
                # Build comprehensive initial context with all pre-filled information
                context_parts = [f"I want to {state['goal_text']}"]
                
                # Add level if provided
                if user_profile.get('level'):
                    context_parts.append(f"My current level is {user_profile['level']}")
                
                # Add daily time commitment
                if user_profile.get('daily_minutes'):
                    context_parts.append(f"I can dedicate {user_profile['daily_minutes']} minutes per day")
                
                # Add learning style if already selected
                if user_profile.get('learning_style'):
                    style_display = user_profile['learning_style'].replace('_', '/').title()
                    context_parts.append(f"My preferred learning style is {style_display}")
                
                # Add pace if already selected
                if user_profile.get('pace'):
                    context_parts.append(f"I prefer a {user_profile['pace']} learning pace")
                
                # Add any additional preferences
                if user_profile.get('preferences') and isinstance(user_profile['preferences'], dict):
                    for key, value in user_profile['preferences'].items():
                        if value:
                            context_parts.append(f"{key}: {value}")
                
                # Combine all context into initial message
                initial_context = {
                    "role": "user",
                    "content": ". ".join(context_parts) + "."
                }
                conversation.append(initial_context)
                logger.info(f"[GoalClarifierAgent] Initial context: {initial_context['content']}")
            elif user_message:
                # Add user's response
                conversation.append({
                    "role": "user",
                    "content": user_message
                })
            
            # Prepare messages for LLM
            messages = [SystemMessage(content=self.system_prompt)]
            
            for turn in conversation:
                if turn["role"] == "user":
                    messages.append(HumanMessage(content=turn["content"]))
                elif turn["role"] == "assistant":
                    messages.append(AIMessage(content=turn["content"]))
            
            # Get agent response
            logger.debug("[GoalClarifierAgent] Invoking LLM")
            response = invoke_llm(messages)
            response_text = response.content
            
            # Add to conversation
            conversation.append({
                "role": "assistant",
                "content": response_text
            })
            
            # Check if clarification is complete
            clarification_complete = False
            extracted_data = None
            
            if "clarification_complete" in response_text.lower():
                logger.info("[GoalClarifierAgent] Clarification marked complete")
                try:
                    # Extract JSON from response
                    extracted_data = self._extract_json(response_text)
                    if extracted_data and extracted_data.get("clarification_complete"):
                        clarification_complete = True
                        logger.info("[GoalClarifierAgent] Successfully extracted clarification data")
                except Exception as e:
                    logger.warning(f"[GoalClarifierAgent] Failed to parse completion JSON: {e}")
            
            # Update state
            state["conversation_history"] = conversation
            state["clarification_complete"] = clarification_complete
            
            if clarification_complete and extracted_data:
                # Update state with extracted information
                if "learning_style" in extracted_data:
                    state["user_profile"]["learning_style"] = extracted_data["learning_style"]
                if "pace" in extracted_data:
                    state["user_profile"]["pace"] = extracted_data["pace"]
                if "preferences" in extracted_data:
                    state["user_profile"]["preferences"].update(extracted_data["preferences"])
                
                logger.info(
                    f"[GoalClarifierAgent] Clarification complete - "
                    f"style: {state['user_profile']['learning_style']}, pace: {state['user_profile']['pace']}"
                )
                
                # CRITICAL: Enrich goal_text with clarified preferences
                # This ensures the content curator receives full context
                original_goal_text = state.get("goal_text", "")
                enriched_goal_text = enrich_goal_text(state)
                
                # Store original for reference
                if "original_goal_text" not in state:
                    state["original_goal_text"] = original_goal_text
                
                # Update with enriched version for downstream agents
                state["goal_text"] = enriched_goal_text
                
                logger.info("[GoalClarifierAgent] ✓ Goal text enriched with user preferences")
                logger.info(f"[GoalClarifierAgent] Original: {original_goal_text[:60]}...")
                logger.info(f"[GoalClarifierAgent] Enriched: {enriched_goal_text[:100]}...")
            
            # Store conversation in database if goal_id exists
            if state.get("goal_id"):
                try:
                    with db_manager.get_session_context() as session:
                        ConversationCRUD.create(
                            session=session,
                            goal_id=state["goal_id"],
                            agent_type="goal_clarifier",
                            user_message=user_message or "[Start conversation]",
                            ai_response=response_text
                        )
                except Exception as db_error:
                    logger.warning(f"[GoalClarifierAgent] Failed to store conversation: {db_error}")
            
            return state
            
        except Exception as e:
            logger.error(f"[GoalClarifierAgent] Error during clarification: {e}", exc_info=True)
            state["error"] = f"Goal clarification failed: {str(e)}"
            return state
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from agent response.
        
        Args:
            text: Response text potentially containing JSON
            
        Returns:
            Parsed JSON dict or None
        """
        try:
            # Try to find JSON in the text
            start_idx = text.find("{")
            end_idx = text.rfind("}") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            
            return None
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}")
            return None
    
    def process_answer(
        self,
        state: AppState,
        user_answer: str
    ) -> AppState:
        """
        Process user's answer to clarification questions.
        
        Args:
            state: Current application state
            user_answer: User's answer to the current question
            
        Returns:
            Updated state with user's answer incorporated
        """
        logger.info("[GoalClarifierAgent] Processing user answer")
        
        try:
            # Invoke clarify_goal to get next question
            # Note: clarify_goal will add the user_message to conversation history
            state = self.clarify_goal(state, user_message=user_answer)
            
            return state
            
        except Exception as e:
            logger.error(f"[GoalClarifierAgent] Error processing answer: {e}", exc_info=True)
            state["error"] = f"Failed to process answer: {str(e)}"
            return state


__all__ = ["GoalClarifierAgent"]
