"""
Course Search Tool - Searches for learning resources.
Mock implementation with sample data (real API integration in production).
"""
from typing import List, Dict, Any, Optional
import re
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Sample resource database (mock)
MOCK_RESOURCES = {
    "python": [
        {
            "title": "Python for Everybody Specialization",
            "url": "https://www.coursera.org/specializations/python",
            "type": "course",
            "platform": "Coursera",
            "description": "Learn to Program and Analyze Data with Python",
            "difficulty": 0.2,
            "estimated_hours": 40,
            "tags": ["beginner", "data", "programming"]
        },
        {
            "title": "Automate the Boring Stuff with Python",
            "url": "https://automatetheboringstuff.com/",
            "type": "book",
            "platform": "Web",
            "description": "Practical programming for total beginners",
            "difficulty": 0.3,
            "estimated_hours": 20,
            "tags": ["beginner", "automation", "practical"]
        },
        {
            "title": "Python Tutorial for Beginners",
            "url": "https://youtube.com/watch?v=_uQrJ0TkZlc",
            "type": "video",
            "platform": "YouTube",
            "description": "Complete Python tutorial in 6 hours",
            "difficulty": 0.2,
            "estimated_hours": 6,
            "tags": ["beginner", "video", "comprehensive"]
        },
    ],
    "javascript": [
        {
            "title": "The Complete JavaScript Course 2024",
            "url": "https://www.udemy.com/course/the-complete-javascript-course/",
            "type": "course",
            "platform": "Udemy",
            "description": "Build real projects with modern JavaScript",
            "difficulty": 0.4,
            "estimated_hours": 50,
            "tags": ["intermediate", "projects", "modern"]
        },
        {
            "title": "JavaScript.info",
            "url": "https://javascript.info/",
            "type": "article",
            "platform": "Web",
            "description": "The Modern JavaScript Tutorial",
            "difficulty": 0.3,
            "estimated_hours": 30,
            "tags": ["beginner", "reference", "comprehensive"]
        },
    ],
    "react": [
        {
            "title": "React - The Complete Guide",
            "url": "https://www.udemy.com/course/react-the-complete-guide/",
            "type": "course",
            "platform": "Udemy",
            "description": "Learn React, Hooks, Redux and more",
            "difficulty": 0.5,
            "estimated_hours": 48,
            "tags": ["intermediate", "hooks", "redux"]
        },
        {
            "title": "Official React Documentation",
            "url": "https://react.dev/",
            "type": "article",
            "platform": "React",
            "description": "Learn React from the official docs",
            "difficulty": 0.4,
            "estimated_hours": 15,
            "tags": ["beginner", "official", "reference"]
        },
    ],
    "machine learning": [
        {
            "title": "Machine Learning Specialization",
            "url": "https://www.coursera.org/specializations/machine-learning-introduction",
            "type": "course",
            "platform": "Coursera",
            "description": "Andrew Ng's famous ML course",
            "difficulty": 0.6,
            "estimated_hours": 60,
            "tags": ["intermediate", "andrew_ng", "comprehensive"]
        },
        {
            "title": "Hands-On Machine Learning with Scikit-Learn",
            "url": "https://github.com/ageron/handson-ml2",
            "type": "book",
            "platform": "GitHub",
            "description": "Practical ML with Python",
            "difficulty": 0.7,
            "estimated_hours": 40,
            "tags": ["intermediate", "practical", "python"]
        },
    ],
}


def calculate_learning_style_match(
    resource_type: str,
    learning_style: str
) -> float:
    """
    Calculate how well a resource type matches a learning style.
    
    Args:
        resource_type: Type of resource (video, course, article, etc.)
        learning_style: User's preferred learning style
        
    Returns:
        Match score from 0.0 to 1.0
    """
    # Learning style preferences
    style_preferences = {
        "visual": {
            "video": 1.0,
            "course": 0.8,
            "interactive": 0.9,
            "article": 0.5,
            "book": 0.4,
            "project": 0.7,
        },
        "kinesthetic": {
            "interactive": 1.0,
            "project": 0.95,
            "course": 0.7,
            "video": 0.6,
            "article": 0.4,
            "book": 0.3,
        },
        "auditory": {
            "video": 0.9,
            "course": 0.85,
            "podcast": 1.0,
            "interactive": 0.6,
            "article": 0.3,
            "book": 0.2,
        },
        "reading": {
            "book": 1.0,
            "article": 0.95,
            "course": 0.7,
            "interactive": 0.6,
            "video": 0.5,
            "project": 0.6,
        },
    }
    
    return style_preferences.get(learning_style, {}).get(resource_type, 0.5)


