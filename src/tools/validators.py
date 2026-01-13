"""
Validation utilities for learning buddy data structures.
"""
from typing import Dict, List, Any, Optional, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)


def validate_roadmap(roadmap: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate roadmap structure.
    
    Required fields:
    - modules: list of module dicts
    - total_weeks: int
    
    Each module must have:
    - id: int
    - title: str
    - description: str
    - estimated_weeks: int
    - topics: list of strings
    
    Args:
        roadmap: Roadmap dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> roadmap = {"modules": [...], "total_weeks": 8}
        >>> is_valid, error = validate_roadmap(roadmap)
        >>> if not is_valid:
        ...     print(f"Invalid: {error}")
    """
    if not isinstance(roadmap, dict):
        return False, "Roadmap must be a dictionary"
    
    # Check required fields
    if "modules" not in roadmap:
        return False, "Roadmap missing 'modules' field"
    
    if "total_weeks" not in roadmap:
        return False, "Roadmap missing 'total_weeks' field"
    
    # Validate modules
    modules = roadmap["modules"]
    if not isinstance(modules, list):
        return False, "'modules' must be a list"
    
    if len(modules) == 0:
        return False, "Roadmap must have at least one module"
    
    # Validate each module
    for i, module in enumerate(modules):
        if not isinstance(module, dict):
            return False, f"Module {i} must be a dictionary"
        
        # Required module fields
        required_fields = ["id", "title", "description", "estimated_weeks", "topics"]
        for field in required_fields:
            if field not in module:
                return False, f"Module {i} missing required field: {field}"
        
        # Validate field types
        if not isinstance(module["id"], int):
            return False, f"Module {i} 'id' must be an integer"
        
        if not isinstance(module["title"], str) or len(module["title"]) == 0:
            return False, f"Module {i} 'title' must be a non-empty string"
        
        if not isinstance(module["description"], str):
            return False, f"Module {i} 'description' must be a string"
        
        if not isinstance(module["estimated_weeks"], int) or module["estimated_weeks"] <= 0:
            return False, f"Module {i} 'estimated_weeks' must be a positive integer"
        
        if not isinstance(module["topics"], list):
            return False, f"Module {i} 'topics' must be a list"
        
        if len(module["topics"]) == 0:
            return False, f"Module {i} must have at least one topic"
    
    # Validate total_weeks
    if not isinstance(roadmap["total_weeks"], int) or roadmap["total_weeks"] <= 0:
        return False, "'total_weeks' must be a positive integer"
    
    logger.debug(f"Roadmap validation passed: {len(modules)} modules, {roadmap['total_weeks']} weeks")
    return True, None


def validate_tasks(tasks: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Validate task list structure.
    
    Each task must have:
    - day: int
    - task: str (task description)
    - why: str (explanation)
    - resources: list of strings (URLs)
    - estimated_minutes: int
    - difficulty: float (0.0-1.0)
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(tasks, list):
        return False, "Tasks must be a list"
    
    if len(tasks) == 0:
        return False, "Task list cannot be empty"
    
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            return False, f"Task {i} must be a dictionary"
        
        # Required fields
        required_fields = ["day", "task", "why", "resources", "estimated_minutes", "difficulty"]
        for field in required_fields:
            if field not in task:
                return False, f"Task {i} missing required field: {field}"
        
        # Validate field types and values
        if not isinstance(task["day"], int) or task["day"] <= 0:
            return False, f"Task {i} 'day' must be a positive integer"
        
        if not isinstance(task["task"], str) or len(task["task"]) == 0:
            return False, f"Task {i} 'task' must be a non-empty string"
        
        if not isinstance(task["why"], str):
            return False, f"Task {i} 'why' must be a string"
        
        if not isinstance(task["resources"], list):
            return False, f"Task {i} 'resources' must be a list"
        
        if not isinstance(task["estimated_minutes"], int) or task["estimated_minutes"] <= 0:
            return False, f"Task {i} 'estimated_minutes' must be a positive integer"
        
        if not isinstance(task["difficulty"], (int, float)):
            return False, f"Task {i} 'difficulty' must be a number"
        
        if not (0.0 <= task["difficulty"] <= 1.0):
            return False, f"Task {i} 'difficulty' must be between 0.0 and 1.0"
    
    logger.debug(f"Task validation passed: {len(tasks)} tasks")
    return True, None


def validate_assessment(assessment: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate assessment structure.
    
    Assessment must have:
    - questions: list of question dicts
    
    Each question must have:
    - id: int
    - question: str
    - type: str (conceptual, practical, problem_solving, recall)
    - difficulty: float (0.0-1.0)
    - topic: str
    - expected_concepts: list of strings
    
    Args:
        assessment: Assessment dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(assessment, dict):
        return False, "Assessment must be a dictionary"
    
    if "questions" not in assessment:
        return False, "Assessment missing 'questions' field"
    
    questions = assessment["questions"]
    if not isinstance(questions, list):
        return False, "'questions' must be a list"
    
    if len(questions) == 0:
        return False, "Assessment must have at least one question"
    
    valid_types = ["conceptual", "practical", "problem_solving", "recall"]
    
    for i, question in enumerate(questions):
        if not isinstance(question, dict):
            return False, f"Question {i} must be a dictionary"
        
        # Required fields
        required_fields = ["id", "question", "type", "difficulty", "topic", "expected_concepts"]
        for field in required_fields:
            if field not in question:
                return False, f"Question {i} missing required field: {field}"
        
        # Validate types
        if not isinstance(question["id"], int):
            return False, f"Question {i} 'id' must be an integer"
        
        if not isinstance(question["question"], str) or len(question["question"]) == 0:
            return False, f"Question {i} 'question' must be a non-empty string"
        
        if question["type"] not in valid_types:
            return False, f"Question {i} 'type' must be one of {valid_types}"
        
        if not isinstance(question["difficulty"], (int, float)):
            return False, f"Question {i} 'difficulty' must be a number"
        
        if not (0.0 <= question["difficulty"] <= 1.0):
            return False, f"Question {i} 'difficulty' must be between 0.0 and 1.0"
        
        if not isinstance(question["topic"], str) or len(question["topic"]) == 0:
            return False, f"Question {i} 'topic' must be a non-empty string"
        
        if not isinstance(question["expected_concepts"], list):
            return False, f"Question {i} 'expected_concepts' must be a list"
        
        if len(question["expected_concepts"]) == 0:
            return False, f"Question {i} must have at least one expected concept"
    
    logger.debug(f"Assessment validation passed: {len(questions)} questions")
    return True, None


def validate_resource(resource: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a single resource structure.
    
    Resource must have:
    - title: str
    - url: str
    - type: str
    - platform: str
    - description: str
    - difficulty: float (0.0-1.0)
    - relevance_score: float (0.0-1.0)
    - learning_style_match: float (0.0-1.0)
    - estimated_hours: int
    
    Args:
        resource: Resource dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(resource, dict):
        return False, "Resource must be a dictionary"
    
    required_fields = [
        "title", "url", "type", "platform", "description",
        "difficulty", "relevance_score", "learning_style_match", "estimated_hours"
    ]
    
    for field in required_fields:
        if field not in resource:
            return False, f"Resource missing required field: {field}"
    
    # Validate types
    if not isinstance(resource["title"], str) or len(resource["title"]) == 0:
        return False, "'title' must be a non-empty string"
    
    if not isinstance(resource["url"], str) or len(resource["url"]) == 0:
        return False, "'url' must be a non-empty string"
    
    if not isinstance(resource["type"], str):
        return False, "'type' must be a string"
    
    if not isinstance(resource["platform"], str):
        return False, "'platform' must be a string"
    
    if not isinstance(resource["description"], str):
        return False, "'description' must be a string"
    
    # Validate numeric ranges
    for field in ["difficulty", "relevance_score", "learning_style_match"]:
        if not isinstance(resource[field], (int, float)):
            return False, f"'{field}' must be a number"
        
        if not (0.0 <= resource[field] <= 1.0):
            return False, f"'{field}' must be between 0.0 and 1.0"
    
    if not isinstance(resource["estimated_hours"], int) or resource["estimated_hours"] <= 0:
        return False, "'estimated_hours' must be a positive integer"
    
    return True, None


def validate_conversation_history(
    conversation: List[Dict[str, str]]
) -> Tuple[bool, Optional[str]]:
    """
    Validate conversation history structure.
    
    Each message must have:
    - role: str ("user" or "assistant")
    - content: str
    
    Args:
        conversation: List of conversation messages
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(conversation, list):
        return False, "Conversation must be a list"
    
    valid_roles = ["user", "assistant", "system"]
    
    for i, message in enumerate(conversation):
        if not isinstance(message, dict):
            return False, f"Message {i} must be a dictionary"
        
        if "role" not in message:
            return False, f"Message {i} missing 'role' field"
        
        if "content" not in message:
            return False, f"Message {i} missing 'content' field"
        
        if message["role"] not in valid_roles:
            return False, f"Message {i} 'role' must be one of {valid_roles}"
        
        if not isinstance(message["content"], str):
            return False, f"Message {i} 'content' must be a string"
    
    return True, None


__all__ = [
    "validate_roadmap",
    "validate_tasks",
    "validate_assessment",
    "validate_resource",
    "validate_conversation_history",
]