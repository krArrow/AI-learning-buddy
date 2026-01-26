"""
LangGraph Nodes Module - 4-Phase Workflow

PHASE 1: DISCOVERY
- goal_clarifier_node: Interactive dialogue + skill assessment
- domain_analyzer_node: Extract domain structure

PHASE 2: ROADMAP ARCHITECTURE
- curriculum_architect_node: Create hierarchical structure
- roadmap_validator_node: Validate and approve roadmap

PHASE 3: CONTENT POPULATION
- module_curator_node: Per-module RAG/search (loop)
- module_task_generator_node: Create tasks per module
- content_aggregator_node: Merge abstract + content

PHASE 4: ADAPTIVE EXECUTION
- progress_tracker_node: Log completion + metrics
- adaptive_controller_node: Detect struggles, recommend actions
- replanning_trigger_node: Decide if re-curation needed
"""

from src.core.nodes.goal_clarifier_node import goal_clarifier_node
from src.core.nodes.domain_analyzer_node import domain_analyzer_node
from src.core.nodes.curriculum_architect_node import curriculum_architect_node
from src.core.nodes.roadmap_validator_node import roadmap_validator_node
from src.core.nodes.module_curator_node import module_curator_node
from src.core.nodes.module_task_generator_node import module_task_generator_node
from src.core.nodes.content_aggregator_node import content_aggregator_node
from src.core.nodes.progress_tracker_node import progress_tracker_node
from src.core.nodes.adaptive_controller_node import adaptive_controller_node
from src.core.nodes.replanning_trigger_node import replanning_trigger_node

# Keep finalize for now if it exists
try:
    from src.core.nodes.finalize import finalize_node, get_workflow_summary
except ImportError:
    finalize_node = None
    get_workflow_summary = None

# Node registry for easy access and compilation
NODE_REGISTRY = {
    # Phase 1: Discovery
    "goal_clarifier_node": goal_clarifier_node,
    "domain_analyzer_node": domain_analyzer_node,
    # Phase 2: Roadmap Architecture
    "curriculum_architect_node": curriculum_architect_node,
    "roadmap_validator_node": roadmap_validator_node,
    # Phase 3: Content Population
    "module_curator_node": module_curator_node,
    "module_task_generator_node": module_task_generator_node,
    "content_aggregator_node": content_aggregator_node,
    # Phase 4: Adaptive Execution
    "progress_tracker_node": progress_tracker_node,
    "adaptive_controller_node": adaptive_controller_node,
    "replanning_trigger_node": replanning_trigger_node,
}

# Include finalize if available
if finalize_node:
    NODE_REGISTRY["finalize"] = finalize_node

__all__ = [
    "goal_clarifier_node",
    "domain_analyzer_node",
    "curriculum_architect_node",
    "roadmap_validator_node",
    "module_curator_node",
    "module_task_generator_node",
    "content_aggregator_node",
    "progress_tracker_node",
    "adaptive_controller_node",
    "replanning_trigger_node",
    "NODE_REGISTRY",
]

if finalize_node:
    __all__.extend(["finalize_node", "get_workflow_summary"])
