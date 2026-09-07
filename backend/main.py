from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from backend import models
from backend.ai_service import (
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
    extract_job_requirements,
    extract_resume_profile,
)
from backend.database import Base, SessionLocal, engine
from backend.job_analysis import build_job_analysis
from backend.job_market import JobMarketProviderError
from backend.market_pipeline import build_market_aware_analysis
from backend.recommendations import get_recommendations
from backend.resume_parser import extract_pdf_text
from backend.schemas import (
    JobAnalysisRequest,
    JobAnalysisResponse,
    MarketAnalysisResponse,
    ProfileResponse,
    ResumeAnalysisResponse,
    UserProfile,
)
from backend.skill_gap import calculate_skill_gap

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)
app = FastAPI(title="SkillBridge AI")
MAX_RESUME_BYTES = 5 * 1024 * 1024


@app.get("/")
def home():
    return {"message":"Welcome to SkillBridge AI"}


@app.post("/resume/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(file: UploadFile = File(...)):
    if (
        not file.filename
        or not file.filename.lower().endswith(".pdf")
        or file.content_type != "application/pdf"
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
    
    current_skills = [skill.strip() for skill in db_profile.skills.split(",")]
    missing_skills = calculate_skill_gap(
        current_skills,
        db_profile.target_role
    )
    if isinstance(missing_skills, dict):
        return {
            "profile_id": profile_id,
            "target_role": db_profile.target_role,
            "error": missing_skills["error"]
        }
    recommendations = get_recommendations(list(missing_skills))
    return {
        "profile_id": profile_id,
        "target_role": db_profile.target_role,
        "missing_skills": list(missing_skills),
        "recommendations": recommendations}


@app.post("/profile/{profile_id}/job-analysis", response_model=JobAnalysisResponse)
def analyze_job_description(
    profile_id: int,
    request: JobAnalysisRequest,
    db: Session = Depends(get_db),
):
    db_profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    current_skills = [
        skill.strip() for skill in (db_profile.skills or "").split(",") if skill.strip()
    ]
    try:
        extraction = extract_job_requirements(request.job_description)
        analysis = build_job_analysis(current_skills, extraction, db_profile.target_role)
    except AIConfigurationError as error:
        raise HTTPException(status_code=503, detail="AI analysis is temporarily unavailable") from error
    except (AIProviderError, AIResponseError) as error:
        raise HTTPException(status_code=502, detail="Unable to analyze this job description") from error

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

    current_skills = [
        skill.strip() for skill in (db_profile.skills or "").split(",") if skill.strip()
    ]
    try:
        analysis = build_market_aware_analysis(db_profile.target_role, current_skills)
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
    db.commit()
    db.refresh(db_profile)
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
