import asyncio
from io import BytesIO
import unittest
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from pydantic import ValidationError
from starlette.datastructures import Headers

from backend.ai_service import (
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
    extract_resume_profile,
)
from backend.main import MAX_RESUME_BYTES, analyze_resume, app
from backend.schemas import ResumeAnalysisResponse, UserProfile


def resume_upload(filename="resume.pdf", content=b"%PDF-1.4", content_type="application/pdf"):
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers=Headers({"content-type": content_type}),
    )


class ResumeAnalysisTests(unittest.TestCase):
    def analyze(self, upload):
        return asyncio.run(analyze_resume(upload))

    def extract(self, payload):
        with patch("backend.ai_service.chat_json", return_value=payload):
            return extract_resume_profile("Resume text")

    def test_resume_route_is_registered_without_affecting_existing_routes(self):
        routes = {route.path for route in app.routes}

        self.assertIn("/resume/analyze", routes)
        self.assertIn("/profile/{profile_id}/skill-gap", routes)
        self.assertIn("/profile/{profile_id}/job-analysis", routes)

    def test_resume_with_only_name_and_experience_uses_defaults(self):
        profile = self.extract({"name": "Ayesha Khan", "experience_years": 2})

        self.assertEqual(profile.name, "Ayesha Khan")
        self.assertEqual(profile.experience_years, 2)
        self.assertEqual(profile.education, "")
        self.assertEqual(profile.skills, [])
        self.assertEqual(profile.target_role, "")

    def test_missing_education_uses_empty_default(self):
        profile = self.extract(
            {
                "name": "Ayesha Khan",
                "education": None,
                "experience_years": 2,
                "skills": ["Python"],
                "target_role": "AI Engineer",
            }
        )

        self.assertEqual(profile.education, "")

    def test_missing_skills_use_empty_default(self):
        profile = self.extract(
            {
                "name": "Ayesha Khan",
                "education": "BS Computer Science",
                "experience_years": 2,
                "skills": None,
                "target_role": "AI Engineer",
            }
        )

        self.assertEqual(profile.skills, [])

    def test_missing_target_role_uses_empty_default(self):
        profile = self.extract(
            {
                "name": "Ayesha Khan",
                "education": "BS Computer Science",
                "experience_years": 2,
                "skills": ["Python"],
                "target_role": None,
            }
        )

        self.assertEqual(profile.target_role, "")

    def test_arbitrary_target_role_is_preserved(self):
        profile = self.extract(
            {
                "name": "Ayesha Khan",
                "education": "BS Computer Science",
                "experience_years": 8,
                "skills": ["AWS", "Docker"],
                "target_role": "Lead Cloud Engineer",
            }
        )

        self.assertEqual(profile.target_role, "Lead Cloud Engineer")

    def test_complete_resume_extraction_normalizes_skills(self):
        profile = self.extract(
            {
                "name": "Ayesha Khan",
                "education": "BS Computer Science",
                "experience_years": 2,
                "skills": ["python", "Node.js", "nodejs", "NLP"],
                "target_role": "AI Engineer",
            }
        )

        self.assertEqual(profile.name, "Ayesha Khan")
        self.assertEqual(profile.education, "BS Computer Science")
        self.assertEqual(profile.experience_years, 2)
        self.assertEqual(
            profile.skills,
            ["Python", "Node.js", "Natural Language Processing"],
        )
        self.assertEqual(profile.target_role, "AI Engineer")

    def test_malformed_resume_extraction_is_rejected(self):
        payload = {
            "name": "Ayesha Khan",
            "education": "BS Computer Science",
            "experience_years": "2",
            "skills": "Python",
            "target_role": "AI Engineer",
        }

        with patch("backend.ai_service.chat_json", return_value=payload):
            with self.assertRaises(AIResponseError):
                extract_resume_profile("Ayesha has Python experience.")

    def test_resume_extraction_rejects_unknown_qwen_fields(self):
        payload = {
            "name": "Ayesha Khan",
            "education": "BS Computer Science",
            "experience_years": 2,
            "skills": ["Python"],
            "target_role": "AI Engineer",
            "email": "ayesha@example.com",
        }

        with patch("backend.ai_service.chat_json", return_value=payload):
            with self.assertRaises(AIResponseError):
                extract_resume_profile("Ayesha has Python experience.")

    def test_profile_validation_still_requires_missing_profile_fields(self):
        with self.assertRaises(ValidationError):
            UserProfile(
                name="Ayesha Khan",
                email="ayesha@example.com",
                education="",
                experience_years=2,
                skills="",
                target_role="",
            )

    def test_valid_pdf_returns_structured_profile_without_database_access(self):
        profile = ResumeAnalysisResponse(
            name="Ayesha Khan",
            education="BS Computer Science",
            experience_years=2,
            skills=["Python", "SQL"],
            target_role="Data Scientist",
        )
        with (
            patch("backend.main.SessionLocal", side_effect=AssertionError("database access")),
            patch("backend.main.extract_pdf_text", return_value="Resume text"),
            patch("backend.main.extract_resume_profile", return_value=profile),
        ):
            response = self.analyze(resume_upload())

        self.assertEqual(response, profile)

    def test_non_pdf_upload_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            self.analyze(resume_upload("resume.txt", b"resume", "text/plain"))

        self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(error.exception.detail, "Please upload a readable PDF resume")

    def test_oversized_pdf_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            self.analyze(resume_upload(content=b"x" * (MAX_RESUME_BYTES + 1)))

        self.assertEqual(error.exception.status_code, 413)
        self.assertEqual(error.exception.detail, "Resume file is too large")

    def test_unreadable_pdf_returns_safe_error(self):
        with patch("backend.main.extract_pdf_text", side_effect=ValueError("parser detail")):
            with self.assertRaises(HTTPException) as error:
                self.analyze(resume_upload())

        self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(error.exception.detail, "Please upload a readable PDF resume")

    def test_unavailable_ai_configuration_returns_safe_error(self):
        with (
            patch("backend.main.extract_pdf_text", return_value="Resume text"),
            patch(
                "backend.main.extract_resume_profile",
                side_effect=AIConfigurationError("missing key"),
            ),
        ):
            with self.assertRaises(HTTPException) as error:
                self.analyze(resume_upload())

        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(error.exception.detail, "AI analysis is temporarily unavailable")

    def test_ai_provider_failure_returns_safe_error(self):
        with (
            patch("backend.main.extract_pdf_text", return_value="Resume text"),
            patch(
                "backend.main.extract_resume_profile",
                side_effect=AIProviderError("timeout"),
            ),
        ):
            with self.assertRaises(HTTPException) as error:
                self.analyze(resume_upload())

        self.assertEqual(error.exception.status_code, 502)
        self.assertEqual(error.exception.detail, "Unable to analyze this resume")


if __name__ == "__main__":
    unittest.main()
