from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class JDFields(BaseModel):
    title: str
    level: str
    mandatory_skills: List[str]
    nice_to_have_skills: Optional[List[str]] = []
    location: str
    team_size: Optional[int] = 1
    budget: Optional[str] = ""
    inclusion_criteria: Optional[List[str]] = []
    exclusion_criteria: Optional[List[str]] = []


class JDCreateRequest(BaseModel):
    fields: JDFields


class JDResponse(BaseModel):
    jd_id: str
    status: str
    fields: JDFields
    jd_text: str
    versions: List[Dict]
    created_at: datetime
    updated_at: datetime


class JDApproveResponse(BaseModel):
    jd_id: str
    status: str


class JDRejectRequest(BaseModel):
    reason: str


class JDUpdateTextRequest(BaseModel):
    jd_text: str


class JDExtractResponse(BaseModel):
    fields: JDFields
    confidence_scores: Dict[str, float]
    original_text: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None


class JDVersion(BaseModel):
    version_id: str
    timestamp: datetime
    status: str
    action: str
    fields: JDFields
    jd_text: str


class ResumeRankingRequest(BaseModel):
    jd_id: str
    drive_folder_url: str


class CandidateSummary(BaseModel):
    ucid: str
    job_id: str
    fit_score: float
    key_skills: List[str]
    experience_summary: str
    strengths: List[str]
    gaps: List[str]
    screening_decision: str


class ResumeRankingResult(BaseModel):
    rank: int
    resume_name: str
    candidate_name: Optional[str] = None
    score: float
    role_category: Optional[str] = None
    experience_level: Optional[float] = None
    matched_keywords: Optional[List[str]] = None
    status: Optional[str] = None
    candidate_summary: Optional[CandidateSummary] = None


class ResumeRankingResponse(BaseModel):
    jd_id: str
    drive_folder_id: str
    results: List[ResumeRankingResult]
