ROLE_SKILLS = {
    "Data Scientist": ["Python", "SQL", "Pandas", "Scikit-learn", "Machine Learning"],
    'AI Engineer': ["Python", "SQL", "TensorFlow", "PyTorch", "Deep Learning"],
    "Software Engineer": ["Python", "Java", "C++", "Algorithms", "Data Structures"],
    "Web Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js"],
    "DevOps Engineer": ["Linux", "Docker", "Kubernetes", "CI/CD", "Cloud Computing"],
    "Cybersecurity Analyst": ["Network Security", "Penetration Testing", "Cryptography", "Incident Response", "Security Auditing"],
    "Mobile App Developer": ["Java", "Kotlin", "Swift", "React Native", "Mobile UI/UX Design"],
    "Game Developer": ["C#", "Unity", "Unreal Engine", "3D Modeling", "Game Physics"],
    "Machine Learning Engineer": ["Python", "R", "TensorFlow", "PyTorch", "Machine Learning Algorithms"],
    "Cloud Solutions Architect": ["AWS", "Azure", "Google Cloud Platform", "Cloud Security", "Cloud Architecture"],
    "Business Analyst": ["Data Analysis", "SQL", "Excel", "Business Intelligence", "Data Visualization"],
    "UI/UX Designer": ["User Research", "Wireframing", "Prototyping", "Interaction Design", "Visual Design"],
    "Digital Marketing Specialist": ["SEO", "Content Marketing", "Social Media Marketing", "Email Marketing", "Analytics"],
    "Blockchain Developer": ["Solidity", "Ethereum", "Smart Contracts", "Cryptography", "Decentralized Applications"],
    "Robotics Engineer": ["Robotics Programming", "Control Systems", "Computer Vision", "Sensor Integration", "Robot Kinematics"],
    "Data Engineer": ["Python", "SQL", "ETL", "Data Warehousing", "Big Data Technologies"],
    "AI Research Scientist": ["Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision", "Research Methodology"],
    "Embedded Systems Engineer": ["C", "C++", "Microcontrollers", "Embedded C Programming", "Real-Time Operating Systems"],
    "Network Engineer": ["Networking Protocols", "Routing and Switching", "Network Security", "Firewall Configuration", "Network Troubleshooting"],
    "IT Support Specialist": ["Troubleshooting", "Hardware and Software Support", "Operating Systems", "Networking Basics", "Customer Service"],
    "Database Administrator": ["SQL", "Database Design", "Performance Tuning", "Backup and Recovery", "Database Security"],
   }

def calculate_skill_gap(current_skills,target_role):
    target_role = next(
    (role for role in ROLE_SKILLS if role.lower() == target_role.lower()),
    None
)
    if target_role not in ROLE_SKILLS:
        return {"error":"Target role not supported"}
    
    required_skills = ROLE_SKILLS[target_role]

    # current = set(current_skills)
    current = set(skill.lower() for skill in current_skills)
    missing = [
    skill for skill in required_skills
    if skill.lower() not in current
    ]
    return missing



