import json
import os
import re

import requests
from pydantic import ValidationError
from requests import RequestException
from typing import Any

from backend.job_analysis import normalize_skills
from backend.schemas import JobSkillExtraction, MarketSummaryResponse, ResumeAnalysisResponse

BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
).rstrip("/")
MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-plus")


class AIServiceError(Exception):
    pass


class AIConfigurationError(AIServiceError):
    pass


class AIProviderError(AIServiceError):
    pass


class AIResponseError(AIServiceError):
    pass


def _json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def chat_json(system, user):
    key = os.getenv("DASHSCOPE_API_KEY")

    if not key:
        raise AIConfigurationError("AI configuration is unavailable")

    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
            timeout=30,
        )
    except RequestException as error:
        raise AIProviderError("AI provider is unavailable") from error

    if not response.ok:
        print("DashScope error:", response.status_code, response.text)
        raise AIProviderError(
            f"AI provider request failed: {response.status_code}"
        )

    try:
        content = response.json()["choices"][0]["message"]["content"]
        return _json(content)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
        raise AIResponseError(
            "AI provider returned an invalid response"
        ) from error


def analyze_resume(text, target_role):
    system = """You are SkillBridge AI, an expert resume analyzer. Never invent information.
Return ONLY JSON:
{"candidate_summary":"","skills":[],"education":[],"experience":[],"projects":[],"certifications":[],"strengths":[],"target_role":""}
Normalize clear skill spelling/case variations."""
    return chat_json(system, f"Target role: {target_role}\nResume:\n{text[:30000]}")


def extract_resume_profile(text: str) -> ResumeAnalysisResponse:
    system = """You are SkillBridge AI's resume profile extractor. Use only facts explicitly supported by the supplied resume. Never invent names, education, skills, years of experience, or roles. Return only a JSON object with this exact structure:
{"name":"","education":"","experience_years":0,"skills":[],"target_role":""}
Do not include email or any additional fields. Use concise canonical skill names. Derive target_role only when the resume clearly supports it; otherwise return an empty string. Use empty strings, 0, or an empty list when information is unavailable."""

    try:
        profile = ResumeAnalysisResponse.model_validate(
            chat_json(system, f"Resume:\n{text[:30000]}")
        )
        return profile.model_copy(
            update={"skills": normalize_skills(profile.skills)}
        )

    except AIProviderError as error:
        print("AI unavailable, using local resume analysis:", error)
        return local_resume_analysis(text)

    except AIConfigurationError:
        raise

    except ValidationError as error:
        raise AIResponseError(
            "AI provider returned an invalid resume analysis"
        ) from error

def local_resume_analysis(text: str) -> ResumeAnalysisResponse:
    text_lower = text.lower()

    skill_patterns = {
        "Python": r"\bpython\b",
        "SQL": r"\bsql\b",
        "C++": r"\bc\+\+\b",
        "C#": r"\bc#\b",
        "Java": r"\bjava\b",
        "JavaScript": r"\bjavascript\b",
        "TypeScript": r"\btypescript\b",
        "React": r"\breact(?:\.js)?\b",
        "Node.js": r"\bnode(?:\.js)?\b",
        "FastAPI": r"\bfastapi\b",
        "Flask": r"\bflask\b",
        "Django": r"\bdjango\b",
        "Pandas": r"\bpandas\b",
        "NumPy": r"\bnumpy\b",
        "Scikit-learn": r"\bscikit[- ]learn\b",
        "TensorFlow": r"\btensorflow\b",
        "PyTorch": r"\bpytorch\b",
        "OpenCV": r"\bopencv\b",
        "Machine Learning": r"\bmachine learning\b",
        "Deep Learning": r"\bdeep learning\b",
        "Artificial Intelligence": r"\bartificial intelligence\b|\bai\b",
        "Git": r"\bgit\b",
        "GitHub": r"\bgithub\b",
        "Docker": r"\bdocker\b",
        "AWS": r"\baws\b",
        "Azure": r"\bazure\b",
        "Power BI": r"\bpower\s*bi\b",
        "Tableau": r"\btableau\b",
    }

    skills = [
        skill
        for skill, pattern in skill_patterns.items()
        if re.search(pattern, text_lower)
    ]

    name = ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        first_line = lines[0]
        if (
            len(first_line.split()) <= 5
            and not any(char.isdigit() for char in first_line)
            and "resume" not in first_line.lower()
            and "curriculum" not in first_line.lower()
        ):
            name = first_line

    target_role = ""

    role_patterns = {
        "Data Scientist": ["data scientist"],
        "AI Engineer": ["ai engineer", "artificial intelligence engineer"],
        "Machine Learning Engineer": ["machine learning engineer", "ml engineer"],
        "Software Engineer": ["software engineer", "software developer"],
        "Web Developer": ["web developer", "frontend developer", "backend developer"],
        "DevOps Engineer": ["devops engineer"],
        "Cybersecurity Analyst": ["cybersecurity analyst", "security analyst"],
        "Data Analyst": ["data analyst"],
    }

    for role, patterns in role_patterns.items():
        if any(pattern in text_lower for pattern in patterns):
            target_role = role
            break

    experience_years = 0

    experience_match = re.search(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)",
        text_lower,
    )

    if experience_match:
        try:
            experience_years = float(experience_match.group(1))
        except ValueError:
            experience_years = 0

    education = ""

    education_keywords = [
        "bachelor",
        "bs ",
        "b.s.",
        "master",
        "ms ",
        "m.s.",
        "phd",
        "computer science",
        "software engineering",
        "information technology",
    ]

    for line in lines:
        if any(keyword in line.lower() for keyword in education_keywords):
            education = line[:100]
            break

    return ResumeAnalysisResponse(
        name=name,
        education=education,
        experience_years=experience_years,
        skills=normalize_skills(skills),
        target_role=target_role,
    )


