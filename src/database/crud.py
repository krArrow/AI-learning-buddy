"""
CRUD (Create, Read, Update, Delete) operations for database models.
Provides a clean interface for database interactions.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from src.database.models import (
    LearningGoal, Roadmap, Task, Progress, 
    Conversation, Assessment
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LearningGoalCRUD:
    """CRUD operations for LearningGoal model."""
    
    @staticmethod
    def create(
        session: Session,
        goal_text: str,
        level: str,
        daily_minutes: int,
        learning_style: Optional[str] = None,
        pace: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> LearningGoal:
        """Create a new learning goal."""
        try:
            # Deactivate existing active goals
            session.query(LearningGoal).filter(
                LearningGoal.is_active == True
            ).update({"is_active": False})
            
            goal = LearningGoal(
                goal_text=goal_text,
                level=level,
                daily_minutes=daily_minutes,
                learning_style=learning_style or "visual",
                pace=pace or "medium",
                preferences=preferences or {},
                is_active=True
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)
            logger.info(f"Created learning goal: {goal.id}")
            return goal
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create learning goal: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_active(session: Session) -> Optional[LearningGoal]:
        """Get the currently active learning goal."""
        return session.query(LearningGoal).filter(
            LearningGoal.is_active == True
        ).first()
    
    @staticmethod
    def get_by_id(session: Session, goal_id: int) -> Optional[LearningGoal]:
        """Get a learning goal by ID."""
        return session.query(LearningGoal).filter(
            LearningGoal.id == goal_id
        ).first()
    
    @staticmethod
    def get_all(session: Session) -> List[LearningGoal]:
        """Get all learning goals."""
        return session.query(LearningGoal).order_by(
            desc(LearningGoal.created_at)
        ).all()
    
    @staticmethod
    def update(
        session: Session,
        goal_id: int,
        **kwargs
    ) -> Optional[LearningGoal]:
        """Update a learning goal."""
        try:
            goal = session.query(LearningGoal).filter(
                LearningGoal.id == goal_id
            ).first()
            
            if goal:
                for key, value in kwargs.items():
                    if hasattr(goal, key):
                        setattr(goal, key, value)
                session.commit()
                session.refresh(goal)
                logger.info(f"Updated learning goal: {goal_id}")
            return goal
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update learning goal {goal_id}: {e}", exc_info=True)
            raise


class RoadmapCRUD:
    """CRUD operations for Roadmap model."""
    
    @staticmethod
    def create(
        session: Session,
        goal_id: int,
        roadmap_json: str,
        modules_count: int,
        estimated_weeks: Optional[int] = None
    ) -> Roadmap:
        """Create a new roadmap."""
        try:
            roadmap = Roadmap(
                goal_id=goal_id,
                roadmap_json=roadmap_json,
                modules_count=modules_count,
                estimated_weeks=estimated_weeks
            )
            session.add(roadmap)
            session.commit()
            session.refresh(roadmap)
            logger.info(f"Created roadmap: {roadmap.id} for goal: {goal_id}")
            return roadmap
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create roadmap: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_by_goal_id(session: Session, goal_id: int) -> Optional[Roadmap]:
        """Get the latest roadmap for a goal."""
        return session.query(Roadmap).filter(
            Roadmap.goal_id == goal_id
        ).order_by(desc(Roadmap.created_at)).first()
    
    @staticmethod
    def get_all_by_goal_id(session: Session, goal_id: int) -> List[Roadmap]:
        """Get all roadmaps for a goal."""
        return session.query(Roadmap).filter(
            Roadmap.goal_id == goal_id
        ).order_by(desc(Roadmap.created_at)).all()


class TaskCRUD:
    """CRUD operations for Task model."""
    
    @staticmethod
    def create(
        session: Session,
        goal_id: int,
        day_number: int,
        task_text: str,
        why_text: Optional[str] = None,
        estimated_minutes: Optional[int] = None,
        resources_json: Optional[List[Dict[str, Any]]] = None,
        difficulty_score: Optional[float] = None
    ) -> Task:
        """Create a new task."""
        try:
            task = Task(
                goal_id=goal_id,
                day_number=day_number,
                task_text=task_text,
                why_text=why_text,
                estimated_minutes=estimated_minutes,
                resources_json=resources_json or [],
                difficulty_score=difficulty_score or 0.5
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            logger.info(f"Created task: {task.id} for day {day_number}")
            return task
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create task: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_by_goal_id(session: Session, goal_id: int) -> List[Task]:
        """Get all tasks for a goal."""
        return session.query(Task).filter(
            Task.goal_id == goal_id
        ).order_by(Task.day_number).all()
    
    @staticmethod
    def get_incomplete_tasks(session: Session, goal_id: int) -> List[Task]:
        """Get all incomplete tasks for a goal."""
        return session.query(Task).filter(
            and_(
                Task.goal_id == goal_id,
                Task.is_completed == False
            )
        ).order_by(Task.day_number).all()
    
    @staticmethod
    def mark_completed(
        session: Session,
        task_id: int,
        completion_time_minutes: Optional[int] = None
    ) -> Optional[Task]:
        """Mark a task as completed."""
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                task.is_completed = True
                task.completed_at = datetime.utcnow()
                task.completion_time_minutes = completion_time_minutes
                session.commit()
                session.refresh(task)
                logger.info(f"Marked task {task_id} as completed")
            return task
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to mark task {task_id} as completed: {e}", exc_info=True)
            raise


class ProgressCRUD:
    """CRUD operations for Progress model."""
    
    @staticmethod
    def create_or_update(
        session: Session,
        goal_id: int,
        progress_date: date,
        tasks_completed: int,
        tasks_total: int,
        notes: Optional[str] = None
    ) -> Progress:
        """Create or update progress record for a date."""
        try:
            progress = session.query(Progress).filter(
                and_(
                    Progress.goal_id == goal_id,
                    Progress.date == progress_date
                )
            ).first()
            
            completion_percentage = (
                (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0.0
            )
            
            if progress:
                progress.tasks_completed = tasks_completed
                progress.tasks_total = tasks_total
                progress.completion_percentage = completion_percentage
                progress.notes = notes
            else:
                progress = Progress(
                    goal_id=goal_id,
                    date=progress_date,
                    tasks_completed=tasks_completed,
                    tasks_total=tasks_total,
                    completion_percentage=completion_percentage,
                    notes=notes
                )
                session.add(progress)
            
            session.commit()
            session.refresh(progress)
            logger.info(f"Updated progress for {progress_date}: {completion_percentage:.1f}%")
            return progress
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create/update progress: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_by_goal_id(session: Session, goal_id: int) -> List[Progress]:
        """Get all progress records for a goal."""
        return session.query(Progress).filter(
            Progress.goal_id == goal_id
        ).order_by(desc(Progress.date)).all()


class ConversationCRUD:
    """CRUD operations for Conversation model."""
    
    @staticmethod
    def create(
        session: Session,
        goal_id: int,
        agent_type: str,
        user_message: str,
        ai_response: str
    ) -> Conversation:
        """Create a new conversation record."""
        try:
            conversation = Conversation(
                goal_id=goal_id,
                agent_type=agent_type,
                user_message=user_message,
                ai_response=ai_response
            )
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            logger.info(f"Created conversation: {conversation.id}")
            return conversation
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create conversation: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_by_goal_id(
        session: Session,
        goal_id: int,
        limit: Optional[int] = None
    ) -> List[Conversation]:
        """Get conversation history for a goal."""
        query = session.query(Conversation).filter(
            Conversation.goal_id == goal_id
        ).order_by(desc(Conversation.timestamp))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()


class AssessmentCRUD:
    """CRUD operations for Assessment model."""
    
    @staticmethod
    def create(
        session: Session,
        goal_id: int,
        question: str,
        user_answer: Optional[str] = None,
        is_correct: Optional[bool] = None,
        confidence_score: Optional[float] = None,
        gap_identified: Optional[str] = None
    ) -> Assessment:
        """Create a new assessment record."""
        try:
            assessment = Assessment(
                goal_id=goal_id,
                question=question,
                user_answer=user_answer,
                is_correct=is_correct,
                confidence_score=confidence_score,
                gap_identified=gap_identified
            )
            session.add(assessment)
            session.commit()
            session.refresh(assessment)
            logger.info(f"Created assessment: {assessment.id}")
            return assessment
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create assessment: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_by_goal_id(session: Session, goal_id: int) -> List[Assessment]:
        """Get all assessments for a goal."""
        return session.query(Assessment).filter(
            Assessment.goal_id == goal_id
        ).order_by(desc(Assessment.created_at)).all()


# ============================================================================
# Helper Functions for Common Operations
# ============================================================================

def create_progress_record(
    goal_id: int,
    completion_percentage: float,
    tasks_completed: int,
    tasks_total: int,
    notes: Optional[str] = None,
    session: Optional[Session] = None
) -> Progress:
    """
    Helper function to create or update a progress record.
    
    Args:
        goal_id: ID of the learning goal
        completion_percentage: Percentage of completion (0-100)
        tasks_completed: Number of tasks completed
        tasks_total: Total number of tasks
        notes: Optional notes about the progress
        session: Database session (creates new if not provided)
        
    Returns:
        Progress record
    """
    from src.database.db import DatabaseManager
    
    if session is None:
        session = DatabaseManager.get_session()
    
    try:
        return ProgressCRUD.create_or_update(
            session=session,
            goal_id=goal_id,
            progress_date=date.today(),
            tasks_completed=tasks_completed,
            tasks_total=tasks_total,
            notes=notes
        )
    except Exception as e:
        logger.error(f"Failed to create progress record: {e}", exc_info=True)
        raise
    finally:
        if session:
            session.close()


# ============================================================================
# Conversation Helper Functions
# ============================================================================

def create_conversation(
    goal_id: int,
    agent_type: str,
    user_message: str,
    ai_response: str,
    session: Optional[Session] = None
) -> Conversation:
    """
    Helper function to create a conversation record.
    
    Args:
        goal_id: ID of the learning goal
        agent_type: Type of agent handling the conversation
        user_message: User's message
        ai_response: AI's response
        session: Database session (creates new if not provided)
        
    Returns:
        Conversation record
    """
    from src.database.db import DatabaseManager
    
    if session is None:
        session = DatabaseManager.get_session()
    
    try:
        return ConversationCRUD.create(
            session=session,
            goal_id=goal_id,
            agent_type=agent_type,
            user_message=user_message,
            ai_response=ai_response
        )
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}", exc_info=True)
        raise
    finally:
        if session:
            session.close()


def get_conversations(
    goal_id: int,
    limit: Optional[int] = None,
    session: Optional[Session] = None
) -> List[Conversation]:
    """
    Helper function to get conversation history for a goal.
    
    Args:
        goal_id: ID of the learning goal
        limit: Maximum number of conversations to retrieve
        session: Database session (creates new if not provided)
        
    Returns:
        List of conversation records
    """
    from src.database.db import DatabaseManager
    
    if session is None:
        session = DatabaseManager.get_session()
    
    try:
        return ConversationCRUD.get_by_goal_id(
            session=session,
            goal_id=goal_id,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}", exc_info=True)
        return []
    finally:
        if session:
            session.close()


def delete_goal_conversations(
    goal_id: int,
    session: Optional[Session] = None
) -> int:
    """
    Helper function to delete all conversations for a goal.
    
    Args:
        goal_id: ID of the learning goal
        session: Database session (creates new if not provided)
        
    Returns:
        Number of conversations deleted
    """
    from src.database.db import DatabaseManager
    
    if session is None:
        session = DatabaseManager.get_session()
    
    try:
        count = session.query(Conversation).filter(
            Conversation.goal_id == goal_id
        ).delete()
        session.commit()
        logger.info(f"Deleted {count} conversations for goal {goal_id}")
        return count
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete conversations: {e}", exc_info=True)
        raise
    finally:
        if session:
            session.close()


# ============================================================================
# Task Helper Functions
# ============================================================================

def get_tasks_by_goal(
    goal_id: int,
    session: Optional[Session] = None
) -> List[Task]:
    """
    Helper function to get all tasks for a goal.
    
    Args:
        goal_id: ID of the learning goal
        session: Database session (creates new if not provided)
        
    Returns:
        List of task records
    """
    from src.database.db import DatabaseManager
    
    if session is None:
        session = DatabaseManager.get_session()
    
    try:
        return TaskCRUD.get_by_goal_id(
            session=session,
            goal_id=goal_id
        )
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}", exc_info=True)
        return []
    finally:
        if session:
            session.close()


# ============================================================================
# Progress Helper Functions
# ============================================================================

def get_progress_records(
    goal_id: int,
    session: Optional[Session] = None
) -> List[Progress]:
    """
    Helper function to get all progress records for a goal.
    
    Args:
        goal_id: ID of the learning goal
        session: Database session (creates new if not provided)
        
    Returns:
        List of progress records
    """
    from src.database.db import DatabaseManager
    
    if session is None:
        session = DatabaseManager.get_session()
    
    try:
        return ProgressCRUD.get_by_goal_id(
            session=session,
            goal_id=goal_id
        )
    except Exception as e:
        logger.error(f"Failed to get progress records: {e}", exc_info=True)
        return []
    finally:
        if session:
            session.close()
