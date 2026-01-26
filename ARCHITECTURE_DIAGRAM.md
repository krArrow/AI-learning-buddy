# 4-PHASE LEARNING WORKFLOW - ARCHITECTURE DIAGRAM

## Complete Graph Flow

```
                                    WORKFLOW START
                                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DISCOVERY (Clarify Goals & Assess Skills)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  goal_clarifier_node                                                 │
│  ├─ 5-turn interactive dialogue                                     │
│  ├─ Extract: level, learning_style, pace, preferences              │
│  └─ Output: conversation_history, user_profile (partial)            │
│       ↓                                                               │
│       └─→ (discovery_complete check)                                │
│            ├─ NO → loop back to goal_clarifier_node                 │
│            └─ YES ↓                                                  │
│                                                                       │
│  domain_analyzer_node                                                │
│  ├─ LLM: Analyze learning domain                                    │
│  ├─ Extract: prerequisites, dependencies, complexity, estimate      │
│  └─ Output: domain_analysis, goal_analysis                           │
│       ↓                                                               │
│  ✓ PHASE 1 OUTPUT                                                   │
│    ├─ user_profile (complete)                                       │
│    ├─ goal_analysis                                                 │
│    └─ domain_analysis                                               │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: ROADMAP ARCHITECTURE (Hierarchical Structure)              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  curriculum_architect_node                                           │
│  ├─ LLM: Build curriculum hierarchy                                 │
│  ├─ Create: Modules → Topics → Subtopics                            │
│  ├─ Add: Learning objectives, prerequisite chains                   │
│  ├─ NO content resources/tasks yet                                  │
│  └─ Output: abstract_roadmap (4-8 modules)                          │
│       ↓                                                               │
│  roadmap_validator_node                                              │
│  ├─ Check: Prerequisites valid for user level                       │
│  ├─ Check: Time estimate vs availability                            │
│  ├─ Get: User approval (auto-validate for now)                      │
│  └─ Output: roadmap_validated = True                                │
│       ↓                                                               │
│       └─→ (roadmap_validated check)                                 │
│            ├─ NO → loop back to curriculum_architect               │
│            └─ YES ↓                                                  │
│                                                                       │
│  ✓ PHASE 2 OUTPUT                                                   │
│    └─ abstract_roadmap (structure, no content)                      │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: CONTENT POPULATION (Per-Module Loop)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ FOR EACH MODULE (pending → completed):                      │   │
│  │                                                              │   │
│  │  module_curator_node                                        │   │
│  │  ├─ Find next pending module                               │   │
│  │  ├─ Search resources (RAG/API): videos, articles, courses   │   │
│  │  ├─ Rank by relevance + difficulty match                   │   │
│  │  ├─ Keep top 15 resources                                  │   │
│  │  └─ Output: module_resources[mod_id]                       │   │
│  │       ↓                                                      │   │
│  │  module_task_generator_node                                 │   │
│  │  ├─ Extract learning objectives from topics                │   │
│  │  ├─ Create: exercises, quizzes, projects, reflections      │   │
│  │  ├─ Align to resources                                     │   │
│  │  └─ Output: module_tasks[mod_id]                           │   │
│  │       ↓                                                      │   │
│  │  (More modules pending?)                                   │   │
│  │  ├─ YES → loop back to module_curator for next module      │   │
│  │  └─ NO ↓                                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       ↓                                                               │
│  content_aggregator_node                                             │
│  ├─ Merge: abstract_roadmap + module_resources + module_tasks       │
│  ├─ Enrich: Each module with "resources" & "tasks" fields           │
│  ├─ Result: Complete, fully-populated roadmap                       │
│  └─ Output: populated_roadmap                                        │
│       ↓                                                               │
│  ✓ PHASE 3 OUTPUT                                                   │
│    └─ populated_roadmap (ready for execution)                       │
│       ├─ Modules with resources & tasks                             │
│       ├─ Learning objectives                                        │
│       └─ Success criteria                                           │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 4: ADAPTIVE EXECUTION (Learning Loop)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ EXECUTION LOOP (continuous):                                │  │
│  │                                                               │  │
│  │  progress_tracker_node                                       │  │
│  │  ├─ Log task completion                                     │  │
│  │  ├─ Record: time_spent vs estimate, difficulty_reported     │  │
│  │  ├─ Calculate: performance_score, velocity, consistency     │  │
│  │  ├─ Update: task_completion_details, performance_metrics    │  │
│  │  └─ Output: performance_metrics dict                        │  │
│  │       ↓                                                       │  │
│  │  adaptive_controller_node                                    │  │
│  │  ├─ Analyze performance metrics                             │  │
│  │  ├─ Detect struggles:                                       │  │
│  │  │  ├─ If difficulty > 0.6 AND performance < 0.75           │  │
│  │  │  ├─ If time_ratio > 1.3 (30% over estimate)              │  │
│  │  │  └─ If consistency < 0.6                                 │  │
│  │  ├─ Recommend actions: [slow down, add practice, ...]       │  │
│  │  ├─ Calculate: pacing_adjustment (0.8 = slow, 1.2 = fast)   │  │
│  │  └─ Output: struggle_severity, adaptation_required          │  │
│  │       ↓                                                       │  │
│  │  replanning_trigger_node                                     │  │
│  │  ├─ Check: struggle_severity > threshold (0.7)?             │  │
│  │  ├─ Decide action:                                          │  │
│  │  │  ├─ Re-curate: If severe struggle                        │  │
│  │  │  │  └─ Set struggling_module_id                          │  │
│  │  │  │  └─ Mark for recuration                               │  │
│  │  │  │  └─ LOOP BACK to module_curator_node                  │  │
│  │  │  │                                                        │  │
│  │  │  ├─ Continue: If minor struggle                          │  │
│  │  │  │  └─ Loop back to progress_tracker_node                │  │
│  │  │  │                                                        │  │
│  │  │  └─ End: If all tasks complete                           │  │
│  │  │     └─ EXIT to END                                       │  │
│  │  └─ Output: re_curation_triggered, recommended_actions      │  │
│  │                                                               │  │
│  │  ✓ PHASE 4 ADAPTATIONS                                      │  │
│  │    ├─ Dynamic resource re-curation for struggling modules    │  │
│  │    ├─ Pacing adjustments                                    │  │
│  │    ├─ Real-time performance tracking                        │  │
│  │    └─ Struggle detection & intervention                     │  │
│  │                                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
                        WORKFLOW END
```

