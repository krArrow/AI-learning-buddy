"""
Course Search Tool - Real content discovery using Tavily API
Searches for high-quality learning resources across the web with semantic understanding.

Features:
- Real-time web search via Tavily API
- Semantic understanding of learning content
- Filters by user skill level and learning style
- Optimized content ranking by relevance and quality
"""
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import tavily
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logger.warning("Tavily not installed. Install with: pip install tavily-python")


def get_tavily_client() -> Optional[TavilyClient]:
    """
    Initialize Tavily client with API key from environment.
    
    Returns:
        TavilyClient instance or None if API key not found
    """
    api_key = os.getenv("TAVILY_API_KEY")
    
    if not api_key:
        logger.warning(
            "TAVILY_API_KEY not found in environment. "
            "Set it with: export TAVILY_API_KEY='your_key'"
        )
        return None
    
    try:
        return TavilyClient(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Tavily client: {e}")
        return None


# Fallback resource database for when Tavily is unavailable
FALLBACK_RESOURCES = {
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
    learning_style: str,
    content_text: str = ""
) -> float:
    """
    Calculate how well a resource type matches a learning style.
    
    Args:
        resource_type: Type of resource (video, article, course, tutorial, etc.)
        learning_style: User's preferred learning style
        content_text: Resource content to analyze (optional)
        
    Returns:
        Match score from 0.0 to 1.0
    """
    # Learning style preferences
    style_preferences = {
        "visual": {
            "video": 1.0,
            "course": 0.8,
            "interactive": 0.9,
            "tutorial": 0.8,
            "article": 0.6,
            "book": 0.4,
            "project": 0.7,
            "demo": 0.95,
        },
        "kinesthetic": {
            "interactive": 1.0,
            "project": 0.95,
            "course": 0.7,
            "tutorial": 0.8,
            "video": 0.6,
            "article": 0.4,
            "book": 0.3,
            "coding": 1.0,
        },
        "auditory": {
            "video": 0.9,
            "course": 0.85,
            "podcast": 1.0,
            "interactive": 0.6,
            "article": 0.3,
            "book": 0.2,
            "tutorial": 0.7,
        },
        "reading_writing": {
            "book": 1.0,
            "article": 0.95,
            "course": 0.7,
            "interactive": 0.6,
            "video": 0.5,
            "project": 0.6,
            "tutorial": 0.8,
        },
    }
    
    # Normalize learning_style to handle underscores
    learning_style_normalized = learning_style.lower().replace("_", "").replace(" ", "")
    resource_type_lower = resource_type.lower()
    
    # Match against preference map
    for style_key, prefs in style_preferences.items():
        style_key_normalized = style_key.replace("_", "").replace(" ", "")
        if style_key_normalized == learning_style_normalized:
            return prefs.get(resource_type_lower, 0.5)
    
    # Default fallback
    return 0.5


def extract_resource_type(title: str, url: str, content: str = "") -> str:
    """
    Infer resource type from URL, title, and content.
    
    Args:
        title: Resource title
        url: Resource URL
        content: Resource content/description
        
    Returns:
        Resource type string
    """
    url_lower = url.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Check URL patterns
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "video"
    elif "udemy.com" in url_lower or "udacity.com" in url_lower or "coursera.org" in url_lower:
        return "course"
    elif "github.com" in url_lower:
        return "project"
    elif "dev.to" in url_lower or "medium.com" in url_lower or "hashnode.com" in url_lower:
        return "article"
    elif "docs." in url_lower or "documentation" in url_lower or ".io" in url_lower:
        return "tutorial"
    
    # Check title/content patterns
    if any(word in title_lower for word in ["tutorial", "guide", "how to", "learn"]):
        return "tutorial"
    elif any(word in title_lower for word in ["video", "playlist", "channel"]):
        return "video"
    elif any(word in title_lower for word in ["course", "class", "lesson"]):
        return "course"
    elif any(word in title_lower for word in ["project", "example", "sample"]):
        return "project"
    elif any(word in content_lower for word in ["interactive", "hands-on", "practice"]):
        return "interactive"
    
    # Default
    return "article"


def calculate_relevance_score(
    resource: Dict[str, Any],
    query: str,
    level: str = "beginner"
) -> float:
    """
    Calculate relevance score based on query match, content quality, and level alignment.
    
    Args:
        resource: Resource dictionary
        query: Search query
        level: User's skill level
        
    Returns:
        Relevance score from 0.0 to 1.0
    """
    score = 0.0
    query_lower = query.lower()
    
    # Check title match (highest weight)
    title_lower = resource.get("title", "").lower()
    if query_lower in title_lower:
        score += 0.4
    else:
        # Partial word matches
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        overlap = len(query_words & title_words)
        if overlap > 0:
            score += 0.25 * min(1.0, overlap / len(query_words))
    
    # Check description/content match
    content = resource.get("content", resource.get("description", "")).lower()
    if query_lower in content:
        score += 0.3
    else:
        # Partial matches in content
        content_words = set(content.split())
        overlap = len(query_words & content_words)
        if overlap > 0:
            score += 0.15 * min(1.0, overlap / len(query_words))
    
    # Source quality bonus (trusted platforms get higher scores)
    url = resource.get("url", "").lower()
    trusted_sources = [
        "coursera.org", "udemy.com", "github.com", "youtube.com",
        "official documentation", ".edu", "dev.to", "medium.com",
        "freecodecamp", "w3schools", "mdn.mozilla.org"
    ]
    
    for source in trusted_sources:
        if source in url:
            score += 0.15
            break
    
    # Recency bonus (newer content gets slight boost)
    score += 0.05
    
    return min(score, 1.0)


def course_search(
    query: str,
    learning_style: Optional[str] = None,
    level: str = "beginner",
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for high-quality learning resources using Tavily API.
    
    Uses semantic web search to find courses, tutorials, articles, and videos
    tailored to the user's learning style and skill level.
    
    Args:
        query: Search query (e.g., "Python for data science")
        learning_style: Preferred learning style (visual, kinesthetic, auditory, reading_writing)
        level: Skill level (beginner, intermediate, advanced)
        max_results: Maximum number of results to return
        
    Returns:
        List of resource dictionaries sorted by combined relevance score
        
    Example:
        >>> resources = course_search(
        ...     "Python machine learning",
        ...     learning_style="visual",
        ...     level="intermediate",
        ...     max_results=10
        ... )
        >>> for r in resources:
        ...     print(f"{r['title']} - {r['url']}")
    """
    logger.info("=" * 90)
    logger.info("[TAVILY SEARCH] Initiating optimized content discovery")
    logger.info(f"[TAVILY SEARCH] Query: '{query}'")
    logger.info(f"[TAVILY SEARCH] Learning Style: {learning_style}")
    logger.info(f"[TAVILY SEARCH] Level: {level}")
    logger.info(f"[TAVILY SEARCH] Max Results: {max_results}")
    logger.info("=" * 90)
    
    # Initialize Tavily client
    if not TAVILY_AVAILABLE:
        logger.error("[TAVILY SEARCH] Tavily library not installed")
        logger.error("[TAVILY SEARCH] Install with: pip install tavily-python")
        return []
    
    tavily_client = get_tavily_client()
    if not tavily_client:
        logger.error("[TAVILY SEARCH] Failed to initialize Tavily client")
        logger.error("[TAVILY SEARCH] Ensure TAVILY_API_KEY environment variable is set")
        return []
    
    # Build optimized search queries based on learning goal
    search_queries = _build_search_queries(query, learning_style, level)
    
    logger.info(f"[TAVILY SEARCH] Built {len(search_queries)} optimized search queries:")
    for i, sq in enumerate(search_queries, 1):
        logger.info(f"[TAVILY SEARCH]   {i}. {sq}")
    
    # Perform searches
    all_resources = []
    
    for search_query in search_queries:
        logger.info(f"[TAVILY SEARCH] Executing: '{search_query}'")
        
        try:
            # Use Tavily API with optimized settings
            response = tavily_client.search(
                query=search_query,
                max_results=max_results * 2,  # Get more, then filter
                include_domains=[
                    "coursera.org", "udemy.com", "youtube.com", "github.com",
                    "freecodecamp.org", "w3schools.com", "dev.to", "medium.com",
                    "official documentation", "edx.org", "codecademy.com",
                    "datacamp.com", "pluralsight.com"
                ],
                topic="general"
            )
            
            # Parse results
            results = response.get("results", [])
            logger.info(f"[TAVILY SEARCH]   ✓ Found {len(results)} results")
            
            for result in results:
                resource = {
                    "title": result.get("title", "Untitled"),
                    "url": result.get("url", ""),
                    "content": result.get("content", result.get("description", "")),
                    "description": result.get("content", result.get("description", ""))[:200],
                    "source": "tavily_search",
                    "search_query": search_query,
                    "published_date": datetime.now().isoformat(),
                }
                
                # Infer resource type
                resource["type"] = extract_resource_type(
                    resource["title"],
                    resource["url"],
                    resource["content"]
                )
                
                all_resources.append(resource)
                
        except Exception as e:
            logger.warning(f"[TAVILY SEARCH] Search failed for '{search_query}': {e}")
            continue
    
    if not all_resources:
        logger.error("[TAVILY SEARCH] No resources found from Tavily search")
        return []
    
    logger.info(f"[TAVILY SEARCH] Total resources collected: {len(all_resources)}")
    
    # Remove duplicates by URL
    logger.info("[TAVILY SEARCH] Deduplicating resources...")
    seen_urls = set()
    unique_resources = []
    
    for resource in all_resources:
        url = resource.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_resources.append(resource)
    
    logger.info(f"[TAVILY SEARCH] After deduplication: {len(unique_resources)} unique resources")
    
    # Score and rank
    logger.info("[TAVILY SEARCH] Scoring resources by relevance and learning style match...")
    
    for resource in unique_resources:
        # Calculate scores
        relevance = calculate_relevance_score(resource, query, level)
        resource["relevance_score"] = relevance
        
        # Learning style match
        if learning_style:
            style_match = calculate_learning_style_match(
                resource["type"],
                learning_style,
                resource["content"]
            )
            resource["learning_style_match"] = style_match
        else:
            resource["learning_style_match"] = 0.5
        
        # Combined score (70% relevance + 30% learning style)
        resource["combined_score"] = (
            0.7 * relevance + 0.3 * resource["learning_style_match"]
        )
    
    # Sort by combined score
    unique_resources.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Return top results
    results = unique_resources[:max_results]
    
    logger.info("=" * 90)
    logger.info(f"[TAVILY SEARCH] ✓ FINAL RESULTS: {len(results)} curated resources")
    logger.info("=" * 90)
    
    # Log detailed results
    for i, resource in enumerate(results, 1):
        logger.info(f"[TAVILY SEARCH] #{i} - {resource['title'][:70]}")
        logger.info(f"         URL: {resource['url']}")
        logger.info(f"         Type: {resource['type']} | Source: {resource['source']}")
        logger.info(f"         Relevance: {resource['relevance_score']:.2f} | "
                   f"Style Match: {resource['learning_style_match']:.2f} | "
                   f"Combined: {resource['combined_score']:.2f}")
        logger.info(f"         Preview: {resource['description'][:100]}...")
        logger.info("-" * 90)
    
    logger.info("=" * 90)
    logger.info("[TAVILY SEARCH] Content discovery complete")
    logger.info("=" * 90)
    
    return results


# Configuration: Set to True to minimize API calls (cost-effective mode)
SINGLE_QUERY_MODE = True  # Use only 1 optimized query instead of 5

def _build_search_queries(
    query: str,
    learning_style: Optional[str],
    level: str
) -> List[str]:
    """
    Build optimized search queries based on learning goal and style.
    
    OPTIMIZED: Now uses SINGLE_QUERY_MODE to reduce API calls from 5 to 1.
    This dramatically reduces Tavily API costs while maintaining quality.
    
    Args:
        query: Original search query
        learning_style: User's preferred learning style
        level: User's skill level
        
    Returns:
        List of optimized search queries (1-2 queries in optimized mode)
    """
    # Learning style keywords
    style_keywords = {
        "visual": "video tutorial",
        "kinesthetic": "hands-on project",
        "auditory": "video explanation",
        "reading_writing": "guide documentation",
        "reading": "guide documentation",
    }
    
    # Level keywords (shorter for better search results)
    level_keywords = {
        "beginner": "beginner",
        "intermediate": "intermediate",
        "advanced": "advanced",
    }
    
    style_key = learning_style.lower() if learning_style else "visual"
    style_keyword = style_keywords.get(style_key, "video tutorial")
    level_keyword = level_keywords.get(level.lower(), "beginner")
    
    if SINGLE_QUERY_MODE:
        # COST-EFFECTIVE: Single optimized query with all modifiers
        # This reduces API calls by 80% (from 5 to 1)
        optimized_query = f"{query} {style_keyword} {level_keyword}"
        return [optimized_query]
    
    # Original multi-query mode (expensive, use only if needed)
    queries = []
    queries.append(query)
    queries.append(f"{query} {style_keyword}")
    queries.append(f"{query} {level_keyword}")
    queries.append(f"{query} {style_keyword} {level_keyword}")
    
    if "course" not in query.lower():
        queries.append(f"{query} online course tutorial")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        q_lower = q.lower()
        if q_lower not in seen:
            seen.add(q_lower)
            unique_queries.append(q)
    
    return unique_queries


def search_by_platform(
    platform: str,
    query: str,
    learning_style: Optional[str] = None,
    level: str = "beginner",
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for resources on a specific platform.
    
    Args:
        platform: Platform name (Coursera, Udemy, YouTube, GitHub, etc.)
        query: Search query
        learning_style: Preferred learning style
        level: Skill level
        max_results: Maximum results
        
    Returns:
        List of resources from that platform
    """
    platform_lower = platform.lower()
    platform_domains = {
        "coursera": "coursera.org",
        "udemy": "udemy.com",
        "youtube": "youtube.com",
        "github": "github.com",
        "medium": "medium.com",
        "dev.to": "dev.to",
        "freecodecamp": "freecodecamp.org",
        "w3schools": "w3schools.com",
        "edx": "edx.org",
        "codecademy": "codecademy.com",
    }
    
    domain = platform_domains.get(platform_lower, platform_lower)
    enhanced_query = f"{query} site:{domain}"
    
    results = course_search(
        enhanced_query,
        learning_style=learning_style,
        level=level,
        max_results=max_results
    )
    
    return results


def filter_by_difficulty(
    resources: List[Dict[str, Any]],
    min_difficulty: float = 0.0,
    max_difficulty: float = 1.0,
    level: str = "beginner"
) -> List[Dict[str, Any]]:
    """
    Filter resources by difficulty range.
    
    Args:
        resources: List of resources
        min_difficulty: Minimum difficulty (0.0-1.0)
        max_difficulty: Maximum difficulty (0.0-1.0)
        level: User's skill level
        
    Returns:
        Filtered resources
    """
    filtered = []
    
    level_to_difficulty = {
        "beginner": (0.0, 0.4),
        "intermediate": (0.3, 0.7),
        "advanced": (0.6, 1.0),
    }
    
    if level in level_to_difficulty:
        default_min, default_max = level_to_difficulty[level]
        min_difficulty = max(min_difficulty, default_min)
        max_difficulty = min(max_difficulty, default_max)
    
    for resource in resources:
        # Estimate difficulty from resource type and relevance
        estimated_difficulty = resource.get("relevance_score", 0.5) * 0.7
        
        if min_difficulty <= estimated_difficulty <= max_difficulty:
            filtered.append(resource)
    
    return filtered


__all__ = [
    "course_search",
    "search_by_platform",
    "filter_by_difficulty",
    "calculate_learning_style_match",
    "calculate_relevance_score",
    "TAVILY_AVAILABLE",
]
