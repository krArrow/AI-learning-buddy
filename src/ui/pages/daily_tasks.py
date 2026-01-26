"""
Daily Tasks Page - View and Complete Learning Tasks
Day 5: Display current task, resources, and track completion
"""

import streamlit as st
from typing import Dict, Optional
import json
import time

from src.ui.utils import (
    get_active_goal, get_tasks_for_goal, get_current_task,
    mark_task_complete, get_resource_emoji, format_duration,
    run_adaptation_loop, get_current_state
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def show():
    """Display the daily tasks page"""
    
    st.markdown('<h1 class="main-header">✅ Daily Learning Tasks</h1>', unsafe_allow_html=True)
    
    try:
        # Check for active goal
        goal = get_active_goal()
        
        if not goal:
            st.warning("⚠️ No active learning goal found.")
            
            if st.button("🎯 Create New Goal", width='stretch'):
                st.session_state.current_page = "Create Goal"
                st.rerun()
            
            return
        
        # Validate goal data
        if not all(k in goal for k in ["id", "goal_text", "level"]):
            st.error("❌ Invalid goal data. Please create a new goal.")
            if st.button("🎯 Create New Goal", width='stretch'):
                st.session_state.current_page = "Create Goal"
                st.rerun()
            return
        
        # Get tasks - try module_tasks format first (new 4-phase flow)
        state = get_current_state()
        
        # Convert module tasks to displayable format
        if state.get("module_tasks") and state.get("populated_roadmap"):
            from src.ui.utils import convert_module_tasks_to_display_format
            tasks = convert_module_tasks_to_display_format(state)
        else:
            # Fall back to old task table format
            tasks = get_tasks_for_goal(goal["id"])
        
        if not tasks:
            st.warning("📋 No tasks have been generated yet.")
            st.info("Tasks are usually generated when you create a goal. Try creating a new goal or regenerating tasks.")
            
            if st.button("🔄 Generate Tasks", width='stretch'):
                with st.spinner("Generating tasks..."):
                    state = get_current_state()
                    updated_state = run_adaptation_loop(state)
                    
                    if updated_state.get("tasks"):
                        st.success("Tasks generated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to generate tasks")
            
            return
        
        # Validate tasks data
        if not isinstance(tasks, list) or len(tasks) == 0:
            st.error("❌ No valid tasks found.")
            return
        
        # Get current task
        current_task = get_current_task(goal["id"])
        
        if current_task:
            show_current_task(current_task, tasks)
        else:
            show_all_complete(goal, tasks)
    
    except Exception as e:
        logger.error(f"Error displaying daily tasks: {e}", exc_info=True)
        st.error(f"❌ An error occurred while loading tasks: {e}")
        
        if st.button("🔄 Retry"):
            st.rerun()
        
        if st.button("🏠 Back to Home"):
            st.session_state.current_page = "Home"
            st.rerun()


def show_current_task(task: Dict, all_tasks: list):
    """Display the current task to complete"""
    
    # Handle both old and new task formats
    day_num = task.get('day_number', task.get('day', 1))
    task_title = task.get('task_text', task.get('task_title', 'Task'))
    why_text = task.get('why_text', task.get('task_description', ''))
    estimated = task.get('estimated_minutes', 30)
    difficulty = task.get('difficulty_score', task.get('difficulty', 5))
    resources = task.get('resources', [])
    
    st.markdown(f"### 📝 Day {day_num} Task")
    
    # Task header
    st.markdown(f"## {task_title}")
    
    # Module context (if available in new format)
    if 'module_title' in task:
        st.caption(f"📚 Module: {task['module_title']}")
    
    # Metadata row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Day", day_num)
    
    with col2:
        difficulty_val = difficulty if isinstance(difficulty, (int, float)) else 5
        if difficulty_val > 1:
            st.metric("Difficulty", f"{difficulty_val}/10")
        else:
            # 0-1 scale (from new format)
            difficulty_pct = int(difficulty_val * 10)
            st.metric("Difficulty", f"{difficulty_pct}/10")
    
    with col3:
        st.metric("Time", format_duration(int(estimated)))
    
    with col4:
        completed = sum(1 for t in all_tasks if t.get('is_completed') or (isinstance(t, dict) and 'completed_at' in t and t['completed_at']))
        total = len(all_tasks)
        st.metric("Progress", f"{completed}/{total}")
    
    st.markdown("---")
    
    # Why this task?
    st.markdown("### 🎯 Why This Task?")
    st.info(why_text if why_text else "This task builds on your previous learning and moves you toward your goal.")
    
    st.markdown("---")
    
    # Resources
    show_task_resources(task, resources)
    
    st.markdown("---")
    
    # Action buttons
    show_task_actions(task, all_tasks)
    
    st.markdown("---")
    
    # Next task preview
    show_next_task_preview(task, all_tasks)


def show_task_resources(task: Dict):
    """Display resources for the task"""
    
    st.markdown("### 📚 Learning Resources")
    
    # Handle both old and new resource formats
    resources = task.get('resources', [])
    if not resources:
        resources = task.get('resources_used', [])
    
    if isinstance(resources, str):
        try:
            resources = json.loads(resources)
        except:
            resources = []
    
    if not resources:
        st.info("No specific resources for this task. Use your preferred learning materials.")
        return
    
    # Display resources
    for idx, resource in enumerate(resources):
        if isinstance(resource, dict):
            title = resource.get('title', f'Resource {idx + 1}')
            url = resource.get('url', resource.get('link', ''))
            res_type = resource.get('type', resource.get('resource_type', 'resource'))
            description = resource.get('description', '')
            
            emoji = get_resource_emoji(res_type)
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Create clickable link if URL exists, otherwise just show the title
                    if url and url.startswith('http'):
                        st.markdown(f"{emoji} **[{title}]({url})**")
                    else:
                        st.markdown(f"{emoji} **{title}**")
                    
                    if description:
                        st.caption(description)
                
                with col2:
                    st.caption(f"_{res_type}_")
        
        elif isinstance(resource, str):
            # Simple string resource
            st.write(f"📌 {resource}")
        
        else:
            # Fallback for other types
            st.write(f"📌 Resource {idx + 1}")
    
    # Tips
    with st.expander("💡 Tips for Using Resources"):
        st.markdown("""
        - **Videos**: Take notes while watching
        - **Articles**: Highlight key concepts
        - **Documentation**: Try the examples
        - **Tutorials**: Code along step-by-step
        - **Interactive**: Complete all exercises
        """)


def show_task_actions(task: Dict, all_tasks: list):
    """Display action buttons for task completion"""
    
    st.markdown("### ⚡ Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Mark as Complete", width='stretch', type="primary"):
            # Get task ID (handle both formats)
            task_id = task.get('id', task.get('task_id'))
            
            if not task_id:
                st.error("Cannot mark task complete: no task ID found")
                return
            
            try:
                # Update in database
                success = mark_task_complete(task_id)
                
                if success:
                    st.session_state.last_completed_task = task
                    st.success("🎉 Great job! Task completed!")
                    st.balloons()
                    
                    # Check if this was the last task
                    remaining = [
                        t for t in all_tasks 
                        if not (t.get('is_completed') or t.get('completed_at'))
                        and t.get('id') != task_id
                    ]
                    
                    if not remaining:
                        st.info("🏆 You've completed all tasks! Time to generate more.")
                    
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to mark task as complete. Please try again.")
            
            except Exception as e:
                logger.error(f"Error marking task complete: {e}")
                st.error(f"Error: {e}")
    
    with col2:
        if st.button("⏭️ Skip for Now", width='stretch'):
            st.warning("Task skipped. It will remain in your task list.")
            st.info("💡 Consider coming back to this task later for complete learning.")
            
            if st.button("Continue to Next Task →"):
                st.rerun()
    
    with col3:
        if st.button("ℹ️ Need Help?", width='stretch'):
            st.info("""
            **Having trouble?**
            - Review the resources provided
            - Break the task into smaller steps
            - Search for additional tutorials
            - Ask for help in community forums
            """)


def show_next_task_preview(current_task: Dict, all_tasks: list):
    """Show preview of next task"""
    
    st.markdown("### 👀 What's Next?")
    
    # Find next task
    current_idx = None
    for idx, task in enumerate(all_tasks):
        if task['id'] == current_task['id']:
            current_idx = idx
            break
    
    if current_idx is not None and current_idx + 1 < len(all_tasks):
        next_task = all_tasks[current_idx + 1]
        
        with st.container():
            st.markdown(f"**Day {next_task['day_number']}: {next_task['task_text']}**")
            st.caption(next_task['why_text'][:150] + "...")
            
            col1, col2 = st.columns(2)
            
            with col1:
                difficulty = next_task.get('difficulty_score', 5)
                st.caption(f"Difficulty: {difficulty}/10")
            
            with col2:
                estimated = next_task.get('estimated_minutes', 30)
                st.caption(f"Time: {format_duration(estimated)}")
    else:
        st.info("This is the last task in your current plan. Complete it to unlock more!")


def show_all_complete(goal: Dict, tasks: list):
    """Show completion screen when all tasks are done"""
    
    st.success("🎉 Congratulations! You've completed all your tasks!")
    
    completed_count = len(tasks)
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tasks Completed", completed_count)
    
    with col2:
        # Calculate total time
        total_minutes = sum(t.get('estimated_minutes', 30) for t in tasks)
        st.metric("Learning Time", format_duration(total_minutes))
    
    with col3:
        # Average difficulty
        avg_difficulty = sum(t.get('difficulty_score', 5) for t in tasks) / len(tasks)
        st.metric("Avg Difficulty", f"{avg_difficulty:.1f}/10")
    
    st.markdown("---")
    
    # Celebration message
    st.markdown("""
    ### 🏆 Outstanding Achievement!
    
    You've shown great dedication to your learning journey. Here's what you can do next:
    
    1. **Generate more tasks** to continue learning
    2. **Review your progress** to see how far you've come
    3. **Get insights** on your learning patterns
    4. **Start a new goal** to learn something different
    """)
    
    st.markdown("---")
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Generate Next 7 Tasks", width='stretch', type="primary"):
            with st.spinner("Generating new tasks based on your progress..."):
                try:
                    state = get_current_state()
                    updated_state = run_adaptation_loop(state)
                    
                    if updated_state.get("tasks"):
                        st.success("✨ New tasks generated!")
                        st.rerun()
                    else:
                        st.error("Failed to generate new tasks")
                
                except Exception as e:
                    logger.error(f"Error generating tasks: {e}")
                    st.error(f"Error: {e}")
    
    with col2:
        if st.button("📈 View My Progress", width='stretch'):
            st.session_state.current_page = "Progress"
            st.rerun()
    
    st.markdown("---")
    
    # Motivation
    st.balloons()
    st.markdown("""
    <div style='background-color: #d4edda; padding: 20px; border-radius: 10px; text-align: center;'>
        <h3>🌟 Keep up the amazing work!</h3>
        <p>Every completed task brings you closer to mastery.</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    show()