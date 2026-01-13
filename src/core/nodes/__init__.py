"""
LangGraph Nodes Module

All nodes for the learning workflow graph.

Nodes:
- goal_analyzer: Validate and store learning goal
- resource_retriever: Curate learning resources via RAG
- roadmap_generator: Generate personalized roadmap
- task_generator: Create daily tasks
- performance_analyzer: Calculate performance metrics
- knowledge_gap_detector: Identify learning gaps
- finalize: Complete workflow and prepare output
"""

from src.core.nodes.goal_analyzer import goal_analysis_node
from src.core.nodes.resource_retriever import resource_retriever_node
from src.core.nodes.roadmap_generator import roadmap_generator_node
from src.core.nodes.task_generator import task_generator_node
from src.core.nodes.performance_analyzer import performance_analyzer_node
from src.core.nodes.knowledge_gap_detector import knowledge_gap_detector_node
from src.core.nodes.finalize import finalize_node, get_workflow_summary

# Node registry for easy access
NODE_REGISTRY = {
    "goal_analyzer": goal_analysis_node,
    "resource_retriever": resource_retriever_node,
    "roadmap_generator": roadmap_generator_node,
    "task_generator": task_generator_node,
    "performance_analyzer": performance_analyzer_node,
    "knowledge_gap_detector": knowledge_gap_detector_node,
    "finalize": finalize_node,
}

__all__ = [
    "goal_analysis_node",
    "resource_retriever_node",
    "roadmap_generator_node",
    "task_generator_node",
    "performance_analyzer_node",
    "knowledge_gap_detector_node",
    "finalize_node",
    "get_workflow_summary",
    "NODE_REGISTRY",
]
