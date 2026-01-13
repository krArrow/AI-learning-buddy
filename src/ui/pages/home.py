"""
Home Page - Welcome and Overview
Day 5: Main landing page with active goal status and quick actions
"""

import streamlit as st
from src.ui.utils import (
    get_active_goal, get_latest_goal, get_completion_rate,
    get_completed_tasks_count, get_tasks_for_goal, format_duration
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def show():
    """Display the home page"""
    
    st.markdown('<h1 class="main-header">📚 AI Learning Buddy</h1>', unsafe_allow_html=True)
    st.markdown("### Your Personalized AI Learning Companion")
    
    st.markdown("---")
    
    # Check for active goal
    active_goal = get_active_goal()
    
    if not active_goal:
        # Try to get the latest goal
        active_goal = get_latest_goal()
        if active_goal:
            st.session_state.active_goal_id = active_goal["id"]
    
    if active_goal:
        show_active_goal_dashboard(active_goal)
    else:
        show_welcome_screen()


def show_welcome_screen():
    """Show welcome screen when no active goal"""
    
    st.info("👋 **Welcome!** You don't have an active learning goal yet.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Get Started with AI-Powered Learning
        
        Create a personalized learning plan tailored to:
        - ✅ Your current skill level
        - ✅ Available time per day
        - ✅ Preferred learning style
        - ✅ Desired learning pace
        
        Our AI will:
        1. **Clarify your goals** through an interactive conversation
        2. **Curate resources** from the best learning materials
        3. **Generate a roadmap** with progressive modules
        4. **Create daily tasks** that fit your schedule
        5. **Track your progress** and adapt to your needs
        """)
    
    with col2:
        st.markdown("### Quick Start")
        
        if st.button("🎯 Create Your First Goal", use_container_width=True):
            st.session_state.current_page = "Create Goal"
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("### Example Goals")
        examples = [
            "Learn Python for data science",
            "Master React web development",
            "Understand machine learning basics",
            "Build iOS apps with Swift"
        ]
        
        for example in examples:
            st.caption(f"• {example}")
    
    # Features section
    st.markdown("---")
    st.markdown("### ✨ Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🧠 AI-Powered")
        st.write("Uses advanced LLMs to understand your needs and generate personalized learning paths.")
    
    with col2:
        st.markdown("#### 📊 Progress Tracking")
        st.write("Monitor your completion rate, consistency, and learning velocity over time.")
    
    with col3:
        st.markdown("#### 🔄 Adaptive Learning")
        st.write("Automatically adjusts difficulty and pace based on your performance and feedback.")


def show_active_goal_dashboard(goal: dict):
    """Show dashboard for active learning goal"""
    
    goal_id = goal["id"]
    
    # Header
    st.success(f"🎓 **Currently Learning:** {goal['goal_text']}")
    
    # Goal metadata
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Level", goal["level"].title())
    
    with col2:
        st.metric("Daily Time", format_duration(goal["daily_minutes"]))
    
    with col3:
        if goal.get("learning_style"):
            st.metric("Style", goal["learning_style"].title())
    
    with col4:
        if goal.get("pace"):
            st.metric("Pace", goal["pace"].title())
    
    st.markdown("---")
    
    # Progress overview
    st.markdown("### 📊 Progress Overview")
    
    tasks = get_tasks_for_goal(goal_id)
    completed_count = get_completed_tasks_count(goal_id)
    total_count = len(tasks)
    completion_rate = get_completion_rate(goal_id)
    
    # Progress metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            "Completion Rate",
            f"{completion_rate:.1f}%",
            delta=f"{completed_count}/{total_count} tasks"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            "Tasks Completed",
            completed_count,
            delta=f"{total_count - completed_count} remaining"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        
        # Calculate streak (simplified)
        if completed_count > 0:
            streak = min(completed_count, 7)
            st.metric("Current Streak", f"{streak} days", delta="Keep going!")
        else:
            st.metric("Current Streak", "0 days", delta="Start today!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Progress bar
    st.progress(completion_rate / 100)
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ View Daily Tasks", use_container_width=True):
            st.session_state.current_page = "Daily Tasks"
            st.rerun()
    
    with col2:
        if st.button("🗺️ View Learning Plan", use_container_width=True):
            st.session_state.current_page = "View Plan"
            st.rerun()
    
    with col3:
        if st.button("📈 Check Progress", use_container_width=True):
            st.session_state.current_page = "Progress"
            st.rerun()
    
    st.markdown("---")
    
    # Recent activity
    st.markdown("### 📌 Recent Activity")
    
    if tasks:
        # Show last 3 completed tasks
        completed_tasks = [t for t in tasks if t["is_completed"]]
        recent_completed = sorted(
            completed_tasks,
            key=lambda x: x["completed_at"] if x["completed_at"] else x["created_at"],
            reverse=True
        )[:3]
        
        if recent_completed:
            for task in recent_completed:
                with st.expander(f"✅ Day {task['day_number']}: {task['task_text'][:60]}..."):
                    st.write(f"**Why:** {task['why_text']}")
                    if task['completed_at']:
                        st.caption(f"Completed on {task['completed_at'].strftime('%B %d, %Y')}")
        else:
            st.info("No completed tasks yet. Start learning today!")
    else:
        st.info("No tasks available. Generate your learning plan to get started!")
    
    st.markdown("---")
    
    # Motivational message
    if completion_rate < 25:
        st.info("🚀 **Just getting started!** Every expert was once a beginner. Keep going!")
    elif completion_rate < 50:
        st.success("💪 **Great progress!** You're building momentum. Stay consistent!")
    elif completion_rate < 75:
        st.success("🔥 **You're on fire!** More than halfway there. Keep pushing!")
    else:
        st.balloons()
        st.success("🎉 **Outstanding work!** You're almost at the finish line!")


if __name__ == "__main__":
    show()