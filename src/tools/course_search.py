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
    "spanish": [
        {
            "title": "Spanish for Beginners - Duolingo",
            "url": "https://www.duolingo.com/course/es/en/Learn-Spanish",
            "type": "interactive",
            "platform": "Duolingo",
            "description": "Learn Spanish basics through interactive lessons",
            "difficulty": 0.2,
            "estimated_hours": 30,
            "tags": ["beginner", "interactive", "conversational"]
        },
        {
            "title": "Learn Spanish with SpanishDict",
            "url": "https://www.spanishdict.com/guide",
            "type": "article",
            "platform": "SpanishDict",
            "description": "Free Spanish lessons and grammar guides",
            "difficulty": 0.25,
            "estimated_hours": 20,
            "tags": ["beginner", "grammar", "reference"]
        },
        {
            "title": "Rosetta Stone - Spanish",
            "url": "https://www.rosettastone.com/languages/spanish/",
            "type": "course",
            "platform": "Rosetta Stone",
            "description": "Immersive Spanish language learning program",
            "difficulty": 0.3,
            "estimated_hours": 60,
            "tags": ["beginner", "immersive", "comprehensive"]
        },
        {
            "title": "Easy Spanish YouTube Channel",
            "url": "https://www.youtube.com/c/EasySpanish",
            "type": "video",
            "platform": "YouTube",
            "description": "Real-world Spanish conversations with subtitles",
            "difficulty": 0.35,
            "estimated_hours": 25,
            "tags": ["beginner", "conversational", "videos"]
        },
        {
            "title": "Spanish Grammar in Context",
            "url": "https://www.spanishdict.com/guide/spanish-grammar",
            "type": "book",
            "platform": "SpanishDict",
            "description": "Comprehensive Spanish grammar reference",
            "difficulty": 0.4,
            "estimated_hours": 35,
            "tags": ["intermediate", "grammar", "reference"]
        },
        {
            "title": "Babbel Spanish Course",
            "url": "https://www.babbel.com/en/language/learn-spanish",
            "type": "course",
            "platform": "Babbel",
            "description": "Interactive Spanish lessons with real-world scenarios",
            "difficulty": 0.35,
            "estimated_hours": 40,
            "tags": ["beginner", "interactive", "practical"]
        },
    ],
    "language": [
        {
            "title": "Busuu Language Learning",
            "url": "https://www.busuu.com/",
            "type": "course",
            "platform": "Busuu",
            "description": "Learn any language with interactive lessons",
            "difficulty": 0.3,
            "estimated_hours": 45,
            "tags": ["beginner", "interactive", "multilingual"]
        },
        {
            "title": "Language Learning Strategies Guide",
            "url": "https://blog.linguashop.com/2020/08/how-to-learn-language.html",
            "type": "article",
            "platform": "Web",
            "description": "Proven strategies for effective language learning",
            "difficulty": 0.2,
            "estimated_hours": 5,
            "tags": ["beginner", "tips", "strategies"]
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
    logger.info("="*80)
    logger.info("[RESOURCE FETCH START] Initiating internet resource search")
    logger.info(f"[RESOURCE FETCH] Query: '{query}'")
    logger.info(f"[RESOURCE FETCH] Learning Style: {learning_style}")
    logger.info(f"[RESOURCE FETCH] Level: {level}")
    logger.info(f"[RESOURCE FETCH] Max Results: {max_results}")
    logger.info("="*80)
    
    # In production, these would be actual API calls
    logger.info("[RESOURCE FETCH] NOTE: Using mock data - In production would query:")
    logger.info("[RESOURCE FETCH]   - Udemy API (udemy.com/api-2.0/courses)")
    logger.info("[RESOURCE FETCH]   - Coursera API (coursera.org/api/courses)")
    logger.info("[RESOURCE FETCH]   - YouTube Data API (youtube.googleapis.com/youtube/v3)")
    logger.info("[RESOURCE FETCH]   - GitHub API (api.github.com/search/repositories)")
    logger.info("[RESOURCE FETCH]   - Web scraping services for free resources")
    
    # Extract key topics from query
    query_lower = query.lower()
    relevant_resources = []
    matched_topics = []
    
    logger.info(f"[RESOURCE FETCH] Analyzing query: '{query_lower}'")
    
    # Enhanced topic-to-keyword mapping for better matching
    topic_keywords = {
        "spanish": ["spanish", "spain", "español", "castellano", "hispanic", "learn spanish", "spanish language"],
        "python": ["python", "py", "programming", "code", "coding", "script", "scripting"],
        "javascript": ["javascript", "js", "web development", "frontend", "backend", "node", "web dev"],
        "react": ["react", "reactjs", "react.js", "jsx", "frontend framework"],
        "machine learning": ["machine learning", "ml", "deep learning", "ai", "artificial intelligence", "neural", "model", "data science"],
        "language": ["language", "learn language", "fluent", "fluency", "bilingual", "multilingual", "vocabulary", "grammar"],
    }
    
    logger.info(f"[RESOURCE FETCH] Available topic categories: {list(topic_keywords.keys())}")
    
    # Search mock database with improved fuzzy keyword matching
    logger.info("[RESOURCE FETCH] Starting topic matching process...")
    
    for topic, resources in MOCK_RESOURCES.items():
        topic_matched = False
        match_method = None
        
        # Direct topic match
        if topic in query_lower:
            if topic not in matched_topics:
                matched_topics.append(topic)
            relevant_resources.extend(resources)
            topic_matched = True
            match_method = "direct_match"
            logger.info(f"[RESOURCE FETCH] ✓ Direct match found: '{topic}' ({len(resources)} resources)")
            continue
        
        # Check topic keywords for this category
        if topic in topic_keywords:
            for keyword in topic_keywords[topic]:
                if keyword in query_lower or query_lower in keyword:
                    if topic not in matched_topics:
                        matched_topics.append(topic)
                    relevant_resources.extend(resources)
                    topic_matched = True
                    match_method = f"keyword_match: '{keyword}'"
                    logger.info(f"[RESOURCE FETCH] ✓ Keyword match found: '{topic}' via keyword '{keyword}' ({len(resources)} resources)")
                    break
        
        # If not matched yet, check word-by-word similarity
        if not topic_matched:
            query_words = set(query_lower.split())
            topic_words = set(topic.split())
            
            # Check for word overlap
            overlap = query_words & topic_words
            if overlap:
                if topic not in matched_topics:
                    matched_topics.append(topic)
                relevant_resources.extend(resources)
                topic_matched = True
                match_method = f"word_overlap: {overlap}"
                logger.info(f"[RESOURCE FETCH] ✓ Word overlap match: '{topic}' with words {overlap} ({len(resources)} resources)")
    
    # Remove duplicates while preserving order
    logger.info(f"[RESOURCE FETCH] Removing duplicates from {len(relevant_resources)} resources...")
    seen = set()
    unique_resources = []
    for resource in relevant_resources:
        resource_id = (resource.get('title'), resource.get('url'))
        if resource_id not in seen:
            seen.add(resource_id)
            unique_resources.append(resource)
    
    relevant_resources = unique_resources
    logger.info(f"[RESOURCE FETCH] After deduplication: {len(relevant_resources)} unique resources")
    
    # Enhanced fallback matching with better logic
    if not relevant_resources:
        logger.warning("="*80)
        logger.warning(f"[RESOURCE FETCH] ⚠ No direct match found for query: '{query}'")
        logger.warning(f"[RESOURCE FETCH] Initiating intelligent fallback matching...")
        logger.warning("="*80)
        
        # Language learning detection
        language_keywords = ["spanish", "french", "german", "italian", "chinese", "japanese", "language", "fluent", "vocabulary", "grammar", "conversation", "speak", "speaking"]
        detected_language_keywords = [word for word in language_keywords if word in query_lower]
        
        if detected_language_keywords:
            logger.info(f"[RESOURCE FETCH] 🌐 Detected language learning goal via keywords: {detected_language_keywords}")
            logger.info(f"[RESOURCE FETCH] Fetching language-specific resources...")
            
            if any(word in query_lower for word in ["spanish", "español"]):
                spanish_resources = MOCK_RESOURCES.get("spanish", [])
                relevant_resources.extend(spanish_resources)
                matched_topics.append("spanish")
                logger.info(f"[RESOURCE FETCH]   → Added {len(spanish_resources)} Spanish resources")
            
            language_resources = MOCK_RESOURCES.get("language", [])
            relevant_resources.extend(language_resources)
            matched_topics.append("language")
            logger.info(f"[RESOURCE FETCH]   → Added {len(language_resources)} general language resources")
        
        # Data science / ML detection
        elif any(word in query_lower for word in ["data", "ai", "artificial", "machine", "neural", "model", "deep learning", "ml", "prediction", "classification"]):
            detected_ml_keywords = [word for word in ["data", "ai", "artificial", "machine", "neural", "model", "deep learning", "ml"] if word in query_lower]
            logger.info(f"[RESOURCE FETCH] 🤖 Detected ML/AI goal via keywords: {detected_ml_keywords}")
            ml_resources = MOCK_RESOURCES.get("machine learning", [])
            relevant_resources.extend(ml_resources)
            matched_topics.append("machine learning")
            logger.info(f"[RESOURCE FETCH]   → Added {len(ml_resources)} ML/AI resources")
        
        # Web development detection
        elif any(word in query_lower for word in ["web", "website", "frontend", "backend", "react", "javascript", "html", "css", "browser"]):
            detected_web_keywords = [word for word in ["web", "website", "frontend", "backend", "react", "javascript", "html", "css"] if word in query_lower]
            logger.info(f"[RESOURCE FETCH] 🌐 Detected web development goal via keywords: {detected_web_keywords}")
            
            if "react" in query_lower:
                react_resources = MOCK_RESOURCES.get("react", [])
                relevant_resources.extend(react_resources)
                matched_topics.append("react")
                logger.info(f"[RESOURCE FETCH]   → Added {len(react_resources)} React resources")
            
            if any(word in query_lower for word in ["javascript", "js", "web"]):
                js_resources = MOCK_RESOURCES.get("javascript", [])
                relevant_resources.extend(js_resources)
                matched_topics.append("javascript")
                logger.info(f"[RESOURCE FETCH]   → Added {len(js_resources)} JavaScript resources")
        
        # General programming - only if nothing else matched
        elif any(word in query_lower for word in ["programming", "code", "coding", "software", "developer", "program"]):
            detected_prog_keywords = [word for word in ["programming", "code", "coding", "software", "developer"] if word in query_lower]
            logger.info(f"[RESOURCE FETCH] 💻 Detected general programming goal via keywords: {detected_prog_keywords}")
            logger.info(f"[RESOURCE FETCH] Defaulting to Python resources as the most beginner-friendly option")
            python_resources = MOCK_RESOURCES.get("python", [])
            relevant_resources.extend(python_resources)
            matched_topics.append("python")
            logger.info(f"[RESOURCE FETCH]   → Added {len(python_resources)} Python resources")
        
        # Last resort: return nothing rather than incorrect resources
        else:
            logger.error("="*80)
            logger.error(f"[RESOURCE FETCH] ❌ Could not match query '{query}' to any topic category")
            logger.error(f"[RESOURCE FETCH] Query words: {query_lower.split()}")
            logger.error(f"[RESOURCE FETCH] Available categories: {list(MOCK_RESOURCES.keys())}")
            logger.error(f"[RESOURCE FETCH] Returning empty results to avoid incorrect recommendations")
            logger.error("="*80)
            # Don't return any resources if we can't match properly
            relevant_resources = []
    
    if matched_topics:
        logger.info("="*80)
        logger.info(f"[RESOURCE FETCH] ✓ Successfully matched topics: {matched_topics}")
        logger.info(f"[RESOURCE FETCH] Total resources found: {len(relevant_resources)}")
        logger.info("="*80)
    
    # Calculate scores for each resource
    logger.info("[RESOURCE FETCH] Calculating relevance and learning style scores...")
    scored_resources = []
    
    for i, resource in enumerate(relevant_resources, 1):
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
        
        # Combined score (weighted: 70% relevance, 30% learning style)
        resource_copy["combined_score"] = (
            0.7 * relevance + 0.3 * resource_copy["learning_style_match"]
        )
        
        logger.debug(
            f"[RESOURCE FETCH] Resource {i}: '{resource['title'][:50]}...' | "
            f"Relevance: {relevance:.2f}, Style Match: {resource_copy['learning_style_match']:.2f}, "
            f"Combined: {resource_copy['combined_score']:.2f}"
        )
        
        scored_resources.append(resource_copy)
    
    # Sort by combined score
    logger.info("[RESOURCE FETCH] Ranking resources by combined score...")
    scored_resources.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Return top results
    results = scored_resources[:max_results]
    
    logger.info("="*80)
    logger.info(f"[RESOURCE FETCH] ✓ FINAL RESULTS: {len(results)} resources selected (from {len(scored_resources)} candidates)")
    logger.info("="*80)
    
    # Log detailed information about top resources
    for i, resource in enumerate(results, 1):
        logger.info(f"[RESOURCE FETCH] #{i} - {resource['title']}")
        logger.info(f"         URL: {resource.get('url', 'N/A')}")
        logger.info(f"         Type: {resource.get('type', 'unknown')} | Platform: {resource.get('platform', 'N/A')}")
        logger.info(f"         Difficulty: {resource.get('difficulty', 0):.1f} | Est. Hours: {resource.get('estimated_hours', 'N/A')}")
        logger.info(f"         Relevance: {resource['relevance_score']:.2f} | Style Match: {resource['learning_style_match']:.2f} | Combined: {resource['combined_score']:.2f}")
        logger.info(f"         Description: {resource.get('description', 'N/A')[:80]}")
        logger.info("-" * 80)
    
    logger.info("="*80)
    logger.info("[RESOURCE FETCH END] Resource fetching complete")
    logger.info("="*80)
    
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
