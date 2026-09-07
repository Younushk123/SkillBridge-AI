import re

from backend.recommendations import RECOMMENDATIONS, get_recommendation
from backend.schemas import InterviewQuestion, JobSkillExtraction, LearningPriority, RoadmapPhase
from backend.skill_gap import ROLE_SKILLS


ALIASES = {
    "pythonprogramming": "Python",
    "structuredquerylanguage": "SQL",
    "reactjs": "React",
    "reactjavascript": "React",
    "nodejs": "Node.js",
    "nodejavascript": "Node.js",
    "scikitlearn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "amazonwebservices": "AWS",
    "googlecloud": "Google Cloud Platform",
    "gcp": "Google Cloud Platform",
    "continuousintegrationcontinuousdeployment": "CI/CD",
    "naturallanguageprocessing": "Natural Language Processing",
    "nlp": "Natural Language Processing",
}


def _skill_key(skill: str) -> str:
    return re.sub(r"[\s._/-]+", "", skill).casefold()


def _canonical_skills() -> dict[str, str]:
    skills = [skill for role_skills in ROLE_SKILLS.values() for skill in role_skills]
    skills.extend(RECOMMENDATIONS)
    return {_skill_key(skill): skill for skill in skills}


CANONICAL_SKILLS = _canonical_skills()


def normalize_skill(skill: str) -> str:
    normalized = " ".join(skill.split())
    if not normalized:
        return ""
    key = _skill_key(normalized)
    return ALIASES.get(key, CANONICAL_SKILLS.get(key, normalized))


def normalize_skills(skills: list[str]) -> list[str]:
    normalized_skills = []
    seen = set()
    for skill in skills:
        normalized = normalize_skill(skill)
        key = _skill_key(normalized)
        if normalized and key not in seen:
            normalized_skills.append(normalized)
            seen.add(key)
    return normalized_skills


def _learning_priorities(missing_required: list[str], missing_preferred: list[str]) -> list[LearningPriority]:
    priorities = [
        LearningPriority(
            skill=skill,
            priority="High",
            requirement_type="Required",
            recommendation=get_recommendation(skill),
        )
        for skill in missing_required
    ]
    priorities.extend(
        LearningPriority(
            skill=skill,
            priority="Medium",
            requirement_type="Preferred",
            recommendation=get_recommendation(skill),
        )
        for skill in missing_preferred
    )
    return priorities


def _roadmap(
    target_role: str,
    missing_required: list[str],
    missing_preferred: list[str],
    matched_skills: list[str],
) -> list[RoadmapPhase]:
    phases = []
    if missing_required:
        focus_skills = missing_required[:3]
        phases.append(
            RoadmapPhase(
                title="Close required skill gaps",
                duration="Weeks 1-2",
                focus_skills=focus_skills,
                actions=[
                    f"Study {skill} fundamentals and complete a targeted exercise."
                    for skill in focus_skills
                ],
            )
        )
    if missing_preferred:
        focus_skills = missing_preferred[:3]
        phases.append(
            RoadmapPhase(
                title="Add preferred capabilities",
                duration="Week 3",
                focus_skills=focus_skills,
                actions=[
                    f"Build a small {target_role} project that demonstrates {skill}."
                    for skill in focus_skills
                ],
            )
        )
    if matched_skills:
        focus_skills = matched_skills[:3]
        phases.append(
            RoadmapPhase(
                title="Prepare job evidence",
                duration="Week 4",
                focus_skills=focus_skills,
                actions=[
                    f"Prepare one outcome-focused example that demonstrates {skill}."
                    for skill in focus_skills
                ],
            )
        )
    if not phases:
        phases.append(
            RoadmapPhase(
                title="Validate the role requirements",
                duration="This week",
                focus_skills=[],
                actions=[
                    "Review the job description with the employer and identify the most important skills."
                ],
            )
        )
    return phases[:3]


def _interview_questions(
    target_role: str,
    required_skills: list[str],
    preferred_skills: list[str],
) -> list[InterviewQuestion]:
    focus_skills = (required_skills + preferred_skills)[:5]
    if not focus_skills:
        return [
            InterviewQuestion(
                skill="Role fit",
                question=f"How would you approach the responsibilities of this {target_role} role?",
            )
        ]
    return [
        InterviewQuestion(
            skill=skill,
            question=f"How would you apply {skill} to solve a problem in this {target_role} role?",
        )
        for skill in focus_skills
    ]


def build_job_analysis(
    current_skills: list[str],
    extraction: JobSkillExtraction,
    target_role: str,
) -> dict:
    normalized_current_skills = normalize_skills(current_skills)
    current_skill_keys = {_skill_key(skill) for skill in normalized_current_skills}
    required_skills = normalize_skills(extraction.required_skills)
    required_skill_keys = {_skill_key(skill) for skill in required_skills}
    preferred_skills = [
        skill
        for skill in normalize_skills(extraction.preferred_skills)
        if _skill_key(skill) not in required_skill_keys
    ]

    matched_required = [
        skill for skill in required_skills if _skill_key(skill) in current_skill_keys
    ]
    missing_required = [
        skill for skill in required_skills if _skill_key(skill) not in current_skill_keys
    ]
    matched_preferred = [
        skill for skill in preferred_skills if _skill_key(skill) in current_skill_keys
    ]
    missing_preferred = [
        skill for skill in preferred_skills if _skill_key(skill) not in current_skill_keys
    ]
    match_score = round(100 * len(matched_required) / len(required_skills)) if required_skills else 0
    matched_skills = matched_required + matched_preferred

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_required + missing_preferred,
        "match_score": match_score,
        "learning_priorities": _learning_priorities(missing_required, missing_preferred),
        "roadmap": _roadmap(target_role, missing_required, missing_preferred, matched_skills),
        "interview_questions": _interview_questions(target_role, required_skills, preferred_skills),
    }
