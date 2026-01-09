"""
AI Learning Buddy - Streamlit UI
Clean, simple interface for the learning buddy application
"""

import streamlit as st
import os
from pathlib import Path
from src.learning_manager import get_learning_manager
from src.llm_service import get_llm_service


# Page configuration
st.set_page_config(
    page_title="AI Learning Buddy",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'manager' not in st.session_state:
    st.session_state.manager = None
if 'current_state' not in st.session_state:
    st.session_state.current_state = None


def initialize_manager():
    """Initialize learning manager with API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        st.error("⚠️ OpenAI API key not found!")
        st.info("Please set the OPENAI_API_KEY environment variable.")
        st.code("# On Windows:\nset OPENAI_API_KEY=your-key-here\n\n# On Linux/Mac:\nexport OPENAI_API_KEY=your-key-here")
        st.stop()
    
    try:
        # Initialize LLM service with API key
        get_llm_service(api_key=api_key)
        st.session_state.manager = get_learning_manager()
    except Exception as e:
        st.error(f"Failed to initialize: {str(e)}")
        st.stop()


def show_welcome_screen():
    """Display welcome screen and goal input"""
    st.title("📚 AI Learning Buddy")
    st.markdown("### Your personalized learning companion")
    
    st.markdown("---")
    
    # Check if there's an existing goal
    existing_state = st.session_state.manager.get_current_state()
    
    if existing_state:
        st.info("💡 You have an active learning plan! View it in the 'My Learning Plan' tab.")
        if st.button("Start a New Learning Goal"):
            # This will show the form below
            st.session_state.show_new_goal = True
    
    # Show new goal form
    if not existing_state or st.session_state.get('show_new_goal', False):
        st.markdown("### 🎯 Let's create your learning plan!")
        
        with st.form("goal_form"):
            goal = st.text_area(
                "What do you want to learn?",
                placeholder="Example: Learn Python for data analysis",
                height=100
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                level = st.selectbox(
                    "Your current level",
                    ["Beginner", "Intermediate", "Advanced"]
                )
            
            with col2:
                daily_minutes = st.number_input(
                    "Daily time available (minutes)",
                    min_value=15,
                    max_value=240,
                    value=30,
                    step=15
                )
            
            submitted = st.form_submit_button("🚀 Generate My Learning Plan", use_container_width=True)
            
            if submitted:
                if not goal.strip():
                    st.error("Please enter a learning goal!")
                else:
                    with st.spinner("Creating your personalized learning plan..."):
                        try:
                            result = st.session_state.manager.create_learning_plan(
                                goal=goal,
                                level=level,
                                daily_minutes=daily_minutes
                            )
                            st.session_state.current_state = st.session_state.manager.get_current_state()
                            st.session_state.show_new_goal = False
                            st.success("✅ Your learning plan is ready!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating plan: {str(e)}")


def show_learning_plan():
    """Display the current learning plan and progress"""
    state = st.session_state.manager.get_current_state()
    
    if not state:
        st.warning("No active learning plan. Go to 'Get Started' to create one!")
        return
    
    goal = state['goal']
    roadmap = state['roadmap']
    tasks = state['tasks']
    progress = state['progress']
    
    # Header with goal
    st.title("📚 My Learning Plan")
    st.markdown(f"### 🎯 Goal: {goal['goal']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Level", goal['level'])
    with col2:
        st.metric("Daily Time", f"{goal['daily_minutes']} min")
    with col3:
        completion = progress['completion_rate']
        st.metric("Progress", f"{completion:.0f}%")
    
    st.markdown("---")
    
    # Tabs for roadmap and tasks
    tab1, tab2 = st.tabs(["📋 Daily Tasks", "🗺️ Learning Roadmap"])
    
    with tab1:
        show_tasks(tasks, goal['id'])
    
    with tab2:
        show_roadmap(roadmap)


def show_tasks(tasks, goal_id):
    """Display tasks with completion tracking"""
    if not tasks:
        st.info("No tasks yet. Generate your plan first!")
        return
    
    st.markdown("### ✅ Your Daily Tasks")
    
    # Progress bar
    completed_count = sum(1 for t in tasks if t['is_completed'])
    total_count = len(tasks)
    
    if total_count > 0:
        progress_pct = completed_count / total_count
        st.progress(progress_pct, text=f"{completed_count}/{total_count} tasks completed")
    
    st.markdown("---")
    
    # Display tasks grouped by completion status
    incomplete_tasks = [t for t in tasks if not t['is_completed']]
    completed_tasks = [t for t in tasks if t['is_completed']]
    
    # Incomplete tasks first
    if incomplete_tasks:
        st.markdown("#### 📌 Pending Tasks")
        for task in incomplete_tasks:
            show_task_card(task, goal_id)
    
    # Completed tasks
    if completed_tasks:
        with st.expander(f"✅ Completed Tasks ({len(completed_tasks)})"):
            for task in completed_tasks:
                show_task_card(task, goal_id)
    
    # Adapt plan button
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Get Next Tasks", use_container_width=True):
            with st.spinner("Adapting your plan based on progress..."):
                try:
                    new_tasks = st.session_state.manager.adapt_plan(goal_id)
                    st.success(f"✅ Added {len(new_tasks)} new tasks!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adapting plan: {str(e)}")


def show_task_card(task, goal_id):
    """Display a single task card"""
    with st.container():
        col1, col2 = st.columns([0.9, 0.1])
        
        with col1:
            # Task header
            task_status = "✅" if task['is_completed'] else "⏳"
            st.markdown(f"**Day {task['day_number']} {task_status}**")
            
            # Task content
            st.markdown(f"**Task:** {task['task_text']}")
            
            if task['why_text']:
                st.markdown(f"*Why:* {task['why_text']}")
            
            if task['estimated_minutes']:
                st.caption(f"⏱️ Estimated time: {task['estimated_minutes']} minutes")
        
        with col2:
            # Completion checkbox
            is_complete = st.checkbox(
                "Done",
                value=task['is_completed'],
                key=f"task_{task['id']}",
                label_visibility="collapsed"
            )
            
            # Update completion status if changed
            if is_complete != task['is_completed']:
                st.session_state.manager.mark_task_complete(task['id'], is_complete)
                st.rerun()
        
        st.markdown("---")


def show_roadmap(roadmap):
    """Display the learning roadmap"""
    st.markdown("### 🗺️ Your Learning Roadmap")
    st.markdown("This is the big picture - the modules you'll work through to achieve your goal.")
    st.markdown("---")
    
    if roadmap:
        st.markdown(roadmap)
    else:
        st.info("Roadmap not available. Create a new learning plan!")


def main():
    """Main application entry point"""
    # Initialize manager
    if st.session_state.manager is None:
        initialize_manager()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        page = st.radio(
            "Go to",
            ["🏠 Get Started", "📚 My Learning Plan"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("AI Learning Buddy helps you achieve your learning goals through personalized daily tasks.")
        st.markdown("---")
        st.caption("Built with Streamlit + OpenAI")
    
    # Route to appropriate page
    if page == "🏠 Get Started":
        show_welcome_screen()
    elif page == "📚 My Learning Plan":
        show_learning_plan()


if __name__ == "__main__":
    main()