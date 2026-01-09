"""
Prompt templates for AI Learning Buddy
All prompts are explicit and structured for deterministic outputs
"""

PROMPT_1_GENERATE_ROADMAP = """You are an expert learning advisor.

USER GOAL: {goal}
USER LEVEL: {level}
DAILY TIME AVAILABLE: {daily_minutes} minutes

Create a structured learning roadmap with these requirements:

1. Break the goal into 3-5 major learning modules
2. Each module should be achievable in 1-2 weeks
3. Order modules from foundational to advanced
4. For each module, explain:
   - What will be learned
   - Why it's important for the goal
   - Prerequisites (if any)

Output format (follow exactly):

MODULE 1: [Module Name]
Duration: [X weeks]
Description: [What will be learned]
Why: [Why this matters for the goal]
Prerequisites: [None or list them]

MODULE 2: ...
(continue for all modules)

IMPORTANT: Consider the user's current level and daily time. Keep it realistic.
"""

PROMPT_2_GENERATE_DAILY_TASKS = """You are an expert learning advisor creating daily tasks.

LEARNING GOAL: {goal}
USER LEVEL: {level}
DAILY TIME AVAILABLE: {daily_minutes} minutes

LEARNING ROADMAP:
{roadmap}

Create 7 daily tasks for the FIRST module. Each task must:
1. Be completable in {daily_minutes} minutes or less
2. Build on the previous day
3. Be concrete and actionable (e.g., "Watch X tutorial", "Build Y project")
4. Include WHY this task matters

Output format (follow exactly):

DAY 1:
Task: [Specific action to take]
Why: [Why this helps achieve the goal]
Estimated Time: [X minutes]

DAY 2:
...
(continue for 7 days)

IMPORTANT: Tasks should be specific, not vague. Include resources when possible (e.g., "Read Chapter 3 of X book").
"""

PROMPT_3_ADAPT_TASKS = """You are an expert learning advisor adapting a learning plan.

ORIGINAL GOAL: {goal}
USER LEVEL: {level}
DAILY TIME AVAILABLE: {daily_minutes} minutes

ORIGINAL ROADMAP:
{roadmap}

COMPLETED TASKS (last 7 days):
{completed_tasks}

INCOMPLETE TASKS (last 7 days):
{incomplete_tasks}

Based on the user's progress:
1. Assess if they're on track, ahead, or behind
2. Generate the NEXT 7 daily tasks
3. If they struggled (many incomplete tasks), adjust difficulty
4. If they excelled (all complete), increase challenge slightly

Output format (follow exactly):

PROGRESS ASSESSMENT:
[Brief analysis of user's progress]

DAY 8:
Task: [Specific action]
Why: [Reason]
Estimated Time: [X minutes]

DAY 9:
...
(continue for 7 days)

IMPORTANT: Adapt to their actual progress. Don't just repeat tasks.
"""

def get_prompt_1(goal: str, level: str, daily_minutes: int) -> str:
    """Generate roadmap prompt"""
    return PROMPT_1_GENERATE_ROADMAP.format(
        goal=goal,
        level=level,
        daily_minutes=daily_minutes
    )

def get_prompt_2(goal: str, level: str, daily_minutes: int, roadmap: str) -> str:
    """Generate initial daily tasks prompt"""
    return PROMPT_2_GENERATE_DAILY_TASKS.format(
        goal=goal,
        level=level,
        daily_minutes=daily_minutes,
        roadmap=roadmap
    )

def get_prompt_3(goal: str, level: str, daily_minutes: int, roadmap: str, 
                 completed_tasks: str, incomplete_tasks: str) -> str:
    """Generate adapted tasks based on progress"""
    return PROMPT_3_ADAPT_TASKS.format(
        goal=goal,
        level=level,
        daily_minutes=daily_minutes,
        roadmap=roadmap,
        completed_tasks=completed_tasks if completed_tasks else "None",
        incomplete_tasks=incomplete_tasks if incomplete_tasks else "None"
    )