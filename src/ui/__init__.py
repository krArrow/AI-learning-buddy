"""
UI Pages Module
Day 5: All Streamlit page modules
"""

from src.ui.pages import home
from src.ui.pages import create_goal
from src.ui.pages import view_plan
from src.ui.pages import daily_tasks
from src.ui.pages import progress
from src.ui.pages import insights

__all__ = [
    'home',
    'create_goal',
    'view_plan',
    'daily_tasks',
    'progress',
    'insights'
]