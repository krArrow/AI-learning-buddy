"""
Daily Tasks Page - View and Complete Learning Tasks
Day 5: Display current task, resources, and track completion
"""

import streamlit as st
from typing import Dict, Optional
import json

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
    
    # Check for active goal
    goal = get_active_goal()
    
    if not goal:
        st.warning("⚠️ No active learning goal found.")
        
        if st.button("🎯 Create New Goal", use_container_width=True):
            st.session_state.current_page = "Create Goal"
            st.rerun()
        
        return
    
    # Get tasks
    tasks = get_tasks_for_goal(goal["id"])
    
    if not tasks:
        st.warning("📋 No tasks have been generated yet.")
        st.info("Tasks are usually generated when you create a goal. Try creating a new goal or regenerating tasks.")
        
        if st.button("🔄 Generate Tasks", use_container_width=True):
            with st.spinner("Generating tasks..."):
                state = get_current_state()
                updated_state = run_adaptation_loop(state)
                
                if updated_state.get("tasks"):
                    st.success("Tasks generated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to generate tasks")
        
        return
    
    # Get current task
    current_task = get_current_task(goal["id"])
    
    if current_task:
        show_current_task(current_task, tasks)
    else:
        show_all_complete(goal, tasks)


def show_current_task(task: Dict, all_tasks: list):
    """Display the current task to complete"""
    
    st.markdown(f"### 📝 Day {task['day_number']} Task")
    
    # Task header
    st.markdown(f"## {task['task_text']}")
    
    # Metadata row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Day", task['day_number'])
    
    with col2:
        difficulty = task.get('difficulty_score', 5)
        st.metric("Difficulty", f"{difficulty}/10")
    
    with col3:
        estimated = task.get('estimated_minutes', 30)
        st.metric("Time", format_duration(estimated))
    
    with col4:
        completed = sum(1 for t in all_tasks if t['is_completed'])
        total = len(all_tasks)
        st.metric("Progress", f"{completed}/{total}")
    
    st.markdown("---")
    
    # Why this task?
    st.markdown("### 🎯 Why This Task?")
    st.info(task['why_text'])
    
    st.markdown("---")
    
    # Resources
    show_task_resources(task)
    
    st.markdown("---")
    
    # Action buttons
    show_task_actions(task, all_tasks)
    
    st.markdown("---")
    
    # Next task preview
    show_next_task_preview(task, all_tasks)


def show_task_resources(task: Dict):
    """Display resources for the task"""
    
    st.markdown("### 📚 Learning Resources")
    
    resources = task.get('resources', [])
    
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
            url = resource.get('url', '#')
            res_type = resource.get('type', 'resource')
            description = resource.get('description', '')
            
            emoji = get_resource_emoji(res_type)
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"{emoji} **[{title}]({url})**")
                    if description:
                        st.caption(description)
                
                with col2:
                    st.caption(f"_{res_type}_")
        
        else:
            # Simple string resource
            st.write(f"• {resource}")
    
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
        if st.button("✅ Mark as Complete", use_container_width=True, type="primary"):
            success = mark_task_complete(task['id'])
            
            if success:
                st.session_state.last_completed_task = task
                st.success("🎉 Great job! Task completed!")
                st.balloons()
                
                # Check if this was the last task
                remaining = [t for t in all_tasks if not t['is_completed'] and t['id'] != task['id']]
                
                if not remaining:
                    st.info("🏆 You've completed all tasks! Time to generate more.")
                
                st.rerun()
            else:
                st.error("Failed to mark task as complete. Please try again.")
    
    with col2:
        if st.button("⏭️ Skip for Now", use_container_width=True):
            st.warning("Task skipped. It will remain in your task list.")
            st.info("💡 Consider coming back to this task later for complete learning.")
            
            # Move to next task (just refresh)
            if st.button("Continue to Next Task →"):
                st.rerun()
    
    with col3:
        if st.button("ℹ️ Need Help?", use_container_width=True):
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
        if st.button("📋 Generate Next 7 Tasks", use_container_width=True, type="primary"):
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
        if st.button("📈 View My Progress", use_container_width=True):
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