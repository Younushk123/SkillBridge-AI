import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

from backend import models
from backend.ai_service import (
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
    extract_job_requirements,
    extract_resume_profile,
    generate_interview_questions,
    generate_job_interview_questions,
    AIServiceError,
)
from backend.database import Base, SessionLocal, engine
from backend.job_analysis import build_job_analysis, _profile_interview_questions,detect_prompt_injection
from backend.schemas import InterviewQuestion
from backend.job_market import JobMarketProviderError
from backend.market_pipeline import build_market_analysis
from backend.recommendations import get_recommendations
from backend.resume_parser import extract_pdf_text
from backend.schemas import (
    JobAnalysisRequest,
    JobInterviewRequest,
    JobAnalysisResponse,
    MarketAnalysisResponse,
    ProfileResponse,
    ResumeAnalysisResponse,
    UserProfile,
    
)
from backend.skill_gap import calculate_skill_gap, get_all_role_skills

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)
app = FastAPI(title="SkillBridge AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
MAX_RESUME_BYTES = 5 * 1024 * 1024


@app.get("/")
def home():
    return {"message":"Welcome to SkillBridge AI"}

@app.get("/skills")
def get_available_skills():
    return {
        "skills": get_all_role_skills()
    }


@app.post("/resume/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(file: UploadFile = File(...)):
    if (
        not file.filename
        or not file.filename.lower().endswith(".pdf")
        or (file.content_type and file.content_type not in {"application/pdf", "application/octet-stream"})
    ):
        raise HTTPException(status_code=422, detail="Please upload a readable PDF resume")

    file_bytes = await file.read(MAX_RESUME_BYTES + 1)
    if not file_bytes:
        raise HTTPException(status_code=422, detail="Please upload a readable PDF resume")
    if len(file_bytes) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail="Resume file is too large")

    try:
        resume_text = extract_pdf_text(file_bytes)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Please upload a readable PDF resume") from error

    try:
        return extract_resume_profile(resume_text)
    except AIConfigurationError as error:
        raise HTTPException(status_code=503, detail="AI analysis is temporarily unavailable") from error
    except (AIProviderError, AIResponseError) as error:
        raise HTTPException(status_code=502, detail="Unable to analyze this resume") from error


@app.post("/profile",response_model=ProfileResponse)
def create_profile(profile:UserProfile, db: Session = Depends(get_db)):
    db_profile = models.Profile(
        name=profile.name,
        email=profile.email,
        education=profile.education,
        experience_years=profile.experience_years,
        skills=profile.skills,
        target_role=profile.target_role
    )
    db.add(db_profile)

    try:
        db.commit()
        db.refresh(db_profile)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A profile with this email already exists."
        )

    return db_profile

@app.get("/profile/{profile_id}", response_model = ProfileResponse)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    db_profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_profile

@app.get("/profile/{profile_id}/skill-gap")
def get_skill_gap(
        profile_id: int,
        db:Session = Depends(get_db)
):
    db_profile = db.query(models.Profile).filter(
        models.Profile.id == profile_id
        ).first()
    
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    current_skills = [skill.strip() for skill in (db_profile.skills or "").split(",") if skill.strip()]
    skill_gap = calculate_skill_gap(
    current_skills,
    db_profile.target_role
)

    if "error" in skill_gap:
        return {
            "profile_id": profile_id,
            "target_role": db_profile.target_role,
            "error": skill_gap["error"]
        }

    missing_skills = skill_gap["missing_skills"]

    recommendations = get_recommendations(missing_skills)

    return {
        "profile_id": profile_id,
        "target_role": db_profile.target_role,
        "missing_skills": missing_skills,
        "recommendations": recommendations
    }


@app.post("/profile/{profile_id}/job-analysis", response_model=JobAnalysisResponse)
def analyze_job_description(
    profile_id: int,
    request: JobAnalysisRequest,
    db: Session = Depends(get_db),
):
    db_profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()

    if db_profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    if detect_prompt_injection(request.job_description):
        raise HTTPException(
            status_code=400,
            detail="Job description contains suspicious instructions and cannot be analyzed.",
        )

    current_skills = [
        skill.strip()
        for skill in (db_profile.skills or "").split(",")
        if skill.strip()
    ]

    try:
        extraction = extract_job_requirements(request.job_description)
        analysis = build_job_analysis(
            current_skills,
            extraction,
            db_profile.target_role,
        )

    except AIConfigurationError as error:
        raise HTTPException(
            status_code=503,
            detail="AI analysis is temporarily unavailable",
        ) from error

    except (AIProviderError, AIResponseError) as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to analyze this job description",
        ) from error

    return JobAnalysisResponse(
        profile_id=profile_id,
        target_role=db_profile.target_role,
        **analysis,
    )


@app.get("/profile/{profile_id}/market-analysis", response_model=MarketAnalysisResponse)
def get_market_analysis(
    profile_id: int,
    db: Session = Depends(get_db),
):
    db_profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    
    try:
        analysis = build_market_analysis(db_profile.target_role)
    except JobMarketProviderError as error:
        raise HTTPException(
            status_code=502,
            detail="Live job-market data is temporarily unavailable",
        ) from error

    return MarketAnalysisResponse(**analysis)


@app.put("/profile/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int,
    profile: UserProfile,
    db:Session = Depends(get_db)
):
    db_profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    db_profile.name = profile.name
    db_profile.email = profile.email
    db_profile.education = profile.education
    db_profile.experience_years = profile.experience_years
    db_profile.skills = profile.skills
    db_profile.target_role = profile.target_role
    try:
        db.commit()
        db.refresh(db_profile)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A profile with this email already exists.",
        ) from error
    return db_profile

@app.delete("/profile/{profile_id}")
def delete_profile(
    profile_id: int,
    db:Session = Depends(get_db)
):
    db_profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(db_profile)
    db.commit()
    return {"message": "Profile deleted successfully"}

@app.get(
    "/profile/{profile_id}/interview",
    response_model=list[InterviewQuestion],
)
def get_profile_interview(
    profile_id: int,
    db: Session = Depends(get_db),
):
    db_profile = (
        db.query(models.Profile)
        .filter(models.Profile.id == profile_id)
        .first()
    )

    if db_profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    current_skills = (
        db_profile.skills.split(",")
        if db_profile.skills
        else []
    )

    current_skills = [
        skill.strip()
        for skill in current_skills
        if skill.strip()
    ]

    skill_gap = calculate_skill_gap(
        current_skills,
        db_profile.target_role,
    )

    if "error" in skill_gap:
        raise HTTPException(
            status_code=400,
            detail=skill_gap["error"],
        )

    missing_skills = skill_gap["missing_skills"]

    try:
        return generate_interview_questions(
            db_profile.target_role,
            current_skills,
            missing_skills,
    )
    except AIServiceError as error:
        print("Interview LLM failed:", error)

        return _profile_interview_questions(
            db_profile.target_role,
            current_skills,
            missing_skills,
        )


@app.post(
    "/profile/{profile_id}/job-interview",
    response_model=list[InterviewQuestion],
)
def get_job_interview(
    profile_id: int,
    request: JobInterviewRequest,
    db: Session = Depends(get_db),
):
    db_profile = (
        db.query(models.Profile)
        .filter(models.Profile.id == profile_id)
        .first()
    )

    if db_profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    try:
        return generate_job_interview_questions(
            db_profile.target_role,
            request.job_description,
        )
    except AIServiceError as error:
        print("Job interview LLM failed:", error)

        raise HTTPException(
            status_code=502,
            detail="Unable to generate job-specific interview questions",
        ) from error