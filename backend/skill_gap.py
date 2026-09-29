import re


ROLE_SKILLS = {
    "AI/ML Engineer": [
            "Python",
            "SQL",
            "Scikit-learn",
            "Machine Learning",
            "Deep Learning",
            "PyTorch",
            "TensorFlow",
            "LLMs",
    ],

    "Data Scientist": [
        "Python",
        "SQL",
        "Pandas",
        "NumPy",
        "Scikit-learn",
        "Machine Learning",
        "Statistics",
        "Data Visualization",
    ],

    "AI Engineer": [
        "Python",
        "SQL",
        "Machine Learning",
        "Deep Learning",
        "PyTorch",
        "TensorFlow",
        "LLMs",
        "RAG",
    ],

    "Software Engineer": [
        "Python",
        "Java",
        "C++",
        "Data Structures",
        "Algorithms",
        "Git",
        "GitHub",
        "Software Development",
    ],

    "Web Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "React",
        "Node.js",
        "REST APIs",
        "Git",
        "GitHub",
    ],

    "DevOps Engineer": [
        "Linux",
        "Docker",
        "Kubernetes",
        "CI/CD",
        "AWS",
        "Git",
        "GitHub",
        "Infrastructure as Code",
    ],

    "Cybersecurity Analyst": [
        "Network Security",
        "Linux",
        "SIEM",
        "Incident Response",
        "Vulnerability Assessment",
        "Security Monitoring",
        "Cryptography",
        "Penetration Testing",
    ],

    "Mobile App Developer": [
        "Java",
        "Kotlin",
        "Swift",
        "Flutter",
        "React Native",
        "Mobile UI/UX Design",
        "REST APIs",
        "Git",
    ],

    "Game Developer": [
        "C#",
        "Unity",
        "Unreal Engine",
        "Game Physics",
        "3D Modeling",
        "Game Development",
        "Git",
        "Object-Oriented Programming",
    ],

    "Machine Learning Engineer": [
        "Python",
        "SQL",
        "Machine Learning",
        "Scikit-learn",
        "PyTorch",
        "TensorFlow",
        "Deep Learning",
        "MLOps",
    ],

    "Cloud Solutions Architect": [
        "AWS",
        "Azure",
        "Google Cloud Platform",
        "Cloud Architecture",
        "Cloud Security",
        "Networking",
        "Docker",
        "Kubernetes",
    ],

    "Business Analyst": [
        "SQL",
        "Excel",
        "Data Analysis",
        "Business Intelligence",
        "Data Visualization",
        "Power BI",
        "Requirements Analysis",
        "Communication",
    ],

    "UI/UX Designer": [
        "User Research",
        "Wireframing",
        "Prototyping",
        "Figma",
        "Interaction Design",
        "Visual Design",
        "Usability Testing",
        "Design Systems",
    ],

    "Digital Marketing Specialist": [
        "SEO",
        "Content Marketing",
        "Social Media Marketing",
        "Google Analytics",
        "Email Marketing",
        "Search Engine Marketing",
        "Content Strategy",
        "Marketing Analytics",
    ],

    "Blockchain Developer": [
        "Solidity",
        "Ethereum",
        "Smart Contracts",
        "Web3",
        "Decentralized Applications",
        "Cryptography",
        "JavaScript",
        "Blockchain Development",
    ],

    "Robotics Engineer": [
        "Python",
        "C++",
        "ROS",
        "Computer Vision",
        "Control Systems",
        "Sensor Integration",
        "Robot Kinematics",
        "Robotics Programming",
    ],

    "Data Engineer": [
        "Python",
        "SQL",
        "ETL",
        "Data Warehousing",
        "Apache Spark",
        "Data Pipelines",
        "Cloud Computing",
        "Database Systems",
    ],

    "AI Research Scientist": [
        "Python",
        "Machine Learning",
        "Deep Learning",
        "Natural Language Processing",
        "Computer Vision",
        "PyTorch",
        "Research Methodology",
        "Mathematics for Machine Learning",
    ],

    "Embedded Systems Engineer": [
        "C",
        "C++",
        "Microcontrollers",
        "Embedded C Programming",
        "Real-Time Operating Systems",
        "Embedded Linux",
        "UART",
        "SPI",
    ],

    "Network Engineer": [
        "Networking Protocols",
        "TCP/IP",
        "Routing and Switching",
        "Network Security",
        "Firewall Configuration",
        "Cisco",
        "Network Troubleshooting",
        "VPN",
    ],

    "IT Support Specialist": [
        "Troubleshooting",
        "Windows",
        "Linux",
        "Hardware and Software Support",
        "Networking Basics",
        "Active Directory",
        "Technical Support",
        "Customer Service",
    ],

    "Database Administrator": [
        "SQL",
        "Database Design",
        "PostgreSQL",
        "MySQL",
        "Performance Tuning",
        "Backup and Recovery",
        "Database Security",
        "Database Administration",
    ],

}


ALIASES = {

    "ml": "Machine Learning",
    "machinelearning": "Machine Learning",
    "dl": "Deep Learning",
    "deeplearning": "Deep Learning",
    "sklearn": "Scikit-learn",
    "scikitlearn": "Scikit-learn",
    "nodejs": "Node.js",
    "reactjs": "React",
    "gcp": "Google Cloud Platform",
    "googlecloud": "Google Cloud Platform",
    "aws": "AWS",
    "k8s": "Kubernetes",
    "cicd": "CI/CD",

}


def _key(skill: str) -> str:
    return re.sub(r"[\s._/\\-]+", "", skill).casefold()


def _canonical(skill: str) -> str:
    clean = " ".join(str(skill).split())
    return ALIASES.get(_key(clean), clean)


def get_all_role_skills() -> list[str]:
    """
    Return one unique list containing every skill defined in ROLE_SKILLS.

    The first occurrence of each skill is preserved.
    """
    skills = []
    seen = set()

    for role_skills in ROLE_SKILLS.values():
        for skill in role_skills:
            key = _key(skill)

            if key not in seen:
                skills.append(skill)
                seen.add(key)

    return skills


def calculate_skill_gap(current_skills, target_role):

    target_role = next(
        (
            role
            for role in ROLE_SKILLS
            if role.casefold() == str(target_role or "").casefold()
        ),
        None,
    )

    if target_role is None:
        return {"error": "Target role not supported"}

    current_keys = {
        _key(_canonical(skill))
        for skill in (current_skills or [])
        if str(skill).strip()
    }

    required_skills = ROLE_SKILLS[target_role]

    matched = [
        skill
        for skill in required_skills
        if _key(skill) in current_keys
    ]

    missing = [
        skill
        for skill in required_skills
        if _key(skill) not in current_keys
    ]

    total = len(required_skills)
    coverage = round((len(matched) / total) * 100) if total else 0

    return {
        "target_role": target_role,
        "required_skills": required_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "coverage": coverage,
    }

