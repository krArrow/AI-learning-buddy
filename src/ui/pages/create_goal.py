"""
Create Goal Page - Interactive Goal Creation with AI Clarification
Day 5: Multi-turn conversation to clarify learning goals and preferences
"""

import streamlit as st
from typing import Dict, List
import time

from src.core.state import create_initial_state
from src.agents.goal_clarifier import GoalClarifierAgent
from src.llm.config import LLMConfig
from src.ui.utils import run_graph_execution
from src.utils.logger import get_logger
from src.utils.goal_enrichment import estimate_goal_hours, calculate_eta

logger = get_logger(__name__)


def show():
    """Display the create goal page"""
    
    st.markdown('<h1 class="main-header">🎯 Create Your Learning Goal</h1>', unsafe_allow_html=True)
    st.markdown("### Let's build a personalized learning plan together")
    
    st.markdown("---")
    
    # Initialize conversation state
    if "goal_creation_step" not in st.session_state:
        st.session_state.goal_creation_step = "initial_input"
    
    if "goal_draft_state" not in st.session_state:
        st.session_state.goal_draft_state = None
    
    if "clarification_complete" not in st.session_state:
        st.session_state.clarification_complete = False
    
    # Route to appropriate step
    if st.session_state.goal_creation_step == "initial_input":
        show_initial_input()
    
    elif st.session_state.goal_creation_step == "clarification":
        show_clarification_conversation()
    
    elif st.session_state.goal_creation_step == "confirmation":
        show_confirmation()
    
    elif st.session_state.goal_creation_step == "generating":
        show_generation_progress()


