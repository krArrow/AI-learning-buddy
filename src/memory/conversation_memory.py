"""
Conversation Memory - Memory Management

Manages multi-turn conversation history between user and agents.
- Stores conversations in database
- Retrieves conversation context
- Implements sliding window (keep last N messages)
- Integrates with LangChain memory classes
- Clears conversations after goal completion

Author: AI Learning Platform Team
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from src.database.crud import (
    create_conversation,
    get_conversations,
    delete_goal_conversations
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    """
    Manages conversation history for multi-turn agent interactions.
    
    Stores all user-agent conversations and retrieves them for context
    in multi-turn flows like goal clarification, assessment, etc.
    
    Features:
    - Store individual messages
    - Retrieve conversation history with sliding window
    - Format history for LLM consumption
    - Clear old conversations
    - Track by goal and agent type
    
    Example:
        >>> memory = ConversationMemory()
        >>> memory.add_message(
        ...     goal_id=1,
        ...     agent_type="goal_clarifier",
        ...     role="user",
        ...     content="I want to learn Python"
        ... )
        >>> history = memory.get_history(goal_id=1, agent_type="goal_clarifier")
        >>> formatted = memory.get_formatted_history(goal_id=1)
    """
    
    def __init__(self, window_size: int = 10):
        """
        Initialize conversation memory.
        
        Args:
            window_size: Number of messages to keep in sliding window
                        Default: 10 (keeps 5 exchanges)
        """
        self.window_size = window_size
        self.logger = logger
        self.logger.info(f"ConversationMemory initialized with window_size={window_size}")
    
    def add_message(
        self,
        goal_id: int,
        agent_type: str,
        role: str,
        content: str
    ) -> Optional[int]:
        """
        Store a conversation message in database.
        
        Args:
            goal_id: ID of the associated learning goal
            agent_type: Type of agent (goal_clarifier, assessment, adaptation, etc.)
            role: Message sender role ("user" or "assistant")
            content: Message content/text
        
        Returns:
            ID of created conversation record, or None on error
            
        Raises:
            ValueError: If required parameters are invalid
            
        Example:
            >>> msg_id = memory.add_message(
            ...     goal_id=1,
            ...     agent_type="goal_clarifier",
            ...     role="user",
            ...     content="I want to learn machine learning"
            ... )
            >>> assert msg_id is not None
        """
        try:
            # Validate inputs
            if not isinstance(goal_id, int) or goal_id <= 0:
                raise ValueError(f"Invalid goal_id: {goal_id}")
            
            if not agent_type or not isinstance(agent_type, str):
                raise ValueError(f"Invalid agent_type: {agent_type}")
            
            if role not in ["user", "assistant"]:
                raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")
            
            if not content or not isinstance(content, str):
                raise ValueError(f"Invalid content: {content}")
            
            # Store in database
            conversation = create_conversation(
                goal_id=goal_id,
                agent_type=agent_type,
                user_message=content if role == "user" else None,
                ai_response=content if role == "assistant" else None
            )
            
            msg_id = conversation.id if hasattr(conversation, 'id') else None
            self.logger.debug(
                f"Stored message: goal_id={goal_id}, agent={agent_type}, "
                f"role={role}, msg_id={msg_id}"
            )
            
            return msg_id
            
        except ValueError as e:
            self.logger.error(f"Validation error in add_message: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error storing conversation message: {str(e)}")
            return None
    
    def get_history(
        self,
        goal_id: int,
        agent_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a goal.
        
        Implements sliding window - returns only the most recent messages
        up to the limit.
        
        Args:
            goal_id: ID of the learning goal
            agent_type: Optional agent type to filter by
            limit: Maximum number of messages to return
        
        Returns:
            List of conversation dictionaries with:
            [{
                "id": int,
                "timestamp": str (ISO format),
                "role": "user" or "assistant",
                "content": str,
                "agent_type": str
            }, ...]
            
        Example:
            >>> history = memory.get_history(goal_id=1)
            >>> assert len(history) <= 10
            >>> assert history[0]["role"] in ["user", "assistant"]
        """
        try:
            # Validate input
            if not isinstance(goal_id, int) or goal_id <= 0:
                raise ValueError(f"Invalid goal_id: {goal_id}")
            
            if limit < 1:
                raise ValueError(f"limit must be >= 1, got {limit}")
            
            # Fetch from database
            conversations = get_conversations(
                goal_id=goal_id,
                agent_type=agent_type,
                limit=limit
            )
            
            # Format results
            history = []
            for conv in conversations:
                # Determine role from whether user_message or ai_response is set
                if hasattr(conv, 'user_message') and conv.user_message:
                    role = "user"
                    content = conv.user_message
                elif hasattr(conv, 'ai_response') and conv.ai_response:
                    role = "assistant"
                    content = conv.ai_response
                else:
                    continue
                
                history.append({
                    "id": conv.id if hasattr(conv, 'id') else None,
                    "timestamp": (
                        conv.timestamp.isoformat() if hasattr(conv, 'timestamp') 
                        else datetime.utcnow().isoformat()
                    ),
                    "role": role,
                    "content": content,
                    "agent_type": conv.agent_type if hasattr(conv, 'agent_type') else None
                })
            
            self.logger.debug(
                f"Retrieved {len(history)} messages for goal_id={goal_id}, "
                f"agent_type={agent_type}"
            )
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error retrieving conversation history: {str(e)}")
            return []
    
    def get_formatted_history(
        self,
        goal_id: int,
        agent_type: Optional[str] = None,
        limit: int = 10
    ) -> str:
        """
        Get formatted conversation history as string for LLM input.
        
        Formats conversation in standard chat format suitable for
        passing to language models as context.
        
        Args:
            goal_id: ID of the learning goal
            agent_type: Optional agent type to filter by
            limit: Maximum messages to include
        
        Returns:
            Formatted conversation string:
            "User: Message here
             Assistant: Response here
             User: Next message..."
        
        Example:
            >>> formatted = memory.get_formatted_history(goal_id=1)
            >>> assert "User:" in formatted or "Assistant:" in formatted
        """
        try:
            history = self.get_history(
                goal_id=goal_id,
                agent_type=agent_type,
                limit=limit
            )
            
            if not history:
                return ""
            
            lines = []
            for msg in history:
                role_label = "User" if msg["role"] == "user" else "Assistant"
                lines.append(f"{role_label}: {msg['content']}")
            
            formatted = "\n".join(lines)
            self.logger.debug(f"Formatted {len(history)} messages for LLM")
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Error formatting conversation history: {str(e)}")
            return ""
    
    def get_last_n_messages(
        self,
        goal_id: int,
        n: int = 5,
        agent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the last N messages from conversation history.
        
        Convenience method for getting recent messages only.
        
        Args:
            goal_id: ID of the learning goal
            n: Number of most recent messages to return
            agent_type: Optional agent type to filter by
        
        Returns:
            List of most recent N messages
            
        Example:
            >>> recent = memory.get_last_n_messages(goal_id=1, n=3)
            >>> assert len(recent) <= 3
        """
        return self.get_history(
            goal_id=goal_id,
            agent_type=agent_type,
            limit=n
        )
    
    def clear_history(self, goal_id: int) -> bool:
        """
        Clear all conversation history for a goal.
        
        Useful when goal is completed or reset.
        
        Args:
            goal_id: ID of the learning goal
        
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> success = memory.clear_history(goal_id=1)
            >>> assert success
        """
        try:
            if not isinstance(goal_id, int) or goal_id <= 0:
                raise ValueError(f"Invalid goal_id: {goal_id}")
            
            delete_goal_conversations(goal_id)
            
            self.logger.info(f"Cleared conversation history for goal_id={goal_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing conversation history: {str(e)}")
            return False
    
    def count_messages(
        self,
        goal_id: int,
        agent_type: Optional[str] = None
    ) -> int:
        """
        Count total messages in conversation history.
        
        Args:
            goal_id: ID of the learning goal
            agent_type: Optional agent type to filter by
        
        Returns:
            Number of messages
        """
        try:
            history = self.get_history(
                goal_id=goal_id,
                agent_type=agent_type,
                limit=10000  # Get all
            )
            return len(history)
        except Exception as e:
            self.logger.error(f"Error counting messages: {str(e)}")
            return 0
    
    def get_conversation_summary(
        self,
        goal_id: int,
        agent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of conversation statistics.
        
        Useful for understanding conversation patterns.
        
        Returns:
            Dictionary with:
            {
                "total_messages": int,
                "user_messages": int,
                "assistant_messages": int,
                "first_message_time": str,
                "last_message_time": str,
                "agents_involved": list
            }
        """
        try:
            history = self.get_history(
                goal_id=goal_id,
                agent_type=agent_type,
                limit=10000
            )
            
            if not history:
                return {
                    "total_messages": 0,
                    "user_messages": 0,
                    "assistant_messages": 0
                }
            
            summary = {
                "total_messages": len(history),
                "user_messages": sum(1 for m in history if m["role"] == "user"),
                "assistant_messages": sum(1 for m in history if m["role"] == "assistant"),
                "first_message_time": history[0]["timestamp"],
                "last_message_time": history[-1]["timestamp"],
                "agents_involved": list(set(m["agent_type"] for m in history if m.get("agent_type")))
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating conversation summary: {str(e)}")
            return {}


# Singleton instance
_conversation_memory_instance: Optional[ConversationMemory] = None


def get_conversation_memory() -> ConversationMemory:
    """
    Get or create singleton instance of ConversationMemory.
    
    Ensures only one conversation memory instance exists throughout
    the application lifecycle.
    
    Returns:
        ConversationMemory singleton instance
        
    Example:
        >>> memory = get_conversation_memory()
        >>> memory.add_message(1, "goal_clarifier", "user", "Hello")
    """
    global _conversation_memory_instance
    if _conversation_memory_instance is None:
        _conversation_memory_instance = ConversationMemory()
    return _conversation_memory_instance
