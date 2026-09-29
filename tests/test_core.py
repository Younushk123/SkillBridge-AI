
from fastapi.testclient import TestClient
from backend.main import app
from backend.ai_service import local_job_skill_extraction, local_resume_analysis
from backend.database import SessionLocal
from backend.models import Profile

client = TestClient(app)


def profile_payload(email="test@example.com", skills=None):
    return {
        "name": "Test User",
        "email": email,
        "education": "BS Computer Science",
        "experience_years": 0,
        "skills": skills or ["Python", "SQL"],
        "target_role": "AI Engineer",
    }

def cleanup_test_profiles():
    db = SessionLocal()

    try:
        db.query(Profile).filter(
            Profile.email.in_([
                "list@example.com",
                "gap@example.com",
            ])
        ).delete(synchronize_session=False)

        db.commit()

    finally:
        db.close()


def test_profile_accepts_skill_list():
    cleanup_test_profiles()

    response = client.post("/profile", json=profile_payload("list@example.com"))
    assert response.status_code == 200
    assert response.json()["skills"] == "Python, SQL"


def test_skill_gap():
    cleanup_test_profiles()

    response = client.post("/profile", json=profile_payload("gap@example.com"))
    assert response.status_code == 200
    profile_id = response.json()["id"]

    gap = client.get(f"/profile/{profile_id}/skill-gap")
    assert gap.status_code == 200
    assert "PyTorch" in gap.json()["missing_skills"]


def test_job_fallback_separates_required_and_preferred():
    extraction = local_job_skill_extraction(
        "We require Python and SQL. PyTorch is preferred. Git is a plus."
    )
    assert extraction.required_skills == ["Python", "SQL"]
    assert extraction.preferred_skills == ["PyTorch", "Git"]


def test_resume_fallback_returns_valid_profile():
    result = local_resume_analysis(
        "Test User\nBS Computer Science\nPython SQL Machine Learning\n2 years experience"
    )
    assert result.name == "Test User"
    assert result.experience_years == 2
    assert "Python" in result.skills
