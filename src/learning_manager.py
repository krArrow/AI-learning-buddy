"""
Learning Manager - Orchestrates the prompt chain and manages learning state
This is the core business logic that ties everything together
"""

import re
from typing import Dict, List, Optional, Tuple
from src.llm_service import get_llm_service
from src.storage import get_storage_manager
from src import prompts


class LearningManager:
    """
    Orchestrates the 3-prompt chain:
    1. Goal → Roadmap
    2. Roadmap → Initial Tasks
    3. Progress → Adapted Tasks
    """
    
    def __init__(self):
        self.llm = get_llm_service()
        self.storage = get_storage_manager()
    
    def create_learning_plan(self, goal: str, level: str, daily_minutes: int) -> Dict:
        """
        Execute Prompt Chain 1 + 2: Create initial learning plan
        
        Returns:
            Dict with goal_id, roadmap, and initial tasks
        """
        # Step 1: Save goal
        goal_id = self.storage.save_goal(goal, level, daily_minutes)
        
        # Step 2: Generate roadmap (Prompt 1)
        print("🔄 Generating learning roadmap...")
        roadmap_prompt = prompts.get_prompt_1(goal, level, daily_minutes)
        roadmap = self.llm.generate_roadmap(roadmap_prompt)
        self.storage.save_roadmap(goal_id, roadmap)
        
        # Step 3: Generate initial daily tasks (Prompt 2)
        print("🔄 Generating daily tasks...")
        tasks_prompt = prompts.get_prompt_2(goal, level, daily_minutes, roadmap)
        tasks_text = self.llm.generate_tasks(tasks_prompt)
        
        # Parse and save tasks
        tasks = self._parse_tasks(tasks_text)
        if tasks:
            self.storage.save_tasks(goal_id, tasks)
        
        return {
            'goal_id': goal_id,
            'roadmap': roadmap,
            'tasks': tasks
        }
    
    def adapt_plan(self, goal_id: int) -> List[Dict]:
        """
        Execute Prompt Chain 3: Adapt plan based on progress
        
        Returns:
            List of new adapted tasks
        """
        # Get goal details
        goal_data = self.storage.get_active_goal()
        if not goal_data:
            raise ValueError("No active goal found")
        
        # Get roadmap
        roadmap = self.storage.get_roadmap(goal_id)
        if not roadmap:
            raise ValueError("No roadmap found for this goal")
        
        # Get completed and incomplete tasks
        completed = self.storage.get_tasks(goal_id, completed=True)
        incomplete = self.storage.get_tasks(goal_id, completed=False)
        
        # Format task lists for prompt
        completed_text = self._format_tasks_for_prompt(completed)
        incomplete_text = self._format_tasks_for_prompt(incomplete)
        
        # Get current max day number
        all_tasks = self.storage.get_tasks(goal_id)
        max_day = max([t['day_number'] for t in all_tasks]) if all_tasks else 0
        
        # Generate adapted tasks (Prompt 3)
        print("🔄 Adapting plan based on your progress...")
        adapt_prompt = prompts.get_prompt_3(
            goal_data['goal'],
            goal_data['level'],
            goal_data['daily_minutes'],
            roadmap,
            completed_text,
            incomplete_text
        )
        adapted_text = self.llm.adapt_tasks(adapt_prompt)
        
        # Parse new tasks (starting from max_day + 1)
        new_tasks = self._parse_tasks(adapted_text, start_day=max_day + 1)
        
        if new_tasks:
            self.storage.save_tasks(goal_id, new_tasks)
        
        return new_tasks
    
    def _parse_tasks(self, tasks_text: str, start_day: int = 1) -> List[Dict]:
        """
        Parse LLM-generated tasks into structured format
        
        Expected format:
        DAY X:
        Task: ...
        Why: ...
        Estimated Time: X minutes
        """
        tasks = []
        
        # Split by DAY markers
        day_sections = re.split(r'DAY \d+:', tasks_text)
        day_sections = [s.strip() for s in day_sections if s.strip()]
        
        for idx, section in enumerate(day_sections):
            day_num = start_day + idx
            
            # Extract task, why, and time
            task_match = re.search(r'Task:\s*(.+?)(?=\n|Why:|Estimated|$)', section, re.DOTALL)
            why_match = re.search(r'Why:\s*(.+?)(?=\n|Estimated|$)', section, re.DOTALL)
            time_match = re.search(r'Estimated Time:\s*(\d+)', section)
            
            if task_match:
                task_text = task_match.group(1).strip()
                why_text = why_match.group(1).strip() if why_match else ""
                estimated_minutes = int(time_match.group(1)) if time_match else 0
                
                tasks.append({
                    'day_number': day_num,
                    'task_text': task_text,
                    'why_text': why_text,
                    'estimated_minutes': estimated_minutes
                })
        
        return tasks
    
    def _format_tasks_for_prompt(self, tasks: List[Dict]) -> str:
        """Format tasks for inclusion in prompts"""
        if not tasks:
            return "None"
        
        formatted = []
        for task in tasks:
            formatted.append(f"Day {task['day_number']}: {task['task_text']}")
        
        return "\n".join(formatted)
    
    def get_current_state(self) -> Optional[Dict]:
        """
        Get current learning state
        
        Returns:
            Dict with goal, roadmap, tasks, and progress
        """
        goal = self.storage.get_active_goal()
        if not goal:
            return None
        
        goal_id = goal['id']
        roadmap = self.storage.get_roadmap(goal_id)
        tasks = self.storage.get_tasks(goal_id)
        progress = self.storage.get_progress_summary(goal_id)
        
        return {
            'goal': goal,
            'roadmap': roadmap,
            'tasks': tasks,
            'progress': progress
        }
    
    def mark_task_complete(self, task_id: int, completed: bool = True):
        """Mark a task as complete or incomplete"""
        self.storage.mark_task_complete(task_id, completed)


# Singleton instance
_learning_manager = None

def get_learning_manager() -> LearningManager:
    """Get or create learning manager instance"""
    global _learning_manager
    if _learning_manager is None:
        _learning_manager = LearningManager()
    return _learning_manager