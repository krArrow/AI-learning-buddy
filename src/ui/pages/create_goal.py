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
    
    elif st.session_state.goal_creation_step == "roadmap_review":
        show_roadmap_review()
    
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
            
            # Create initial state with timeline included
            state = create_initial_state(
                goal_text=goal_text.strip(),
                level=level.lower(),
                daily_minutes=daily_minutes,
                learning_style=None if learning_style == "Not sure" else learning_style.lower().replace("/", "_"),
                pace=None if pace == "Not sure" else pace.lower(),
                target_completion_days=target_days  # Pass timeline directly
            )
            
            # Add display text for UI (convenience field)
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
        user_profile = state.get("user_profile", {})
        level = user_profile.get("level", "Not specified")
        st.info(level.title() if level else "Not specified")
        
        st.markdown("#### ⏱️ Daily Time")
        daily_minutes = user_profile.get("daily_minutes", 60)
        st.info(f"{daily_minutes} minutes")
    
    with col2:
        st.markdown("#### 🎨 Learning Style")
        style = user_profile.get("learning_style", "Not specified")
        st.info(style.replace("_", "/").title() if style and style != "Not specified" else "Visual (default)")
        
        st.markdown("#### 🚀 Pace")
        pace = user_profile.get("pace", "Not specified")
        st.info(pace.title() if pace and pace != "Not specified" else "Moderate (default)")
        
        st.markdown("#### 📚 Additional Preferences")
        preferences = user_profile.get("preferences", {})
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
            st.session_state.goal_creation_step = "roadmap_review"
            st.rerun()


