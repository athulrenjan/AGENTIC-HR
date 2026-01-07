from typing import Dict
from datetime import datetime

JD_STORE: Dict[str, dict] = {}

JD_TEMPLATES = {
    "Software Engineer": {
        "title": "Software Engineer",
        "level": "Mid",
        "mandatory_skills": ["Python", "JavaScript", "SQL"],
        "nice_to_have_skills": ["React", "Docker"],
        "location": "Remote",
        "team_size": 5,
        "budget": "$80k-$120k",
        "inclusion_criteria": ["Bachelor's in CS", "3+ years experience"],
        "exclusion_criteria": ["No remote work experience"]
    },
    "Backend Engineer": {
        "title": "Backend Engineer",
        "level": "Senior",
        "mandatory_skills": ["Python", "Django", "PostgreSQL"],
        "nice_to_have_skills": ["AWS", "Kubernetes"],
        "location": "New York",
        "team_size": 3,
        "budget": "$100k-$150k",
        "inclusion_criteria": ["5+ years backend experience"],
        "exclusion_criteria": []
    },
    "ML Engineer": {
        "title": "ML Engineer",
        "level": "Senior",
        "mandatory_skills": ["Python", "TensorFlow", "PyTorch"],
        "nice_to_have_skills": ["MLOps", "AWS"],
        "location": "San Francisco",
        "team_size": 4,
        "budget": "$120k-$180k",
        "inclusion_criteria": ["PhD in ML", "Published papers"],
        "exclusion_criteria": []
    },
    "Data Analyst": {
        "title": "Data Analyst",
        "level": "Mid",
        "mandatory_skills": ["SQL", "Python", "Tableau"],
        "nice_to_have_skills": ["R", "Machine Learning"],
        "location": "Chicago",
        "team_size": 2,
        "budget": "$70k-$100k",
        "inclusion_criteria": ["Statistics degree"],
        "exclusion_criteria": []
    },
    "DevOps Engineer": {
        "title": "DevOps Engineer",
        "level": "Senior",
        "mandatory_skills": ["AWS", "Docker", "Kubernetes"],
        "nice_to_have_skills": ["Terraform", "Jenkins"],
        "location": "Austin",
        "team_size": 3,
        "budget": "$110k-$160k",
        "inclusion_criteria": ["5+ years DevOps"],
        "exclusion_criteria": []
    }
}
