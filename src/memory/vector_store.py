"""
Vector Store - RAG Integration

ChromaDB-based vector store for learning resources.
- Embed and store learning resources
- Semantic search for relevant materials
- Filter by learning style and difficulty
- Track resource usage and relevance scores
- Singleton pattern for single instance

Author: AI Learning Platform Team
"""

import logging
import os
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger_init = logging.getLogger(__name__)
    logger_init.warning("ChromaDB not installed. Vector store will be limited.")

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class VectorStore:
    """
    Vector-based storage and retrieval for learning resources using ChromaDB.
    
    Features:
    - Embed and store learning resources (videos, articles, courses)
    - Semantic search by topic and learning style
    - Persistent storage to disk
    - Relevance scoring and tracking
    - Singleton pattern
    
    Example:
        >>> vector_store = VectorStore()
        >>> resources = [
        ...     {
        ...         "title": "Python Basics",
        ...         "description": "Learn Python fundamentals",
        ...         "url": "https://...",
        ...         "type": "video",
        ...         "learning_style": "visual"
        ...     }
        ... ]
        >>> vector_store.add_resources(resources)
        >>> results = vector_store.search("python basics", k=5)
    """
    
    def __init__(
        self,
        persist_dir: str = "data/chroma",
        collection_name: str = "learning_resources"
    ):
        """
        Initialize vector store with ChromaDB.
        
        Args:
            persist_dir: Directory to persist vector store data
            collection_name: Name of ChromaDB collection
            
        Raises:
            ImportError: If ChromaDB is not installed
        """
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "ChromaDB is required for vector store. "
                "Install with: pip install chromadb"
            )
        
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.logger = logger
        
        # Create persist directory if needed
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=persist_dir)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Cosine similarity
            )
            
            self.logger.info(
                f"VectorStore initialized at {persist_dir} "
                f"with collection '{collection_name}'"
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise
    
    def add_resources(self, resources: List[Dict[str, Any]]) -> bool:
        """
        Embed and add resources to the vector store.
        
        Each resource is embedded using the document text
        (title + description) and stored with metadata.
        
        Args:
            resources: List of resource dictionaries with:
            [{
                "id": str (optional, auto-generated if not provided),
                "title": str (required),
                "description": str (optional),
                "url": str (required),
                "type": str ("video", "article", "course", "tutorial"),
                "platform": str ("YouTube", "Udemy", "Coursera", etc.),
                "difficulty": int (1-5, optional),
                "learning_style": str ("visual", "kinesthetic", "auditory", "reading"),
                "tags": list (optional, ["python", "beginner"])
            }, ...]
        
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> resources = [
            ...     {
            ...         "title": "Python for Beginners",
            ...         "description": "Learn Python from scratch",
            ...         "url": "https://youtube.com/...",
            ...         "type": "video",
            ...         "learning_style": "visual"
            ...     }
            ... ]
            >>> success = vector_store.add_resources(resources)
        """
        try:
            if not resources:
                self.logger.warning("No resources to add")
                return False
            
            # Prepare documents, embeddings, metadatas, and IDs
            documents = []
            metadatas = []
            ids = []
            
            for i, resource in enumerate(resources):
                # Validate required fields
                if "title" not in resource or "url" not in resource:
                    self.logger.warning(f"Skipping resource {i}: missing title or url")
                    continue
                
                # Create document text for embedding
                title = resource.get("title", "")
                description = resource.get("description", "")
                document_text = f"{title} {description}".strip()
                
                # Generate ID if not provided
                resource_id = resource.get("id") or f"resource_{i}_{hash(title) % 10000}"
                
                # Extract metadata
                metadata = {
                    "title": title,
                    "url": resource.get("url", ""),
                    "type": resource.get("type", "unknown"),
                    "platform": resource.get("platform", "unknown"),
                    "learning_style": resource.get("learning_style", "general"),
                    "difficulty": str(resource.get("difficulty", 3)),  # ChromaDB requires strings
                }
                
                # Add optional tags
                if "tags" in resource:
                    metadata["tags"] = ",".join(resource["tags"])
                
                documents.append(document_text)
                metadatas.append(metadata)
                ids.append(resource_id)
            
            if not documents:
                self.logger.warning("No valid resources to add after filtering")
                return False
            
            # Add to ChromaDB collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Added {len(documents)} resources to vector store")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding resources to vector store: {str(e)}")
            return False
    
    def search(
        self,
        query: str,
        k: int = 10,
        learning_style: Optional[str] = None,
        resource_type: Optional[str] = None,
        min_relevance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant resources using semantic similarity.
        
        Finds resources most similar to the query, optionally filtered
        by learning style and resource type.
        
        Args:
            query: Search query (e.g., "Python for data analysis")
            k: Number of results to return (default: 10)
            learning_style: Optional filter by style
            resource_type: Optional filter by type (video, article, etc.)
            min_relevance: Minimum relevance score (0.0-1.0)
        
        Returns:
            List of matching resources sorted by relevance:
            [{
                "id": str,
                "title": str,
                "description": str,
                "url": str,
                "type": str,
                "platform": str,
                "learning_style": str,
                "relevance_score": 0.92,
                "distance": 0.08
            }, ...]
        
        Example:
            >>> results = vector_store.search(
            ...     "Python basics",
            ...     k=5,
            ...     learning_style="visual"
            ... )
            >>> for r in results:
            ...     print(f"{r['title']}: {r['relevance_score']}")
        """
        try:
            if not query or not isinstance(query, str):
                raise ValueError(f"Invalid query: {query}")
            
            if k < 1:
                raise ValueError(f"k must be >= 1, got {k}")
            
            if not (0.0 <= min_relevance <= 1.0):
                raise ValueError(f"min_relevance must be 0-1, got {min_relevance}")
            
            self.logger.debug(f"Searching for: '{query}' (k={k}, style={learning_style})")
            
            # Build where filter if needed
            where_filter = None
            if learning_style or resource_type:
                where_filter = {}
                if learning_style:
                    where_filter["learning_style"] = {"$eq": learning_style}
                if resource_type:
                    if where_filter:
                        # Combine filters with AND
                        where_filter = {
                            "$and": [
                                where_filter,
                                {"type": {"$eq": resource_type}}
                            ]
                        }
                    else:
                        where_filter = {"type": {"$eq": resource_type}}
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where_filter
            )
            
            if not results or not results.get("ids") or not results["ids"][0]:
                self.logger.info(f"No results found for query: '{query}'")
                return []
            
            # Format results
            formatted_results = []
            
            for i, resource_id in enumerate(results["ids"][0]):
                # Get metadata and distance
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                distance = results["distances"][0][i] if results.get("distances") else 1.0
                
                # Convert distance to relevance score (cosine distance)
                # Distance 0 = perfect match (relevance 1.0)
                # Distance 2 = no match (relevance 0.0)
                relevance_score = max(0, 1 - (distance / 2))
                
                # Filter by minimum relevance
                if relevance_score < min_relevance:
                    continue
                
                # Build result dictionary
                result = {
                    "id": resource_id,
                    "title": metadata.get("title", "Unknown"),
                    "url": metadata.get("url", ""),
                    "type": metadata.get("type", "unknown"),
                    "platform": metadata.get("platform", "unknown"),
                    "learning_style": metadata.get("learning_style", "general"),
                    "difficulty": int(metadata.get("difficulty", 3)),
                    "relevance_score": round(relevance_score, 3),
                    "distance": round(distance, 3),
                }
                
                # Add tags if present
                if "tags" in metadata and metadata["tags"]:
                    result["tags"] = metadata["tags"].split(",")
                
                formatted_results.append(result)
            
            self.logger.info(f"Found {len(formatted_results)} results for query: '{query}'")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def search_by_topic_and_style(
        self,
        topic: str,
        learning_style: str,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for resources by topic and learning style.
        
        Convenience method for filtering by style while searching topic.
        
        Args:
            topic: Learning topic (e.g., "Python basics")
            learning_style: Preferred style (visual, kinesthetic, auditory, reading)
            k: Number of results
        
        Returns:
            Filtered list of resources
            
        Example:
            >>> results = vector_store.search_by_topic_and_style(
            ...     topic="Python",
            ...     learning_style="visual",
            ...     k=5
            ... )
        """
        return self.search(
            query=topic,
            k=k,
            learning_style=learning_style
        )
    
    def get_resource_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific resource by ID.
        
        Args:
            resource_id: Resource identifier
        
        Returns:
            Resource dictionary or None if not found
        """
        try:
            result = self.collection.get(ids=[resource_id])
            
            if not result or not result.get("ids"):
                self.logger.warning(f"Resource not found: {resource_id}")
                return None
            
            metadata = result["metadatas"][0] if result.get("metadatas") else {}
            
            return {
                "id": resource_id,
                "title": metadata.get("title", "Unknown"),
                "url": metadata.get("url", ""),
                "type": metadata.get("type", "unknown"),
                "platform": metadata.get("platform", "unknown"),
                "learning_style": metadata.get("learning_style", "general"),
                "difficulty": int(metadata.get("difficulty", 3))
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving resource {resource_id}: {str(e)}")
            return None
    
    def delete_resource(self, resource_id: str) -> bool:
        """
        Delete a resource from the vector store.
        
        Args:
            resource_id: Resource identifier
        
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[resource_id])
            self.logger.info(f"Deleted resource: {resource_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting resource: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.
        
        Returns:
            Dictionary with collection statistics:
            {
                "total_resources": int,
                "collection_name": str,
                "persist_directory": str
            }
        """
        try:
            count = self.collection.count()
            return {
                "total_resources": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_dir
            }
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def clear_collection(self) -> bool:
        """
        Clear all resources from the collection.
        
        Use with caution! This deletes all stored resources.
        
        Returns:
            True if successful
        """
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.warning(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing collection: {str(e)}")
            return False


# Singleton instance
_vector_store_instance: Optional[VectorStore] = None


def get_vector_store(
    persist_dir: str = "data/chroma",
    collection_name: str = "learning_resources"
) -> VectorStore:
    """
    Get or create singleton instance of VectorStore.
    
    Ensures only one vector store instance exists throughout
    the application lifecycle.
    
    Args:
        persist_dir: Directory for persistence (used on first creation)
        collection_name: Collection name (used on first creation)
    
    Returns:
        VectorStore singleton instance
        
    Example:
        >>> vs = get_vector_store()
        >>> results = vs.search("Python basics")
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(persist_dir, collection_name)
    return _vector_store_instance


def reset_vector_store() -> None:
    """
    Reset the singleton instance (useful for testing).
    """
    global _vector_store_instance
    _vector_store_instance = None
