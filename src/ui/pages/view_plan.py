"""
View Plan Page - Display Generated Learning Roadmap
Day 5: Shows modules, timeline, and learning path visualization
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
import json

from src.ui.utils import get_active_goal, get_roadmap, format_duration, get_resource_emoji
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def show():
    """Display the learning plan page"""
    
    st.markdown('<h1 class="main-header">🗺️ Your Learning Roadmap</h1>', unsafe_allow_html=True)
    
    # Check for active goal
    goal = get_active_goal()
    
    if not goal:
        st.warning("⚠️ No active learning goal found.")
        st.info("Create a new learning goal to generate your personalized roadmap.")
        
        if st.button("🎯 Create New Goal", use_container_width=True):
            st.session_state.current_page = "Create Goal"
            st.rerun()
        
        return
    
    # Get roadmap
    roadmap = get_roadmap(goal["id"])
    
    if not roadmap:
        st.warning("📋 Your learning roadmap hasn't been generated yet.")
        st.info("This usually happens automatically when you create a goal. Try creating a new goal.")
        
        if st.button("🎯 Create New Goal", use_container_width=True):
            st.session_state.current_page = "Create Goal"
            st.rerun()
        
        return
    
    # Display roadmap
    show_roadmap_overview(goal, roadmap)
    show_modules_detail(roadmap)
    show_timeline_visualization(roadmap)
    show_action_buttons()


def show_roadmap_overview(goal: Dict, roadmap: Dict):
    """Display roadmap overview and metadata"""
    
    st.markdown(f"### 📚 {goal['goal_text']}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Modules", roadmap["modules_count"])
    
    with col2:
        st.metric("Estimated Duration", f"{roadmap['estimated_weeks']} weeks")
    
    with col3:
        st.metric("Your Level", goal["level"].title())
    
    with col4:
        st.metric("Daily Time", format_duration(goal["daily_minutes"]))
    
    st.markdown("---")


def show_modules_detail(roadmap: Dict):
    """Display detailed module information"""
    
    st.markdown("### 📖 Learning Modules")
    st.write("Your learning journey is organized into progressive modules:")
    
    modules = roadmap["modules"]
    
    if isinstance(modules, str):
        try:
            modules = json.loads(modules)
        except:
            modules = []
    
    if not modules:
        st.warning("No modules found in roadmap")
        return
    
    # Display each module
    for idx, module in enumerate(modules):
        # Module number badge
        module_num = idx + 1
        
        with st.expander(
            f"📚 Module {module_num}: {module.get('title', 'Untitled Module')}",
            expanded=(idx == 0)  # First module expanded by default
        ):
            # Module metadata
            col1, col2, col3 = st.columns(3)
            
            with col1:
                duration = module.get('duration_weeks', module.get('estimated_weeks', 'N/A'))
                st.info(f"⏱️ **Duration:** {duration} week(s)")
            
            with col2:
                difficulty = module.get('difficulty', 'moderate')
                st.info(f"📊 **Difficulty:** {difficulty.title()}")
            
            with col3:
                topics_count = len(module.get('topics', []))
                st.info(f"📝 **Topics:** {topics_count}")
            
            # Description
            if module.get('description'):
                st.markdown("**Description:**")
                st.write(module['description'])
            
            # Learning objectives
            if module.get('objectives') or module.get('learning_objectives'):
                objectives = module.get('objectives') or module.get('learning_objectives', [])
                st.markdown("**Learning Objectives:**")
                
                if isinstance(objectives, str):
                    st.write(objectives)
                elif isinstance(objectives, list):
                    for obj in objectives:
                        st.write(f"• {obj}")
            
            # Topics covered
            if module.get('topics'):
                st.markdown("**Topics Covered:**")
                topics = module['topics']
                
                if isinstance(topics, str):
                    topics = [t.strip() for t in topics.split(',')]
                
                # Display topics in columns
                topic_cols = st.columns(min(3, len(topics)))
                for i, topic in enumerate(topics):
                    with topic_cols[i % len(topic_cols)]:
                        st.caption(f"✓ {topic}")
            
            # Resources
            if module.get('resources'):
                st.markdown("**Recommended Resources:**")
                resources = module['resources']
                
                if isinstance(resources, list):
                    for resource in resources[:5]:  # Show max 5
                        if isinstance(resource, dict):
                            title = resource.get('title', 'Resource')
                            url = resource.get('url', '#')
                            res_type = resource.get('type', 'resource')
                            emoji = get_resource_emoji(res_type)
                            
                            st.markdown(f"{emoji} [{title}]({url}) - _{res_type}_")
                        else:
                            st.write(f"• {resource}")
            
            # Milestones
            if module.get('milestones'):
                st.markdown("**Milestones:**")
                milestones = module['milestones']
                
                if isinstance(milestones, list):
                    for milestone in milestones:
                        st.write(f"🎯 {milestone}")
                else:
                    st.write(f"🎯 {milestones}")
    
    st.markdown("---")


def show_timeline_visualization(roadmap: Dict):
    """Display timeline visualization"""
    
    st.markdown("### 📅 Learning Timeline")
    
    modules = roadmap["modules"]
    
    if isinstance(modules, str):
        try:
            modules = json.loads(modules)
        except:
            modules = []
    
    if not modules:
        return
    
    # Create timeline data
    timeline_data = []
    cumulative_weeks = 0
    
    for idx, module in enumerate(modules):
        duration = module.get('duration_weeks', module.get('estimated_weeks', 2))
        
        if isinstance(duration, str):
            try:
                duration = int(duration.split()[0])
            except:
                duration = 2
        
        timeline_data.append({
            "Module": f"Module {idx + 1}",
            "Title": module.get('title', 'Untitled')[:30],
            "Duration (weeks)": duration,
            "Start Week": cumulative_weeks + 1,
            "End Week": cumulative_weeks + duration
        })
        
        cumulative_weeks += duration
    
    # Display as bar chart
    df = pd.DataFrame(timeline_data)
    
    st.bar_chart(df.set_index("Module")["Duration (weeks)"])
    
    # Display as table
    with st.expander("📊 Detailed Timeline"):
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True
        )
    
    # Total duration
    total_weeks = cumulative_weeks
    months = total_weeks // 4
    remaining_weeks = total_weeks % 4
    
    duration_str = f"{months} month(s)" if months > 0 else ""
    if remaining_weeks > 0:
        duration_str += f" {remaining_weeks} week(s)" if duration_str else f"{remaining_weeks} week(s)"
    
    st.info(f"📆 **Total Learning Duration:** {duration_str} (~{total_weeks} weeks)")
    
    st.markdown("---")


def show_action_buttons():
    """Display action buttons"""
    
    st.markdown("### ⚡ What's Next?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Start Learning", use_container_width=True, type="primary"):
            st.session_state.current_page = "Daily Tasks"
            st.rerun()
    
    with col2:
        if st.button("📈 View Progress", use_container_width=True):
            st.session_state.current_page = "Progress"
            st.rerun()
    
    with col3:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.current_page = "Home"
            st.rerun()
    
    # Export option
    st.markdown("---")
    
    with st.expander("💾 Export Your Roadmap"):
        st.write("Download your learning plan for offline reference:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Download as PDF", use_container_width=True):
                st.info("PDF export coming soon!")
        
        with col2:
            if st.button("📋 Download as Markdown", use_container_width=True):
                st.info("Markdown export coming soon!")


if __name__ == "__main__":
    show()