def show_roadmap_review():
    """Step 3b: Review and approve abstract roadmap before content population"""
    
    st.markdown("### 🗺️ Review Your Learning Roadmap")
    st.write("Here's the structure of your learning path. Approve to continue or request changes.")
    
    state = st.session_state.goal_draft_state
    
    if not state:
        st.error("State not found")
        return
    
    # Check if roadmap was generated
    abstract_roadmap = state.get("abstract_roadmap")
    
    if not abstract_roadmap:
        st.warning("Roadmap not generated yet. Generating now...")
        
        # Generate roadmap if not already done
        try:
            from src.core.nodes.goal_clarifier_node import goal_clarifier_node
            from src.core.nodes.domain_analyzer_node import domain_analyzer_node
            from src.core.nodes.curriculum_architect_node import curriculum_architect_node
            
            with st.spinner("Analyzing your goal..."):
                state = goal_clarifier_node(state)
            
            with st.spinner("Analyzing domain..."):
                state = domain_analyzer_node(state)
            
            with st.spinner("Creating curriculum structure..."):
                state = curriculum_architect_node(state)
            
            st.session_state.goal_draft_state = state
            abstract_roadmap = state.get("abstract_roadmap")
            
        except Exception as e:
            logger.error(f"Error generating roadmap: {e}")
            st.error(f"Failed to generate roadmap: {e}")
            
            if st.button("← Back to Confirmation"):
                st.session_state.goal_creation_step = "confirmation"
                st.rerun()
            
            return
    
    # Display roadmap
    st.markdown("---")
    st.markdown("#### 📚 Your Learning Modules")
    
    modules = abstract_roadmap.get("structure", {}).get("modules", [])
    total_weeks = abstract_roadmap.get("total_estimated_weeks", 0)
    
    if not modules:
        st.error("No modules found in roadmap")
        return
    
    # Show summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Modules", len(modules))
    
    with col2:
        st.metric("Estimated Duration", f"{total_weeks} weeks")
    
    with col3:
        daily_mins = state.get("user_profile", {}).get("daily_minutes", 30)
        st.metric("Your Daily Time", f"{daily_mins} min")
    
    st.markdown("---")
    
    # Display each module
    for idx, module in enumerate(modules, 1):
        with st.expander(
            f"📚 Module {idx}: {module.get('title', 'Module')}",
            expanded=(idx == 1)
        ):
            # Module details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                duration = module.get("estimated_weeks", "?")
                st.caption(f"⏱️ **Duration:** {duration} week(s)")
            
            with col2:
                difficulty = module.get("difficulty", 0.5)
                diff_label = "Easy" if difficulty < 0.4 else "Medium" if difficulty < 0.7 else "Hard"
                st.caption(f"📊 **Difficulty:** {diff_label}")
            
            with col3:
                topics_count = len(module.get("topics", []))
                st.caption(f"📝 **Topics:** {topics_count}")
            
            # Description
            if module.get("description"):
                st.write(f"**Description:** {module['description']}")
            
            # Prerequisites
            prereqs = module.get("prerequisites", [])
            if prereqs:
                st.caption(f"✓ **Prerequisites:** {', '.join(prereqs) if prereqs else 'None'}")
            
            # Topics
            if module.get("topics"):
                st.markdown("**Topics:**")
                for topic in module["topics"]:
                    topic_name = topic.get("title", "Topic")
                    objectives = topic.get("learning_objectives", [])
                    
                    with st.container():
                        st.write(f"• {topic_name}")
                        if objectives:
                            for obj in objectives:
                                st.caption(f"  - {obj}")
    
    st.markdown("---")
    
    # Approval section
    st.markdown("#### ✅ What happens next?")
    
    st.info("""
    **If you approve:**
    - We'll add curated learning resources for each module
    - We'll create personalized tasks aligned to your learning style
    - You'll get a day-by-day learning plan
    
    **If you want to revise:**
    - Tell us what needs to change
    - We'll regenerate with your feedback
    """)
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✅ Approve & Continue", width='stretch', type="primary"):
            state["roadmap_validated"] = True
            st.session_state.goal_draft_state = state
            st.session_state.goal_creation_step = "generating"
            st.rerun()
    
    with col2:
        if st.button("🔄 Request Changes", width='stretch'):
            st.session_state.roadmap_feedback_mode = True
            st.rerun()
    
    with col3:
        if st.button("← Back", width='stretch'):
            st.session_state.goal_creation_step = "confirmation"
            st.rerun()
    
    # Feedback mode
    if st.session_state.get("roadmap_feedback_mode"):
        st.markdown("---")
        st.markdown("#### 📝 Tell us what to change")
        
        feedback = st.text_area(
            "What would you like to change about the roadmap?",
            placeholder="E.g., Too many modules, want more focus on practical projects, need shorter learning path...",
            height=100
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Submit Feedback", width='stretch', type="primary"):
                if feedback.strip():
                    state["roadmap_validated"] = False
                    state["roadmap_validation_feedback"] = feedback
                    st.session_state.goal_draft_state = state
                    st.session_state.roadmap_feedback_mode = False
                    st.session_state.goal_creation_step = "generating"
                    st.rerun()
                else:
                    st.error("Please provide feedback")
        
        with col2:
            if st.button("Cancel", width='stretch'):
                st.session_state.roadmap_feedback_mode = False
                st.rerun()


def show_generation_progress():
    """Show progress while generating the learning plan"""
    
    st.markdown("### 🔄 Generating Your Personalized Learning Plan")
    st.write("Please wait while we curate resources and create your daily tasks...")
    
    state = st.session_state.goal_draft_state
    
    if not state:
        st.error("State not found")
        return
    
    # Progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Phases already done: Phase 1 (Discovery) and Phase 2 (Roadmap)
        # Now doing: Phase 3 (Content Population) and Phase 4 (Adaptive Execution)
        
        # If roadmap not yet generated, generate it first
        if not state.get("abstract_roadmap"):
            status_text.text("📋 Analyzing your learning goal...")
            progress_bar.progress(5)
            
            from src.core.nodes.goal_clarifier_node import goal_clarifier_node
            state = goal_clarifier_node(state)
            progress_bar.progress(10)
            
            status_text.text("🔍 Analyzing domain structure...")
            
            from src.core.nodes.domain_analyzer_node import domain_analyzer_node
            state = domain_analyzer_node(state)
            progress_bar.progress(20)
            
            status_text.text("🗺️ Creating curriculum structure...")
            
            from src.core.nodes.curriculum_architect_node import curriculum_architect_node
            state = curriculum_architect_node(state)
            progress_bar.progress(30)
            
            status_text.text("✅ Validating roadmap...")
            
            from src.core.nodes.roadmap_validator_node import roadmap_validator_node
            state = roadmap_validator_node(state)
            progress_bar.progress(35)
        else:
            progress_bar.progress(35)
        
        # Phase 3: Content Population
        status_text.text("🔍 Finding learning resources...")
        progress_bar.progress(40)
        
        from src.core.nodes.module_curator_node import module_curator_node
        from src.core.nodes.module_task_generator_node import module_task_generator_node
        from src.core.nodes.content_aggregator_node import content_aggregator_node
        
        # Curate resources and generate tasks for all modules
        modules = state.get("abstract_roadmap", {}).get("structure", {}).get("modules", [])
        module_count = len(modules)
        
        for idx, module in enumerate(modules):
            mod_id = module.get("id")
            state["current_module"] = mod_id
            
            # Curate resources for this module
            state = module_curator_node(state)
            progress_bar.progress(40 + int((idx / module_count) * 15))
            
            # Generate tasks for this module
            state = module_task_generator_node(state)
            progress_bar.progress(40 + int(((idx + 0.5) / module_count) * 15))
        
        status_text.text("📦 Aggregating content...")
        progress_bar.progress(60)
        
        # Aggregate all content
        state = content_aggregator_node(state)
        
        # Phase 4: Adaptive Execution setup
        status_text.text("🎯 Setting up learning tracker...")
        progress_bar.progress(75)
        
        from src.core.nodes.progress_tracker_node import progress_tracker_node
        state = progress_tracker_node(state)
        progress_bar.progress(80)
        
        status_text.text("✨ Finalizing your plan...")
        progress_bar.progress(90)
        time.sleep(0.5)
        
        # Save to database
        try:
            from src.ui.utils import save_graph_output_to_db
            goal_id = save_graph_output_to_db(state)
            state["goal_id"] = goal_id
            logger.info(f"Saved learning plan to database: goal_id={goal_id}")
        except Exception as db_error:
            logger.warning(f"Failed to save to database: {db_error}")
        
        # Complete
        progress_bar.progress(100)
        status_text.text("✨ All done!")
        
        # Set as active goal
        if state.get("goal_id"):
            st.session_state.active_goal_id = state["goal_id"]
            st.session_state.current_state = state
        
        # Success message
        st.success("🎉 Your personalized learning plan has been created!")
        
        populated_roadmap = state.get("populated_roadmap")
        if populated_roadmap:
            modules = populated_roadmap.get("structure", {}).get("modules", [])
            st.info(f"""
            ✅ Plan Generated Successfully!
            - **Modules:** {len(modules)}
            - **Duration:** {populated_roadmap.get('total_estimated_weeks', '?')} weeks
            - **Estimated Completion:** {state.get('target_display', 'As planned')}
            """)
        
        time.sleep(1)
        
        # Redirect to plan view
        st.info("Redirecting to your learning plan...")
        time.sleep(1)
        
        st.session_state.current_page = "View Plan"
        st.session_state.goal_creation_step = "initial_input"  # Reset for next time
        st.rerun()
    
    except Exception as e:
        logger.error(f"Error generating plan: {e}", exc_info=True)
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
