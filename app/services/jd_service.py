import uuid
import json
from datetime import datetime
from app.services.llm_service import call_llm
from app.storage import JD_STORE, JD_TEMPLATES
from datetime import datetime

def generate_jd_text(fields: dict) -> str:
    try:
        prompt = f"""
You are a professional HR recruiter creating a job description. Based on the following structured data, generate a complete, professional job description.

INPUT DATA:
- Title: {fields.get('title', 'N/A')}
- Level: {fields.get('level', 'N/A')}
- Mandatory Skills: {', '.join(fields.get('mandatory_skills', []))}
- Nice to Have Skills: {', '.join(fields.get('nice_to_have_skills', []))}
- Location: {fields.get('location', 'N/A')}
- Team Size: {fields.get('team_size', 'N/A')}
- Budget: {fields.get('budget', 'N/A')}
- Inclusion Criteria: {', '.join(fields.get('inclusion_criteria', []))}
- Exclusion Criteria: {', '.join(fields.get('exclusion_criteria', []))}

INSTRUCTIONS:
1. Create a professional, well-structured job description with these sections:
   - Job Title and Employment Type
   - About the Role / Company Introduction
   - Key Responsibilities (bullet points)
   - Required Qualifications (bullet points)
   - Nice-to-Have Skills (optional section)
   - What We Offer / Benefits (if applicable)

2. IMPORTANT RULES:
   - Do NOT include any email addresses, contact information, or application instructions
   - Do NOT mention "how to apply" or submission details
   - Do NOT include company names unless specified in the input
   - Do NOT add generic company information not provided in the input
   - Keep content focused and relevant to the provided data
   - Use professional, clear language
   - Make it suitable for the specified role level and skills

3. CONTENT GUIDELINES:
   - Expand on the provided skills and responsibilities naturally
   - Use the location and team size information appropriately
   - If budget is provided, mention compensation contextually
   - Focus on creating an attractive, accurate description for the role

Return ONLY the formatted job description text. No additional commentary, explanations, or metadata.
"""
        return call_llm(prompt)
    except RuntimeError as e:
        if "rate limit" in str(e).lower():
            # Fallback: Generate a basic JD text from fields
            title = fields.get('title', 'Job Title')
            level = fields.get('level', 'Mid-level')
            skills = ', '.join(fields.get('mandatory_skills', []))
            location = fields.get('location', 'Remote')
            return f"""
{title} ({level})

We are seeking a talented {title} to join our team.

Key Responsibilities:
- Utilize skills in {skills} to contribute to projects
- Collaborate with team members to achieve goals

Required Qualifications:
- Experience with {skills}
- Located in {location}

This is a generated job description due to API limitations. Please upgrade your Groq plan for full functionality.
"""
        else:
            raise


def extract_fields_from_text(text: str) -> dict:
    try:
        prompt = f"""
Extract structured job description fields from the following text. Return a JSON object with the following keys:
- title: string
- level: string (e.g., Junior, Mid, Senior)
- mandatory_skills: array of strings
- nice_to_have_skills: array of strings
- location: string
- team_size: number or null
- budget: string or null
- inclusion_criteria: array of strings
- exclusion_criteria: array of strings

Also include confidence_scores for each field (0-1).

Text:
{text}

Return ONLY valid JSON.
"""
        response = call_llm(prompt)
        try:
            data = json.loads(response)
            return {
                "fields": {k: v for k, v in data.items() if k != "confidence_scores"},
                "confidence_scores": data.get("confidence_scores", {}),
                "original_text": text
            }
        except:
            # Fallback extraction
            return {
                "fields": {
                    "title": "Extracted Title",
                    "level": "Mid",
                    "mandatory_skills": [],
                    "nice_to_have_skills": [],
                    "location": "Remote",
                    "team_size": 1,
                    "budget": "",
                    "inclusion_criteria": [],
                    "exclusion_criteria": []
                },
                "confidence_scores": {k: 0.5 for k in ["title", "level", "mandatory_skills", "location"]},
                "original_text": text
            }
    except RuntimeError as e:
        if "rate limit" in str(e).lower():
            # Fallback extraction when rate limited
            return {
                "fields": {
                    "title": "Rate Limited - Basic Extraction",
                    "level": "Mid",
                    "mandatory_skills": ["Please upgrade Groq plan for full extraction"],
                    "nice_to_have_skills": [],
                    "location": "Remote",
                    "team_size": 1,
                    "budget": "",
                    "inclusion_criteria": [],
                    "exclusion_criteria": []
                },
                "confidence_scores": {k: 0.1 for k in ["title", "level", "mandatory_skills", "location"]},
                "original_text": text,
                "error": "Rate limit exceeded. Using basic extraction."
            }
        else:
            raise


