# """
# AI Learning Buddy Advanced - Main Application Entry Point
# Streamlit interface for the advanced learning platform.
# """
# import streamlit as st
# from pathlib import Path

# # Import configuration and database
# from src.utils.config import get_settings
# from src.utils.logger import get_logger
# from src.database import init_database

# logger = get_logger(__name__)


# def main():
#     """Main application entry point."""
    
#     # Page configuration
#     st.set_page_config(
#         page_title="AI Learning Buddy Advanced",
#         page_icon="🎓",
#         layout="wide",
#         initial_sidebar_state="expanded"
#     )
    
#     # Initialize settings
#     try:
#         settings = get_settings()
#         logger.info("Settings loaded successfully")
#     except Exception as e:
#         st.error(f"Failed to load settings: {e}")
#         st.info("Please create a .env file based on .env.example")
#         return
    
#     # Initialize database
#     try:
#         init_database()
#         logger.info("Database initialized successfully")
#     except Exception as e:
#         st.error(f"Failed to initialize database: {e}")
#         logger.error(f"Database initialization failed: {e}", exc_info=True)
#         return
    
#     # Application title
#     st.title("🎓 AI Learning Buddy Advanced")
#     st.markdown("---")
    
#     # Placeholder content
#     st.info("⚙️ **Day 1 Complete!** Database foundation is ready.")
#     st.markdown("""
#     ### ✅ Completed Setup:
#     - ✓ Project structure created
#     - ✓ Dependencies configured
#     - ✓ Database models defined
#     - ✓ Logging system configured
#     - ✓ Configuration management ready
    
#     ### 🔜 Coming Next (Day 2):
#     - LangGraph core setup
#     - State management
#     - Node implementations
#     - Agent framework
#     """)
    
#     # Show database connection status
#     with st.expander("📊 System Status"):
#         st.success(f"Database: Connected ({settings.database_url})")
#         st.success(f"OpenAI Model: {settings.openai_model}")
#         st.info(f"Log Level: {settings.log_level}")
#         st.info(f"Debug Mode: {settings.debug_mode}")


# if __name__ == "__main__":
#     main()

"""
AI Learning Buddy Advanced - Main Streamlit Application
Day 5: Complete UI Implementation with Multi-Page Navigation
"""

import streamlit as st
from typing import Optional
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.core.graph import build_graph_with_retry, get_graph
from src.database.db import init_database, DatabaseManager
from src.memory.vector_store import VectorStoreManager
from src.utils.logger import setup_logger
from src.utils.config import get_settings

# Initialize logger
logger = setup_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Learning Buddy",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-message {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
        height: 3rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize all session state variables"""
    
    # Graph instance
    if "graph" not in st.session_state:
        try:
            logger.info("Building LangGraph instance...")
            st.session_state.graph = build_graph_with_retry()
            logger.info("Graph built successfully")
        except Exception as e:
            logger.error(f"Failed to build graph: {e}")
            st.session_state.graph = None
            st.error(f"Failed to initialize graph: {e}")
    
    # Vector store instance
    if "vector_store" not in st.session_state:
        try:
            logger.info("Initializing vector store...")
            st.session_state.vector_store = VectorStoreManager()
            logger.info("Vector store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            st.session_state.vector_store = None
            st.warning("Vector store initialization failed. RAG features may be limited.")
    
    # Database initialization
    if "db_initialized" not in st.session_state:
        try:
            logger.info("Initializing database...")
            init_database()
            st.session_state.db_initialized = True
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            st.session_state.db_initialized = False
            st.error(f"Database initialization failed: {e}")
    
    # Active goal
    if "active_goal_id" not in st.session_state:
        st.session_state.active_goal_id = None
    
    # Current state
    if "current_state" not in st.session_state:
        st.session_state.current_state = None
    
    # UI state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"
    
    # Conversation history for goal clarification
    if "clarification_messages" not in st.session_state:
        st.session_state.clarification_messages = []
    
    # Task completion state
    if "last_completed_task" not in st.session_state:
        st.session_state.last_completed_task = None
    
    # Loading states
    if "is_loading" not in st.session_state:
        st.session_state.is_loading = False
    
    # Error state
    if "last_error" not in st.session_state:
        st.session_state.last_error = None


def show_sidebar():
    """Display sidebar with navigation and status"""
    
    with st.sidebar:
        st.markdown('<div class="main-header">📚</div>', unsafe_allow_html=True)
        st.markdown("### AI Learning Buddy")
        st.markdown("---")
        
        # System status
        st.markdown("#### System Status")
        
        # Graph status
        if st.session_state.graph:
            st.success("✅ Graph: Ready")
        else:
            st.error("❌ Graph: Not Ready")
        
        # Database status
        if st.session_state.db_initialized:
            st.success("✅ Database: Connected")
        else:
            st.error("❌ Database: Error")
        
        # Vector store status
        if st.session_state.vector_store:
            st.success("✅ Vector Store: Ready")
        else:
            st.warning("⚠️ Vector Store: Limited")
        
        st.markdown("---")
        
        # Navigation
        st.markdown("#### Navigation")
        
        pages = {
            "🏠 Home": "Home",
            "🎯 Create Goal": "Create Goal",
            "🗺️ View Plan": "View Plan",
            "✅ Daily Tasks": "Daily Tasks",
            "📈 Progress": "Progress",
            "💡 Insights": "Insights"
        }
        
        for label, page_name in pages.items():
            if st.button(label, key=f"nav_{page_name}", use_container_width=True):
                st.session_state.current_page = page_name
                st.rerun()
        
        st.markdown("---")
        
        # Active goal info
        if st.session_state.active_goal_id:
            st.markdown("#### Active Goal")
            try:
                from src.ui.utils import get_active_goal
                goal = get_active_goal()
                if goal:
                    st.info(f"🎓 {goal['goal_text'][:50]}...")
                    st.caption(f"Level: {goal['level'].title()}")
            except Exception as e:
                logger.error(f"Error displaying active goal: {e}")
        
        st.markdown("---")
        
        # Settings
        with st.expander("⚙️ Settings"):
            st.markdown("**Theme**")
            st.caption("Auto (System)")
            
            st.markdown("**Debug Mode**")
            debug_mode = st.checkbox("Enable", value=False)
            if debug_mode:
                st.caption("Showing detailed logs")
        
        # Footer
        st.markdown("---")
        st.caption("v1.0.0 | Built with ❤️")
        st.caption("Powered by LangGraph & OpenAI")


def main():
    """Main application entry point"""
    
    # Initialize session state
    initialize_session_state()
    
    # Show sidebar
    show_sidebar()
    
    # Route to appropriate page
    page = st.session_state.current_page
    
    try:
        if page == "Home":
            from src.ui.pages import home
            home.show()
        
        elif page == "Create Goal":
            from src.ui.pages import create_goal
            create_goal.show()
        
        elif page == "View Plan":
            from src.ui.pages import view_plan
            view_plan.show()
        
        elif page == "Daily Tasks":
            from src.ui.pages import daily_tasks
            daily_tasks.show()
        
        elif page == "Progress":
            from src.ui.pages import progress
            progress.show()
        
        elif page == "Insights":
            from src.ui.pages import insights
            insights.show()
        
        else:
            st.error(f"Unknown page: {page}")
    
    except Exception as e:
        logger.error(f"Error rendering page {page}: {e}")
        st.error(f"An error occurred while loading the page: {e}")
        
        if st.button("🔄 Retry"):
            st.rerun()
        
        if st.button("🏠 Go to Home"):
            st.session_state.current_page = "Home"
            st.rerun()


if __name__ == "__main__":
    main()



