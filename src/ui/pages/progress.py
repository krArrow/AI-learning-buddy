"""
Progress Page - Track Learning Progress and Performance
Day 5: Display metrics, charts, and performance trends
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List

from src.ui.utils import (
    get_active_goal, get_performance_metrics, get_progress_history,
    get_tasks_for_goal, get_completion_rate, format_duration, get_current_state
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def show_adaptation_alerts(state: Dict):
    """Display alerts about detected struggles and recommended adaptations"""
    
    if state.get("struggles_detected"):
        severity = state.get("struggle_severity", 0)
        
        if severity > 0.7:
            st.warning("⚠️ **Significant Learning Challenges Detected**")
        else:
            st.info("📢 **Adaptive Recommendations Available**")
        
        # Show struggle details
        if state.get("struggle_topic"):
            st.markdown(f"**Struggling with:** {state['struggle_topic']}")
        
        if state.get("struggling_module_id"):
            st.markdown(f"**Module:** {state['struggling_module_id']}")
        
        # Show recommended actions
        if state.get("recommended_actions"):
            st.markdown("**Recommended Actions:**")
            for action in state["recommended_actions"]:
                st.write(f"• {action}")
        
        # Show pacing adjustment
        if state.get("pacing_adjustment") and state["pacing_adjustment"] != 1.0:
            pacing = state["pacing_adjustment"]
            if pacing < 1.0:
                pacing_pct = int((1 - pacing) * 100)
                st.warning(f"🐢 **Suggestion:** Slow down by {pacing_pct}% to consolidate learning")
            else:
                pacing_pct = int((pacing - 1) * 100)
                st.success(f"🚀 **Great pace!** You're ahead by {pacing_pct}%")
        
        # Re-curation option
        if state.get("re_curation_triggered"):
            st.info("♻️ Generating alternative resources for your struggling topic...")
            if st.button("📚 View Alternative Resources"):
                st.session_state.current_page = "View Plan"
                st.rerun()
        
        st.markdown("---")


def show():
    """Display the progress page"""
    
    st.markdown('<h1 class="main-header">📈 Your Learning Progress</h1>', unsafe_allow_html=True)
    
    # Check for active goal
    goal = get_active_goal()
    
    if not goal:
        st.warning("⚠️ No active learning goal found.")
        
        if st.button("🎯 Create New Goal", width='stretch'):
            st.session_state.current_page = "Create Goal"
            st.rerun()
        
        return
    
    # Display progress overview
    show_progress_overview(goal)
    
    # Show adaptation status if available
    state = get_current_state()
    if state.get("struggles_detected") or state.get("adaptation_required"):
        show_adaptation_alerts(state)
    
    # Display detailed metrics
    show_performance_metrics(goal)
    
    # Display progress trends
    show_progress_trends(goal)
    
    # Display task breakdown
    show_task_breakdown(goal)


def show_progress_overview(goal: Dict):
    """Display high-level progress overview"""
    
    st.markdown(f"### 📚 {goal['goal_text']}")
    
    # Get metrics
    goal_id = goal["id"]
    completion_rate = get_completion_rate(goal_id)
    metrics = get_performance_metrics(goal_id)
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        delta_color = "normal"
        if completion_rate >= 75:
            delta_color = "normal"
        
        st.metric(
            "Completion Rate",
            f"{completion_rate:.1f}%",
            delta=f"{metrics.get('tasks_completed', 0)} tasks done",
            delta_color=delta_color
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        avg_time = metrics.get('average_completion_time', 0)
        target_time = goal.get('daily_minutes', 60)
        delta = avg_time - target_time if avg_time > 0 else 0
        
        st.metric(
            "Avg Task Time",
            format_duration(int(avg_time)) if avg_time > 0 else "N/A",
            delta=f"{delta:+.0f} min vs target" if avg_time > 0 else "No data",
            delta_color="inverse" if delta > 0 else "normal"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        consistency = metrics.get('consistency_score', 0)
        consistency_pct = consistency * 10 if consistency <= 1 else consistency
        
        st.metric(
            "Consistency",
            f"{consistency_pct:.1f}/10",
            delta="Great!" if consistency_pct >= 7 else "Room to improve"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        difficulty_match = metrics.get('difficulty_match', 'unknown')
        
        emoji = "✅" if difficulty_match == "appropriate" else "⚠️"
        st.metric(
            "Difficulty Match",
            difficulty_match.title(),
            delta=emoji
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Progress bar
    st.progress(completion_rate / 100)
    
    st.markdown("---")


def show_performance_metrics(goal: Dict):
    """Display detailed performance metrics"""
    
    st.markdown("### 📊 Performance Metrics")
    
    goal_id = goal["id"]
    metrics = get_performance_metrics(goal_id)
    tasks = get_tasks_for_goal(goal_id)
    
    # Create tabs for different metric views
    tab1, tab2, tab3 = st.tabs(["📈 Overview", "⏱️ Time Analysis", "📉 Difficulty Analysis"])
    
    with tab1:
        show_overview_metrics(metrics, tasks)
    
    with tab2:
        show_time_metrics(metrics, tasks)
    
    with tab3:
        show_difficulty_metrics(metrics, tasks)


def show_overview_metrics(metrics: Dict, tasks: List[Dict]):
    """Show overview metrics"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Task Completion")
        
        completed = metrics.get('tasks_completed', 0)
        total = metrics.get('tasks_total', len(tasks))
        pending = total - completed
        
        completion_data = {
            "Status": ["Completed", "Pending"],
            "Count": [completed, pending]
        }
        
        df = pd.DataFrame(completion_data)
        st.bar_chart(df.set_index("Status"))
        
        st.caption(f"**{completed}** tasks completed out of **{total}** total")
    
    with col2:
        st.markdown("#### Learning Velocity")
        
        # Calculate tasks per week
        if completed > 0:
            # Estimate based on task completion
            days_active = len(set(t['completed_at'].date() for t in tasks if t.get('completed_at')))
            
            if days_active > 0:
                tasks_per_day = completed / days_active
                tasks_per_week = tasks_per_day * 7
                
                st.metric("Tasks/Week", f"{tasks_per_week:.1f}")
                st.metric("Tasks/Day", f"{tasks_per_day:.1f}")
                
                if tasks_per_week >= 5:
                    st.success("🔥 Excellent pace!")
                elif tasks_per_week >= 3:
                    st.info("👍 Good pace!")
                else:
                    st.warning("Consider increasing your pace")
        else:
            st.info("Complete some tasks to see velocity metrics")


