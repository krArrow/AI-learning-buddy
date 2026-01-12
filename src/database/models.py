"""
SQLAlchemy ORM models for the AI Learning Buddy application.
Defines the database schema with proper relationships and constraints.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, 
    DateTime, Date, ForeignKey, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class LearningGoal(Base):
    """
    Represents a user's learning goal with preferences and metadata.
    """
    __tablename__ = "learning_goals"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    goal_text: str = Column(String(500), nullable=False, index=True)
    level: str = Column(
        String(50), 
        nullable=False,
        default="beginner",
        comment="beginner, intermediate, or advanced"
    )
    daily_minutes: int = Column(Integer, nullable=False, default=30)
    learning_style: str = Column(
        String(50),
        nullable=True,
        default="visual",
        comment="visual, kinesthetic, auditory, or reading"
    )
    pace: str = Column(
        String(50),
        nullable=True,
        default="medium",
        comment="slow, medium, or fast"
    )
    preferences: Dict[str, Any] = Column(JSON, nullable=True, default=dict)
    created_at: datetime = Column(
        DateTime, 
        nullable=False, 
        default=func.now(),
        index=True
    )
    updated_at: datetime = Column(
        DateTime, 
        nullable=False, 
        default=func.now(),
        onupdate=func.now()
    )
    is_active: bool = Column(Boolean, nullable=False, default=True, index=True)
    
    # Relationships
    roadmaps: List["Roadmap"] = relationship(
        "Roadmap", 
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    tasks: List["Task"] = relationship(
        "Task",
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    progress_records: List["Progress"] = relationship(
        "Progress",
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    conversations: List["Conversation"] = relationship(
        "Conversation",
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    assessments: List["Assessment"] = relationship(
        "Assessment",
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<LearningGoal(id={self.id}, goal='{self.goal_text[:50]}...', level='{self.level}')>"


class Roadmap(Base):
    """
    Represents a generated learning roadmap for a goal.
    """
    __tablename__ = "roadmaps"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: int = Column(
        Integer, 
        ForeignKey("learning_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    roadmap_json: str = Column(
        Text,
        nullable=False,
        comment="Full roadmap structure as JSON string"
    )
    modules_count: int = Column(Integer, nullable=False, default=0)
    estimated_weeks: int = Column(Integer, nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    goal: LearningGoal = relationship("LearningGoal", back_populates="roadmaps")
    
    def __repr__(self) -> str:
        return f"<Roadmap(id={self.id}, goal_id={self.goal_id}, modules={self.modules_count})>"


class Task(Base):
    """
    Represents a daily learning task with completion tracking.
    """
    __tablename__ = "tasks"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: int = Column(
        Integer,
        ForeignKey("learning_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    day_number: int = Column(Integer, nullable=False, index=True)
    task_text: str = Column(String(1000), nullable=False)
    why_text: str = Column(Text, nullable=True)
    estimated_minutes: int = Column(Integer, nullable=True)
    resources_json: List[Dict[str, Any]] = Column(
        JSON,
        nullable=True,
        default=list,
        comment="List of learning resources"
    )
    difficulty_score: float = Column(
        Float,
        nullable=True,
        default=0.5,
        comment="Difficulty score between 0.0 and 1.0"
    )
    is_completed: bool = Column(Boolean, nullable=False, default=False, index=True)
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)
    completion_time_minutes: Optional[int] = Column(Integer, nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    goal: LearningGoal = relationship("LearningGoal", back_populates="tasks")
    
    def __repr__(self) -> str:
        status = "✓" if self.is_completed else "○"
        return f"<Task(id={self.id}, day={self.day_number}, {status} '{self.task_text[:50]}...')>"


class Progress(Base):
    """
    Tracks daily progress metrics for a learning goal.
    """
    __tablename__ = "progress"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: int = Column(
        Integer,
        ForeignKey("learning_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    date: datetime = Column(Date, nullable=False, index=True)
    tasks_completed: int = Column(Integer, nullable=False, default=0)
    tasks_total: int = Column(Integer, nullable=False, default=0)
    completion_percentage: float = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Percentage of tasks completed"
    )
    notes: str = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    goal: LearningGoal = relationship("LearningGoal", back_populates="progress_records")
    
    def __repr__(self) -> str:
        return f"<Progress(id={self.id}, date={self.date}, {self.completion_percentage:.1f}%)>"


class Conversation(Base):
    """
    Stores conversation history between user and AI agents.
    """
    __tablename__ = "conversations"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: int = Column(
        Integer,
        ForeignKey("learning_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_type: str = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of agent that handled the conversation"
    )
    user_message: str = Column(Text, nullable=False)
    ai_response: str = Column(Text, nullable=False)
    timestamp: datetime = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        index=True
    )
    
    # Relationships
    goal: LearningGoal = relationship("LearningGoal", back_populates="conversations")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, agent='{self.agent_type}', time={self.timestamp})>"


class Assessment(Base):
    """
    Stores assessment questions and answers for knowledge gap detection.
    """
    __tablename__ = "assessments"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: int = Column(
        Integer,
        ForeignKey("learning_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question: str = Column(Text, nullable=False)
    user_answer: str = Column(Text, nullable=True)
    is_correct: bool = Column(Boolean, nullable=True)
    confidence_score: float = Column(
        Float,
        nullable=True,
        comment="User's confidence in their answer (0.0 to 1.0)"
    )
    gap_identified: str = Column(
        String(500),
        nullable=True,
        comment="Identified knowledge gap if answer was incorrect"
    )
    created_at: datetime = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        index=True
    )
    
    # Relationships
    goal: LearningGoal = relationship("LearningGoal", back_populates="assessments")
    
    def __repr__(self) -> str:
        correct_mark = "✓" if self.is_correct else "✗" if self.is_correct is not None else "?"
        return f"<Assessment(id={self.id}, {correct_mark} question='{self.question[:50]}...')>"
