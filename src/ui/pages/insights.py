"""
Insights Page - AI-Generated Learning Insights and Recommendations
Day 5: Display personalized insights, patterns, and predictions
"""

import streamlit as st
from datetime import date
from typing import Dict, List

from src.ui.utils import (
    get_active_goal, get_performance_metrics, get_learning_gaps,
    predict_completion_date, get_tasks_for_goal, get_completion_rate, get_current_state
)
from src.agents.insight_agent import InsightAgent
from src.llm.config import LLMConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


def show_adaptive_insights(state: Dict):
    """Display insights from adaptive controller analysis"""
    
    st.markdown("### 🎯 Personalized Adaptive Insights")
    
    struggles = state.get("struggles_detected", False)
    severity = state.get("struggle_severity", 0)
    
    if struggles:
        # Show struggle alert
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if severity > 0.7:
                st.error("🚨 **Significant Learning Challenges Detected**")
            else:
                st.warning("⚠️ **Some Areas Need Attention**")
            
            st.markdown(f"**Struggle Severity:** {severity:.0%}")
        
        with col2:
            if st.button("📚 View Alternatives"):
                st.session_state.current_page = "View Plan"
                st.rerun()
        
        # Show struggling topics
        if state.get("struggling_topics"):
            st.markdown("**Topics with Challenges:**")
            for topic in state["struggling_topics"]:
                st.write(f"• {topic}")
        
        # Show struggling modules
        if state.get("struggling_module_id"):
            st.info(f"📦 **Module:** {state['struggling_module_id']}")
    
    # Show recommended actions
    if state.get("recommended_actions"):
        st.markdown("**What You Can Do:**")
        for action in state["recommended_actions"]:
            st.write(f"✓ {action}")
    
    # Show pacing recommendation
    if state.get("pacing_adjustment") and state["pacing_adjustment"] != 1.0:
        pacing = state["pacing_adjustment"]
        if pacing < 1.0:
            pacing_pct = int((1 - pacing) * 100)
            st.info(f"🐢 Consider slowing down by {pacing_pct}% to better consolidate learning")
        else:
            pacing_pct = int((pacing - 1) * 100)
            st.success(f"🚀 You're excelling! Consider accelerating by {pacing_pct}%")
    
    # Re-curation status
    if state.get("re_curation_triggered"):
        st.success("✨ Alternative resources are being generated for your struggling areas")
    
    st.markdown("---")



def show():
    """Display the insights page"""
    
    st.markdown('<h1 class="main-header">💡 Learning Insights</h1>', unsafe_allow_html=True)
    st.markdown("### AI-Powered Analysis of Your Learning Journey")
    
    # Check for active goal
    goal = get_active_goal()
    
    if not goal:
        st.warning("⚠️ No active learning goal found.")
        
        if st.button("🎯 Create New Goal", width='stretch'):
            st.session_state.current_page = "Create Goal"
            st.rerun()
        
        return
    
    # Get current state for adaptive insights
    state = get_current_state()
    
    # Check if enough data exists
    tasks = get_tasks_for_goal(goal["id"])
    completed_tasks = [t for t in tasks if t.get('is_completed')]
    
    if len(completed_tasks) < 3:
        show_insufficient_data_message(completed_tasks)
        return
    
    # Show adaptation alerts first if available
    if state.get("struggles_detected") or state.get("adaptation_required"):
        show_adaptive_insights(state)
    
    # Display insights
    show_ai_insights(goal)
    show_learning_patterns(goal)
    show_recommendations(goal)
    show_predictions(goal)


def show_insufficient_data_message(completed_tasks: List[Dict]):
    """Show message when not enough data for insights"""
    
    st.info("📊 **Not enough data yet for comprehensive insights**")
    
    tasks_needed = 3 - len(completed_tasks)
    
    st.markdown(f"""
    ### Keep Learning!
    
    Complete **{tasks_needed} more task(s)** to unlock detailed AI-powered insights about your learning journey.
    
    Once you have enough data, you'll see:
    - 🎯 Personalized learning patterns
    - 💡 AI-generated recommendations
    - 📈 Performance predictions
    - 🚀 Optimization suggestions
    """)
    
    if st.button("✅ Go to Tasks", width='stretch', type="primary"):
        st.session_state.current_page = "Daily Tasks"
        st.rerun()


