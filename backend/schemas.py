from pydantic import BaseModel,ConfigDict,EmailStr, Field

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
    experience_years:int
    skills: str
    target_role: str

    model_config = ConfigDict(from_attributes=True)

    