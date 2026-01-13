"""
Memory Management Module

Handles conversation history, learning progress, and resource storage.

Includes:
- ConversationMemory: Chat history management
- LearningMemory: Performance tracking and analytics
- VectorStore: Semantic search over learning resources
"""

from src.memory.conversation_memory import (
    ConversationMemory,
    get_conversation_memory
)
from src.memory.learning_memory import (
    LearningMemory,
    get_learning_memory
)
from src.memory.vector_store import (
    VectorStore,
    get_vector_store,
    reset_vector_store
)

__all__ = [
    "ConversationMemory",
    "LearningMemory",
    "VectorStore",
    "get_conversation_memory",
    "get_learning_memory",
    "get_vector_store",
    "reset_vector_store",
]