def show_ai_insights(goal: Dict):
    """Generate and display AI-powered insights"""
    
    st.markdown("### 🤖 AI-Generated Insights")
    
    goal_id = goal["id"]
    metrics = get_performance_metrics(goal_id)
    
    try:
        # Generate insights using Insight Agent
        with st.spinner("🔮 Analyzing your learning patterns..."):
            insight_agent = InsightAgent()
            state = get_current_state()
            
            # Generate insights
            insights_text = insight_agent.generate_insights(state, metrics)
        
        # Display insights
        st.markdown(insights_text)
    
    except Exception as e:
        logger.error(f"Error generating AI insights: {e}")
        st.error("Unable to generate AI insights at this time.")
        
        # Fallback: show basic insights
        show_basic_insights(metrics)
    
    st.markdown("---")


def show_basic_insights(metrics: Dict):
    """Show basic insights when AI generation fails"""
    
    completion_rate = metrics.get('completion_rate', 0)
    consistency = metrics.get('consistency_score', 0)
    difficulty_match = metrics.get('difficulty_match', 'unknown')
    
    st.markdown("#### 📊 Key Observations")
    
    # Completion rate insight
    if completion_rate >= 75:
        st.success("✅ **Excellent Progress**: You're maintaining a strong completion rate of over 75%!")
    elif completion_rate >= 50:
        st.info("👍 **Good Progress**: You're completing tasks at a reasonable pace.")
    else:
        st.warning("⚠️ **Room for Improvement**: Try to increase your task completion rate.")
    
    # Consistency insight
    if consistency >= 0.8:
        st.success("🔄 **Highly Consistent**: Your learning schedule is very regular!")
    elif consistency >= 0.5:
        st.info("📅 **Moderately Consistent**: Good consistency with room to improve.")
    else:
        st.warning("⚡ **Variable Schedule**: Try to establish a more consistent learning routine.")
    
    # Difficulty insight
    if difficulty_match == "appropriate":
        st.success("🎯 **Perfect Match**: Task difficulty aligns well with your skill level!")
    elif difficulty_match == "too_easy":
        st.info("⬆️ **Challenge Yourself**: Consider tackling more advanced topics.")
    elif difficulty_match == "too_hard":
        st.info("⬇️ **Take It Easy**: You might benefit from easier foundational tasks.")


def show_learning_patterns(goal: Dict):
    """Display identified learning patterns"""
    
    st.markdown("### 🔍 Learning Patterns")
    
    goal_id = goal["id"]
    metrics = get_performance_metrics(goal_id)
    tasks = get_tasks_for_goal(goal_id)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⏰ Time Patterns")
        
        avg_time = metrics.get('average_completion_time', 0)
        target_time = goal.get('daily_minutes', 60)
        
        if avg_time > 0:
            if avg_time < target_time * 0.8:
                st.info("⚡ **Fast Learner**: You complete tasks faster than estimated!")
                st.caption("Consider taking on more challenging tasks.")
            elif avg_time > target_time * 1.2:
                st.info("🐢 **Thorough Learner**: You take your time to understand deeply.")
                st.caption("This thoroughness will serve you well!")
            else:
                st.success("🎯 **On Target**: Your pace matches the planned schedule perfectly.")
        else:
            st.caption("Complete more tasks to identify patterns")
    
    with col2:
        st.markdown("#### 📊 Performance Patterns")
        
        completed = [t for t in tasks if t.get('is_completed')]
        
        if completed:
            # Find best performing difficulty range
            easy_completed = sum(1 for t in completed if t.get('difficulty_score', 5) < 4)
            medium_completed = sum(1 for t in completed if 4 <= t.get('difficulty_score', 5) < 7)
            hard_completed = sum(1 for t in completed if t.get('difficulty_score', 5) >= 7)
            
            best_range = "medium"
            if easy_completed > medium_completed and easy_completed > hard_completed:
                best_range = "easy"
            elif hard_completed > medium_completed:
                best_range = "hard"
            
            st.info(f"💪 **Strength Area**: You excel at {best_range} difficulty tasks")
            
            # Completion trend
            if len(completed) >= 5:
                recent_completion = len([t for t in completed[-5:]])
                if recent_completion >= 4:
                    st.success("🔥 **Hot Streak**: You're on a roll recently!")
                else:
                    st.caption("📈 Keep building momentum")
        else:
            st.caption("Complete tasks to identify patterns")
    
    st.markdown("---")


