"""
Learning Memory - Performance Tracking

Manages learning progress and performance metrics.
- Aggregates task completion data
- Calculates performance metrics (completion rate, consistency, velocity)
- Retrieves learning history
- Identifies learning patterns and gaps
- Tracks topic-specific performance

Author: AI Learning Platform Team
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from statistics import mean, stdev, variance
from src.database.crud import (
    get_tasks_by_goal,
    get_progress_records,
    create_progress_record
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LearningMemory:
    """
    Manages learning progress and performance analytics.
    
    Tracks and analyzes:
    - Task completion history
    - Performance metrics (completion rate, velocity, consistency)
    - Learning patterns (strong/weak topics)
    - Progress over time
    
    Example:
        >>> memory = LearningMemory()
        >>> memory.record_completion(task_id=1, time_minutes=45, rating=5)
        >>> metrics = memory.get_performance_metrics(goal_id=1)
        >>> print(metrics["completion_rate"])
        0.75
    """
    
    def __init__(self):
        """Initialize learning memory."""
        self.logger = logger
        self._metrics_cache: Dict[int, Any] = {}
        self.logger.info("LearningMemory initialized")
    
    def record_completion(
        self,
        task_id: int,
        time_minutes: int,
        quality_rating: Optional[int] = None,
        completed_at: Optional[str] = None
    ) -> bool:
        """
        Record task completion.
        
        Args:
            task_id: ID of completed task
            time_minutes: How long task took
            quality_rating: Optional 1-5 rating of task quality
            completed_at: Optional completion timestamp (ISO format)
        
        Returns:
            True if recorded successfully
            
        Example:
            >>> success = memory.record_completion(
            ...     task_id=1,
            ...     time_minutes=45,
            ...     quality_rating=5
            ... )
        """
        try:
            if not isinstance(task_id, int) or task_id <= 0:
                raise ValueError(f"Invalid task_id: {task_id}")
            
            if not isinstance(time_minutes, int) or time_minutes < 1:
                raise ValueError(f"Invalid time_minutes: {time_minutes}")
            
            if quality_rating and not (1 <= quality_rating <= 5):
                raise ValueError(f"Rating must be 1-5, got {quality_rating}")
            
            # TODO: Update task in database with completion info
            # This would call database CRUD function
            
            self.logger.debug(
                f"Recorded completion: task_id={task_id}, "
                f"time={time_minutes}min, rating={quality_rating}"
            )
            
            # Invalidate cache
            self._invalidate_cache()
            
            return True
            
        except ValueError as e:
            self.logger.error(f"Error recording completion: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error recording completion: {str(e)}")
            return False
    
    def get_completion_history(self, goal_id: int) -> List[Dict[str, Any]]:
        """
        Get all completed tasks for a goal.
        
        Args:
            goal_id: ID of the learning goal
        
        Returns:
            List of completed tasks with details:
            [{
                "id": int,
                "day_number": int,
                "task_text": str,
                "completed_at": str (ISO),
                "completion_time_minutes": int,
                "difficulty": float,
                "quality_rating": int
            }, ...]
        """
        try:
            if not isinstance(goal_id, int) or goal_id <= 0:
                raise ValueError(f"Invalid goal_id: {goal_id}")
            
            # Get all tasks for goal
            all_tasks = get_tasks_by_goal(goal_id)
            
            # Filter completed tasks and format
            completed = []
            for task in all_tasks:
                if hasattr(task, 'is_completed') and task.is_completed:
                    completed.append({
                        "id": task.id if hasattr(task, 'id') else None,
                        "day_number": task.day_number if hasattr(task, 'day_number') else None,
                        "task_text": task.task_text if hasattr(task, 'task_text') else None,
                        "completed_at": (
                            task.completed_at.isoformat() 
                            if hasattr(task, 'completed_at') else None
                        ),
                        "completion_time_minutes": (
                            task.completion_time_minutes 
                            if hasattr(task, 'completion_time_minutes') else 0
                        ),
                        "difficulty": (
                            task.difficulty_score 
                            if hasattr(task, 'difficulty_score') else 0
                        ),
                        "quality_rating": (
                            task.quality_rating 
                            if hasattr(task, 'quality_rating') else None
                        )
                    })
            
            self.logger.debug(f"Retrieved {len(completed)} completed tasks for goal_id={goal_id}")
            return completed
            
        except Exception as e:
            self.logger.error(f"Error getting completion history: {str(e)}")
            return []
    
    def get_performance_metrics(self, goal_id: int) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics for a goal.
        
        Calculates:
        - completion_rate: 0-1 float (completed / total)
        - avg_time: Average minutes per completed task
        - consistency: 0-10 score (inverse of std dev)
        - velocity: Tasks completed per week
        - difficulty_assessment: "too_easy", "appropriate", or "too_hard"
        - total_time_spent: Total minutes spent on goal
        - days_active: Number of days with activity
        
        Args:
            goal_id: ID of the learning goal
        
        Returns:
            Dictionary with all metrics:
            {
                "completion_rate": 0.75,
                "completion_percentage": "75.0%",
                "avg_time": 42.5,
                "consistency": 8.2,
                "velocity": 2.3,
                "difficulty_assessment": "appropriate",
                "total_time_spent": 512,
                "total_tasks": 20,
                "completed_tasks": 15,
                "days_active": 14
            }
        """
        try:
            # Check cache
            if goal_id in self._metrics_cache:
                self.logger.debug(f"Using cached metrics for goal_id={goal_id}")
                return self._metrics_cache[goal_id]
            
            if not isinstance(goal_id, int) or goal_id <= 0:
                raise ValueError(f"Invalid goal_id: {goal_id}")
            
            # Get all tasks
            all_tasks = get_tasks_by_goal(goal_id)
            
            if not all_tasks:
                return self._get_empty_metrics()
            
            # Separate completed and total
            completed_tasks = [t for t in all_tasks if hasattr(t, 'is_completed') and t.is_completed]
            total_tasks = len(all_tasks)
            
            # Calculate completion rate
            completion_rate = len(completed_tasks) / total_tasks if total_tasks > 0 else 0
            
            # Get completion times
            completion_times = [
                t.completion_time_minutes 
                for t in completed_tasks 
                if hasattr(t, 'completion_time_minutes') and t.completion_time_minutes
            ]
            
            # Calculate time metrics
            avg_time = mean(completion_times) if completion_times else 0
            total_time = sum(completion_times) if completion_times else 0
            
            # Calculate consistency score (0-10)
            consistency = self._calculate_consistency(completion_times)
            
            # Calculate velocity (tasks per week)
            velocity = self._calculate_velocity(goal_id, completed_tasks)
            
            # Assess difficulty match
            difficulty_assessment = self._assess_difficulty(completion_rate, consistency)
            
            # Calculate days active
            days_active = self._calculate_days_active(completed_tasks)
            
            # Build metrics dictionary
            metrics = {
                "completion_rate": round(completion_rate, 3),
                "completion_percentage": f"{completion_rate * 100:.1f}%",
                "avg_time": round(avg_time, 1),
                "consistency": round(consistency, 1),
                "velocity": round(velocity, 2),
                "difficulty_assessment": difficulty_assessment,
                "total_time_spent": int(total_time),
                "total_tasks": total_tasks,
                "completed_tasks": len(completed_tasks),
                "pending_tasks": total_tasks - len(completed_tasks),
                "days_active": days_active
            }
            
            # Cache metrics
            self._metrics_cache[goal_id] = metrics
            
            self.logger.debug(f"Calculated metrics for goal_id={goal_id}: {metrics}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {str(e)}")
            return self._get_empty_metrics()
    
    def get_learning_gaps(self, goal_id: int) -> List[str]:
        """
        Identify learning gaps based on incomplete/failed tasks.
        
        Args:
            goal_id: ID of the learning goal
        
        Returns:
            List of identified gaps (topic areas to focus on):
            ["Python syntax", "Functions", "Object-oriented programming"]
        """
        try:
            all_tasks = get_tasks_by_goal(goal_id)
            
            gaps = []
            for task in all_tasks:
                # Check if task was skipped
                if hasattr(task, 'is_completed') and not task.is_completed:
                    # Attempt to extract topic from task text
                    task_text = task.task_text if hasattr(task, 'task_text') else ""
                    if task_text and task_text not in gaps:
                        # Extract first few words as topic hint
                        topic = " ".join(task_text.split()[:3])
                        gaps.append(topic)
            
            self.logger.debug(f"Identified {len(gaps)} gaps for goal_id={goal_id}")
            return gaps[:5]  # Return top 5 gaps
            
        except Exception as e:
            self.logger.error(f"Error identifying learning gaps: {str(e)}")
            return []
    
    def get_topic_performance(self, goal_id: int, topic: str) -> Dict[str, Any]:
        """
        Get performance metrics for a specific topic.
        
        Args:
            goal_id: ID of the learning goal
            topic: Topic name to analyze
        
        Returns:
            Dictionary with topic-specific metrics:
            {
                "topic": "Python Basics",
                "total_tasks": 5,
                "completed": 4,
                "completion_rate": 0.8,
                "avg_time": 40,
                "difficulty_avg": 5.2
            }
        """
        try:
            all_tasks = get_tasks_by_goal(goal_id)
            
            # Filter tasks for this topic (simple matching)
            topic_tasks = [
                t for t in all_tasks
                if hasattr(t, 'task_text') and topic.lower() in t.task_text.lower()
            ]
            
            if not topic_tasks:
                return {"topic": topic, "error": "No tasks found for this topic"}
            
            completed = sum(1 for t in topic_tasks if hasattr(t, 'is_completed') and t.is_completed)
            
            times = [
                t.completion_time_minutes 
                for t in topic_tasks 
                if hasattr(t, 'completion_time_minutes') and t.completion_time_minutes
            ]
            
            difficulties = [
                t.difficulty_score 
                for t in topic_tasks 
                if hasattr(t, 'difficulty_score')
            ]
            
            return {
                "topic": topic,
                "total_tasks": len(topic_tasks),
                "completed": completed,
                "completion_rate": completed / len(topic_tasks) if topic_tasks else 0,
                "avg_time": round(mean(times), 1) if times else 0,
                "difficulty_avg": round(mean(difficulties), 1) if difficulties else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting topic performance: {str(e)}")
            return {}
    
    def _calculate_consistency(self, times: List[int]) -> float:
        """
        Calculate consistency score (0-10).
        
        Higher score = more consistent (lower variation).
        - score < 3: Very inconsistent
        - score 3-5: Somewhat inconsistent
        - score 5-7: Moderate consistency
        - score 7-9: Very consistent
        - score > 9: Extremely consistent
        """
        if not times or len(times) < 2:
            return 5.0  # Default mid-range
        
        try:
            # Calculate coefficient of variation
            mean_time = mean(times)
            if mean_time == 0:
                return 5.0
            
            std = stdev(times)
            cv = (std / mean_time) * 100  # Percentage
            
            # Convert to 0-10 scale (inverse: high variation = low score)
            consistency = 10 - (cv / 10)  # Assumes max 100% variation
            consistency = max(0, min(10, consistency))  # Clamp to 0-10
            
            return consistency
            
        except Exception as e:
            self.logger.warning(f"Error calculating consistency: {str(e)}")
            return 5.0
    
    def _calculate_velocity(self, goal_id: int, completed_tasks: List[Any]) -> float:
        """
        Calculate velocity in tasks per week.
        """
        if not completed_tasks:
            return 0.0
        
        try:
            # Get date range of completed tasks
            completed_dates = []
            for task in completed_tasks:
                if hasattr(task, 'completed_at') and task.completed_at:
                    completed_dates.append(task.completed_at)
            
            if not completed_dates or len(completed_dates) < 2:
                return 0.0
            
            # Calculate days between first and last completion
            min_date = min(completed_dates)
            max_date = max(completed_dates)
            days_elapsed = (max_date - min_date).days
            
            if days_elapsed == 0:
                return float(len(completed_tasks))  # All same day
            
            weeks_elapsed = days_elapsed / 7
            velocity = len(completed_tasks) / weeks_elapsed if weeks_elapsed > 0 else 0
            
            return velocity
            
        except Exception as e:
            self.logger.warning(f"Error calculating velocity: {str(e)}")
            return 0.0
    
    def _assess_difficulty(self, completion_rate: float, consistency: float) -> str:
        """
        Assess if task difficulty is appropriate.
        
        Returns: "too_easy", "appropriate", or "too_hard"
        """
        if completion_rate > 0.9 and consistency > 8:
            return "too_easy"
        elif completion_rate < 0.4:
            return "too_hard"
        else:
            return "appropriate"
    
    def _calculate_days_active(self, completed_tasks: List[Any]) -> int:
        """
        Calculate number of unique days with activity.
        """
        try:
            dates = set()
            for task in completed_tasks:
                if hasattr(task, 'completed_at') and task.completed_at:
                    dates.add(task.completed_at.date())
            return len(dates)
        except Exception as e:
            self.logger.warning(f"Error calculating days active: {str(e)}")
            return 0
    
    def _invalidate_cache(self) -> None:
        """Invalidate metrics cache when new data is recorded."""
        self._metrics_cache.clear()
        self.logger.debug("Invalidated metrics cache")
    
    @staticmethod
    def _get_empty_metrics() -> Dict[str, Any]:
        """Return empty metrics dictionary for goals with no tasks."""
        return {
            "completion_rate": 0.0,
            "completion_percentage": "0.0%",
            "avg_time": 0,
            "consistency": 5.0,
            "velocity": 0.0,
            "difficulty_assessment": "N/A",
            "total_time_spent": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "pending_tasks": 0,
            "days_active": 0
        }


class LearningMemoryManager:
    """
    Manager interface for learning memory operations.
    
    Provides a higher-level API for accessing learning metrics
    and progress tracking. Acts as a wrapper around LearningMemory.
    
    Example:
        >>> manager = LearningMemoryManager()
        >>> summary = manager.get_performance_summary(goal_id=1)
    """
    
    def __init__(self):
        """Initialize the learning memory manager."""
        self.memory = get_learning_memory()
    
    def get_performance_summary(self, goal_id: int) -> Dict[str, Any]:
        """
        Get a performance summary for a goal.
        
        Wraps get_performance_metrics() to provide a consistent interface.
        
        Args:
            goal_id: ID of the learning goal
        
        Returns:
            Dictionary with performance metrics
        """
        return self.memory.get_performance_metrics(goal_id)
    
    def record_task_completion(
        self,
        task_id: int,
        time_minutes: int,
        quality_rating: Optional[int] = None
    ) -> bool:
        """
        Record a task completion.
        
        Args:
            task_id: ID of the completed task
            time_minutes: Time spent on task in minutes
            quality_rating: Optional quality rating (1-5)
        
        Returns:
            True if recorded successfully
        """
        return self.memory.record_completion(
            task_id=task_id,
            time_minutes=time_minutes,
            quality_rating=quality_rating
        )
    
    def get_completion_history(self, goal_id: int) -> List[Dict[str, Any]]:
        """
        Get completion history for a goal.
        
        Args:
            goal_id: ID of the learning goal
        
        Returns:
            List of completed tasks
        """
        return self.memory.get_completion_history(goal_id)
    
    def get_learning_gaps(self, goal_id: int) -> List[str]:
        """
        Get identified learning gaps for a goal.
        
        Args:
            goal_id: ID of the learning goal
        
        Returns:
            List of learning gaps/weak areas
        """
        return self.memory.get_learning_gaps(goal_id)


# Singleton instance
_learning_memory_instance: Optional[LearningMemory] = None


def get_learning_memory() -> LearningMemory:
    """
    Get or create singleton instance of LearningMemory.
    
    Ensures only one learning memory instance exists throughout
    the application lifecycle.
    
    Returns:
        LearningMemory singleton instance
        
    Example:
        >>> memory = get_learning_memory()
        >>> metrics = memory.get_performance_metrics(goal_id=1)
    """
    global _learning_memory_instance
    if _learning_memory_instance is None:
        _learning_memory_instance = LearningMemory()
    return _learning_memory_instance
