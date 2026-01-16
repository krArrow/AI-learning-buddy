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
    
    try:
        # Check for active goal
        goal = get_active_goal()
        
        if not goal:
            st.warning("⚠️ No active learning goal found.")
            st.info("Create a new learning goal to generate your personalized roadmap.")
            
            if st.button("🎯 Create New Goal", width='stretch'):
                st.session_state.current_page = "Create Goal"
                st.rerun()
            
            return
        
        # Validate goal data
        if not all(k in goal for k in ["id", "goal_text", "level", "daily_minutes"]):
            st.error("❌ Invalid goal data structure. Please create a new goal.")
            if st.button("🎯 Create New Goal", width='stretch'):
                st.session_state.current_page = "Create Goal"
                st.rerun()
            return
        
        # Get roadmap
        roadmap = get_roadmap(goal["id"])
        
        if not roadmap:
            st.warning("📋 Your learning roadmap hasn't been generated yet.")
            st.info("This usually happens automatically when you create a goal. Try creating a new goal.")
            
            if st.button("🎯 Create New Goal", width='stretch'):
                st.session_state.current_page = "Create Goal"
                st.rerun()
            
            return
        
        # Validate roadmap data
        if not isinstance(roadmap, dict):
            st.error("❌ Invalid roadmap data structure.")
            return
        
        # Display roadmap
        show_roadmap_overview(goal, roadmap)
        show_modules_detail(roadmap)
        show_timeline_visualization(roadmap)
        show_action_buttons()
        
    except Exception as e:
        logger.error(f"Error displaying view plan: {e}", exc_info=True)
        st.error(f"❌ An error occurred while loading the learning plan: {e}")
        
        if st.button("🔄 Retry"):
            st.rerun()
        
        if st.button("🏠 Back to Home"):
            st.session_state.current_page = "Home"
            st.rerun()


def show_roadmap_overview(goal: Dict, roadmap: Dict):
    """Display roadmap overview and metadata"""
    
    st.markdown(f"### 📚 {goal.get('goal_text', 'Learning Goal')}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        modules_count = roadmap.get("modules_count", 0)
        if not modules_count:
            # Count modules if not provided
            modules = roadmap.get("modules", [])
            if isinstance(modules, str):
                try:
                    modules = json.loads(modules)
                except:
                    modules = []
            modules_count = len(modules) if isinstance(modules, list) else 0
        st.metric("Total Modules", modules_count)
    
    with col2:
        estimated_weeks = roadmap.get('estimated_weeks', 'N/A')
        st.metric("Estimated Duration", f"{estimated_weeks} weeks" if isinstance(estimated_weeks, int) else str(estimated_weeks))
    
    with col3:
        level = goal.get("level", "Beginner")
        st.metric("Your Level", level.title() if isinstance(level, str) else "Beginner")
    
    with col4:
        daily_minutes = goal.get("daily_minutes", 60)
        st.metric("Daily Time", format_duration(daily_minutes))
    
    st.markdown("---")


def show_modules_detail(roadmap: Dict):
    """Display detailed module information"""
    
    st.markdown("### 📖 Learning Modules")
    st.write("Your learning journey is organized into progressive modules:")
    
    modules = roadmap.get("modules", [])
    
    # Parse modules if they're a JSON string
    if isinstance(modules, str):
        try:
            modules = json.loads(modules)
        except Exception as e:
            st.error(f"Error parsing modules: {e}")
            modules = []
    
    # Ensure modules is a list
    if not isinstance(modules, list):
        modules = []
    
    if not modules:
        st.warning("No modules found in roadmap")
        return
    
    # Display each module
    for idx, module in enumerate(modules):
        # Skip if module is not a dictionary
        if not isinstance(module, dict):
            continue
        
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
                            url = resource.get('url', resource.get('link', ''))
                            res_type = resource.get('type', resource.get('resource_type', 'resource'))
                            emoji = get_resource_emoji(res_type)
                            
                            # Create clickable link if URL exists
                            if url and url.startswith('http'):
                                st.markdown(f"{emoji} [{title}]({url}) - _{res_type}_")
                            else:
                                st.markdown(f"{emoji} **{title}** - _{res_type}_")
                        elif isinstance(resource, str):
                            st.write(f"📌 {resource}")
                else:
                    st.write(f"📌 {resources}")
            
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
    
    modules = roadmap.get("modules", [])
    
    # Parse modules if they're a JSON string
    if isinstance(modules, str):
        try:
            modules = json.loads(modules)
        except Exception as e:
            st.error(f"Error parsing modules: {e}")
            modules = []
    
    # Ensure modules is a list
    if not isinstance(modules, list):
        modules = []
    
    if not modules:
        return
    
    # Create timeline data
    timeline_data = []
    cumulative_weeks = 0
    
    for idx, module in enumerate(modules):
        # Skip if module is not a dictionary
        if not isinstance(module, dict):
            continue
        
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
    
    if not timeline_data:
        st.warning("No valid timeline data available")
        return
    
    # Display as bar chart
    df = pd.DataFrame(timeline_data)
    
    st.bar_chart(df.set_index("Module")["Duration (weeks)"])
    
    # Display as table
    with st.expander("📊 Detailed Timeline"):
        st.dataframe(
            df,
            hide_index=True,
            width='stretch'
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
        if st.button("✅ Start Learning", width='stretch', type="primary"):
            st.session_state.current_page = "Daily Tasks"
            st.rerun()
    
    with col2:
        if st.button("📈 View Progress", width='stretch'):
            st.session_state.current_page = "Progress"
            st.rerun()
    
    with col3:
        if st.button("🏠 Back to Home", width='stretch'):
            st.session_state.current_page = "Home"
            st.rerun()
    
    # Export option
    st.markdown("---")
    
    with st.expander("💾 Export Your Roadmap"):
        st.write("Download your learning plan for offline reference:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Download as PDF", width='stretch'):
                st.info("PDF export coming soon!")
        
        with col2:
            if st.button("📋 Download as Markdown", width='stretch'):
                st.info("Markdown export coming soon!")


if __name__ == "__main__":
    show()