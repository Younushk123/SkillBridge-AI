# SkillBridge AI

## AI-Powered Career Intelligence

SkillBridge AI is an intelligent career development platform that bridges the gap between a candidate's current skills and real-world job requirements.

Instead of providing generic career advice, SkillBridge AI analyzes a user's resume, identifies skill gaps, analyzes available job-market demand, matches the candidate against specific job descriptions, and generates a personalized learning roadmap and interview preparation plan.

---

## The Problem

Students and early-career professionals often struggle to determine:

* Which skills they already have
* Which skills they are missing
* Which skills employers currently demand
* How well they match a specific job
* What they should learn next
* How to prepare for relevant interviews

Traditional career guidance is often generic and disconnected from changing employer requirements.

SkillBridge AI addresses this problem by connecting an individual's skills with real-world job requirements and market demand.

---

## The Solution

SkillBridge AI provides an end-to-end career intelligence workflow:

```text
Resume / Profile
       ↓
Profile & Skill Extraction
       ↓
Skill Gap Analysis
       ↓
Job-Market Analysis
       ↓
Job Description Matching
       ↓
Personalized Learning Roadmap
       ↓
Interview Preparation
```

The goal is to turn career uncertainty into a clear, actionable path.

---

## Key Features

### 1. Resume Intelligence

Users can upload a text-based PDF resume.

The system extracts relevant profile information including:

* Name
* Education
* Experience
* Technical skills
* Career-related information

The extracted profile can be reviewed before continuing with career analysis.

---

### 2. Personalized Skill Gap Analysis

SkillBridge AI compares the user's current skills with the requirements of their selected target role.

Example:

```text
Target Role: AI Engineer

Current Skills:
Python
Machine Learning
Scikit-learn
Docker

Missing Skills:
TensorFlow
PyTorch
Deep Learning
```

The system then generates recommendations for the identified gaps.

---

### 3. Job-Market Analysis

A key feature of SkillBridge AI is market-aware career analysis.

The platform analyzes available job-market data for a target role and identifies skills appearing across relevant job descriptions.

The analysis provides:

* Number of jobs analyzed
* Top in-demand skills
* User's market matches
* Market skill gaps
* Priority skills

Example:

```text
AI Engineer Market

Jobs Analyzed: 8

Top Skills:
AWS
Kubernetes
Azure
Docker
Python
```

The user's existing skills are compared against these market requirements so they can prioritize the most relevant skills.

---

### 4. Job Description Matching

Users can either:

* Describe the role they are targeting, or
* Paste a specific job description

SkillBridge AI analyzes the input and provides:

* Match score
* Required skills
* Preferred skills
* Matched skills
* Missing skills
* Learning priorities
* Job-specific preparation guidance

Example:

```text
Match Score: 55%

Matched:
Python
SQL
Pandas
Scikit-learn
Machine Learning
Git

Missing:
Java
JavaScript
PyTorch
AWS
Azure
```

This turns a job description into an actionable preparation plan.

---

### 5. Personalized Learning Roadmap

SkillBridge AI converts identified skill gaps into a structured learning roadmap.

The roadmap includes:

* Learning priorities
* Time-based stages
* Skills to focus on
* Practical learning actions

Example:

```text
Weeks 1–2

Close Required Skill Gaps

Focus:
Java
JavaScript
PyTorch

Week 4

Prepare Job Evidence

Focus:
Python
SQL
Pandas
```

---

### 6. Interview Preparation

SkillBridge AI generates interview questions based on the user's target role and relevant skills.

Example:

```text
How would you apply Python to solve a problem
in this AI Engineer role?

How would you apply SQL to solve a problem
in this role?
```

This connects skill development directly to interview preparation.

---

## AI Implementation

SkillBridge AI integrates Alibaba Cloud DashScope / Qwen for intelligent text analysis.

AI capabilities include:

* Resume profile extraction
* Skill extraction
* Job requirement extraction
* Required vs. preferred skill identification
* Structured career analysis

The application also contains a local intelligence layer for deterministic:

* Skill matching
* Skill normalization
* Skill-gap calculations
* Market analysis
* Recommendations
* Career roadmap generation

This hybrid architecture helps maintain useful application behavior when an external AI service is temporarily unavailable.

External job descriptions are treated as untrusted input, and the application validates structured AI responses before using them.

---

## Technology Stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* SQLite
* Pydantic

### Frontend

* HTML
* CSS
* JavaScript
* Static frontend architecture

### AI

* Alibaba Cloud DashScope
* Qwen

### Processing

* PyPDF
* Requests
* Skill extraction and normalization
* Job analysis
* Job-market analysis

### Server

* Uvicorn

### Deployment

* Render

---

## Project Structure

