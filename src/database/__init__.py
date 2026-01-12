"""
Database models, connection management, and CRUD operations.
"""
from src.database.models import (
    Base, LearningGoal, Roadmap, Task, 
    Progress, Conversation, Assessment
)
from src.database.db import (
    DatabaseManager, db_manager, 
    init_database, get_db
)
from src.database.crud import (
    LearningGoalCRUD, RoadmapCRUD, TaskCRUD,
    ProgressCRUD, ConversationCRUD, AssessmentCRUD
)

__all__ = [
    # Models
    "Base",
    "LearningGoal",
    "Roadmap",
    "Task",
    "Progress",
    "Conversation",
    "Assessment",
    # Database Manager
    "DatabaseManager",
    "db_manager",
    "init_database",
    "get_db",
    # CRUD Operations
    "LearningGoalCRUD",
    "RoadmapCRUD",
    "TaskCRUD",
    "ProgressCRUD",
    "ConversationCRUD",
    "AssessmentCRUD"
]