def show_time_metrics(metrics: Dict, tasks: List[Dict]):
    """Show time-related metrics"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Time Spent")
        
        avg_time = metrics.get('average_completion_time', 0)
        min_time = metrics.get('min_completion_time', 0)
        max_time = metrics.get('max_completion_time', 0)
        
        if avg_time > 0:
            st.metric("Average", format_duration(int(avg_time)))
            st.metric("Minimum", format_duration(int(min_time)))
            st.metric("Maximum", format_duration(int(max_time)))
            
            # Time consistency
            if max_time > 0:
                time_variance = (max_time - min_time) / max_time
                if time_variance < 0.3:
                    st.success("✅ Very consistent timing")
                elif time_variance < 0.6:
                    st.info("👍 Reasonably consistent")
                else:
                    st.warning("⚠️ Highly variable timing")
        else:
            st.info("No time data available yet")
    
    with col2:
        st.markdown("#### Time Distribution")
        
        # Get completed tasks
        completed_tasks = [t for t in tasks if t.get('is_completed')]
        
        if completed_tasks:
            # Categorize by time spent
            quick = sum(1 for t in completed_tasks if t.get('estimated_minutes', 30) < 20)
            medium = sum(1 for t in completed_tasks if 20 <= t.get('estimated_minutes', 30) < 45)
            long = sum(1 for t in completed_tasks if t.get('estimated_minutes', 30) >= 45)
            
            time_dist = {
                "Duration": ["< 20 min", "20-45 min", "> 45 min"],
                "Tasks": [quick, medium, long]
            }
            
            df = pd.DataFrame(time_dist)
            st.bar_chart(df.set_index("Duration"))
        else:
            st.info("Complete tasks to see distribution")


def show_difficulty_metrics(metrics: Dict, tasks: List[Dict]):
    """Show difficulty-related metrics"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Difficulty Match")
        
        difficulty_match = metrics.get('difficulty_match', 'unknown')
        avg_difficulty = metrics.get('average_difficulty', 5)
        
        st.metric("Overall Match", difficulty_match.title())
        st.metric("Avg Difficulty", f"{avg_difficulty:.1f}/10")
        
        # Recommendations
        if difficulty_match == "too_easy":
            st.warning("⬆️ Consider increasing difficulty")
        elif difficulty_match == "too_hard":
            st.warning("⬇️ Consider reducing difficulty")
        else:
            st.success("✅ Difficulty is well-matched!")
    
    with col2:
        st.markdown("#### Task Difficulty Distribution")
        
        if tasks:
            # Group by difficulty
            easy = sum(1 for t in tasks if t.get('difficulty_score', 5) < 4)
            medium = sum(1 for t in tasks if 4 <= t.get('difficulty_score', 5) < 7)
            hard = sum(1 for t in tasks if t.get('difficulty_score', 5) >= 7)
            
            diff_dist = {
                "Difficulty": ["Easy (1-3)", "Medium (4-6)", "Hard (7-10)"],
                "Tasks": [easy, medium, hard]
            }
            
            df = pd.DataFrame(diff_dist)
            st.bar_chart(df.set_index("Difficulty"))
        else:
            st.info("No tasks available")


