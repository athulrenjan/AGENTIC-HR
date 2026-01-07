import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, BackgroundTasks
from app.models import JDCreateRequest, JDResponse, JDApproveResponse, JDRejectRequest, JDUpdateTextRequest, JDExtractResponse, ResumeRankingRequest, ResumeRankingResponse
from app.services.jd_service import create_jd, approve_jd, reject_jd, regenerate_jd, update_jd_text, extract_fields_from_text, get_templates
from app.services.resume_ranker import extract_folder_id, get_drive_service, fetch_pdfs_from_drive, rank_resumes_against_jd
from app.storage import JD_STORE

router = APIRouter(prefix="/jd", tags=["Job Description"])

@router.post("/create", response_model=JDResponse)
def create_jd_api(payload: JDCreateRequest):
    jd = create_jd(payload.fields.dict())
    return jd


@router.post("/{jd_id}/approve", response_model=JDApproveResponse)
def approve_jd_api(jd_id: str):
    try:
        jd = approve_jd(jd_id)
        return {"jd_id": jd["jd_id"], "status": jd["status"]}
    except ValueError:
        raise HTTPException(status_code=404, detail="JD not found")


@router.post("/{jd_id}/reject")
def reject_jd_api(jd_id: str, payload: JDRejectRequest):
    try:
        jd = reject_jd(jd_id, payload.reason)
        return {"jd_id": jd["jd_id"], "status": jd["status"]}
    except ValueError:
        raise HTTPException(status_code=404, detail="JD not found")


@router.post("/{jd_id}/regenerate", response_model=JDResponse)
def regenerate_jd_api(jd_id: str):
    try:
        jd = regenerate_jd(jd_id)
        return jd
    except ValueError:
        raise HTTPException(status_code=404, detail="JD not found")


@router.post("/extract/text")
def extract_from_text_api(text: str = Query(..., description="JD text to extract fields from")):
    data = extract_fields_from_text(text)
    return data


@router.post("/extract/file")
def extract_from_file_api(file: UploadFile = File(...)):
    try:
        # Extract text from file
        if file.filename.lower().endswith('.pdf'):
            import pdfplumber
            with pdfplumber.open(file.file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        elif file.filename.lower().endswith('.docx'):
            from docx import Document
            doc = Document(file.file)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            text = "Unsupported file format"

        # Extract fields from the text
        from app.services.jd_service import extract_fields_from_text
        result = extract_fields_from_text(text)
        result["file_name"] = file.filename
        result["file_size"] = len(text.encode('utf-8'))
        return result

    except Exception as e:
        # Return mock data on error
        return {
            "fields": {
                "title": "Extracted from File",
                "level": "Mid",
                "mandatory_skills": ["Python", "Testing"],
                "nice_to_have_skills": [],
                "location": "Remote",
                "team_size": 1,
                "budget": "",
                "inclusion_criteria": [],
                "exclusion_criteria": []
            },
            "confidence_scores": {"title": 0.8, "level": 0.7, "mandatory_skills": 0.6, "location": 0.9},
            "file_name": file.filename,
            "file_size": 0,
            "error": str(e)
        }


@router.get("/templates")
def get_templates_api():
    return get_templates()


@router.get("/list")
def list_jds():
    return list(JD_STORE.values())


@router.get("/{jd_id}")
def get_jd_api(jd_id: str):
    jd = JD_STORE.get(jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="JD not found")
    return jd


@router.post("/rank-resumes", response_model=ResumeRankingResponse)
def rank_resumes_api(request: ResumeRankingRequest, background_tasks: BackgroundTasks):
    try:
        # Get JD from storage
        jd = JD_STORE.get(request.jd_id)
        if not jd:
            raise HTTPException(status_code=404, detail="JD not found")

        # Extract folder ID from URL
        folder_id = extract_folder_id(request.drive_folder_url)

        # Note: In production, you'd pass the actual credentials path
        # For now, this is a placeholder - credentials need to be configured
        credentials_path = "path/to/service-account.json"  # TODO: Configure this

        try:
            # Check if credentials file exists
            credentials_path = "app/credentials.json"
            if not os.path.exists(credentials_path):
                # Return mock results if no credentials
                mock_results = [
                    {
                        "rank": 1,
                        "resume_name": "John_Doe_Resume.pdf",
                        "score": 0.85,
                        "role_category": "development",
                        "experience_level": 0.8,
                        "matched_keywords": ["Python", "Django", "React", "SQL"],
                        "status": "High Match"
                    },
                    {
                        "rank": 2,
                        "resume_name": "Jane_Smith_Resume.pdf",
                        "score": 0.78,
                        "role_category": "development",
                        "experience_level": 0.6,
                        "matched_keywords": ["Python", "JavaScript", "Node.js"],
                        "status": "High Match"
                    },
                    {
                        "rank": 3,
                        "resume_name": "Bob_Johnson_Resume.pdf",
                        "score": 0.72,
                        "role_category": "testing",
                        "experience_level": 0.7,
                        "matched_keywords": ["Selenium", "Java", "TestNG"],
                        "status": "Medium Match"
                    },
                    {
                        "rank": 4,
                        "resume_name": "Alice_Williams_Resume.pdf",
                        "score": 0.68,
                        "role_category": "development",
                        "experience_level": 0.5,
                        "matched_keywords": ["Python", "Flask"],
                        "status": "Medium Match"
                    },
                    {
                        "rank": 5,
                        "resume_name": "Charlie_Brown_Resume.pdf",
                        "score": 0.65,
                        "role_category": "general",
                        "experience_level": 0.4,
                        "matched_keywords": ["Communication", "Teamwork"],
                        "status": "Low Match"
                    }
                ]
                return {
                    "jd_id": request.jd_id,
                    "drive_folder_id": folder_id,
                    "results": mock_results,
                    "note": "Using mock data - Google credentials not configured"
                }

            # Use actual Drive integration if credentials exist
            service = get_drive_service(credentials_path)
            pdfs = fetch_pdfs_from_drive(service, folder_id)
            results = rank_resumes_against_jd(jd["jd_text"], pdfs)

            # Ensure all required fields are present in results
            for result in results:
                if 'role_category' not in result:
                    result['role_category'] = 'general'
                if 'experience_level' not in result:
                    result['experience_level'] = 0.0
                if 'matched_keywords' not in result:
                    result['matched_keywords'] = []
                if 'status' not in result:
                    result['status'] = 'Low Match'

            return {
                "jd_id": request.jd_id,
                "drive_folder_id": folder_id,
                "results": results
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Resume ranking error: {str(e)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
