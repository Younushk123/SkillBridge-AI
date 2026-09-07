import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError
from requests import RequestException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.ai_service import (
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
    generate_market_summary,
)
from backend.database import Base
from backend.job_market import JobMarketProviderError, URL, fetch_current_jobs
from backend.main import app, get_market_analysis
from backend.market_pipeline import build_market_aware_analysis, extract_market_skills
from backend.schemas import MarketAnalysisResponse, MarketSkillDemand


TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


class MarketAnalysisTests(unittest.TestCase):
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

    def create_profile(self, skills="Python, AWS, nodejs", target_role="Data Scientist"):
        db = TestingSessionLocal()
        profile = models.Profile(
            name="Ayesha Khan",
            email="ayesha@example.com",
            education="Computer Science",
            experience_years=2,
            skills=skills,
            target_role=target_role,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        profile_id = profile.id
        db.close()
        return profile_id

    @staticmethod
    def jobs():
        return [
            {"description": "Python and SQL are required. Docker experience is helpful."},
            {"descriptionHtml": "<p>Python, Node.js, and C++ are required.</p>"},
            {"excerpt": "SQL and AWS experience are required."},
        ]

    @staticmethod
    def market_payload(target_role="Data Scientist"):
        return {
            "target_role": target_role,
            "jobs_analyzed": 1,
            "market_skills": [
                {"skill": "Python", "demand_count": 1, "demand_percentage": 100.0}
            ],
            "matched_skills": ["Python"],
            "missing_skills": [],
            "priority_skills": [],
            "market_summary": "Python is currently demanded in the supplied listings.",
        }

    def test_fetch_current_jobs_uses_himalayas_and_filters_invalid_entries(self):
        response = Mock()
        response.json.return_value = {"jobs": [{"description": "Python"}, "invalid"]}
        with patch("backend.job_market.requests.get", return_value=response) as mock_get:
            jobs = fetch_current_jobs("Lead Cloud Engineer")

        self.assertEqual(jobs, [{"description": "Python"}])
        mock_get.assert_called_once_with(
            URL,
            params={"q": "Lead Cloud Engineer", "sort": "recent", "page": 1},
            timeout=20,
        )

    def test_fetch_current_jobs_wraps_provider_failures(self):
        with patch(
            "backend.job_market.requests.get",
            side_effect=RequestException("network detail"),
        ):
            with self.assertRaises(JobMarketProviderError):
                fetch_current_jobs("Data Scientist")

    def test_fetch_current_jobs_rejects_malformed_payloads(self):
        response = Mock()
        response.json.return_value = {"unexpected": []}
        with patch("backend.job_market.requests.get", return_value=response):
            with self.assertRaises(JobMarketProviderError):
                fetch_current_jobs("Data Scientist")

    def test_market_analysis_counts_normalized_skills_deterministically(self):
        with (
            patch("backend.market_pipeline.fetch_current_jobs", return_value=self.jobs()),
            patch(
                "backend.market_pipeline.generate_market_summary",
                return_value="The supplied listings emphasize Python and SQL.",
            ) as mock_summary,
        ):
            analysis = build_market_aware_analysis(
                "Data Scientist",
                ["python", "AWS", "nodejs"],
            )

        self.assertEqual(analysis["jobs_analyzed"], 3)
        self.assertEqual(
            analysis["market_skills"],
            [
                {"skill": "Python", "demand_count": 2, "demand_percentage": 66.7},
                {"skill": "SQL", "demand_count": 2, "demand_percentage": 66.7},
                {"skill": "AWS", "demand_count": 1, "demand_percentage": 33.3},
                {"skill": "C++", "demand_count": 1, "demand_percentage": 33.3},
                {"skill": "Docker", "demand_count": 1, "demand_percentage": 33.3},
                {"skill": "Node.js", "demand_count": 1, "demand_percentage": 33.3},
            ],
        )
        self.assertEqual(analysis["matched_skills"], ["Python", "AWS", "Node.js"])
        self.assertEqual(analysis["missing_skills"], ["SQL", "C++", "Docker"])
        self.assertEqual(
            analysis["priority_skills"],
            [
                {"skill": "SQL", "demand_count": 2, "demand_percentage": 66.7},
                {"skill": "C++", "demand_count": 1, "demand_percentage": 33.3},
                {"skill": "Docker", "demand_count": 1, "demand_percentage": 33.3},
            ],
        )
        self.assertEqual(mock_summary.call_args.args[0], "Data Scientist")
        self.assertEqual(mock_summary.call_args.args[1], 3)
        self.assertEqual(mock_summary.call_args.args[2], analysis["market_skills"])
        self.assertNotIn("description", str(mock_summary.call_args.args))

    def test_skill_extraction_normalizes_aliases_and_avoids_overlaps(self):
        skills = extract_market_skills("PYTHON, python, Node JS, NLP, C++, and C.")

        self.assertEqual(
            set(skills),
            {"Python", "Node.js", "Natural Language Processing", "C++", "C"},
        )
        self.assertEqual(extract_market_skills("C++ development"), ["C++"])

    def test_each_skill_counts_once_per_job(self):
        jobs = [{"description": "Python, python, and PYTHON are all mentioned."}]
        with (
            patch("backend.market_pipeline.fetch_current_jobs", return_value=jobs),
            patch(
                "backend.market_pipeline.generate_market_summary",
                return_value="Python appears in the supplied listing.",
            ),
        ):
            analysis = build_market_aware_analysis("Data Scientist", [])

        self.assertEqual(
            analysis["market_skills"],
            [{"skill": "Python", "demand_count": 1, "demand_percentage": 100.0}],
        )

    def test_empty_market_returns_valid_analysis_without_ai(self):
        with (
            patch("backend.market_pipeline.fetch_current_jobs", return_value=[]),
            patch("backend.market_pipeline.generate_market_summary") as mock_summary,
        ):
            analysis = build_market_aware_analysis("Lead Cloud Engineer", ["AWS"])

        self.assertEqual(analysis["target_role"], "Lead Cloud Engineer")
        self.assertEqual(analysis["jobs_analyzed"], 0)
        self.assertEqual(analysis["market_skills"], [])
        self.assertEqual(analysis["matched_skills"], [])
        self.assertEqual(analysis["missing_skills"], [])
        self.assertEqual(analysis["priority_skills"], [])
        self.assertIn("No recent job descriptions", analysis["market_summary"])
        mock_summary.assert_not_called()

    def test_invalid_job_descriptions_are_skipped(self):
        jobs = [
            {"description": None},
            {"description": ["Python"]},
            {"descriptionHtml": "<p> </p>"},
        ]
        with (
            patch("backend.market_pipeline.fetch_current_jobs", return_value=jobs),
            patch("backend.market_pipeline.generate_market_summary") as mock_summary,
        ):
            analysis = build_market_aware_analysis("Data Scientist", [])

        self.assertEqual(analysis["jobs_analyzed"], 0)
        self.assertEqual(analysis["market_skills"], [])
        mock_summary.assert_not_called()

    def test_priority_skills_are_ranked_by_demand_and_limited(self):
        jobs = [
            {"description": "Python SQL Docker AWS Kubernetes Java C++"},
            {"description": "Python SQL Docker AWS Kubernetes Java"},
            {"description": "Python SQL Docker AWS Kubernetes"},
            {"description": "Python SQL Docker AWS"},
            {"description": "Python SQL Docker"},
            {"description": "Python SQL"},
        ]
        with (
            patch("backend.market_pipeline.fetch_current_jobs", return_value=jobs),
            patch(
                "backend.market_pipeline.generate_market_summary",
                return_value="The supplied listings show consistent skill demand.",
            ),
        ):
            analysis = build_market_aware_analysis("Data Scientist", [])

        self.assertEqual(
            [item["skill"] for item in analysis["priority_skills"]],
            ["Python", "SQL", "Docker", "AWS", "Kubernetes"],
        )

    def test_ai_summary_is_validated_and_receives_only_aggregates(self):
        with patch(
            "backend.ai_service.chat_json",
            return_value={"market_summary": "Python is the strongest supplied demand signal."},
        ) as mock_chat:
            summary = generate_market_summary(
                "Data Scientist",
                3,
                [{"skill": "Python", "demand_count": 2, "demand_percentage": 66.7}],
                ["Python"],
                ["SQL"],
                [{"skill": "SQL", "demand_count": 2, "demand_percentage": 66.7}],
            )

        self.assertEqual(summary, "Python is the strongest supplied demand signal.")
        self.assertNotIn("description", mock_chat.call_args.args[1])

    def test_ai_summary_failure_uses_deterministic_fallback(self):
        for error in (
            AIConfigurationError("missing key"),
            AIProviderError("timeout"),
            AIResponseError("invalid response"),
        ):
            with self.subTest(error=type(error).__name__):
                with (
                    patch("backend.market_pipeline.fetch_current_jobs", return_value=self.jobs()),
                    patch("backend.market_pipeline.generate_market_summary", side_effect=error),
                ):
                    analysis = build_market_aware_analysis("Data Scientist", ["Python"])

                self.assertEqual(analysis["market_skills"][0]["skill"], "Python")
                self.assertIn("Market demand was calculated", analysis["market_summary"])

    def test_market_endpoint_is_registered(self):
        self.assertTrue(
            any(
                route.path == "/profile/{profile_id}/market-analysis" and "GET" in route.methods
                for route in app.routes
            )
        )

    def test_market_endpoint_requires_existing_profile(self):
        db = TestingSessionLocal()
        with self.assertRaises(HTTPException) as error:
            get_market_analysis(999, db)
        db.close()

        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(error.exception.detail, "Profile not found")

    def test_market_endpoint_uses_persisted_arbitrary_role(self):
        profile_id = self.create_profile(target_role="Lead Cloud Engineer")
        db = TestingSessionLocal()
        with patch(
            "backend.main.build_market_aware_analysis",
            return_value=self.market_payload("Lead Cloud Engineer"),
        ) as mock_analysis:
            response = get_market_analysis(profile_id, db)
        db.close()

        self.assertEqual(response.target_role, "Lead Cloud Engineer")
        mock_analysis.assert_called_once_with(
            "Lead Cloud Engineer",
            ["Python", "AWS", "nodejs"],
        )

    def test_market_endpoint_maps_provider_errors_safely(self):
        profile_id = self.create_profile()
        db = TestingSessionLocal()
        with patch(
            "backend.main.build_market_aware_analysis",
            side_effect=JobMarketProviderError("provider details"),
        ):
            with self.assertRaises(HTTPException) as error:
                get_market_analysis(profile_id, db)
        db.close()

        self.assertEqual(error.exception.status_code, 502)
        self.assertEqual(
            error.exception.detail,
            "Live job-market data is temporarily unavailable",
        )

    def test_market_response_schema_is_strict(self):
        with self.assertRaises(ValidationError):
            MarketSkillDemand(
                skill="Python",
                demand_count="1",
                demand_percentage=100.0,
            )
        with self.assertRaises(ValidationError):
            MarketAnalysisResponse(
                **self.market_payload(),
                extra_field="not allowed",
            )


if __name__ == "__main__":
    unittest.main()