def show_recommendations(goal: Dict):
    """Display personalized recommendations"""
    
    st.markdown("### 🎯 Personalized Recommendations")
    
    goal_id = goal["id"]
    metrics = get_performance_metrics(goal_id)
    gaps = get_learning_gaps(goal_id)
    completion_rate = get_completion_rate(goal_id)
    
    recommendations = []
    
    # Completion-based recommendations
    if completion_rate < 50:
        recommendations.append({
            "icon": "🚀",
            "title": "Increase Your Pace",
            "description": "Try to complete at least one task per day to build momentum.",
            "priority": "high"
        })
    
    # Consistency recommendations
    consistency = metrics.get('consistency_score', 0)
    if consistency < 0.5:
        recommendations.append({
            "icon": "📅",
            "title": "Establish a Routine",
            "description": "Set a specific time each day for learning to build consistency.",
            "priority": "medium"
        })
    
    # Difficulty recommendations
    difficulty_match = metrics.get('difficulty_match', 'unknown')
    if difficulty_match == "too_easy":
        recommendations.append({
            "icon": "⬆️",
            "title": "Challenge Yourself More",
            "description": "You're ready for more advanced topics. Don't be afraid to tackle harder material.",
            "priority": "medium"
        })
    elif difficulty_match == "too_hard":
        recommendations.append({
            "icon": "📚",
            "title": "Review Fundamentals",
            "description": "Spend more time on foundational concepts before advancing.",
            "priority": "high"
        })
    
    # Gap-based recommendations
    if gaps:
        recommendations.append({
            "icon": "🔍",
            "title": "Address Learning Gaps",
            "description": f"Focus on: {', '.join(gaps[:3])}",
            "priority": "high"
        })
    
    # Time-based recommendations
    avg_time = metrics.get('average_completion_time', 0)
    target_time = goal.get('daily_minutes', 60)
    if avg_time > target_time * 1.5:
        recommendations.append({
            "icon": "⏱️",
            "title": "Optimize Your Time",
            "description": "Consider breaking tasks into smaller chunks or using time management techniques.",
            "priority": "low"
        })
    
    # General recommendations
    if not recommendations:
        recommendations.append({
            "icon": "✅",
            "title": "Keep Up the Great Work!",
            "description": "You're doing everything right. Maintain your current pace and consistency.",
            "priority": "low"
        })
    
    # Display recommendations
    for rec in recommendations:
        priority_color = {
            "high": "error",
            "medium": "warning",
            "low": "info"
        }.get(rec["priority"], "info")
        
        with st.container():
            st.markdown(f"#### {rec['icon']} {rec['title']}")
            
            if rec["priority"] == "high":
                st.error(rec["description"])
            elif rec["priority"] == "medium":
                st.warning(rec["description"])
            else:
                st.info(rec["description"])
    
    st.markdown("---")


def show_predictions(goal: Dict):
    """Show predictions about learning journey"""
    
    st.markdown("### 🔮 Predictions & Forecasts")
    
    goal_id = goal["id"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📅 Completion Forecast")
        
        predicted_date = predict_completion_date(goal_id)
        st.info(f"**Estimated Completion:** {predicted_date}")
        
        if predicted_date != "Unable to predict" and predicted_date != "Not enough data":
            st.caption("Based on your current pace and consistency")
        else:
            st.caption("Complete more tasks for accurate prediction")
    
    with col2:
        st.markdown("#### 🎓 Mastery Level")
        
        completion_rate = get_completion_rate(goal_id)
        
        if completion_rate >= 80:
            mastery = "Advanced"
            emoji = "🏆"
        elif completion_rate >= 50:
            mastery = "Intermediate"
            emoji = "📚"
        else:
            mastery = "Beginner"
            emoji = "🌱"
        
        st.info(f"{emoji} **Current Level:** {mastery}")
        st.caption(f"{completion_rate:.0f}% of planned learning completed")
    
    st.markdown("---")
    
    # Motivational message
    completion_rate = get_completion_rate(goal_id)
    
    if completion_rate >= 75:
        st.success("🌟 **Outstanding progress!** You're on track to master your goal!")
    elif completion_rate >= 50:
        st.info("💪 **Great work!** You're making solid progress. Keep it up!")
    elif completion_rate >= 25:
        st.info("🚀 **Good start!** Stay consistent and you'll see great results!")
    else:
        st.info("🌱 **Just beginning!** Every expert started where you are. Keep going!")


if __name__ == "__main__":
    show()