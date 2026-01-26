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
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

Base = declarative_base()


class LearningGoal(Base):
    """
    Represents a user's learning goal with preferences and metadata.
    """
    __tablename__ = "learning_goals"
    
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    goal_text: Mapped[str] = Column(String(500), nullable=False, index=True)
    level: Mapped[str] = Column(
        String(50), 
        nullable=False,
        default="beginner",
        comment="beginner, intermediate, or advanced"
    )
    daily_minutes: Mapped[int] = Column(Integer, nullable=False, default=30)
    learning_style: Mapped[Optional[str]] = Column(
        String(50),
        nullable=True,
        default="visual",
        comment="visual, kinesthetic, auditory, or reading_writing"
    )
    pace: Mapped[Optional[str]] = Column(
        String(50),
        nullable=True,
        default="medium",
        comment="slow, medium, or fast"
    )
    preferences: Mapped[Optional[Dict[str, Any]]] = Column(JSON, nullable=True, default=dict)
    
    # User's Target Completion Timeline
    target_completion_days: Mapped[Optional[int]] = Column(
        Integer,
        nullable=True,
        comment="User's target days to complete the goal"
    )
    target_display_text: Mapped[Optional[str]] = Column(
        String(100),
        nullable=True,
        comment="Human-readable target (e.g., '30 Days', '3 Months')"
    )
    
    created_at: Mapped[datetime] = Column(
        DateTime, 
        nullable=False, 
        default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = Column(
        DateTime, 
        nullable=False, 
        default=func.now(),
        onupdate=func.now()
    )
    is_active: Mapped[bool] = Column(Boolean, nullable=False, default=True, index=True)
    
    # Relationships
    roadmaps: Mapped[List["Roadmap"]] = relationship(
        "Roadmap", 
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    progress_records: Mapped[List["Progress"]] = relationship(
        "Progress",
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    assessments: Mapped[List["Assessment"]] = relationship(
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
    
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: Mapped[int] = Column(
        Integer, 
        ForeignKey("learning_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    roadmap_json: Mapped[str] = Column(
        Text,
        nullable=False,
        comment="Full roadmap structure as JSON string"
    )
    modules_count: Mapped[int] = Column(Integer, nullable=False, default=0)
    estimated_weeks: Mapped[Optional[int]] = Column(Integer, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    goal: Mapped["LearningGoal"] = relationship("LearningGoal", back_populates="roadmaps")
    
    def __repr__(self) -> str:
        return f"<Roadmap(id={self.id}, goal_id={self.goal_id}, modules={self.modules_count})>"


class Task(Base):
    """
    Represents a daily learning task with completion tracking.
    """
    __tablename__ = "tasks"
    
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: Mapped[int] = Column(
        Integer,
        ForeignKey("learning_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    day_number: Mapped[int] = Column(Integer, nullable=False, index=True)
    task_text: Mapped[str] = Column(String(1000), nullable=False)
    why_text: Mapped[Optional[str]] = Column(Text, nullable=True)
    estimated_minutes: Mapped[Optional[int]] = Column(Integer, nullable=True)
    resources_json: Mapped[Optional[List[Dict[str, Any]]]] = Column(
        JSON,
        nullable=True,
        default=list,
        comment="List of learning resources"
    )
    difficulty_score: Mapped[Optional[float]] = Column(
        Float,
        nullable=True,
        default=0.5,
        comment="Difficulty score between 0.0 and 1.0"
    )
    is_completed: Mapped[bool] = Column(Boolean, nullable=False, default=False, index=True)
    completed_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    completion_time_minutes: Mapped[Optional[int]] = Column(Integer, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    goal: Mapped["LearningGoal"] = relationship("LearningGoal", back_populates="tasks")
    
    def __repr__(self) -> str:
        status = "✓" if self.is_completed else "○"
        return f"<Task(id={self.id}, day={self.day_number}, {status} '{self.task_text[:50]}...')>"


class Progress(Base):
    """
    Tracks daily progress metrics for a learning goal.
    """
    __tablename__ = "progress"
    
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: Mapped[int] = Column(
        Integer,
        ForeignKey("learning_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    date: Mapped[datetime] = Column(Date, nullable=False, index=True)
    tasks_completed: Mapped[int] = Column(Integer, nullable=False, default=0)
    tasks_total: Mapped[int] = Column(Integer, nullable=False, default=0)
    completion_percentage: Mapped[float] = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Percentage of tasks completed"
    )
    notes: Mapped[Optional[str]] = Column(Text, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    goal: Mapped["LearningGoal"] = relationship("LearningGoal", back_populates="progress_records")
    
    def __repr__(self) -> str:
        return f"<Progress(id={self.id}, date={self.date}, {self.completion_percentage:.1f}%)>"


class Conversation(Base):
    """
    Stores conversation history between user and AI agents.
    """
    __tablename__ = "conversations"
    
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: Mapped[int] = Column(
        Integer,
        ForeignKey("learning_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_type: Mapped[str] = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of agent that handled the conversation"
    )
    user_message: Mapped[str] = Column(Text, nullable=False)
    ai_response: Mapped[str] = Column(Text, nullable=False)
    timestamp: Mapped[datetime] = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        index=True
    )
    
    # Relationships
    goal: Mapped["LearningGoal"] = relationship("LearningGoal", back_populates="conversations")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, agent='{self.agent_type}', time={self.timestamp})>"


class Assessment(Base):
    """
    Stores assessment questions and answers for knowledge gap detection.
    """
    __tablename__ = "assessments"
    
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: Mapped[int] = Column(
        Integer,
        ForeignKey("learning_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question: Mapped[str] = Column(Text, nullable=False)
    user_answer: Mapped[Optional[str]] = Column(Text, nullable=True)
    is_correct: Mapped[Optional[bool]] = Column(Boolean, nullable=True)
    confidence_score: Mapped[Optional[float]] = Column(
        Float,
        nullable=True,
        comment="User's confidence in their answer (0.0 to 1.0)"
    )
    gap_identified: Mapped[Optional[str]] = Column(
        String(500),
        nullable=True,
        comment="Identified knowledge gap if answer was incorrect"
    )
    created_at: Mapped[datetime] = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        index=True
    )
    
    # Relationships
    goal: Mapped["LearningGoal"] = relationship("LearningGoal", back_populates="assessments")
    
    def __repr__(self) -> str:
        correct_mark = "✓" if self.is_correct else "✗" if self.is_correct is not None else "?"
        return f"<Assessment(id={self.id}, {correct_mark} question='{self.question[:50]}...')>"
