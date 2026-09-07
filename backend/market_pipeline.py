
import re
from collections import Counter
from functools import lru_cache
from html import unescape

from backend.ai_service import AIServiceError, generate_market_summary
from backend.job_analysis import CANONICAL_SKILLS, normalize_skills
from backend.job_market import fetch_current_jobs


MARKET_SKILL_VARIANTS = {
    "Amazon Web Services": "AWS",
    "Continuous Integration Continuous Deployment": "CI/CD",
    "GCP": "Google Cloud Platform",
    "Google Cloud": "Google Cloud Platform",
    "NLP": "Natural Language Processing",
    "React JS": "React",
    "Structured Query Language": "SQL",
}


def _phrase_pattern(phrase: str, canonical_skill: str) -> re.Pattern[str]:
    if canonical_skill in {"C#", "C++"} and phrase == canonical_skill:
        expression = re.escape(phrase)
    else:
        terms = re.findall(r"[A-Za-z0-9]+", phrase)
        expression = r"[\s._/-]*".join(re.escape(term) for term in terms)
    flags = 0 if canonical_skill in {"C", "R"} and phrase == canonical_skill else re.IGNORECASE
    return re.compile(
        rf"(?<![A-Za-z0-9]){expression}(?![A-Za-z0-9])",
        flags,
    )


@lru_cache
def _market_skill_matchers() -> tuple[tuple[str, re.Pattern[str]], ...]:
    phrases = [(skill, skill) for skill in set(CANONICAL_SKILLS.values())]
    phrases.extend(MARKET_SKILL_VARIANTS.items())
    matchers = []
    seen = set()
    for phrase, skill in phrases:
        normalized = normalize_skills([skill])
        if not normalized:
            continue
        canonical_skill = normalized[0]
        key = (phrase.casefold(), canonical_skill.casefold())
        if key in seen:
            continue
        seen.add(key)
        matchers.append((canonical_skill, _phrase_pattern(phrase, canonical_skill)))
    return tuple(
        sorted(
            matchers,
            key=lambda item: (-len(item[0]), item[0].casefold()),
        )
    )


def _job_description(job: dict) -> str:
    for field in ("description", "descriptionHtml", "excerpt"):
        value = job.get(field)
        if isinstance(value, str):
            text = " ".join(unescape(re.sub(r"<[^>]+>", " ", value)).split())
            if text:
                return text
    return ""


def extract_market_skills(description: str) -> list[str]:
    occupied = [False] * len(description)
    skills = []
    for skill, pattern in _market_skill_matchers():
        for match in pattern.finditer(description):
            start, end = match.span()
            if any(occupied[start:end]):
                continue
            for position in range(start, end):
                occupied[position] = True
            skills.append(skill)
    return normalize_skills(skills)


def _fallback_summary(target_role: str, jobs_analyzed: int, market_skills: list[dict]) -> str:
    if not jobs_analyzed:
        return f"No recent job descriptions were available for {target_role}, so market demand cannot be calculated yet."
    if not market_skills:
        return f"Recent job descriptions were available for {target_role}, but no supported skills were identified for market comparison."
    return f"Market demand was calculated from {jobs_analyzed} recent job descriptions. Review the ranked missing skills to focus your preparation."


def build_market_aware_analysis(target_role: str, current_skills: list[str]) -> dict:
    jobs = fetch_current_jobs(target_role)
    descriptions = [
        description
        for job in jobs
        if (description := _job_description(job))
    ]
    jobs_analyzed = len(descriptions)
    demand_counts = Counter()
    for description in descriptions:
        demand_counts.update(extract_market_skills(description))

    market_skills = [
        {
            "skill": skill,
            "demand_count": demand_count,
            "demand_percentage": round(100 * demand_count / jobs_analyzed, 1),
        }
        for skill, demand_count in sorted(
            demand_counts.items(),
            key=lambda item: (-item[1], item[0].casefold()),
        )
    ]
    current_skill_keys = {skill.casefold() for skill in normalize_skills(current_skills)}
    matched_skill_details = [
        item for item in market_skills if item["skill"].casefold() in current_skill_keys
    ]
    missing_skill_details = [
        item for item in market_skills if item["skill"].casefold() not in current_skill_keys
    ]
    matched_skills = [item["skill"] for item in matched_skill_details]
    missing_skills = [item["skill"] for item in missing_skill_details]
    priority_skills = missing_skill_details[:5]
    fallback_summary = _fallback_summary(target_role, jobs_analyzed, market_skills)

    if market_skills:
        try:
            market_summary = generate_market_summary(
                target_role,
                jobs_analyzed,
                market_skills,
                matched_skills,
                missing_skills,
                priority_skills,
            )
        except AIServiceError:
            market_summary = fallback_summary
    else:
        market_summary = fallback_summary

    return {
        "target_role": target_role,
        "jobs_analyzed": jobs_analyzed,
        "market_skills": market_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "priority_skills": priority_skills,
        "market_summary": market_summary,
    }
