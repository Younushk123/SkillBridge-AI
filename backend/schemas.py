from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class UserProfile(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    education: str = Field(min_length=2, max_length=100)
    experience_years: int = Field(ge=0, le=50)
    skills: str = Field(min_length=2, max_length=1000)
    target_role: str = Field(min_length=2, max_length=100)


class ProfileResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    education: str
    experience_years: int
    skills: str
    target_role: str

    model_config = ConfigDict(from_attributes=True)


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class ResumeAnalysisResponse(StrictSchema):
    name: str = Field(default="", max_length=100)
    education: str = Field(default="", max_length=100)
    experience_years: int = Field(default=0, ge=0, le=50)
    skills: list[str] = Field(default_factory=list, max_length=50)
    target_role: str = Field(default="", max_length=100)

    @model_validator(mode="before")
    @classmethod
    def unknown_values_use_defaults(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        normalized = value.copy()
        for field, default in {
            "name": "",
            "education": "",
            "experience_years": 0,
            "skills": [],
            "target_role": "",
        }.items():
            if normalized.get(field) is None:
                normalized[field] = default
        return normalized

    @field_validator("skills")
    @classmethod
    def skills_must_not_be_blank(cls, value: list[str]) -> list[str]:
        if any(not skill for skill in value):
            raise ValueError("Skills must not be blank")
        return value


class JobAnalysisRequest(StrictSchema):
    job_description: str = Field(min_length=20, max_length=30000)

    @field_validator("job_description")
    @classmethod
    def job_description_must_not_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("Job description must not be blank")
        return value


class JobSkillExtraction(StrictSchema):
    required_skills: list[str] = Field(default_factory=list, max_length=50)
    preferred_skills: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("required_skills", "preferred_skills")
    @classmethod
    def skills_must_not_be_blank(cls, value: list[str]) -> list[str]:
        if any(not skill for skill in value):
            raise ValueError("Skills must not be blank")
        return value


class LearningPriority(StrictSchema):
    skill: str = Field(min_length=1, max_length=100)
    priority: Literal["High", "Medium"]
    requirement_type: Literal["Required", "Preferred"]
    recommendation: str = Field(min_length=1, max_length=500)


class RoadmapPhase(StrictSchema):
    title: str = Field(min_length=1, max_length=100)
    duration: str = Field(min_length=1, max_length=100)
    focus_skills: list[str] = Field(default_factory=list, max_length=10)
    actions: list[str] = Field(default_factory=list, max_length=10)


class InterviewQuestion(StrictSchema):
    skill: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=500)


class JobAnalysisResponse(StrictSchema):
    profile_id: int = Field(ge=1)
    target_role: str = Field(min_length=1, max_length=100)
    required_skills: list[str] = Field(default_factory=list, max_length=50)
    preferred_skills: list[str] = Field(default_factory=list, max_length=50)
    matched_skills: list[str] = Field(default_factory=list, max_length=100)
    missing_skills: list[str] = Field(default_factory=list, max_length=100)
    match_score: int = Field(ge=0, le=100)
    learning_priorities: list[LearningPriority] = Field(default_factory=list, max_length=100)
    roadmap: list[RoadmapPhase] = Field(default_factory=list, max_length=5)
    interview_questions: list[InterviewQuestion] = Field(default_factory=list, max_length=10)


class MarketSkillDemand(StrictSchema):
    skill: str = Field(min_length=1, max_length=100)
    demand_count: int = Field(ge=1)
    demand_percentage: float = Field(ge=0, le=100)


class MarketSummaryResponse(StrictSchema):
    market_summary: str = Field(min_length=1, max_length=500)


class MarketAnalysisResponse(StrictSchema):
    target_role: str = Field(min_length=1, max_length=100)
    jobs_analyzed: int = Field(ge=0)
    market_skills: list[MarketSkillDemand] = Field(default_factory=list, max_length=100)
    matched_skills: list[str] = Field(default_factory=list, max_length=100)
    missing_skills: list[str] = Field(default_factory=list, max_length=100)
    priority_skills: list[MarketSkillDemand] = Field(default_factory=list, max_length=5)
    market_summary: str = Field(min_length=1, max_length=500)