---

## Conditional Edge Map

```
DISCOVERY PHASE:
  domain_analyzer_node →  [if discovery_complete]
                         ├─ YES → curriculum_architect_node (ROADMAP)
                         └─ NO  → goal_clarifier_node (DISCOVERY loop)

ROADMAP PHASE:
  roadmap_validator_node → [if roadmap_validated]
                          ├─ YES → module_curator_node (CONTENT)
                          └─ NO  → curriculum_architect_node (ROADMAP loop)

CONTENT PHASE:
  module_task_generator_node → [if more modules pending]
                              ├─ YES → module_curator_node (per-module loop)
                              └─ NO  → content_aggregator_node (done)

ADAPTIVE PHASE:
  replanning_trigger_node → [if re_curation_triggered]
                           ├─ YES → module_curator_node (re-curate loop)
                           ├─ NO  → progress_tracker_node (continue execution)
                           └─ [END] → WORKFLOW END (on completion)
```

---

## State Transitions

```
Phase 1: DISCOVERY
├─ START
├─ goal_clarifier_node (conversation)
├─ domain_analyzer_node (LLM analysis)
└─ OUTPUT: user_profile, goal_analysis, domain_analysis

Phase 2: ROADMAP_ARCHITECTURE  
├─ INPUT: user_profile, goal_analysis, domain_analysis
├─ curriculum_architect_node (LLM structure builder)
├─ roadmap_validator_node (validation)
└─ OUTPUT: abstract_roadmap (no content)

Phase 3: CONTENT_POPULATION
├─ INPUT: abstract_roadmap
├─ [Loop for each module]
│  ├─ module_curator_node (RAG search)
│  └─ module_task_generator_node (task generation)
├─ content_aggregator_node (merge)
└─ OUTPUT: populated_roadmap (full content)

Phase 4: ADAPTIVE_EXECUTION
├─ INPUT: populated_roadmap
├─ [Loop while learning]
│  ├─ progress_tracker_node (track completion)
│  ├─ adaptive_controller_node (detect struggles)
│  └─ replanning_trigger_node (decide re-curation)
│     └─ [If struggles] → back to module_curator (re-curate)
└─ OUTPUT: performance_metrics, completed_tasks, recommendations
```

---

## Key Design Patterns

### 1. **Per-Module Curation** (Phase 3)
- Modules are curated ONE AT A TIME, not all at once
- Enables: Adaptive resource selection, progressive curation, user feedback
- Flow: Find pending → Search → Rank → Store → Next module

