"""
Insight Agent - LangChain Agent

Generates intelligent insights about user learning patterns.
- Analyzes completion history and metrics
- Identifies strengths and weaknesses
- Predicts completion dates
- Generates actionable recommendations
- Creates natural language insights for UI display

Author: AI Learning Platform Team
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from statistics import mean, stdev
from src.llm.config import LLMConfig
from src.llm.prompts import INSIGHT_SYSTEM_PROMPT
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class InsightAgent:
    """
    Agent for generating learning insights and recommendations.
    
    This agent analyzes performance metrics and generates:
    - Pattern identification (learning habits, topic strengths/weaknesses)
    - Natural language insights
    - Actionable recommendations
    - Completion predictions
    
    Example:
        >>> agent = InsightAgent(llm_config)
        >>> metrics = {
        ...     "completion_rate": 0.75,
        ...     "avg_time": 45,
        ...     "consistency": 8.5
        ... }
        >>> insights = agent.generate_insights(state, metrics)
        >>> print(insights)
        "You're doing great! 75% completion rate. Keep it up..."
    """
    
    def __init__(self, llm_service: Optional[LLMConfig] = None):
        """
        Initialize the Insight Agent.
        
        Args:
            llm_service: LLMConfig instance for API calls
                        If None, creates new instance
        """
        self.llm_service = llm_service or LLMConfig()
        self.llm = self.llm_service.get_llm()
        self.logger = logger
        self.logger.info("InsightAgent initialized")
    
    def generate_insights(
        self,
        state: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> str:
        """
        Generate natural language insights from performance metrics.
        
        Takes raw metrics and generates readable insights using LLM.
        
        Args:
            state: Current application state containing:
                - goal_text: Learning goal
                - level: Skill level
                - tasks: List of completed/pending tasks
                - completion_history: Historical completion data
            metrics: Calculated performance metrics containing:
                - completion_rate: 0-1 float
                - avg_time: Average minutes per task
                - consistency: 0-10 score
                - velocity: tasks per week
                
        Returns:
            Natural language insights as formatted string
            
        Example:
            >>> insights = agent.generate_insights(state, metrics)
            >>> assert "completion" in insights.lower()
        """
        try:
            self.logger.info("Generating insights from metrics")
            
            # Prepare data for LLM
            analysis = self._analyze_patterns(state, metrics)
            
            # Create prompt for insight generation
            prompt = self._create_insight_prompt(state, metrics, analysis)
            
            # Call LLM to generate insights
            response = self.llm.invoke([
                {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ])
            
            insights_text = response.content if hasattr(response, 'content') else str(response)
            
            self.logger.info("Insights generated successfully")
            return insights_text
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            return f"Unable to generate insights: {str(e)}"
    
    def identify_patterns(self, completion_history: List[Dict]) -> Dict[str, Any]:
        """
        Identify learning patterns from completion history.
        
        Analyzes:
        - Completion consistency (steady vs variable)
        - Task type preferences
        - Time patterns
        - Topic strengths/weaknesses
        
        Args:
            completion_history: List of completed tasks with timestamps and metrics
                [{
                    "day": 1,
                    "task": "...",
                    "completed": True,
                    "time_minutes": 45,
                    "topic": "basics"
                }, ...]
        
        Returns:
            Dictionary with identified patterns:
            {
                "consistency_type": "steady|variable|improving|declining",
                "preferred_task_types": ["video", "coding"],
                "strong_topics": ["basics", "syntax"],
                "weak_topics": ["advanced", "theory"],
                "time_pattern": "consistent|variable",
                "trend": "improving|stable|declining"
            }
        """
        try:
            if not completion_history:
                return {}
            
            patterns = {}
            
            # Analyze completion times for consistency
            times = [task.get("time_minutes", 0) for task in completion_history if task.get("completed")]
            if times and len(times) > 1:
                time_std = stdev(times)
                time_mean = mean(times)
                cv = (time_std / time_mean) if time_mean > 0 else 0
                
                patterns["consistency_type"] = (
                    "variable" if cv > 0.5 else
                    "steady" if cv < 0.2 else
                    "moderate"
                )
                patterns["time_coefficient_variation"] = round(cv, 2)
            
            # Analyze task type preferences
            task_types = {}
            for task in completion_history:
                if task.get("completed"):
                    task_type = task.get("type", "other")
                    task_types[task_type] = task_types.get(task_type, 0) + 1
            
            if task_types:
                patterns["preferred_task_types"] = sorted(
                    task_types.keys(),
                    key=lambda x: task_types[x],
                    reverse=True
                )
            
            # Analyze topic performance
            topic_performance = {}
            for task in completion_history:
                topic = task.get("topic", "general")
                completed = task.get("completed", False)
                if topic not in topic_performance:
                    topic_performance[topic] = {"completed": 0, "total": 0}
                topic_performance[topic]["total"] += 1
                if completed:
                    topic_performance[topic]["completed"] += 1
            
            strong_topics = []
            weak_topics = []
            
            for topic, data in topic_performance.items():
                if data["total"] > 0:
                    rate = data["completed"] / data["total"]
                    if rate > 0.75:
                        strong_topics.append(topic)
                    elif rate < 0.5:
                        weak_topics.append(topic)
            
            patterns["strong_topics"] = strong_topics
            patterns["weak_topics"] = weak_topics
            
            # Analyze trend
            if len(completion_history) >= 3:
                recent = completion_history[-3:]
                older = completion_history[:-3]
                
                recent_completion = sum(1 for t in recent if t.get("completed")) / len(recent)
                older_completion = sum(1 for t in older if t.get("completed")) / len(older)
                
                if recent_completion > older_completion * 1.1:
                    patterns["trend"] = "improving"
                elif recent_completion < older_completion * 0.9:
                    patterns["trend"] = "declining"
                else:
                    patterns["trend"] = "stable"
            
            self.logger.debug(f"Identified patterns: {patterns}")
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error identifying patterns: {str(e)}")
            return {}
    
    def generate_recommendations(
        self,
        gaps: List[str],
        metrics: Dict[str, Any],
        patterns: Optional[Dict] = None
    ) -> List[str]:
        """
        Generate actionable recommendations for the learner.
        
        Creates specific, actionable suggestions based on:
        - Identified gaps
        - Performance metrics
        - Learning patterns
        
        Args:
            gaps: List of identified knowledge gaps
            metrics: Performance metrics dictionary
            patterns: Optional patterns from identify_patterns()
        
        Returns:
            List of recommendation strings
            
        Example:
            >>> gaps = ["theory", "advanced topics"]
            >>> metrics = {"completion_rate": 0.5, "avg_time": 120}
            >>> recs = agent.generate_recommendations(gaps, metrics)
            >>> assert len(recs) > 0
        """
        recommendations = []
        patterns = patterns or {}
        
        try:
            # Recommendation based on completion rate
            completion_rate = metrics.get("completion_rate", 0)
            if completion_rate < 0.5:
                recommendations.append(
                    "📉 Your completion rate is low. Try reducing task difficulty or daily time commitment."
                )
            elif completion_rate > 0.9:
                recommendations.append(
                    "🚀 Excellent completion rate! Consider increasing difficulty for more challenge."
                )
            
            # Recommendation based on consistency
            consistency = metrics.get("consistency", 5)
            if consistency < 5:
                recommendations.append(
                    "⏱️ Your learning is inconsistent. Try to establish a regular daily schedule."
                )
            elif consistency > 8:
                recommendations.append(
                    "✨ Great consistency! You're building solid learning habits."
                )
            
            # Recommendation based on gaps
            if gaps:
                gap_list = ", ".join(gaps[:3])
                recommendations.append(
                    f"🎯 Focus on these weak areas: {gap_list}"
                )
            
            # Recommendation based on patterns
            weak_topics = patterns.get("weak_topics", [])
            if weak_topics:
                recommendations.append(
                    f"📚 You struggle with: {', '.join(weak_topics)}. "
                    "Consider more review tasks or visual explanations."
                )
            
            preferred_types = patterns.get("preferred_task_types", [])
            if preferred_types:
                recommendations.append(
                    f"💡 You learn best with: {preferred_types[0]}. "
                    "We'll focus more on this format."
                )
            
            # Recommendation based on velocity
            velocity = metrics.get("velocity", 0)
            if velocity > 0:
                weeks_remaining = metrics.get("estimated_weeks_remaining", 0)
                if weeks_remaining > 0:
                    recommendations.append(
                        f"📅 At current pace, you'll finish in about {weeks_remaining} weeks."
                    )
            
            # Trend-based recommendation
            trend = patterns.get("trend", "stable")
            if trend == "improving":
                recommendations.append("📈 Your performance is improving! Keep pushing forward.")
            elif trend == "declining":
                recommendations.append("⚠️ Your performance is declining. Take a break or adjust your schedule.")
            
            self.logger.debug(f"Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return ["Unable to generate recommendations at this time."]
    
    def predict_completion(
        self,
        velocity: float,
        remaining_tasks: int,
        start_date: Optional[str] = None
    ) -> Optional[str]:
        """
        Predict when the learning goal will be completed.
        
        Uses velocity (tasks per week) to estimate completion date.
        
        Args:
            velocity: Tasks completed per week
            remaining_tasks: Number of tasks left
            start_date: Optional start date (ISO format)
                       If not provided, uses today
        
        Returns:
            Predicted completion date as formatted string
            e.g., "February 15, 2025"
            
        Example:
            >>> date = agent.predict_completion(
            ...     velocity=2.5,  # 2.5 tasks per week
            ...     remaining_tasks=10
            ... )
            >>> assert "February" in date or "March" in date
        """
        try:
            if velocity <= 0:
                return "Unable to predict (insufficient progress)"
            
            # Calculate weeks needed
            weeks_needed = remaining_tasks / velocity
            
            # Calculate completion date
            if start_date:
                try:
                    start = datetime.fromisoformat(start_date)
                except ValueError:
                    start = datetime.utcnow()
            else:
                start = datetime.utcnow()
            
            completion_date = start + timedelta(weeks=weeks_needed)
            
            # Format as readable string
            formatted_date = completion_date.strftime("%B %d, %Y")
            
            self.logger.debug(f"Predicted completion: {formatted_date}")
            return formatted_date
            
        except Exception as e:
            self.logger.error(f"Error predicting completion: {str(e)}")
            return None
    
    def _analyze_patterns(
        self,
        state: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze patterns from state and metrics.
        
        Helper method for generate_insights.
        """
        analysis = {
            "goal": state.get("goal_text", "Unknown"),
            "level": state.get("level", "Unknown"),
            "learning_style": state.get("learning_style", "Unknown"),
            "completion_rate_pct": f"{metrics.get('completion_rate', 0) * 100:.1f}%",
            "avg_time_minutes": metrics.get("avg_time", 0),
            "consistency_score": metrics.get("consistency", 0),
            "velocity_tasks_week": metrics.get("velocity", 0),
        }
        
        # Add patterns
        completion_history = state.get("completion_history", [])
        if completion_history:
            patterns = self.identify_patterns(completion_history)
            analysis["patterns"] = patterns
        
        return analysis
    
    def _create_insight_prompt(
        self,
        state: Dict[str, Any],
        metrics: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """
        Create prompt for LLM to generate insights.
        
        Structures data into readable format for LLM.
        """
        prompt = f"""
Analyze this learner's progress and generate insightful, encouraging feedback:

LEARNING GOAL: {state.get('goal_text', 'Unknown')}
SKILL LEVEL: {state.get('level', 'Unknown').title()}
LEARNING STYLE: {state.get('learning_style', 'Not specified').title()}

PERFORMANCE METRICS:
- Completion Rate: {analysis['completion_rate_pct']}
- Average Time per Task: {analysis['avg_time_minutes']} minutes
- Consistency Score: {analysis['consistency_score']}/10
- Learning Velocity: {analysis['velocity_tasks_week']} tasks/week

PATTERNS:
{self._format_patterns(analysis.get('patterns', {}))}

Please provide:
1. An encouraging summary of their progress
2. Specific strengths they've demonstrated
3. Areas where they can improve
4. Actionable next steps
5. Motivational closing statement

Keep the tone positive and supportive. Use emojis for visual interest.
"""
        return prompt
    
    def _format_patterns(self, patterns: Dict) -> str:
        """Format patterns dictionary for readability."""
        if not patterns:
            return "No patterns identified yet."
        
        lines = []
        if "strong_topics" in patterns and patterns["strong_topics"]:
            lines.append(f"- Strong Topics: {', '.join(patterns['strong_topics'])}")
        
        if "weak_topics" in patterns and patterns["weak_topics"]:
            lines.append(f"- Weak Topics: {', '.join(patterns['weak_topics'])}")
        
        if "consistency_type" in patterns:
            lines.append(f"- Consistency: {patterns['consistency_type'].title()}")
        
        if "trend" in patterns:
            lines.append(f"- Trend: {patterns['trend'].title()}")
        
        if "preferred_task_types" in patterns:
            lines.append(f"- Preferred Formats: {', '.join(patterns['preferred_task_types'])}")
        
        return "\n".join(lines) if lines else "No patterns identified yet."