def show_progress_trends(goal: Dict):
    """Show progress trends over time"""
    
    st.markdown("### 📅 Progress Over Time")
    
    goal_id = goal["id"]
    
    # Get progress history
    history = get_progress_history(goal_id, days=30)
    
    if not history:
        st.info("No progress data available yet. Complete some tasks to see trends!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(history)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Completion trend
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Completion Percentage Trend")
        st.line_chart(df.set_index('date')['completion_percentage'])
    
    with col2:
        st.markdown("#### Tasks Completed Over Time")
        st.area_chart(df.set_index('date')['tasks_completed'])
    
    # Statistics
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_tracked = len(history)
        st.metric("Days Tracked", days_tracked)
    
    with col2:
        if len(history) > 1:
            avg_daily_progress = (history[-1]['completion_percentage'] - history[0]['completion_percentage']) / len(history)
            st.metric("Avg Daily Progress", f"{avg_daily_progress:.1f}%")
    
    with col3:
        if history:
            best_day = max(history, key=lambda x: x['tasks_completed'])
            st.metric("Best Day", f"{best_day['tasks_completed']} tasks")


def show_task_breakdown(goal: Dict):
    """Show detailed task breakdown"""
    
    st.markdown("### 📋 Task Breakdown")
    
    tasks = get_tasks_for_goal(goal["id"])
    
    if not tasks:
        st.info("No tasks available")
        return
    
    # Create DataFrame
    task_data = []
    for task in tasks:
        task_data.append({
            "Day": task['day_number'],
            "Task": task['task_text'][:50] + "..." if len(task['task_text']) > 50 else task['task_text'],
            "Difficulty": task.get('difficulty_score', 5),
            "Est. Time (min)": task.get('estimated_minutes', 30),
            "Status": "✅ Done" if task['is_completed'] else "⏳ Pending"
        })
    
    df = pd.DataFrame(task_data)
    
    # Display table
    st.dataframe(
        df,
        hide_index=True,
        width='stretch',
        column_config={
            "Day": st.column_config.NumberColumn("Day", format="%d"),
            "Difficulty": st.column_config.ProgressColumn(
                "Difficulty",
                min_value=0,
                max_value=10,
                format="%d/10"
            )
        }
    )
    
    # Download option
    st.markdown("---")
    
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Task List (CSV)",
        data=csv,
        file_name=f"learning_tasks_{date.today()}.csv",
        mime="text/csv"
    )


if __name__ == "__main__":
    show()