def generate_market_summary(
    target_role: str,
    jobs_analyzed: int,
    market_skills: list[dict],
    matched_skills: list[str],
    missing_skills: list[str],
    priority_skills: list[dict],
) -> str:
    system = """You are SkillBridge AI's market intelligence assistant. Summarize only the supplied deterministic market findings in two concise professional sentences. Do not invent or alter job counts, percentages, skills, companies, salaries, rankings, or other market statistics. Return only JSON:
{"market_summary":""}"""
    findings = {
        "target_role": target_role,
        "jobs_analyzed": jobs_analyzed,
        "market_skills": market_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "priority_skills": priority_skills,
    }
    try:
        response = MarketSummaryResponse.model_validate(
            chat_json(system, json.dumps(findings, ensure_ascii=False))
        )
        return response.market_summary
    except AIServiceError:
        raise
    except ValidationError as error:
        raise AIResponseError("AI provider returned an invalid market summary") from error


def extract_job_requirements(job_description: str) -> JobSkillExtraction:
    system = """You are SkillBridge AI's job-description skill extractor. Use only skills explicitly stated or clearly requested in the supplied job description. Do not infer technologies, responsibilities, credentials, or experience that are not stated. Return only a JSON object with this exact structure:
{"required_skills":[""],"preferred_skills":[""]}
Use concise canonical skill names such as "Python", "SQL", "Node.js", and "CI/CD". Put a skill in required_skills only when the job explicitly requires it. Put it in preferred_skills only when the job describes it as preferred, a plus, nice to have, or equivalent. Do not include duplicate skills or commentary."""

    try:
        payload = chat_json(system, f"Job description:\n{job_description}")
        return JobSkillExtraction.model_validate(payload)

    except AIProviderError as error:
        print("AI unavailable, using local job analysis:", error)
        return local_job_skill_extraction(job_description)

    except AIConfigurationError:
        raise

    except ValidationError as error:
        raise AIResponseError(
            "AI provider returned an invalid skill extraction"
        ) from error

def local_job_skill_extraction(job_description: str) -> JobSkillExtraction:
    text = job_description.lower()

    skills = {
        "Python": r"\bpython\b",
        "SQL": r"\bsql\b",
        "C++": r"\bc\+\+\b",
        "C#": r"\bc#\b",
        "Java": r"\bjava\b",
        "JavaScript": r"\bjavascript\b",
        "TypeScript": r"\btypescript\b",
        "React": r"\breact(?:\.js)?\b",
        "Node.js": r"\bnode(?:\.js)?\b",
        "FastAPI": r"\bfastapi\b",
        "Flask": r"\bflask\b",
        "Django": r"\bdjango\b",
        "Pandas": r"\bpandas\b",
        "NumPy": r"\bnumpy\b",
        "Scikit-learn": r"\bscikit[- ]learn\b",
        "TensorFlow": r"\btensorflow\b",
        "PyTorch": r"\bpytorch\b",
        "OpenCV": r"\bopencv\b",
        "Machine Learning": r"\bmachine learning\b",
        "Deep Learning": r"\bdeep learning\b",
        "Git": r"\bgit\b",
        "GitHub": r"\bgithub\b",
        "Docker": r"\bdocker\b",
        "AWS": r"\baws\b",
        "Azure": r"\bazure\b",
        "Power BI": r"\bpower\s*bi\b",
        "Tableau": r"\btableau\b",
        "REST API": r"\brest(?:ful)?\s*(?:api|apis)\b",
    }

    found = [
        skill for skill, pattern in skills.items()
        if re.search(pattern, text)
    ]

    preferred_markers = [
        "preferred",
        "nice to have",
        "nice-to-have",
        "plus",
        "bonus",
        "preferred skills",
    ]

    required = []
    preferred = []

    for skill in found:
        skill_lower = skill.lower()

        is_preferred = any(
            marker in text
            for marker in preferred_markers
        )

        if is_preferred:
            preferred.append(skill)
        else:
            required.append(skill)

    return JobSkillExtraction(
        required_skills=required,
        preferred_skills=preferred,
    )