def calculate_relevance_score(
    resource: Dict[str, Any],
    query: str,
    level: str = "beginner"
) -> float:
    """
    Calculate relevance score based on query match and level.
    
    Args:
        resource: Resource dictionary
        query: Search query
        level: User's skill level
        
    Returns:
        Relevance score from 0.0 to 1.0
    """
    score = 0.0
    query_lower = query.lower()
    
    # Check title match
    title_lower = resource["title"].lower()
    if query_lower in title_lower:
        score += 0.4
    else:
        # Partial word matches
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        overlap = len(query_words & title_words)
        if overlap > 0:
            score += 0.2 * (overlap / len(query_words))
    
    # Check description match
    desc_lower = resource["description"].lower()
    if query_lower in desc_lower:
        score += 0.3
    
    # Check tags match
    tags = resource.get("tags", [])
    for tag in tags:
        if tag in query_lower or query_lower in tag:
            score += 0.1
    
    # Level match bonus
    if level in tags:
        score += 0.2
    
    return min(score, 1.0)


def course_search(
    query: str,
    learning_style: Optional[str] = None,
    level: str = "beginner",
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for learning resources based on query.
    
    This is a MOCK implementation. In production, this would:
    - Call Udemy API
    - Call Coursera API
    - Search YouTube API
    - Query web scraping service
    - Search GitHub for projects
    
    Args:
        query: Search query (e.g., "python data science")
        learning_style: Preferred learning style (visual, kinesthetic, etc.)
        level: Skill level (beginner, intermediate, advanced)
        max_results: Maximum number of results to return
        
    Returns:
        List of resource dictionaries with relevance scores
        
    Example:
        >>> resources = course_search("python", "visual", "beginner")
        >>> print(resources[0]['title'])
        'Python for Everybody Specialization'
    """
    logger.info(f"Searching for resources: query='{query}', style={learning_style}, level={level}")
    
    # Extract key topics from query
    query_lower = query.lower()
    relevant_resources = []
    
    # Search mock database
    for topic, resources in MOCK_RESOURCES.items():
        if topic in query_lower or any(word in topic for word in query_lower.split()):
            relevant_resources.extend(resources)
    
    # If no matches, return some generic resources
    if not relevant_resources:
        logger.warning(f"No resources found for query: {query}")
        # Return Python resources as default
        relevant_resources = MOCK_RESOURCES.get("python", [])
    
    # Calculate scores for each resource
    scored_resources = []
    for resource in relevant_resources:
        resource_copy = resource.copy()
        
        # Calculate relevance score
        relevance = calculate_relevance_score(resource, query, level)
        resource_copy["relevance_score"] = relevance
        
        # Calculate learning style match
        if learning_style:
            style_match = calculate_learning_style_match(
                resource["type"],
                learning_style
            )
            resource_copy["learning_style_match"] = style_match
        else:
            resource_copy["learning_style_match"] = 0.5
        
        # Combined score (weighted)
        resource_copy["combined_score"] = (
            0.7 * relevance + 0.3 * resource_copy["learning_style_match"]
        )
        
        scored_resources.append(resource_copy)
    
    # Sort by combined score
    scored_resources.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Return top results
    results = scored_resources[:max_results]
    
    logger.info(f"Found {len(results)} resources for query: {query}")
    for i, resource in enumerate(results[:3], 1):
        logger.debug(
            f"  {i}. {resource['title']} "
            f"(relevance={resource['relevance_score']:.2f}, "
            f"style_match={resource['learning_style_match']:.2f})"
        )
    
    return results


def search_by_platform(
    platform: str,
    query: str,
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for resources on a specific platform.
    
    Args:
        platform: Platform name (Udemy, Coursera, YouTube, etc.)
        query: Search query
        max_results: Maximum results
        
    Returns:
        List of resources from that platform
    """
    all_resources = course_search(query, max_results=100)
    
    platform_resources = [
        r for r in all_resources
        if r["platform"].lower() == platform.lower()
    ]
    
    return platform_resources[:max_results]


def filter_by_difficulty(
    resources: List[Dict[str, Any]],
    min_difficulty: float = 0.0,
    max_difficulty: float = 1.0
) -> List[Dict[str, Any]]:
    """
    Filter resources by difficulty range.
    
    Args:
        resources: List of resources
        min_difficulty: Minimum difficulty (0.0-1.0)
        max_difficulty: Maximum difficulty (0.0-1.0)
        
    Returns:
        Filtered resources
    """
    return [
        r for r in resources
        if min_difficulty <= r["difficulty"] <= max_difficulty
    ]


__all__ = [
    "course_search",
    "search_by_platform",
    "filter_by_difficulty",
    "calculate_learning_style_match",
    "calculate_relevance_score",
]