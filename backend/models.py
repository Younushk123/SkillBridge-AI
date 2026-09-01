from backend.database import Base
from sqlalchemy import Column,Integer,String

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer,
                primary_key=True,
                index=True
                )
    name = Column(String,nullable=False)
    email = Column(String,
                   nullable=False,
                   unique=True,
                   index=True
                   )
    education = Column(String, nullable=True)
    experience_years = Column(Integer, nullable=True)
    skills = Column(String, nullable=True)
    target_role = Column(String, nullable=True)
    
    