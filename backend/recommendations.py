RECOMMENDATIONS = {
    # Data Scientist
    "Python": "Learn Python programming and build small data projects",
    "SQL": "Learn SQL and practice database queries",
    "Pandas": "Learn Pandas for data manipulation and analysis",
    "Scikit-learn": "Learn Scikit-learn and build machine learning models",
    "Machine Learning": "Study machine learning fundamentals and practice with datasets",

    # AI Engineer
    "TensorFlow": "Learn TensorFlow and build neural network models",
    "PyTorch": "Learn PyTorch and build deep learning models",
    "Deep Learning": "Study neural networks and deep learning fundamentals",

    # Software Engineer
    "Java": "Learn Java programming and build object-oriented applications",
    "C++": "Learn C++ programming and practice problem solving",
    "Algorithms": "Study algorithms and practice algorithmic problems",
    "Data Structures": "Study data structures and implement them in code",

    # Web Developer
    "HTML": "Learn HTML and build structured web pages",
    "CSS": "Learn CSS and practice responsive web design",
    "JavaScript": "Learn JavaScript and build interactive web applications",
    "React": "Learn React and build frontend applications",
    "Node.js": "Learn Node.js and build backend web applications",

    # DevOps Engineer
    "Linux": "Learn Linux commands and system administration",
    "Docker": "Learn Docker and containerize applications",
    "Kubernetes": "Learn Kubernetes and practice container orchestration",
    "CI/CD": "Learn CI/CD pipelines and automate application deployment",
    "Cloud Computing": "Learn cloud computing fundamentals and deploy applications",

    # Cybersecurity Analyst
    "Network Security": "Learn network security concepts and defensive techniques",
    "Penetration Testing": "Learn penetration testing methodology in legal lab environments",
    "Cryptography": "Study cryptography fundamentals and secure communication",
    "Incident Response": "Learn incident response processes and security investigation",
    "Security Auditing": "Learn security auditing and vulnerability assessment",

    # Mobile App Developer
    "Kotlin": "Learn Kotlin and build Android applications",
    "Swift": "Learn Swift and build iOS applications",
    "React Native": "Learn React Native and build cross-platform mobile apps",
    "Mobile UI/UX Design": "Learn mobile UI/UX principles and design mobile interfaces",

    # Game Developer
    "C#": "Learn C# programming for game development",
    "Unity": "Learn Unity and build a small game",
    "Unreal Engine": "Learn Unreal Engine and practice game development",
    "3D Modeling": "Learn 3D modeling and create basic game assets",
    "Game Physics": "Study game physics and implement movement and collision systems",

    # Machine Learning Engineer
    "R": "Learn R for statistical analysis and machine learning",
    "Machine Learning Algorithms": "Study machine learning algorithms and implement them on datasets",

    # Cloud Solutions Architect
    "AWS": "Learn AWS fundamentals and deploy a cloud application",
    "Azure": "Learn Azure fundamentals and practice cloud deployment",
    "Google Cloud Platform": "Learn Google Cloud fundamentals and deploy an application",
    "Cloud Security": "Learn cloud security principles and identity management",
    "Cloud Architecture": "Study cloud architecture and design scalable systems",

    # Business Analyst
    "Data Analysis": "Learn data analysis techniques and work with real datasets",
    "Excel": "Learn advanced Excel and practice data analysis",
    "Business Intelligence": "Learn business intelligence tools and reporting",
    "Data Visualization": "Learn data visualization and create informative dashboards",

    # UI/UX Designer
    "User Research": "Learn user research methods and analyze user needs",
    "Wireframing": "Learn wireframing and create interface layouts",
    "Prototyping": "Learn prototyping and build interactive product prototypes",
    "Interaction Design": "Study interaction design and improve user experiences",
    "Visual Design": "Learn visual design principles, typography, and layout",

    # Digital Marketing Specialist
    "SEO": "Learn SEO fundamentals and optimize web content",
    "Content Marketing": "Learn content marketing and create valuable content",
    "Social Media Marketing": "Learn social media marketing and develop campaigns",
    "Email Marketing": "Learn email marketing and design effective campaigns",
    "Analytics": "Learn digital analytics and measure campaign performance",

    # Blockchain Developer
    "Solidity": "Learn Solidity and build basic smart contracts",
    "Ethereum": "Learn Ethereum fundamentals and decentralized application development",
    "Smart Contracts": "Learn smart contract development and security",
    "Decentralized Applications": "Learn DApp architecture and build a simple decentralized application",

    # Robotics Engineer
    "Robotics Programming": "Learn robotics programming and control a simulated robot",
    "Control Systems": "Study control systems and implement basic controllers",
    "Computer Vision": "Learn computer vision and build image-processing projects",
    "Sensor Integration": "Learn sensor integration and process sensor data",
    "Robot Kinematics": "Study robot kinematics and model robotic movement",

    # Data Engineer
    "ETL": "Learn ETL processes and build a simple data pipeline",
    "Data Warehousing": "Learn data warehousing concepts and design a basic warehouse",
    "Big Data Technologies": "Learn big data technologies and distributed data processing",

    # AI Research Scientist
    "Natural Language Processing": "Learn NLP fundamentals and build a text-processing project",
    "Research Methodology": "Learn research methodology and practice reading and evaluating research papers",

    # Embedded Systems Engineer
    "C": "Learn C programming and practice embedded programming",
    "Microcontrollers": "Learn microcontrollers and build basic hardware projects",
    "Embedded C Programming": "Learn Embedded C and program microcontrollers",
    "Real-Time Operating Systems": "Learn RTOS concepts and build real-time applications",

    # Network Engineer
    "Networking Protocols": "Learn networking protocols such as TCP/IP and HTTP",
    "Routing and Switching": "Learn routing and switching fundamentals and practice network configuration",
    "Firewall Configuration": "Learn firewall configuration and network traffic control",
    "Network Troubleshooting": "Learn network troubleshooting and diagnose connectivity problems",

    # IT Support Specialist
    "Troubleshooting": "Learn systematic troubleshooting for common technical problems",
    "Hardware and Software Support": "Learn hardware and software support and diagnose common issues",
    "Operating Systems": "Learn operating system administration and configuration",
    "Networking Basics": "Learn basic networking concepts and connectivity troubleshooting",
    "Customer Service": "Develop technical customer service and communication skills",

    # Database Administrator
    "Database Design": "Learn database design and relational database modeling",
    "Performance Tuning": "Learn database performance tuning and query optimization",
    "Backup and Recovery": "Learn database backup and recovery strategies",
    "Database Security": "Learn database security, access control, and protection",
}
def get_recommendations(missing_skills):
    recommendations = []

    for skill in missing_skills:
        recommendation = next(
        (value for key, value in RECOMMENDATIONS.items() if key.lower() == skill.lower()),
        None
        )

        if recommendation:
            recommendations.append(recommendation)
    return recommendations


def get_recommendation(skill):
    recommendation = next(
        (value for key, value in RECOMMENDATIONS.items() if key.lower() == skill.lower()),
        None,
    )
    if recommendation:
        return recommendation
    return f"Build a focused project that demonstrates {skill} in a job-relevant scenario."