def create_jd(fields: dict):
    jd_id = f"JD-{uuid.uuid4().hex[:8].upper()}"
    jd_text = generate_jd_text(fields)
    now = datetime.now()

    version = {
        "version_id": f"V1-{uuid.uuid4().hex[:4].upper()}",
        "timestamp": now,
        "status": "DRAFT",
        "action": "Created",
        "fields": fields,
        "jd_text": jd_text
    }

    JD_STORE[jd_id] = {
        "jd_id": jd_id,
        "status": "DRAFT",
        "fields": fields,
        "jd_text": jd_text,
        "versions": [version],
        "created_at": now,
        "updated_at": now
    }
    return JD_STORE[jd_id]


def approve_jd(jd_id: str):
    jd = JD_STORE.get(jd_id)
    if not jd:
        raise ValueError("JD not found")

    jd["status"] = "APPROVED"
    jd["updated_at"] = datetime.now()
    # Add version
    version = {
        "version_id": f"V{len(jd['versions'])+1}-{uuid.uuid4().hex[:4].upper()}",
        "timestamp": jd["updated_at"],
        "status": "APPROVED",
        "action": "Approved",
        "fields": jd["fields"],
        "jd_text": jd["jd_text"]
    }
    jd["versions"].append(version)
    return jd


def reject_jd(jd_id: str, reason: str):
    jd = JD_STORE.get(jd_id)
    if not jd:
        raise ValueError("JD not found")

    jd["status"] = "REJECTED"
    jd["updated_at"] = datetime.now()
    # Add version
    version = {
        "version_id": f"V{len(jd['versions'])+1}-{uuid.uuid4().hex[:4].upper()}",
        "timestamp": jd["updated_at"],
        "status": "REJECTED",
        "action": f"Rejected: {reason}",
        "fields": jd["fields"],
        "jd_text": jd["jd_text"]
    }
    jd["versions"].append(version)
    return jd


def regenerate_jd(jd_id: str):
    jd = JD_STORE.get(jd_id)
    if not jd:
        raise ValueError("JD not found")

    jd["jd_text"] = generate_jd_text(jd["fields"])
    jd["updated_at"] = datetime.now()
    # Add version
    version = {
        "version_id": f"V{len(jd['versions'])+1}-{uuid.uuid4().hex[:4].upper()}",
        "timestamp": jd["updated_at"],
        "status": jd["status"],
        "action": "Regenerated",
        "fields": jd["fields"],
        "jd_text": jd["jd_text"]
    }
    jd["versions"].append(version)
    return jd


def update_jd_text(jd_id: str, new_jd_text: str):
    jd = JD_STORE.get(jd_id)
    if not jd:
        raise ValueError("JD not found")

    jd["jd_text"] = new_jd_text
    jd["updated_at"] = datetime.now()
    # Add version
    version = {
        "version_id": f"V{len(jd['versions'])+1}-{uuid.uuid4().hex[:4].upper()}",
        "timestamp": jd["updated_at"],
        "status": jd["status"],
        "action": "Updated Text",
        "fields": jd["fields"],
        "jd_text": jd["jd_text"]
    }
    jd["versions"].append(version)
    return jd


def get_templates():
    return JD_TEMPLATES
