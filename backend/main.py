from backend.database import Base, engine, SessionLocal
from backend.schemas import UserProfile, ProfileResponse
from backend.skill_gap import calculate_skill_gap
from backend.recommendations import get_recommendations
from sqlalchemy.exc import IntegrityError
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import models

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)
app = FastAPI(title="SkillBridge AI")

@app.get("/")
def home():
    return {"message":"Welcome to SkillBridge AI"}

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
