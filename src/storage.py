"""
Storage Manager - SQLite-based persistence
Handles all database operations for learning plans and progress
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from pathlib import Path


class StorageManager:
    """
    Manages persistence of learning goals, plans, and progress using SQLite.
    
    Schema:
    - learning_goals: Stores user goals and metadata
    - roadmaps: Stores generated learning roadmaps
    - tasks: Stores daily tasks with completion status
    """
    
    def __init__(self, db_path: str = "data/learning_buddy.db"):
        """Initialize storage and create tables if needed"""
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        self._create_tables()
    
    def _create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()
        
        # Learning goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                level TEXT NOT NULL,
                daily_minutes INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Roadmaps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roadmaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                roadmap_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES learning_goals(id)
            )
        """)
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                day_number INTEGER NOT NULL,
                task_text TEXT NOT NULL,
                why_text TEXT,
                estimated_minutes INTEGER,
                is_completed BOOLEAN DEFAULT 0,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES learning_goals(id)
            )
        """)
        
        self.conn.commit()
    
    def save_goal(self, goal: str, level: str, daily_minutes: int) -> int:
        """
        Save a new learning goal and deactivate previous ones
        
        Returns:
            goal_id: ID of the newly created goal
        """
        cursor = self.conn.cursor()
        
        # Deactivate all previous goals
        cursor.execute("UPDATE learning_goals SET is_active = 0")
        
        # Insert new goal
        cursor.execute("""
            INSERT INTO learning_goals (goal, level, daily_minutes)
            VALUES (?, ?, ?)
        """, (goal, level, daily_minutes))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def save_roadmap(self, goal_id: int, roadmap_text: str):
        """Save generated roadmap"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO roadmaps (goal_id, roadmap_text)
            VALUES (?, ?)
        """, (goal_id, roadmap_text))
        self.conn.commit()
    
    def save_tasks(self, goal_id: int, tasks: List[Dict[str, any]]):
        """
        Save multiple tasks
        
        Args:
            goal_id: Associated goal ID
            tasks: List of dicts with keys: day_number, task_text, why_text, estimated_minutes
        """
        cursor = self.conn.cursor()
        
        for task in tasks:
            cursor.execute("""
                INSERT INTO tasks (goal_id, day_number, task_text, why_text, estimated_minutes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                goal_id,
                task['day_number'],
                task['task_text'],
                task.get('why_text', ''),
                task.get('estimated_minutes', 0)
            ))
        
        self.conn.commit()
    
    def get_active_goal(self) -> Optional[Dict]:
        """Get the current active learning goal"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM learning_goals
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_roadmap(self, goal_id: int) -> Optional[str]:
        """Get roadmap for a goal"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT roadmap_text FROM roadmaps
            WHERE goal_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (goal_id,))
        row = cursor.fetchone()
        return row['roadmap_text'] if row else None
    
    def get_tasks(self, goal_id: int, completed: Optional[bool] = None) -> List[Dict]:
        """
        Get tasks for a goal
        
        Args:
            goal_id: Goal ID
            completed: If True, only completed tasks. If False, only incomplete. If None, all tasks.
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM tasks WHERE goal_id = ?"
        params = [goal_id]
        
        if completed is not None:
            query += " AND is_completed = ?"
            params.append(1 if completed else 0)
        
        query += " ORDER BY day_number ASC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_task_complete(self, task_id: int, completed: bool = True):
        """Mark a task as complete or incomplete"""
        cursor = self.conn.cursor()
        
        if completed:
            cursor.execute("""
                UPDATE tasks
                SET is_completed = 1, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (task_id,))
        else:
            cursor.execute("""
                UPDATE tasks
                SET is_completed = 0, completed_at = NULL
                WHERE id = ?
            """, (task_id,))
        
        self.conn.commit()
    
    def get_progress_summary(self, goal_id: int) -> Dict:
        """Get progress statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed_tasks
            FROM tasks
            WHERE goal_id = ?
        """, (goal_id,))
        
        row = cursor.fetchone()
        total = row['total_tasks']
        completed = row['completed_tasks']
        
        return {
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': (completed / total * 100) if total > 0 else 0
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()


# Singleton instance
_storage_manager = None

def get_storage_manager() -> StorageManager:
    """Get or create storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager