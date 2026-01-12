"""
AI Learning Buddy Advanced - Main Application Entry Point
Streamlit interface for the advanced learning platform.
"""
import streamlit as st
from pathlib import Path

# Import configuration and database
from src.utils.config import get_settings
from src.utils.logger import get_logger
from src.database import init_database

logger = get_logger(__name__)


def main():
    """Main application entry point."""
    
    # Page configuration
    st.set_page_config(
        page_title="AI Learning Buddy Advanced",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize settings
    try:
        settings = get_settings()
        logger.info("Settings loaded successfully")
    except Exception as e:
        st.error(f"Failed to load settings: {e}")
        st.info("Please create a .env file based on .env.example")
        return
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        st.error(f"Failed to initialize database: {e}")
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return
    
    # Application title
    st.title("🎓 AI Learning Buddy Advanced")
    st.markdown("---")
    
    # Placeholder content
    st.info("⚙️ **Day 1 Complete!** Database foundation is ready.")
    st.markdown("""
    ### ✅ Completed Setup:
    - ✓ Project structure created
    - ✓ Dependencies configured
    - ✓ Database models defined
    - ✓ Logging system configured
    - ✓ Configuration management ready
    
    ### 🔜 Coming Next (Day 2):
    - LangGraph core setup
    - State management
    - Node implementations
    - Agent framework
    """)
    
    # Show database connection status
    with st.expander("📊 System Status"):
        st.success(f"Database: Connected ({settings.database_url})")
        st.success(f"OpenAI Model: {settings.openai_model}")
        st.info(f"Log Level: {settings.log_level}")
        st.info(f"Debug Mode: {settings.debug_mode}")


if __name__ == "__main__":
    main()
