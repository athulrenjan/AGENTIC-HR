from pathlib import Path
import re
import tempfile
import os
import numpy as np
from typing import List, Dict

import pdfminer.high_level as pdfminer
from sentence_transformers import SentenceTransformer, CrossEncoder, util

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import io
import signal
import logging
import platform
import threading
import time
import ssl

from app.services.llm_service import call_llm

# Set up logging
logger = logging.getLogger(__name__)


# =========================================================
# JD-DRIVEN KEYWORD EXTRACTION
# =========================================================
def extract_role_keywords(jd_text: str, top_n: int = 25) -> List[str]:
    """
    Extract skill-focused keywords from JD (role-agnostic)
    """
    # Add technical skill patterns
    tech_patterns = [
        r"\b[A-Z]{2,}[+#.]?\b",  # SQL, HTML5, React.js
        r"\b\w+\.js\b",  # Node.js, React.js
        r"\b\w+\.py\b",  # Django.py
    ]

    # Extract common skills regardless of role
    skill_categories = {
        "testing": ["selenium", "testng", "jira", "postman", "manual", "automation"],
        "dev": ["python", "java", "react", "node", "sql"],
        "tools": ["git", "docker", "jenkins", "aws"],
    }

    words = re.findall(r"[a-zA-Z][a-zA-Z+.#]{2,}", jd_text.lower())

    # Boost technical terms
    for pattern in tech_patterns:
        words.extend(re.findall(pattern, jd_text, re.I))

    # Add predefined skills if present
    for category, skills in skill_categories.items():
        for skill in skills:
            if skill in jd_text.lower():
                words.append(skill)

    stopwords = {
        "and","the","with","for","this","that","will","should","must",
        "experience","knowledge","ability","skills","role","responsibilities",
        "requirements","team","environment","work","using"
    }

    freq = {}
    for w in words:
        if w not in stopwords and not w.isdigit():
            freq[w] = freq.get(w, 0) + 1

    # 🔥 bias towards SKILLS, not generic nouns
    skill_like = [
        w for w in freq
        if w in jd_text.lower() and (
            len(w) >= 4 or "+" in w or "." in w
        )
    ]

    ranked = sorted(skill_like, key=lambda w: freq[w], reverse=True)
    return ranked[:top_n]


def jd_keyword_boost(resume_text: str, jd_keywords: List[str]) -> float:
    resume_l = resume_text.lower()
    hits = sum(1 for kw in jd_keywords if kw in resume_l)
    return min(hits / len(jd_keywords), 1.0)


def role_category_detection(jd_text: str) -> str:
    """
    Detect general role category to adjust matching weights
    """
    text_lower = jd_text.lower()

    if any(word in text_lower for word in ["tester", "qa", "quality", "testing"]):
        return "testing"
    elif any(word in text_lower for word in ["developer", "engineer", "full stack"]):
        return "development"
    elif any(word in text_lower for word in ["analyst", "data", "business"]):
        return "analyst"
    elif any(word in text_lower for word in ["devops", "cloud", "infrastructure"]):
        return "devops"
    return "general"


def calculate_dynamic_weights(role_category: str) -> Dict[str, float]:
    """
    Adjust weights based on role type
    """
    weights = {
        "testing": {"bi_encoder": 0.40, "cross_encoder": 0.35, "keywords": 0.25},
        "development": {"bi_encoder": 0.35, "cross_encoder": 0.40, "keywords": 0.25},
        "general": {"bi_encoder": 0.45, "cross_encoder": 0.40, "keywords": 0.15}
    }
    return weights.get(role_category, weights["general"])


