"""
Curriculum Architect Agent
Builds hierarchical curriculum structure: Modules → Topics → Subtopics
"""
import json
from typing import Dict, Any, Optional
from src.llm.config import get_llm
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CurriculumArchitect:
    """
    Agent that creates a hierarchical curriculum structure.
    
    Transforms domain analysis into a structured curriculum with:
    - Modules (main learning blocks)
    - Topics (within each module)
    - Subtopics (learning components)
    - Prerequisites and dependencies
    - Learning objectives per level
    """
    
    def __init__(self, temperature: float = 0.5):
        """Initialize the curriculum architect agent."""
        self.llm = get_llm(temperature=temperature)
        logger.info("CurriculumArchitect initialized")
    
    def architect(
        self,
        goal_text: str,
        domain_analysis: Dict[str, Any],
        user_profile: Dict[str, Any],
        goal_analysis: Optional[Dict[str, Any]] = None,
        target_weeks: Optional[int] = None,
        target_completion_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create hierarchical curriculum structure.
        
        Args:
            goal_text: User's learning goal
            domain_analysis: Domain structure from phase 1
            user_profile: User preferences and level
            goal_analysis: Additional goal analysis
            target_weeks: User's target timeline in weeks (prioritized over domain analysis)
            target_completion_days: User's target timeline in days
            
        Returns:
            Abstract roadmap with hierarchical structure (NO content yet)
        """
        logger.info("[CurriculumArchitect] Creating curriculum structure")
        
        # Use user's target timeline if provided, otherwise use domain analysis estimate
        if target_weeks:
            curriculum_weeks = target_weeks
            timeline_source = "user_specified"
        else:
            curriculum_weeks = domain_analysis.get('estimated_weeks', 8)
            timeline_source = "domain_analysis"
        
        logger.info(f"  Timeline: {curriculum_weeks} weeks ({timeline_source})")
        
        # Calculate available learning hours
        daily_minutes = user_profile.get('daily_minutes', 30)
        if target_completion_days:
            total_hours = (daily_minutes * target_completion_days) / 60
        else:
            total_hours = (daily_minutes * curriculum_weeks * 7) / 60
        
        try:
            # Build prompt with timeline constraints
            system_prompt = f"""You are an expert curriculum designer creating a structured learning path.
            
CRITICAL TIMELINE CONSTRAINT:
- The curriculum MUST be completable in exactly {curriculum_weeks} weeks
- User has {daily_minutes} minutes per day = {total_hours:.0f} total learning hours
- Adjust scope and depth to FIT this timeline - DO NOT exceed it
- If the topic is too large, focus on essentials and mark advanced topics as optional
            
Generate a hierarchical curriculum as JSON with this structure:
{{
    "structure": {{
        "modules": [
            {{
                "id": "mod_1",
                "title": "Module Title",
                "description": "Brief description",
                "estimated_weeks": 2,
                "difficulty": 0.3,
                "topics": [
                    {{
                        "id": "topic_1_1",
                        "title": "Topic Title",
                        "learning_objectives": ["objective 1", "objective 2"],
                        "subtopics": ["subtopic1", "subtopic2"]
                    }}
                ],
                "prerequisites": ["mod_0"],
                "dependencies_after": ["mod_2"]
            }}
        ]
    }},
    "milestones": [
        {{"week": 2, "checkpoint": "Quiz on Module 1", "success_criteria": "80%"}}
    ],
    "total_estimated_weeks": {curriculum_weeks}
}}

Guidelines:
- SUM of all module estimated_weeks MUST equal {curriculum_weeks}
- Create 3-6 modules (fewer for shorter timelines)
- Ensure logical progression
- Link prerequisites and dependencies
- Consider user level and pace
- Each module has 2-4 topics
- Each topic has 2-4 subtopics
- For short timelines ({curriculum_weeks} <= 4 weeks): focus on 3-4 essential modules
- For medium timelines (4-12 weeks): include 4-5 modules with practice
- For long timelines (12+ weeks): comprehensive 5-8 modules with projects"""
            
            user_prompt = f"""Create a {curriculum_weeks}-week curriculum for: {goal_text}

Domain Prerequisites: {', '.join(domain_analysis.get('prerequisites', []))}
Core Competencies: {', '.join(domain_analysis.get('core_competencies', []))}
Complexity: {domain_analysis.get('complexity_estimate', 0.5)}/1.0

User Level: {user_profile.get('level', 'beginner')}
Pace Preference: {user_profile.get('pace', 'medium')}
Daily Minutes Available: {daily_minutes}
Total Available Hours: {total_hours:.0f}

IMPORTANT: The total_estimated_weeks in your response MUST be exactly {curriculum_weeks}.
Return only valid JSON."""
            
            # Call LLM
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            response_text = response.content if hasattr(response, "content") else str(response)
            
            # Parse JSON
            try:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    roadmap = json.loads(json_str)
                else:
                    roadmap = self._create_default_roadmap(goal_text, domain_analysis, curriculum_weeks)
                    logger.warning("Could not parse curriculum JSON, using default")
            
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {e}, using default roadmap")
                roadmap = self._create_default_roadmap(goal_text, domain_analysis, curriculum_weeks)
            
            # Validate total weeks matches target
            actual_weeks = roadmap.get("total_estimated_weeks", curriculum_weeks)
            if actual_weeks != curriculum_weeks:
                logger.warning(f"  Adjusting total_estimated_weeks from {actual_weeks} to {curriculum_weeks}")
                roadmap["total_estimated_weeks"] = curriculum_weeks
            
            logger.info(f"  ✓ Curriculum created: {len(roadmap.get('structure', {}).get('modules', []))} modules in {curriculum_weeks} weeks")
            
            return roadmap
            
        except Exception as e:
            logger.error(f"✗ Architecture failed: {str(e)}", exc_info=True)
            return self._create_default_roadmap(goal_text, domain_analysis, curriculum_weeks if target_weeks else None)
    
    @staticmethod
    def _create_default_roadmap(
        goal_text: str, 
        domain_analysis: Dict[str, Any],
        target_weeks: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a default roadmap structure that fits the target timeline."""
        # Use target_weeks if provided, otherwise use domain analysis
        estimated_weeks = target_weeks if target_weeks else domain_analysis.get("estimated_weeks", 8)
        
        return {
            "structure": {
                "modules": [
                    {
                        "id": "mod_1",
                        "title": "Foundations",
                        "description": "Core foundations and prerequisites",
                        "estimated_weeks": max(1, estimated_weeks // 4),
                        "difficulty": 0.2,
                        "topics": [
                            {
                                "id": "topic_1_1",
                                "title": "Fundamentals",
                                "learning_objectives": ["Understand core concepts"],
                                "subtopics": ["Introduction", "Basic principles", "Key terminology"]
                            }
                        ],
                        "prerequisites": [],
                        "dependencies_after": ["mod_2"]
                    },
                    {
                        "id": "mod_2",
                        "title": "Core Concepts",
                        "description": "Main learning objectives",
                        "estimated_weeks": max(1, estimated_weeks // 2),
                        "difficulty": 0.5,
                        "topics": [
                            {
                                "id": "topic_2_1",
                                "title": "Main Content",
                                "learning_objectives": ["Master core concepts"],
                                "subtopics": ["Topic A", "Topic B", "Topic C"]
                            }
                        ],
                        "prerequisites": ["mod_1"],
                        "dependencies_after": ["mod_3"]
                    },
                    {
                        "id": "mod_3",
                        "title": "Advanced Topics",
                        "description": "Advanced applications and synthesis",
                        "estimated_weeks": max(1, estimated_weeks // 4),
                        "difficulty": 0.7,
                        "topics": [
                            {
                                "id": "topic_3_1",
                                "title": "Advanced Applications",
                                "learning_objectives": ["Apply knowledge in advanced scenarios"],
                                "subtopics": ["Use case 1", "Use case 2", "Integration"]
                            }
                        ],
                        "prerequisites": ["mod_2"],
                        "dependencies_after": []
                    }
                ]
            },
            "milestones": [
                {
                    "week": max(1, estimated_weeks // 4),
                    "checkpoint": "Module 1 Assessment",
                    "success_criteria": "80%"
                },
                {
                    "week": max(1, estimated_weeks // 2),
                    "checkpoint": "Module 2 Project",
                    "success_criteria": "Completion"
                },
                {
                    "week": estimated_weeks,
                    "checkpoint": "Final Assessment",
                    "success_criteria": "85%"
                }
            ],
            "total_estimated_weeks": estimated_weeks
        }
