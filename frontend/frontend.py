import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"

for key, default in {
    "validation_errors": {},
    "active_profile_id": None,
    "skill_gap_data": None,
    "job_analysis_data": None,
    "job_analysis_error": None,
    "market_analysis_data": None,
    "market_analysis_error": None,
    "resume_analysis_data": None,
    "resume_analysis_error": None,
    "profile_name": "",
    "profile_email": "",
    "profile_education": "",
    "profile_experience_years": 0,
    "profile_skills": [],
    "profile_target_role": "Data Scientist",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def request_error_message(response, fallback):
    try:
        return response.json().get("detail", fallback)
    except ValueError:
        return fallback


def render_skill_list(skills, empty_message):
    if skills:
        for skill in skills:
            st.write(f"• {skill}")
    else:
        st.write(empty_message)


st.title("SkillBridge AI")
st.write("Upload your resume or enter your details, then analyze your skills against a real job.")

st.header("Resume Intelligence")
st.write("Upload a text-based PDF resume to extract a profile you can review before saving.")
uploaded_resume = st.file_uploader("Resume PDF", type=["pdf"], key="resume_file")

if st.button("Analyze Resume", key="analyze_resume"):
    st.session_state.resume_analysis_error = None
    st.session_state.resume_analysis_data = None
    if uploaded_resume is None:
        st.session_state.resume_analysis_error = "Please choose a PDF resume first."
    else:
        with st.spinner("Extracting your resume profile..."):
            try:
                resume_response = requests.post(
                    f"{API_BASE_URL}/resume/analyze",
                    files={
                        "file": (
                            uploaded_resume.name,
                            uploaded_resume.getvalue(),
                            "application/pdf",
                        )
                    },
                    timeout=100,
                )
            except requests.RequestException:
                st.session_state.resume_analysis_error = (
                    "Resume analysis is temporarily unavailable. Please try again."
                )
            else:
                if resume_response.status_code == 200:
                    st.session_state.resume_analysis_data = resume_response.json()
                else:
                    st.session_state.resume_analysis_error = request_error_message(
                        resume_response,
                        "Unable to analyze this resume. Please try again.",
                    )

if st.session_state.resume_analysis_error:
    st.error(st.session_state.resume_analysis_error)

if st.session_state.resume_analysis_data:
    resume = st.session_state.resume_analysis_data
    st.subheader("Extracted Profile")
    st.write("Name:", resume["name"] or "Not identified")
    st.write("Education:", resume["education"] or "Not identified")
    st.write("Experience:", f"{resume['experience_years']} years")
    st.write("Target role:", resume["target_role"] or "Not identified")
    st.markdown("**Skills**")
    render_skill_list(resume["skills"], "No skills identified.")

    if st.button("Use This Profile", key="use_resume_profile"):
        if resume["name"]:
            st.session_state.profile_name = resume["name"]
        if resume["education"]:
            st.session_state.profile_education = resume["education"]
        if resume["experience_years"]:
            st.session_state.profile_experience_years = resume["experience_years"]
        if resume["skills"]:
            st.session_state.profile_skills = resume["skills"]
        if resume["target_role"]:
            st.session_state.profile_target_role = resume["target_role"]
        st.session_state.validation_errors = {}
        st.session_state.active_profile_id = None
        st.session_state.skill_gap_data = None
        st.session_state.job_analysis_data = None
        st.session_state.job_analysis_error = None
        st.session_state.market_analysis_data = None
        st.session_state.market_analysis_error = None
        st.success("Profile details added to the form. Add your email and review them before saving.")

skill_options = [
    "Python", "SQL", "Pandas", "Scikit-learn", "Machine Learning",
    "TensorFlow", "PyTorch", "Deep Learning",
    "Java", "C++", "Algorithms", "Data Structures",
    "HTML", "CSS", "JavaScript", "React", "Node.js",
    "Linux", "Docker", "Kubernetes", "CI/CD", "Cloud Computing",
    "Network Security", "Penetration Testing", "Cryptography",
    "Incident Response", "Security Auditing",
    "Kotlin", "Swift", "React Native", "Mobile UI/UX Design",
    "C#", "Unity", "Unreal Engine", "3D Modeling", "Game Physics",
    "R", "Machine Learning Algorithms",
    "AWS", "Azure", "Google Cloud Platform", "Cloud Security",
    "Cloud Architecture",
    "Data Analysis", "Excel", "Business Intelligence", "Data Visualization",
    "User Research", "Wireframing", "Prototyping", "Interaction Design",
    "Visual Design", "SEO", "Content Marketing", "Social Media Marketing",
    "Email Marketing", "Analytics", "Solidity", "Ethereum", "Smart Contracts",
    "Decentralized Applications", "Robotics Programming", "Control Systems",
    "Computer Vision", "Sensor Integration", "Robot Kinematics",
    "ETL", "Data Warehousing", "Big Data Technologies",
    "Natural Language Processing", "Research Methodology",
    "C", "Microcontrollers", "Embedded C Programming",
    "Real-Time Operating Systems", "Networking Protocols",
    "Routing and Switching", "Firewall Configuration",
    "Network Troubleshooting", "Troubleshooting",
    "Hardware and Software Support", "Operating Systems",
    "Networking Basics", "Customer Service", "Database Design",
    "Performance Tuning", "Backup and Recovery", "Database Security",
]
target_role_options = [
    "Data Scientist", "AI Engineer", "Software Engineer", "Web Developer",
    "DevOps Engineer", "Cybersecurity Analyst", "Mobile App Developer",
    "Game Developer", "Machine Learning Engineer", "Cloud Solutions Architect",
    "Business Analyst", "UI/UX Designer", "Digital Marketing Specialist",
    "Blockchain Developer", "Robotics Engineer", "Data Engineer",
    "AI Research Scientist", "Embedded Systems Engineer", "Network Engineer",
    "IT Support Specialist", "Database Administrator",
]

if st.session_state.resume_analysis_data:
    for skill in st.session_state.resume_analysis_data["skills"]:
        if skill not in skill_options:
            skill_options.append(skill)
    extracted_role = st.session_state.resume_analysis_data["target_role"]
    if extracted_role and extracted_role not in target_role_options:
        target_role_options.append(extracted_role)

current_target_role = st.session_state.profile_target_role
if current_target_role and current_target_role not in target_role_options:
    target_role_options.append(current_target_role)

st.divider()
name = st.text_input("Name", key="profile_name")
if "name" in st.session_state.validation_errors:
    st.error(st.session_state.validation_errors["name"])

email = st.text_input("Email", key="profile_email")
if "email" in st.session_state.validation_errors:
    st.error(st.session_state.validation_errors["email"])

education = st.text_input("Education", key="profile_education")
if "education" in st.session_state.validation_errors:
    st.error(st.session_state.validation_errors["education"])

experience = st.number_input(
    "Experience (years)",
    min_value=0,
    step=1,
    key="profile_experience_years",
)
if "experience_years" in st.session_state.validation_errors:
    st.error(st.session_state.validation_errors["experience_years"])

skills = st.multiselect("Skills", skill_options, key="profile_skills")
target_role = st.selectbox("Target Role", target_role_options, key="profile_target_role")

if st.button("Analyze My Skills", type="primary"):
    st.session_state.validation_errors = {}
    st.session_state.active_profile_id = None
    st.session_state.skill_gap_data = None
    st.session_state.job_analysis_data = None
    st.session_state.job_analysis_error = None
    st.session_state.market_analysis_data = None
    st.session_state.market_analysis_error = None

    profile_data = {
        "name": name,
        "email": email,
        "education": education,
        "experience_years": experience,
        "skills": ",".join(skills),
        "target_role": target_role,
    }

    try:
        response = requests.post(f"{API_BASE_URL}/profile", json=profile_data, timeout=15)
    except requests.RequestException:
        st.error("Unable to reach the SkillBridge API. Please try again.")
    else:
        if response.status_code == 200:
            profile = response.json()
            st.session_state.active_profile_id = profile["id"]
            st.success("Profile created successfully.")

            try:
                skill_gap_response = requests.get(
                    f"{API_BASE_URL}/profile/{profile['id']}/skill-gap",
                    timeout=15,
                )
            except requests.RequestException:
                st.error("Profile saved, but career analysis could not be loaded.")
            else:
                if skill_gap_response.status_code == 200:
                    st.session_state.skill_gap_data = skill_gap_response.json()
                    st.success("Career analysis generated successfully.")
                else:
                    st.error("Profile saved, but career analysis could not be generated.")
        else:
            if response.status_code == 422:
                try:
                    for error in response.json().get("detail", []):
                        field = error.get("loc", ["field"])[-1]
                        messages = {
                            "name": "Please enter a valid name.",
                            "email": "Please enter a valid email address.",
                            "education": "Please enter valid education details.",
                            "experience_years": "Experience must be between 0 and 50 years.",
                            "skills": "Select at least one skill.",
                            "target_role": "Select a valid target role.",
                        }
                        st.session_state.validation_errors[field] = messages.get(
                            field,
                            "Please check your input and try again.",
                        )
                except ValueError:
                    st.error("Failed to create the profile. Please try again.")
            elif response.status_code == 409:
                st.session_state.validation_errors["email"] = (
                    "A profile with this email already exists."
                )
            else:
                st.error("Failed to create the profile. Please try again.")

if st.session_state.skill_gap_data:
    skill_gap_data = st.session_state.skill_gap_data
    st.divider()
    st.subheader("Career Analysis")
    st.write("Target role:", skill_gap_data.get("target_role", ""))
    if skill_gap_data.get("error"):
        st.warning(skill_gap_data["error"])
    else:
        left_column, right_column = st.columns(2)
        with left_column:
            st.markdown("**Missing skills**")
            render_skill_list(skill_gap_data.get("missing_skills", []), "No skill gaps identified.")
        with right_column:
            st.markdown("**Recommendations**")
            render_skill_list(
                skill_gap_data.get("recommendations", []),
                "No recommendations available.",
            )

if st.session_state.active_profile_id:
    st.divider()
    st.header("Real-Time Job Market")
    st.write("Analyze recent job listings for your saved target role.")

    if st.button("Analyze Current Job Market", key="analyze_current_job_market"):
        st.session_state.market_analysis_error = None
        st.session_state.market_analysis_data = None
        with st.spinner("Analyzing current job-market demand..."):
            try:
                market_response = requests.get(
                    f"{API_BASE_URL}/profile/{st.session_state.active_profile_id}/market-analysis",
                    timeout=100,
                )
            except requests.RequestException:
                st.session_state.market_analysis_error = (
                    "Live job-market analysis is temporarily unavailable. Please try again."
                )
            else:
                if market_response.status_code == 200:
                    st.session_state.market_analysis_data = market_response.json()
                else:
                    st.session_state.market_analysis_error = request_error_message(
                        market_response,
                        "Unable to analyze the current job market. Please try again.",
                    )

    if st.session_state.market_analysis_error:
        st.error(st.session_state.market_analysis_error)

    if st.session_state.market_analysis_data:
        market = st.session_state.market_analysis_data
        st.subheader("Current Market")
        market_column, jobs_column = st.columns(2)
        with market_column:
            st.write("Target Role:", market["target_role"])
        with jobs_column:
            st.metric("Jobs Analyzed", market["jobs_analyzed"])

        if not market["jobs_analyzed"]:
            st.info("No recent job descriptions were available for this role.")

        st.subheader("Top In-Demand Skills")
        if market["market_skills"]:
            for demand in market["market_skills"]:
                st.write(
                    f"• {demand['skill']} — {demand['demand_percentage']:.1f}% "
                    f"({demand['demand_count']} jobs)"
                )
        else:
            st.write("No market skills were identified.")

        match_column, gap_column = st.columns(2)
        with match_column:
            st.subheader("Your Market Match")
            render_skill_list(
                market["matched_skills"],
                "No currently demanded skills matched your profile.",
            )
        with gap_column:
            st.subheader("Market Skill Gaps")
            render_skill_list(
                market["missing_skills"],
                "No market skill gaps were identified.",
            )

        st.subheader("Priority Skills")
        if market["priority_skills"]:
            for priority in market["priority_skills"]:
                st.write(
                    f"• {priority['skill']} — {priority['demand_percentage']:.1f}% "
                    f"({priority['demand_count']} jobs)"
                )
        else:
            st.write("No priority skills were identified.")

        st.subheader("AI Market Insight")
        st.write(market["market_summary"])

    st.divider()
    st.header("Job Description Analysis")
    st.write("Paste a real job description to see how your profile aligns with it.")
    job_description = st.text_area(
        "Job Description",
        placeholder="Paste the full job description here...",
        height=240,
    )

    if st.button("Analyze Job Description"):
        st.session_state.job_analysis_error = None
        if not job_description.strip():
            st.session_state.job_analysis_error = "Please paste a job description first."
        else:
            with st.spinner("Analyzing job requirements and matching your skills..."):
                try:
                    job_response = requests.post(
                        f"{API_BASE_URL}/profile/{st.session_state.active_profile_id}/job-analysis",
                        json={"job_description": job_description},
                        timeout=100,
                    )
                except requests.RequestException:
                    st.session_state.job_analysis_error = (
                        "Job analysis is temporarily unavailable. Please try again."
                    )
                else:
                    if job_response.status_code == 200:
                        st.session_state.job_analysis_data = job_response.json()
                    else:
                        st.session_state.job_analysis_error = request_error_message(
                            job_response,
                            "Unable to analyze this job description. Please try again.",
                        )

    if st.session_state.job_analysis_error:
        st.error(st.session_state.job_analysis_error)

    if st.session_state.job_analysis_data:
        analysis = st.session_state.job_analysis_data
        st.subheader("Job Match")
        st.metric("Match Score", f"{analysis['match_score']}%")

        requirement_column, match_column = st.columns(2)
        with requirement_column:
            st.markdown("**Required skills**")
            render_skill_list(analysis["required_skills"], "No explicit required skills found.")
            st.markdown("**Preferred skills**")
            render_skill_list(analysis["preferred_skills"], "No preferred skills found.")
        with match_column:
            st.markdown("**Matched skills**")
            render_skill_list(analysis["matched_skills"], "No matched skills found.")
            st.markdown("**Missing skills**")
            render_skill_list(analysis["missing_skills"], "No missing skills found.")

        st.subheader("Priority Skills")
        if analysis["learning_priorities"]:
            for priority in analysis["learning_priorities"]:
                st.markdown(
                    f"**{priority['priority']} — {priority['skill']}** "
                    f"({priority['requirement_type']}): {priority['recommendation']}"
                )
        else:
            st.success("Your current profile covers the identified job skills.")

        st.subheader("Personalized Roadmap")
        for phase in analysis["roadmap"]:
            st.markdown(f"**{phase['title']}** · {phase['duration']}")
            if phase["focus_skills"]:
                st.write("Focus:", ", ".join(phase["focus_skills"]))
            for action in phase["actions"]:
                st.write(f"• {action}")

        st.subheader("Interview Preparation")
        for item in analysis["interview_questions"]:
            st.markdown(f"**{item['skill']}:** {item['question']}")
