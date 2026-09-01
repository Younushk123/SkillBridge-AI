# SkillBridge AI

## Project Overview

SkillBridge AI is a career development application that helps users identify the skills they need for a selected career role.

The user enters basic profile information, selects their current skills, and chooses a target role. The backend stores the profile, compares the selected skills with the required skills for the target role, identifies missing skills, and provides learning recommendations.

The project uses a Streamlit frontend, FastAPI backend, SQLite database, SQLAlchemy ORM, and Pydantic for data validation.

---

## Features

* User profile creation
* Profile retrieval, update, and deletion
* Target career role selection
* Current skill selection
* Skill-gap analysis
* Learning recommendations
* Email validation
* Input field validation
* Duplicate email handling
* Profile-not-found handling
* REST API with FastAPI
* SQLite database storage
* Swagger API documentation
* Manual testing of different valid and invalid inputs

---

## Technologies Used

* Python
* FastAPI
* Streamlit
* SQLite
* SQLAlchemy
* Pydantic
* Requests
* Uvicorn

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
│   └── recommendations.py
│
├── frontend/
│   └── frontend.py
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

## Backend

The backend is developed using FastAPI.

It handles profile data, database operations, validation, skill-gap analysis, and recommendations.

### API Endpoints

| Method | Endpoint                          | Purpose                       |
| ------ | --------------------------------- | ----------------------------- |
| GET    | `/`                               | Check that the API is running |
| POST   | `/profile`                        | Create a new profile          |
| GET    | `/profile/{profile_id}`           | Get a profile                 |
| PUT    | `/profile/{profile_id}`           | Update a profile              |
| DELETE | `/profile/{profile_id}`           | Delete a profile              |
| GET    | `/profile/{profile_id}/skill-gap` | Calculate the skill gap       |

FastAPI also provides interactive API documentation through Swagger UI.

```text
http://127.0.0.1:8000/docs
```

---

## Database

SQLite is used as the database for the project.

SQLAlchemy is used to interact with the database.

The `Profile` table contains:

* ID
* Name
* Email
* Education
* Experience
* Skills
* Target Role

The email field is configured as unique to prevent duplicate profiles.

The database file is excluded from Git using `.gitignore`.

---

## Validation and Error Handling

Pydantic validation is used in the backend to validate profile data before it is stored.

Current validation includes:

* Name length
* Email format
* Education length
* Experience value
* Skills input
* Target role input

The frontend displays validation messages for the relevant fields.

The backend also handles:

* `404` when a profile does not exist
* `409` when an email already exists
* `422` when submitted data fails validation
* Database integrity errors using transaction rollback

Example validation messages include:

```text
Please enter a valid name.
Please enter a valid email address.
Please enter valid education details.
Experience must be between 0 and 50 years.
A profile with this email already exists.
```

---

## Skill Gap Analysis

The project contains role-specific skill requirements.

When the user selects a target role, the system compares the user's selected skills with the required skills for that role.

For example:

```text
Target Role: Data Scientist

Current Skills:
Python
SQL

Missing Skills:
Pandas
Scikit-learn
Machine Learning
```

The comparison is handled by the `skill_gap.py` module.

---

## Recommendations

The `recommendations.py` module provides learning recommendations for identified missing skills.

For example:

```text
Missing Skill:
Pandas

Recommendation:
Learn Pandas for data manipulation and analysis.
```

The recommendation system is separated from the skill-gap calculation so that recommendations can be expanded later.

---

## Testing

The application was manually tested using the frontend and FastAPI Swagger documentation.

### Functional Testing

* Creating a profile
* Retrieving a profile
* Updating a profile
* Deleting a profile
* Generating skill-gap analysis
* Generating recommendations

### Validation Testing

* Short name
* Invalid email
* Invalid education input
* Invalid experience value
* Other invalid profile data

### Error Testing

* Duplicate email
* Non-existent profile
* Invalid API input
* Database integrity error

Screenshots and demonstration videos are included in the `demo` folder.

---

## How to Run

### 1. Create a Virtual Environment

```bash
python -m venv venv
```

### 2. Activate the Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Start the Backend

From the project root:

```bash
uvicorn backend.main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

### 5. Start the Frontend

Open another terminal and run:

```bash
streamlit run frontend/frontend.py
```

The Streamlit application will open in the browser.

---

## Demo

The `demo` folder contains:

* Application demonstration videos
* Validation screenshots
* Error-handling screenshots

These demonstrate the main application workflow and the tested validation/error cases.

---

## Future Improvements

The current version can be extended with more advanced features, such as:

* AI-based resume analysis
* Personalized learning paths
* AI-powered interview preparation
* Job-market skill analysis
* Learning resource recommendations
* More advanced career guidance
* Cloud deployment
* Integration with external AI services
