import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.ai_service import AIConfigurationError, AIProviderError, AIResponseError, extract_job_requirements
from backend.database import Base
from backend.job_analysis import build_job_analysis
from backend.main import analyze_job_description, app, get_skill_gap
from backend.schemas import JobAnalysisRequest, JobSkillExtraction


TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


class JobAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=TEST_ENGINE)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=TEST_ENGINE)

    def setUp(self):
        db = TestingSessionLocal()
        db.query(models.Profile).delete()
        db.commit()
        db.close()

    def create_profile(self, skills="Python, Docker"):
        db = TestingSessionLocal()
        profile = models.Profile(
            name="Ayesha Khan",
            email="ayesha@example.com",
            education="Computer Science",
            experience_years=2,
            skills=skills,
            target_role="Data Scientist",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        profile_id = profile.id
        db.close()
        return profile_id

    def request(self):
        return JobAnalysisRequest(
            job_description="We require Python and SQL. Docker experience is a preferred qualification."
        )

    @patch("backend.main.extract_job_requirements")
    def test_job_analysis_returns_deterministic_score(self, mock_extractor):
        profile_id = self.create_profile()
        mock_extractor.return_value = JobSkillExtraction(
            required_skills=["python", "SQL", "Python"],
            preferred_skills=["Docker", "sql"],
        )
        db = TestingSessionLocal()

        response = analyze_job_description(profile_id, self.request(), db)
        payload = response.model_dump()
        db.close()

        self.assertEqual(payload["required_skills"], ["Python", "SQL"])
        self.assertEqual(payload["preferred_skills"], ["Docker"])
        self.assertEqual(payload["matched_skills"], ["Python", "Docker"])
        self.assertEqual(payload["missing_skills"], ["SQL"])
        self.assertEqual(payload["match_score"], 50)
        self.assertEqual(payload["learning_priorities"][0]["skill"], "SQL")
        self.assertEqual(payload["learning_priorities"][0]["priority"], "High")
        self.assertTrue(payload["roadmap"])
        self.assertTrue(payload["interview_questions"])

    def test_zero_required_skills_has_safe_score(self):
        analysis = build_job_analysis(
            ["Python"],
            JobSkillExtraction(required_skills=[], preferred_skills=["Docker"]),
            "Data Scientist",
        )

        self.assertEqual(analysis["match_score"], 0)
        self.assertEqual(analysis["missing_skills"], ["Docker"])
        self.assertEqual(analysis["learning_priorities"][0].priority, "Medium")

    def test_skill_aliases_normalize_before_matching(self):
        analysis = build_job_analysis(
            ["nodejs", "NLP"],
            JobSkillExtraction(
                required_skills=["Node.js", "Natural Language Processing"],
                preferred_skills=[],
            ),
            "AI Engineer",
        )

        self.assertEqual(analysis["required_skills"], ["Node.js", "Natural Language Processing"])
        self.assertEqual(analysis["match_score"], 100)

    def test_job_analysis_route_is_registered(self):
        self.assertTrue(
            any(
                route.path == "/profile/{profile_id}/job-analysis" and "POST" in route.methods
                for route in app.routes
            )
        )

    def test_job_analysis_requires_existing_profile(self):
        db = TestingSessionLocal()
        with self.assertRaises(HTTPException) as error:
            analyze_job_description(999, self.request(), db)
        db.close()

        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(error.exception.detail, "Profile not found")

    def test_job_analysis_rejects_empty_and_oversized_descriptions(self):
        with self.assertRaises(ValidationError):
            JobAnalysisRequest(job_description="")
        with self.assertRaises(ValidationError):
            JobAnalysisRequest(job_description="x" * 30001)

    @patch("backend.main.extract_job_requirements", side_effect=AIResponseError("invalid"))
    def test_malformed_ai_output_returns_safe_error(self, _mock_extractor):
        profile_id = self.create_profile()
        db = TestingSessionLocal()
        with self.assertRaises(HTTPException) as error:
            analyze_job_description(profile_id, self.request(), db)
        db.close()

        self.assertEqual(error.exception.status_code, 502)
        self.assertEqual(error.exception.detail, "Unable to analyze this job description")

    @patch("backend.main.extract_job_requirements", side_effect=AIConfigurationError("missing key"))
    def test_unavailable_ai_configuration_returns_safe_error(self, _mock_extractor):
        profile_id = self.create_profile()
        db = TestingSessionLocal()
        with self.assertRaises(HTTPException) as error:
            analyze_job_description(profile_id, self.request(), db)
        db.close()

        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(error.exception.detail, "AI analysis is temporarily unavailable")

    @patch("backend.main.extract_job_requirements", side_effect=AIProviderError("timeout"))
    def test_ai_provider_failure_returns_safe_error(self, _mock_extractor):
        profile_id = self.create_profile()
        db = TestingSessionLocal()
        with self.assertRaises(HTTPException) as error:
            analyze_job_description(profile_id, self.request(), db)
        db.close()

        self.assertEqual(error.exception.status_code, 502)
        self.assertEqual(error.exception.detail, "Unable to analyze this job description")

    def test_malformed_provider_extraction_is_rejected(self):
        with patch("backend.ai_service.chat_json", return_value={"required_skills": "Python"}):
            with self.assertRaises(AIResponseError):
                extract_job_requirements(self.request().job_description)

    def test_existing_skill_gap_route_still_works(self):
        profile_id = self.create_profile(skills="Python, SQL")
        db = TestingSessionLocal()
        payload = get_skill_gap(profile_id, db)
        db.close()

        self.assertEqual(payload["target_role"], "Data Scientist")
        self.assertIn("Pandas", payload["missing_skills"])
        self.assertIn("Learn Pandas for data manipulation and analysis", payload["recommendations"])


if __name__ == "__main__":
    unittest.main()