### 2. **Conditional Routing** (All Phases)
- Each phase can loop back (approval, clarification, re-planning)
- Discovery loops until clarification_complete
- Roadmap loops until roadmap_validated
- Content loops for each module
- Adaptive loops on struggles

### 3. **Struggle Detection** (Phase 4)
- Multi-criteria: difficulty > 0.6 AND performance < 0.75
- Time-based: ratio > 1.3 (30% over estimate)
- Consistency-based: score < 0.6
- Triggers: re-curation, pacing adjustment, interventions

### 4. **State Accumulation**
- Each node adds to/updates state
- No node deletes previous data
- Metadata tracks phase transitions
- Final state contains EVERYTHING

---

## Node Specifications

| Node | Phase | Input | Output | Type |
|------|-------|-------|--------|------|
| goal_clarifier_node | 1 | goal_text | user_profile, conversation_history | Interactive |
| domain_analyzer_node | 1 | user_profile | domain_analysis | LLM |
| curriculum_architect_node | 2 | domain_analysis | abstract_roadmap | LLM |
| roadmap_validator_node | 2 | abstract_roadmap | roadmap_validated | Validation |
| module_curator_node | 3 | abstract_roadmap | module_resources[id] | Search+Rank |
| module_task_generator_node | 3 | module_resources | module_tasks[id] | LLM |
| content_aggregator_node | 3 | resources+tasks | populated_roadmap | Merge |
| progress_tracker_node | 4 | populated_roadmap | performance_metrics | Tracking |
| adaptive_controller_node | 4 | performance_metrics | struggle_severity | Analysis |
| replanning_trigger_node | 4 | struggle_severity | re_curation_triggered | Decision |

---

## Agents (LLM-based)

1. **GoalClarifierAgent** → goal_clarifier_node
   - 5-turn max conversation
   - Builds user profile dynamically

2. **CurriculumArchitect** → curriculum_architect_node
   - Builds hierarchical curriculum
   - Creates Modules → Topics → Subtopics
   - No content, only structure

3. **AdaptiveController** → adaptive_controller_node
   - Analyzes performance
   - Detects struggles
   - Recommends interventions

---

## Example Execution Flow

```
User: "Learn Python for data science"
  ↓ [PHASE 1: 15 min]
  ├─ goal_clarifier: "What's your level?" → "Beginner"
  ├─ goal_clarifier: "Preferred style?" → "Visual"
  ├─ domain_analyzer: "Prerequisites: math, basic stats"
  └─ discovery_complete = TRUE
  ↓ [PHASE 2: 5 min]
  ├─ curriculum_architect: Creates 5 modules
  │  ├─ Module 1: Python Fundamentals (2 weeks)
  │  ├─ Module 2: Data Structures (2 weeks)
  │  ├─ Module 3: NumPy & Pandas (3 weeks)
  │  ├─ Module 4: Data Analysis (3 weeks)
  │  └─ Module 5: Real Projects (2 weeks)
  ├─ roadmap_validator: "Roadmap OK, proceed?"
  └─ roadmap_validated = TRUE
  ↓ [PHASE 3: 20 min]
  ├─ module_curator: Search resources for Module 1 (15 resources)
  ├─ module_task_generator: Create 3 tasks for Module 1
  ├─ module_curator: Search resources for Module 2 (15 resources)
  ├─ module_task_generator: Create 3 tasks for Module 2
  ├─ ... [repeat for modules 3-5]
  ├─ content_aggregator: Merge all into populated_roadmap
  └─ READY FOR LEARNING
  ↓ [PHASE 4: Continuous]
  ├─ progress_tracker: User completes Module 1, Task 1
  │  ├─ Time: 35 min (est 30) → 1.17x
  │  ├─ Difficulty: 0.3 (perceived)
  │  └─ Performance: 0.90
  ├─ adaptive_controller: No struggle detected
  ├─ replanning_trigger: Continue learning
  └─ progress_tracker: Next task...
     
  [Later: User struggling with Module 3]
  ├─ progress_tracker: Low performance (0.55), high time (2.1x)
  ├─ adaptive_controller: STRUGGLE DETECTED (severity 0.8)
  ├─ replanning_trigger: Re-curation triggered!
  └─ module_curator: Re-search Module 3 with different focus
     └─ Return to progress_tracker with new resources
```

---

## Summary

✓ **4 phases** with clear transitions
✓ **10 nodes** with specific responsibilities
✓ **Conditional edges** enabling loops and adaptations
✓ **2 agents** for intelligent decisions
✓ **Per-module** content curation (scalable)
✓ **Real-time** performance tracking
✓ **Automatic** struggle detection & re-planning