def show_initial_input():
    """Show initial goal input form"""
    
    st.markdown("### Step 1: Basic Information")
    st.write("Tell us what you want to learn and we'll help you create the perfect plan.")
    
    with st.form("initial_goal_form"):
        # Goal text
        goal_text = st.text_area(
            "What do you want to learn? *",
            placeholder="e.g., Learn Python for data science, Master React web development...",
            help="Be specific about what you want to achieve",
            height=100
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Level
            level = st.selectbox(
                "Your Current Level *",
                ["Beginner", "Intermediate", "Advanced"],
                help="Choose the level that best describes your current knowledge"
            )
        
        with col2:
            # Daily time
            daily_minutes = st.slider(
                "Daily Learning Time (minutes) *",
                min_value=10,
                max_value=480,
                value=60,
                step=10,
                help="How much time can you dedicate each day?"
            )
        
        # Target completion time
        st.markdown("### 🎯 Your Goal Timeline")
        
        col3, col4 = st.columns(2)
        
        with col3:
            target_number = st.number_input(
                "I want to complete this in:",
                min_value=1,
                max_value=365,
                value=30,
                step=1,
                help="How long do you want to take to achieve this goal?"
            )
        
        with col4:
            target_unit = st.selectbox(
                "Time Unit",
                ["Days", "Weeks", "Months"],
                index=1,  # Default to Weeks
                help="Select the time unit"
            )
        
        st.markdown("---")
        
        # Optional preferences
        with st.expander("⚙️ Optional: Set Your Preferences"):
            learning_style = st.selectbox(
                "Learning Style",
                ["Not sure", "Visual", "Kinesthetic", "Auditory", "Reading/Writing"],
                help="How do you learn best? (We'll help you discover this if you're not sure)"
            )
            
            pace = st.selectbox(
                "Preferred Pace",
                ["Not sure", "Slow", "Medium", "Fast"],
                help="How quickly do you want to progress?"
            )
        
        # Submit button
        submitted = st.form_submit_button("Next: Clarify Details ➡️", width='stretch')
        
        if submitted:
            # Validation
            if not goal_text or len(goal_text.strip()) < 10:
                st.error("Please provide a more detailed learning goal (at least 10 characters)")
                return
            
            # Calculate target completion in days
            if target_unit == "Days":
                target_days = target_number
            elif target_unit == "Weeks":
                target_days = target_number * 7
            else:  # Months
                target_days = target_number * 30
            
            # Create initial state
            state = create_initial_state(
                goal_text=goal_text.strip(),
                level=level.lower(),
                daily_minutes=daily_minutes,
                learning_style=None if learning_style == "Not sure" else learning_style.lower().replace("/", "_"),
                pace=None if pace == "Not sure" else pace.lower()
            )
            
            # Add target completion days to state
            state["target_completion_days"] = target_days
            state["target_display"] = f"{target_number} {target_unit}"
            
            st.session_state.goal_draft_state = state
            st.session_state.goal_creation_step = "clarification"
            st.session_state.clarification_messages = []
            st.rerun()


def show_clarification_conversation():
    """Show multi-turn clarification conversation"""
    
    st.markdown("### Step 2: Clarify Your Goals")
    st.write("Our AI will ask you a few questions to personalize your learning experience.")
    
    state = st.session_state.goal_draft_state
    
    if not state:
        st.error("State not initialized. Please go back.")
        if st.button("← Back to Step 1"):
            st.session_state.goal_creation_step = "initial_input"
            st.rerun()
        return
    
    # Initialize agent
    agent = GoalClarifierAgent()
    max_questions = 3
    
    # Check if we need to generate the FIRST question (only when conversation is empty)
    if len(st.session_state.clarification_messages) == 0:
        try:
            with st.spinner("🤔 Preparing your first question..."):
                # Generate the initial question
                state = agent.clarify_goal(state)
            
            # Extract the first agent response
            if state.get("conversation_history"):
                last_message = state["conversation_history"][-1]
                if last_message.get("role") == "assistant":
                    question = last_message.get("content", "")
                    
                    # Add to UI conversation
                    st.session_state.clarification_messages.append({
                        "role": "agent",
                        "content": question
                    })
                    
                    # Save state
                    st.session_state.goal_draft_state = state
                    st.rerun()
        
        except Exception as e:
            logger.error(f"Error generating initial question: {e}")
            st.error(f"An error occurred: {e}")
            
            if st.button("🔄 Retry"):
                st.rerun()
            
            if st.button("← Start Over"):
                st.session_state.goal_creation_step = "initial_input"
                st.session_state.clarification_messages = []
                st.rerun()
            
            return
    
    # Display conversation history
    for message in st.session_state.clarification_messages:
        if message["role"] == "agent":
            with st.chat_message("assistant"):
                st.write(message["content"])
        else:
            with st.chat_message("user"):
                st.write(message["content"])
    
    # Check if clarification is complete
    if st.session_state.clarification_complete:
        st.success("✅ All questions answered! Let's review your preferences.")
        
        if st.button("Next: Review & Confirm ➡️", width='stretch'):
            st.session_state.goal_creation_step = "confirmation"
            st.rerun()
        
        return
    
    # Check if max question EXCHANGES (question + answer pairs) reached
    # Only auto-complete if user has answered max_questions, not just if max questions were asked
    answer_count = len([m for m in st.session_state.clarification_messages if m["role"] == "user"])
    
    if answer_count >= max_questions:
        # Auto-complete if user has answered max questions
        st.session_state.clarification_complete = True
        st.session_state.goal_draft_state = state
        st.rerun()
        return
    
    # User input form - only show if not complete
    with st.form("clarification_answer_form", clear_on_submit=True):
        user_answer = st.text_input(
            "Your answer:",
            placeholder="Type your response here...",
            label_visibility="collapsed"
        )
        
        submitted = st.form_submit_button("Send ➡️")
        
        if submitted and user_answer:
            try:
                # Add user response to UI conversation
                st.session_state.clarification_messages.append({
                    "role": "user",
                    "content": user_answer
                })
                
                # Process answer through agent to get next question
                state = st.session_state.goal_draft_state
                
                with st.spinner("🤔 Processing your response..."):
                    state = agent.process_answer(state, user_answer)
                
                # Check if clarification is complete (agent returned completion JSON)
                if state.get("clarification_complete"):
                    st.session_state.clarification_complete = True
                    st.session_state.goal_draft_state = state
                    st.rerun()
                    return
                
                # Extract and display the next question/response
                if state.get("conversation_history"):
                    last_message = state["conversation_history"][-1]
                    if last_message.get("role") == "assistant":
                        response = last_message.get("content", "")
                        
                        # Check if response contains completion JSON (agent finished early)
                        if "clarification_complete" in response.lower():
                            st.session_state.clarification_complete = True
                        
                        st.session_state.clarification_messages.append({
                            "role": "agent",
                            "content": response
                        })
                
                # Save updated state
                st.session_state.goal_draft_state = state
                st.rerun()
            
            except Exception as e:
                logger.error(f"Error processing answer: {e}")
                st.error(f"An error occurred: {e}")
                
                if st.button("🔄 Retry"):
                    st.rerun()
    
    # Skip button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Skip Remaining →"):
            st.session_state.clarification_complete = True
            st.rerun()


def show_confirmation():
    """Show confirmation of user preferences"""
    
    st.markdown("### 🎯 Review Your Learning Plan")
    
    state = st.session_state.goal_draft_state
    
    if not state:
        st.error("State not found")
        return
    
    # Display target timeline prominently
    target_display = state.get("target_display", "Not specified")
    target_days = state.get("target_completion_days", 0)
    daily_minutes = state.get("daily_minutes", 60)
    
    st.markdown(f"### 📅 Your Timeline: **{target_display}**")
    
    timeline_col1, timeline_col2 = st.columns(2)
    
    with timeline_col1:
        daily_hours = daily_minutes / 60
        st.info(f"⏱️ **Daily Commitment:** {daily_hours:.1f} hour(s) per day")
    
    with timeline_col2:
        st.info(f"🎯 **Target Completion:** {target_display}")
    
    st.caption(f"💡 Your plan will be tailored to complete your goal within {target_display} at {daily_hours:.1f} hours/day")
    
    st.markdown("---")
    
    # Display preferences
    st.markdown("### 📚 Your Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📝 Learning Goal")
        # Show original goal (not enriched version)
        display_goal = state.get("original_goal_text", state.get("goal_text", ""))
        st.info(display_goal)
        
        st.markdown("#### 📊 Level")
        st.info(state["level"].title())
        
        st.markdown("#### ⏱️ Daily Time")
        st.info(f"{state['daily_minutes']} minutes")
    
    with col2:
        st.markdown("#### 🎨 Learning Style")
        style = state.get("learning_style", "Not specified")
        st.info(style.replace("_", "/").title() if style and style != "Not specified" else "Visual (default)")
        
        st.markdown("#### 🚀 Pace")
        pace = state.get("pace", "Not specified")
        st.info(pace.title() if pace and pace != "Not specified" else "Moderate (default)")
        
        st.markdown("#### 📚 Additional Preferences")
        preferences = state.get("preferences", {})
        if preferences and isinstance(preferences, dict) and len(preferences) > 0:
            # Display preferences from dictionary
            pref_items = [(k, v) for k, v in preferences.items() if v]
            if pref_items:
                for key, value in pref_items[:3]:
                    st.caption(f"• {key.replace('_', ' ').title()}: {value}")
            else:
                st.caption("• No specific preferences")
        elif preferences and isinstance(preferences, str):
            # Handle string format (backward compatibility)
            for pref in preferences.split(",")[:3]:
                st.caption(f"• {pref.strip()}")
        else:
            st.caption("• No specific preferences")
    
    st.markdown("---")
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Edit Preferences", width='stretch'):
            st.session_state.goal_creation_step = "initial_input"
            st.session_state.clarification_complete = False
            st.rerun()
    
    with col2:
        if st.button("✅ Generate My Learning Plan", width='stretch', type="primary"):
            st.session_state.goal_creation_step = "generating"
            st.rerun()


def show_generation_progress():
    """Show progress while generating the learning plan"""
    
    st.markdown("### 🔄 Generating Your Personalized Learning Plan")
    st.write("Please wait while we create your customized roadmap and tasks...")
    
    state = st.session_state.goal_draft_state
    
    if not state:
        st.error("State not found")
        return
    
    # Progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Analyzing goal
        status_text.text("📋 Analyzing your learning goal...")
        progress_bar.progress(10)
        time.sleep(0.5)
        
        # Step 2: Retrieving resources
        status_text.text("🔍 Finding the best learning resources...")
        progress_bar.progress(30)
        time.sleep(0.5)
        
        # Step 3: Generating roadmap
        status_text.text("🗺️ Creating your learning roadmap...")
        progress_bar.progress(50)
        
        # Execute graph
        with st.spinner("Executing workflow..."):
            final_state = run_graph_execution(state)
        
        progress_bar.progress(70)
        time.sleep(0.5)
        
        # Step 4: Creating tasks
        status_text.text("✅ Generating your first week of tasks...")
        progress_bar.progress(90)
        time.sleep(0.5)
        
        # Complete
        progress_bar.progress(100)
        status_text.text("✨ All done!")
        
        # Set as active goal
        if final_state.get("goal_id"):
            st.session_state.active_goal_id = final_state["goal_id"]
            st.session_state.current_state = final_state
        
        # Success message
        st.success("🎉 Your learning plan has been created successfully!")
        
        time.sleep(1)
        
        # Redirect to plan view
        st.info("Redirecting to your learning plan...")
        time.sleep(1)
        
        st.session_state.current_page = "View Plan"
        st.session_state.goal_creation_step = "initial_input"  # Reset for next time
        st.rerun()
    
    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        progress_bar.empty()
        status_text.empty()
        
        st.error(f"❌ Failed to generate learning plan: {e}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Try Again", width='stretch'):
                st.rerun()
        
        with col2:
            if st.button("← Start Over", width='stretch'):
                st.session_state.goal_creation_step = "initial_input"
                st.session_state.clarification_messages = []
                st.rerun()


if __name__ == "__main__":
    show()
