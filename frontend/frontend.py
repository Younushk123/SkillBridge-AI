import streamlit as st
import requests

if "validation_errors" not in st.session_state:
    st.session_state.validation_errors = {}

st.title("SkillBridge AI")
st.write("Analyze your skills and identify what you should learn next")
name = st.text_input("Name")
if "name" in st.session_state.validation_errors:
    st.error(st.session_state.validation_errors["name"])

email = st.text_input("Email")
if "email" in st.session_state.validation_errors:
    st.error(st.session_state.validation_errors["email"])

education = st.text_input("Education")
if "education" in st.session_state.validation_errors:
    st.error(st.session_state.validation_errors["education"])

experience = st.number_input(
    "Experience (years)",
    min_value=0,
    step=1
)
if "experience_years" in st.session_state.validation_errors:
    st.error(st.session_state.validation_errors["experience_years"])
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
    "Performance Tuning", "Backup and Recovery", "Database Security"
]

skills = st.multiselect("Skills", skill_options)
target_role = st.selectbox(
    "Target Role",
    [
        "Data Scientist",
        "AI Engineer",
        "Software Engineer",
        "Web Developer",
        "DevOps Engineer",
        "Cybersecurity Analyst",
        "Mobile App Developer",
        "Game Developer",
        "Machine Learning Engineer",
        "Cloud Solutions Architect",
        "Business Analyst",
        "UI/UX Designer",
        "Digital Marketing Specialist",
        "Blockchain Developer",
        "Robotics Engineer",
        "Data Engineer",
        "AI Research Scientist",
        "Embedded Systems Engineer",
        "Network Engineer",
        "IT Support Specialist",
        "Database Administrator"
    ]
)
if st.button("Analyze My Skills"):
    st.session_state.validation_errors = {}

    profile_data = {
    "name": name,
    "email": email,
    "education": education,
    "experience_years": experience,
    "skills": ",".join(skills),
    "target_role": target_role
    }
    response = requests.post(
    "http://127.0.0.1:8000/profile",
    json=profile_data)
    if response.status_code == 200:
        st.success("Profile created successfully!")
        profile = response.json()
        profile_id = profile["id"]
    else:
        try:
            error_data = response.json()

            if response.status_code == 422:
                for error in error_data.get("detail",[]):
                        field = error.get("loc",["field"])[-1]

                        if field == "name":
                            st.session_state.validation_errors["name"] = (
                                "Please enter a valid name."
                            )
                        elif field == "email":
                            st.session_state.validation_errors["email"] = (
                                "Please enter a valid email address."
                            )
                        elif field == "education":
                            st.session_state.validation_errors["education"] = (
                                "Please enter valid education details."
                            )
                        elif field == "experience_years":
                            st.session_state.validation_errors["experience_years"] = (
                                "Experience must be between 0 and 50 years."
                            )
                        else:
                            st.session_state.validation_errors[field] = (
                                "Please check your input and try again."
                            )
            elif response.status_code == 409:
                st.session_state.validation_errors["email"] = (
                    "A profile with this email already exists."
                )
            else:
                 st.error("Failed to create profile.Please try again.")
        except ValueError:
            st.error("Failed to create profile. Please try again.")
        st.stop()
   
    skill_gap_response = requests.get(
    f"http://127.0.0.1:8000/profile/{profile_id}/skill-gap"
    )
    if skill_gap_response.status_code == 200:
            st.success("Career analysis generated successfully!")
            skill_gap_data = skill_gap_response.json()
    else:
            st.error("Failed to generate career analysis. Please try again.")
            
    
    st.subheader("Career Analysis")
    st.write("Target Role:", skill_gap_data["target_role"])
    st.subheader("Missing Skills")

    for skill in skill_gap_data["missing_skills"]:
        st.write("•", skill)

    st.subheader("Recommendations")

    for recommendation in skill_gap_data["recommendations"]:
        st.write("→", recommendation)
    