def extract_candidate_name(resume_text: str) -> str:
    """
    Extract candidate name from resume text
    """
    # Common name patterns
    name_patterns = [
        r"^([A-Z][a-z]+ [A-Z][a-z]+)",  # First Last
        r"^([A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+)",  # First M. Last
        r"^([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)",  # First Middle Last
        r"Name[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)",  # Name: First Last
        r"([A-Z][a-z]+ [A-Z][a-z]+).*?\n.*?(?:email|contact|phone)",  # Name followed by contact info
        r"([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+).*?\n.*?(?:email|contact|phone)",  # First Middle Last followed by contact
        r"([A-Z]+ [A-Z]+)",  # ALL CAPS First Last
        r"([A-Z]+ [A-Z]+ [A-Z]+)",  # ALL CAPS First Middle Last
    ]

    # Check first 15 lines for name
    lines = resume_text.strip().split('\n')[:15]
    text_sample = ' '.join(lines)

    for pattern in name_patterns:
        matches = re.findall(pattern, text_sample, re.MULTILINE | re.I)
        for match in matches:
            name = match.strip()
            words = name.split()
            # Validate: 2-4 words, each starting with upper case or all caps
            if 2 <= len(words) <= 4 and all(word and (word[0].isupper() or word.isupper()) for word in words):
                # Convert to title case if all caps
                if name.isupper():
                    name = name.title()
                return name

    # Fallback: search entire text for name patterns
    for pattern in name_patterns:
        matches = re.findall(pattern, resume_text, re.MULTILINE | re.I)
        for match in matches:
            name = match.strip()
            words = name.split()
            if 2 <= len(words) <= 4 and all(word and (word[0].isupper() or word.isupper()) for word in words):
                if name.isupper():
                    name = name.title()
                return name

    # Additional fallback: look for names in specific sections
    sections = ["summary", "objective", "profile", "about", "personal", "contact"]
    for section in sections:
        section_match = re.search(rf"(?:{section}).*?\n(.*?)\n", resume_text, re.I | re.S)
        if section_match:
            section_text = section_match.group(1)
            for pattern in name_patterns:
                matches = re.findall(pattern, section_text, re.MULTILINE | re.I)
                for match in matches:
                    name = match.strip()
                    words = name.split()
                    if 2 <= len(words) <= 4 and all(word and (word[0].isupper() or word.isupper()) for word in words):
                        if name.isupper():
                            name = name.title()
                        return name

    # Last resort: try to find any capitalized phrase that looks like a name
    potential_names = re.findall(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', resume_text)
    if potential_names:
        # Return the first one that appears early in the text
        for name in potential_names:
            if resume_text.find(name) < 500:  # Within first 500 chars
                return name

    return "Unknown Candidate"


def extract_experience_level(resume_text: str) -> float:
    """
    Extract and normalize experience level
    """
    patterns = [
        r"(\d+)\s*(?:year|yr)s?.*?experience",
        r"experience.*?(\d+)\s*(?:year|yr)",
        r"(fresher|entry level|junior|senior|lead)",
    ]

    exp_years = 0
    for pattern in patterns:
        match = re.search(pattern, resume_text.lower())
        if match:
            group1 = match.group(1)
            if group1.isdigit():
                exp_years = float(group1)
            else:
                level = group1
                if "senior" in level:
                    exp_years = 5.0
                elif "junior" in level:
                    exp_years = 2.0
                elif "fresher" in level:
                    exp_years = 0.5
                elif "entry level" in level:
                    exp_years = 1.0

    return min(exp_years / 10.0, 1.0)  # Normalize to 0-1


def extract_candidate_summary(resume_text: str) -> str:
    """
    Generate a short 2-3 sentence summary of the candidate using LLM
    """
    # Limit to first 2000 chars to avoid token limits
    limited_text = resume_text[:2000]
    prompt = f"""
    Based on the following resume text, provide a concise 2-3 sentence summary of the candidate's background, skills, and experience.

    Resume Text:
    {limited_text}

    Summary:
    """
    try:
        summary = call_llm(prompt)
        return summary.strip()
    except Exception as e:
        return "Summary not available."


def extract_experience_summary(resume_text: str) -> str:
    """
    Extract a summary of the candidate's experience
    """
    patterns = [
        r"(\d+)\s*(?:year|yr)s?.*?experience",
        r"experience.*?(\d+)\s*(?:year|yr)",
    ]
    for pattern in patterns:
        match = re.search(pattern, resume_text.lower())
        if match:
            years = match.group(1)
            return f"{years} years of experience"
    return "Experience level not specified"


def extract_strengths(resume_text: str, jd_keywords: List[str]) -> List[str]:
    """
    Extract strengths based on matched keywords
    """
    matched = [kw for kw in jd_keywords if kw in resume_text.lower()]
    return matched[:5]  # Top 5


def extract_gaps(resume_text: str, jd_keywords: List[str]) -> List[str]:
    """
    Extract gaps based on unmatched keywords
    """
    unmatched = [kw for kw in jd_keywords if kw not in resume_text.lower()]
    return unmatched[:5]  # Top 5


# =========================================================
# GOOGLE DRIVE CONFIG
# =========================================================
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def get_drive_service(credentials_json_path: str):
    creds = Credentials.from_service_account_file(
        credentials_json_path, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def extract_folder_id(drive_url: str) -> str:
    """
    Extract folder ID from Google Drive URL
    """
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", drive_url)
    if not match:
        raise ValueError("Invalid Google Drive folder URL")
    return match.group(1)


def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def run_with_timeout(func, timeout_seconds):
    """Cross-platform timeout wrapper"""
    if platform.system() == "Windows":
        # Use threading for Windows
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout_seconds)

        if thread.is_alive():
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
        if exception[0]:
            raise exception[0]
        return result[0]
    else:
        # Use signal for Unix-like systems
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        try:
            return func()
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

def fetch_pdfs_from_drive(service, folder_id: str, timeout_seconds: int = 60, max_retries: int = 5) -> Dict[str, bytes]:
    """
    Download all PDF files from a Drive folder with timeout and retry logic
    """
    logger.info(f"Fetching PDFs from folder {folder_id}")

    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        logger.warning(f"No PDF files found in folder {folder_id}")
        return {}

    logger.info(f"Found {len(files)} PDF files to download")

    pdfs = {}
    for file in files:
        file_name = file["name"]
        logger.info(f"Downloading {file_name}")

        for attempt in range(max_retries):
            if attempt > 0:
                sleep_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying download for {file_name} in {sleep_time} seconds (attempt {attempt + 1}/{max_retries})")
                time.sleep(sleep_time)

            try:
                def download_file():
                    request = service.files().get_media(fileId=file["id"])
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        _, done = downloader.next_chunk()
                    return fh.getvalue()

                pdfs[file_name] = run_with_timeout(download_file, timeout_seconds)
                logger.info(f"Successfully downloaded {file_name}")
                break  # Success, exit retry loop

            except TimeoutError:
                logger.warning(f"Timeout downloading {file_name} (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to download {file_name} after {max_retries} attempts")
                    continue  # Skip this file
            except ssl.SSLError as e:
                logger.warning(f"SSL error downloading {file_name}: {str(e)} (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to download {file_name} after {max_retries} attempts due to SSL errors")
                    continue  # Skip this file
            except Exception as e:
                logger.error(f"Error downloading {file_name}: {str(e)}")
                if attempt == max_retries - 1:
                    continue  # Skip this file

    logger.info(f"Downloaded {len(pdfs)} out of {len(files)} PDF files successfully")
    return pdfs


# =========================================================
# TEXT EXTRACTION
# =========================================================
def extract_text_from_pdf_bytes(pdf_bytes: bytes, timeout_seconds: int = 10) -> str:
    """
    Extract text from PDF bytes with timeout handling
    """
    def _extract_with_timeout():
        try:
            # Try pdfminer first
            temp_file = None
            try:
                temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                temp_file.write(pdf_bytes)
                temp_file.close()  # Close the file so pdfminer can read it

                text = pdfminer.extract_text(temp_file.name) or ""
                if text.strip():  # If we got meaningful text, return it
                    os.unlink(temp_file.name)
                    return text
            except Exception:
                pass
            finally:
                if temp_file and os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

            # Fallback to PyPDF2 if pdfminer fails
            try:
                import PyPDF2
                pdf_file = io.BytesIO(pdf_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                if text.strip():
                    return text
            except Exception:
                pass

            # Fallback to PyMuPDF if available
            try:
                import fitz  # PyMuPDF
                pdf_file = io.BytesIO(pdf_bytes)
                doc = fitz.open(stream=pdf_file, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                if text.strip():
                    return text
            except Exception:
                pass

            # Final fallback: OCR for image-based PDFs
            try:
                import pytesseract
                from PIL import Image
                import fitz  # Try to use PyMuPDF for image extraction

                pdf_file = io.BytesIO(pdf_bytes)
                doc = fitz.open(stream=pdf_file, filetype="pdf")
                text = ""

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    page_text = pytesseract.image_to_string(img)
                    text += page_text + "\n"

                if text.strip():
                    return text
            except Exception:
                pass

            return ""
        except Exception:
            return ""

    try:
        return run_with_timeout(_extract_with_timeout, timeout_seconds)
    except TimeoutError:
        logger.warning(f"Text extraction timed out after {timeout_seconds} seconds")
        return ""
    except Exception as e:
        logger.error(f"Error during text extraction: {str(e)}")
        return ""


def clean_text(text: str) -> str:
    text = text.replace("\x0c", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def chunk_text(text, max_words=250, max_chunks=5):
    words = text.split()
    chunks = [
        " ".join(words[i:i+max_words])
        for i in range(0, len(words), max_words)
    ]
    return chunks[:max_chunks]


def extract_relevant_sections(text: str, role_category: str = "general") -> str:
    """
    Role-aware section extraction
    """
    section_priority = {
        "testing": ["skills", "experience", "projects", "tools", "certifications"],
        "development": ["skills", "projects", "experience", "education", "github"],
        "general": ["experience", "skills", "education", "summary"]
    }

    sections = []
    priority = section_priority.get(role_category, section_priority["general"])

    for section in priority:
        pattern = rf"({section})(.*?)(\n[A-Z ]{{3,}}|\Z)"
        matches = re.finditer(pattern, text, re.I | re.S)
        for m in matches:
            sections.append(m.group(0))

    return "\n".join(sections) if sections else text


# =========================================================
# RANKING PIPELINE
# =========================================================
def classify_match_by_rank(rank: int, total: int) -> str:
    if rank == 1:
        return "High Match"
    elif rank <= max(2, total // 2):
        return "Medium Match"
    else:
        return "Low Match"

def rank_resumes_against_jd(
    jd_text: str,
    resumes: Dict[str, bytes],
    top_k: int = 7
) -> List[Dict]:

    # Detect role type
    role_category = role_category_detection(jd_text)
    weights = calculate_dynamic_weights(role_category)

    embed_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    cross_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    jd_text = clean_text(jd_text)
    jd_keywords = extract_role_keywords(jd_text)
    jd_emb = embed_model.encode(jd_text, convert_to_tensor=True)

    resume_texts = {}
    candidate_names = {}
    candidate_summaries = {}
    for name, pdf_bytes in resumes.items():
        full_text = extract_text_from_pdf_bytes(pdf_bytes)
        full_text = clean_text(full_text)
        candidate_name = extract_candidate_name(full_text)
        summary = extract_candidate_summary(full_text)
        text = extract_relevant_sections(full_text, role_category)
        resume_texts[name] = text
        candidate_names[name] = candidate_name
        candidate_summaries[name] = summary

    bi_scores = {}
    for name, text in resume_texts.items():
        chunks = chunk_text(text)
        if not chunks:
            bi_scores[name] = 0.0
        else:
            embs = embed_model.encode(chunks, convert_to_tensor=True)
            bi_scores[name] = float(util.cos_sim(jd_emb, embs).max())

    top_candidates = sorted(
        bi_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_k]

    pairs = [(jd_text, resume_texts[name]) for name, _ in top_candidates]
    cross_scores = cross_model.predict(pairs)

    cross_scores = np.array(cross_scores)
    cross_norm = 1 / (1 + np.exp(-cross_scores))  # sigmoid

    final_results = []
    for (name, bi), cross in zip(top_candidates, cross_norm):
        # Calculate all components
        boost = jd_keyword_boost(resume_texts[name], jd_keywords)
        exp_level = extract_experience_level(resume_texts[name])

        # Weighted scoring with role-specific weights
        final_score = (
            weights["bi_encoder"] * bi +
            weights["cross_encoder"] * cross +
            weights["keywords"] * boost
        )

        # Optional: Adjust for seniority if JD mentions experience
        if "year" in jd_text.lower() or "experience" in jd_text.lower():
            exp_match = 1.0 - abs(exp_level - extract_experience_level(jd_text))
            final_score = 0.8 * final_score + 0.2 * exp_match

        # Extract additional fields
        exp_summary = extract_experience_summary(resume_texts[name])
        strengths = extract_strengths(resume_texts[name], jd_keywords)
        gaps = extract_gaps(resume_texts[name], jd_keywords)

        final_results.append({
            "rank": 0,  # Will be updated later
            "resume_name": name,
            "score": round(float(final_score), 4),
            "candidate_name": candidate_names[name],
            "role_category": role_category,
            "experience_level": extract_experience_level(resume_texts[name]),
            "matched_keywords": [
                kw for kw in jd_keywords if kw in resume_texts[name].lower()
            ][:10],
            "status": classify_match_by_rank(0, 1),  # Will be updated later
            "candidate_summary": {
                "ucid": f"UCID-{name[:8]}",
                "job_id": "JOB-001",
                "fit_score": round(float(final_score), 4),
                "key_skills": [
                    kw for kw in jd_keywords if kw in resume_texts[name].lower()
                ][:10],
                "experience_summary": exp_summary,
                "strengths": strengths,
                "gaps": gaps,
                "screening_decision": classify_match_by_rank(0, 1)  # Will be updated later
            }
        })

    # Sort by score in descending order
    final_results.sort(key=lambda x: x["score"], reverse=True)

    # Update ranks and status after sorting
    for i, result in enumerate(final_results, start=1):
        result["rank"] = i
        result["status"] = classify_match_by_rank(i, len(final_results))
        result["candidate_summary"]["screening_decision"] = classify_match_by_rank(i, len(final_results))

    return final_results
