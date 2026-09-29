
from backend.market_pipeline import extract_market_skills

def test_market_skill_extraction():
    text = "Python, PyTorch, AWS and FastAPI are used in this role."
    skills = extract_market_skills(text)
    assert "Python" in skills
    assert "PyTorch" in skills
    assert "AWS" in skills
    assert "FastAPI" in skills