```text
SkillBridge-AI/
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── skill_gap.py
│   ├── recommendations.py
│   ├── ai_service.py
│   ├── resume_parser.py
│   ├── job_analysis.py
│   ├── job_market.py
│   └── market_pipeline.py
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_job_analysis.py
│   └── test_market_pipeline.py
│
├── demo/
│   ├── error-handling-and-validations/
│   └── demo-videos/
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Backend API

| Method | Endpoint                                | Purpose                                  |
| ------ | --------------------------------------- | ---------------------------------------- |
| GET    | `/`                                     | Check API status                         |
| POST   | `/profile`                              | Create a profile                         |
| GET    | `/profile/{profile_id}`                 | Retrieve a profile                       |
| PUT    | `/profile/{profile_id}`                 | Update a profile                         |
| DELETE | `/profile/{profile_id}`                 | Delete a profile                         |
| GET    | `/profile/{profile_id}/skill-gap`       | Calculate skill gap                      |
| POST   | `/profile/{profile_id}/job-analysis`    | Analyze a career goal or job description |
| GET    | `/profile/{profile_id}/market-analysis` | Analyze job-market demand                |
| POST   | `/resume/analyze`                       | Analyze an uploaded resume               |

FastAPI provides interactive API documentation through Swagger UI.

---

## Database

SQLite is used for profile storage in the current application architecture.

SQLAlchemy provides database interaction.

The `Profile` model contains:

* ID
* Name
* Email
* Education
* Experience
* Skills
* Target Role

The email field is unique to prevent duplicate profiles.

The local database file is excluded from Git.

For a production-scale deployment, a managed database such as PostgreSQL can be introduced for durable persistence.

---

## Validation & Error Handling

The backend uses Pydantic validation and structured error handling.

Validation includes:

* Name validation
* Email format validation
* Education validation
* Experience range validation
* Skills validation
* Target-role validation
* Resume file type and size validation
* Job-analysis input validation

The application handles common API errors including:

```text
404 - Profile not found
409 - Duplicate email
422 - Validation error
502 - External provider error
503 - AI configuration unavailable
```

Database integrity errors are handled using transaction rollback.

The job-analysis pipeline also detects suspicious prompt-injection-style instructions in submitted job descriptions.

---

## Testing

The project includes automated tests for the main analytical components.

Run the test suite with:

```bash
pytest -q
```

Current test status:

```text
8 passed
```

Testing covers:

* Core application functionality
* Job-description analysis
* Market analysis
* Skill matching
* Skill-gap calculations

The application was also manually tested through:

* Static frontend
* FastAPI Swagger UI
* Valid inputs
* Invalid inputs
* Error-handling scenarios
* Resume analysis
* Profile creation and updates
* Career-goal analysis
* Job-description analysis

Demonstration and validation evidence is included in the `demo` directory.

---

## Setup

### 1. Create a Virtual Environment

```bash
python -m venv venv
```

### 2. Activate the Environment

Windows:

```cmd
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Alibaba Cloud AI

Set the Alibaba Cloud DashScope API key as an environment variable.

Windows CMD:

```cmd
set DASHSCOPE_API_KEY=YOUR_API_KEY
```

Optional configuration:

```cmd
set DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
set DASHSCOPE_MODEL=qwen-plus
```

**Never commit API keys or other secrets to GitHub.**

### 5. Start the Backend

```bash
uvicorn backend.main:app --reload
```

### 6. Start the Frontend

The current frontend is a static HTML/CSS/JavaScript application.

From the project root, open another terminal:

```bash
python -m http.server 5500 --directory frontend
```

Then open:

```text
http://127.0.0.1:5500
```

---

## Demo

The complete SkillBridge AI workflow can be demonstrated through the frontend:

```text
Resume Upload
      ↓
Extracted Profile
      ↓
Career Skill Gap
      ↓
Job-Market Analysis
      ↓
Job Description / Career Goal Analysis
      ↓
Personalized Roadmap
      ↓
Interview Preparation
```

For Job Analysis, users can either describe a target such as:

```text
Python backend development
```

or paste a complete job description.

The `demo` directory contains demonstration videos and validation evidence.

---

## Impact

SkillBridge AI makes career preparation more personalized, market-aware, and actionable.

It answers three important questions:

### Where am I now?

Analyze the candidate's existing skills and career profile.

### Where does the market need me to be?

Identify skills appearing in relevant job-market data and job descriptions.

### What should I do next?

Generate prioritized learning recommendations, a structured roadmap, and interview preparation.

---

## Future Scope

Future versions can include:

* Expanded live job-market integrations
* Pakistani job-market intelligence
* Multilingual career guidance
* AI-powered mock interviews
* Learning-resource recommendations
* Career progress tracking
* Intelligent candidate-job matching
* Managed production database
* Additional AI model providers

---

## Hackathon

**Project:** SkillBridge AI

**Event:** Alibaba Cloud AI Hackathon Pakistan 2026

**Theme:** AI for Pakistan's Future

SkillBridge AI aims to help students and professionals make better career decisions by connecting their existing skills with real-world employment demand.

---

## Security

API keys and other sensitive configuration values must be provided through environment variables.

Never commit:

* Credentials
* API keys
* `.env` files
* Virtual environments
* Local database files

The application also treats externally submitted job descriptions as untrusted content and applies input validation and prompt-injection detection before processing.
