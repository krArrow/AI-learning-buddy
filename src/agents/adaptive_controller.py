"""
Adaptive Controller Agent
Monitors performance, detects struggles, and recommends adaptations.
"""
from typing import Dict, Any, Optional
from src.llm.config import get_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AdaptiveController:
    """
    Agent that monitors learner performance and triggers adaptations.
    
    Detects:
    - Struggling topics (high difficulty, low performance)
    - Pacing issues (time vs estimate mismatch)
    - Consistency problems
    
    Recommends:
    - Adjust learning pace
    - Add prerequisite review
    - Provide additional practice
    - Slow down or skip ahead
    """
    
    def __init__(self, temperature: float = 0.5):
        """Initialize the adaptive controller agent."""
        self.llm = get_llm(temperature=temperature)
        logger.info("AdaptiveController initialized")
    
    def analyze(
        self,
        performance_metrics: Dict[str, Any],
        user_profile: Dict[str, Any],
        populated_roadmap: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze performance and recommend adaptations.
        
        Args:
            performance_metrics: Current performance data
            user_profile: User preferences and info
            populated_roadmap: The learning plan
            
        Returns:
            Adaptation recommendations:
            {
                "struggles_detected": bool,
                "struggle_severity": 0.0-1.0,
                "struggling_topics": ["topic1"],
                "struggling_modules": ["mod_3"],
                "pacing_adjustment": 0.8,  # multiply
                "recommended_actions": ["action1"],
                "adaptation_required": bool
            }
        """
        logger.info("[AdaptiveController] Analyzing performance")
        
        try:
            # Extract metrics
            avg_difficulty = performance_metrics.get("avg_difficulty_reported", 0.5)
            avg_performance = performance_metrics.get("avg_performance_score", 0.8)
            time_ratio = performance_metrics.get("time_spent_minutes", 0) / max(1, performance_metrics.get("estimated_time_minutes", 60))
            
            # Detect struggles
            struggles_detected = False
            struggle_severity = 0.0
            recommended_actions = []
            pacing_adjustment = 1.0
            struggling_topics = []
            
            # Check if user is struggling
            if avg_difficulty > 0.6 and avg_performance < 0.75:
                struggles_detected = True
                struggle_severity = 0.7
                recommended_actions.append("Add practice exercises for struggling topic")
                recommended_actions.append("Review prerequisite material")
                pacing_adjustment = 0.8  # Slow down
            
            # Check time mismatch
            if time_ratio > 1.3:  # Takes 30% longer
                struggles_detected = True
                struggle_severity = max(struggle_severity, 0.5)
                recommended_actions.append("Take more time with current topic")
                pacing_adjustment = min(pacing_adjustment, 0.9)
            
            # Check consistency
            consistency = performance_metrics.get("consistency_score", 0.75)
            if consistency < 0.6:
                struggles_detected = True
                recommended_actions.append("Practice regularly without gaps")
            
            adaptation_required = struggles_detected and struggle_severity > 0.5
            
            result = {
                "struggles_detected": struggles_detected,
                "struggle_severity": struggle_severity,
                "struggling_topics": struggling_topics,
                "struggling_modules": [],
                "pacing_adjustment": pacing_adjustment,
                "recommended_actions": recommended_actions,
                "adaptation_required": adaptation_required
            }
            
            logger.info(f"  ✓ Analysis complete")
            logger.debug(f"    Struggles detected: {struggles_detected}")
            logger.debug(f"    Severity: {struggle_severity:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Analysis failed: {str(e)}", exc_info=True)
            # Return safe default
            return {
                "struggles_detected": False,
                "struggle_severity": 0.0,
                "struggling_topics": [],
                "struggling_modules": [],
                "pacing_adjustment": 1.0,
                "recommended_actions": [],
                "adaptation_required": False
            }
