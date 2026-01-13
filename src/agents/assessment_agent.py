"""
Assessment Agent - Generates and evaluates knowledge assessments.
"""
import json
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.state import AppState
from src.llm.config import invoke_llm
from src.llm.prompts import ASSESSMENT_SYSTEM_PROMPT
from src.tools.validators import validate_assessment
from src.database import db_manager, AssessmentCRUD
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AssessmentAgent:
    """
    Agent that generates and evaluates knowledge assessments.
    
    Capabilities:
    - Generate targeted questions
    - Evaluate user responses
    - Identify knowledge gaps
    - Provide constructive feedback
    """
    
    def __init__(self, temperature: float = 0.7):
        """
        Initialize assessment agent.
        
        Args:
            temperature: LLM temperature for generation
        """
        self.system_prompt = ASSESSMENT_SYSTEM_PROMPT
        self.temperature = temperature
        logger.info("AssessmentAgent initialized")
    
    def generate_assessment(
        self,
        state: AppState,
        topics: List[str],
        num_questions: int = 3
    ) -> Dict[str, Any]:
        """
        Generate knowledge assessment questions.
        
        Args:
            state: Current application state
            topics: Topics to assess
            num_questions: Number of questions to generate
            
        Returns:
            Assessment dictionary with questions
        """
        logger.info(f"[AssessmentAgent] Generating {num_questions} questions for topics: {topics}")
        
        try:
            level = state.get("level", "beginner")
            
            # Prepare prompt
            prompt = f"""Generate {num_questions} assessment questions for these topics: {', '.join(topics)}

User level: {level}

Return ONLY valid JSON in the required format."""
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Get LLM response
            response = invoke_llm(messages, temperature=self.temperature)
            response_text = response.content
            
            # Parse JSON
            assessment = self._extract_json(response_text)
            
            if not assessment:
                raise ValueError("Failed to parse assessment JSON")
            
            # Validate assessment structure
            is_valid, error = validate_assessment(assessment)
            if not is_valid:
                raise ValueError(f"Invalid assessment structure: {error}")
            
            logger.info(f"[AssessmentAgent] Generated {len(assessment['questions'])} questions")
            
            return assessment
            
        except Exception as e:
            logger.error(f"[AssessmentAgent] Error generating assessment: {e}", exc_info=True)
            # Return empty assessment on error
            return {"questions": []}
    
    def evaluate_response(
        self,
        question: str,
        user_answer: str,
        expected_concepts: List[str],
        state: AppState
    ) -> Dict[str, Any]:
        """
        Evaluate a user's answer to an assessment question.
        
        Args:
            question: The assessment question
            user_answer: User's answer text
            expected_concepts: Expected concepts to cover
            state: Current application state
            
        Returns:
            Evaluation dictionary with score and feedback
        """
        logger.info("[AssessmentAgent] Evaluating user response")
        
        try:
            # Prepare evaluation prompt
            prompt = f"""Evaluate this response:

Question: {question}
User Answer: {user_answer}
Expected Concepts: {', '.join(expected_concepts)}

Return ONLY valid JSON in the evaluation format."""
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Get LLM response
            response = invoke_llm(messages, temperature=self.temperature)
            response_text = response.content
            
            # Parse JSON
            evaluation = self._extract_json(response_text)
            
            if not evaluation:
                raise ValueError("Failed to parse evaluation JSON")
            
            # Store in database if goal_id exists
            if state.get("goal_id"):
                try:
                    with db_manager.get_session_context() as session:
                        AssessmentCRUD.create(
                            session=session,
                            goal_id=state["goal_id"],
                            question=question,
                            user_answer=user_answer,
                            is_correct=evaluation.get("is_correct"),
                            confidence_score=evaluation.get("correctness_score"),
                            gap_identified=", ".join(evaluation.get("gaps_identified", []))
                        )
                except Exception as db_error:
                    logger.warning(f"[AssessmentAgent] Failed to store assessment: {db_error}")
            
            logger.info(
                f"[AssessmentAgent] Evaluation complete: "
                f"correct={evaluation.get('is_correct')}, "
                f"score={evaluation.get('correctness_score', 0):.2f}"
            )
            
            return evaluation
            
        except Exception as e:
            logger.error(f"[AssessmentAgent] Error evaluating response: {e}", exc_info=True)
            return {
                "is_correct": False,
                "correctness_score": 0.0,
                "gaps_identified": ["evaluation_failed"],
                "feedback": f"Unable to evaluate response: {str(e)}",
                "concepts_understood": [],
                "concepts_missing": []
            }
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response.
        
        Args:
            text: Response text potentially containing JSON
            
        Returns:
            Parsed JSON dict or None
        """
        try:
            # Find JSON in text
            start_idx = text.find("{")
            end_idx = text.rfind("}") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            
            return None
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}")
            return None


__all__ = ["AssessmentAgent"]