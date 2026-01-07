# Agentic Recruitment Platform

An AI-powered recruitment platform that streamlines the job description creation process and automates resume ranking using advanced language models and document processing capabilities.

## 🚀 Features

- **AI-Powered JD Generation**: Create professional job descriptions using Groq LLM based on structured input fields
- **Document Extraction**: Extract job description fields from PDF and DOCX files automatically
- **Approval Workflow**: Manage job description approval and rejection with version tracking
- **Resume Ranking**: Automatically rank resumes against job descriptions using semantic similarity and keyword matching
- **Google Drive Integration**: Fetch and process resumes stored in Google Drive folders
- **Modern Web Interface**: Clean, responsive React frontend with Tailwind CSS styling
- **RESTful API**: FastAPI backend with comprehensive endpoints for all operations
- **Version Control**: Track changes and versions of job descriptions with timestamps

## 🛠 Tech Stack

### Backend
- **FastAPI**: High-performance web framework for building APIs
- **Python 3.8+**: Core programming language
- **Groq API**: For AI-powered text generation and processing
- **Google Drive API**: For resume document retrieval
- **Pydantic**: Data validation and serialization
- **Sentence Transformers**: For semantic similarity calculations
- **Document Processing**: pdfplumber, python-docx, pdfminer.six for PDF/DOCX handling

### Frontend
- **React 18**: Modern JavaScript library for building user interfaces
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API communication

### Infrastructure
- **Uvicorn**: ASGI server for FastAPI
- **CORS**: Cross-origin resource sharing support

## 📋 Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn package manager
- Google Cloud Platform account (for Drive integration)
- Groq API key

## 🔧 Installation and Setup

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
   ```

5. **Run the backend server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173` and the backend API at `http://localhost:8000`.

## 🌍 Environment Variables

Create a `.env` file in the backend root directory with the following variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | API key for Groq LLM services | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google service account JSON file | No (mock data used if not provided) |

## 📖 Usage

### Creating a Job Description

1. Access the web interface at `http://localhost:5173`
2. Fill in the job description fields:
   - Job title
   - Experience level
   - Mandatory skills
   - Nice-to-have skills
   - Location
   - Team size
   - Budget (optional)
   - Inclusion/exclusion criteria
3. Click "Generate JD" to create an AI-powered job description
4. Review and edit the generated text
5. Approve or reject the job description

### Extracting Fields from Documents

- Upload PDF or DOCX files containing job descriptions
- The system will automatically extract structured fields using AI
- Review extracted fields and confidence scores

### Resume Ranking

1. Create or select a job description
2. Provide a Google Drive folder URL containing resume PDFs
3. The system will:
   - Fetch all PDF files from the folder
   - Extract text content from resumes
   - Calculate semantic similarity scores
   - Rank candidates based on job requirements
   - Return detailed ranking with matched keywords and experience levels

## 📚 API Documentation

The API is built with FastAPI and includes automatic interactive documentation at `http://localhost:8000/docs`.

### Key Endpoints

#### Job Description Management
- `POST /jd/create` - Create a new job description
- `GET /jd/list` - List all job descriptions
- `GET /jd/{jd_id}` - Get specific job description
- `POST /jd/{jd_id}/approve` - Approve a job description
- `POST /jd/{jd_id}/reject` - Reject a job description
- `POST /jd/{jd_id}/regenerate` - Regenerate JD text

#### Document Processing
- `POST /jd/extract/text` - Extract fields from text
- `POST /jd/extract/file` - Extract fields from uploaded file (PDF/DOCX)

#### Resume Ranking
- `POST /jd/rank-resumes` - Rank resumes against a job description

#### Templates
- `GET /jd/templates` - Get available job description templates

### Example API Usage

```python
import requests

# Create a job description
jd_data = {
    "fields": {
        "title": "Senior Python Developer",
        "level": "Senior",
        "mandatory_skills": ["Python", "Django", "PostgreSQL"],
        "nice_to_have_skills": ["React", "AWS"],
        "location": "Remote",
        "team_size": 5
    }
}

response = requests.post("http://localhost:8000/jd/create", json=jd_data)
print(response.json())
```

## 📁 Project Structure

```
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application configuration
│   ├── models.py            # Pydantic data models
│   ├── storage.py           # In-memory data storage
│   ├── routes/
│   │   └── jd_routes.py     # Job description API routes
│   └── services/
│       ├── jd_service.py    # JD creation and management logic
│       ├── llm_service.py   # LLM integration service
│       └── resume_ranker.py # Resume ranking logic
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React application
│   │   ├── main.jsx         # React entry point
│   │   ├── index.css        # Global styles
│   │   ├── api/
│   │   │   └── jdApi.js     # API client functions
│   │   ├── components/
│   │   │   └── Navbar.jsx   # Navigation component
│   │   └── pages/
│   │       ├── JDCreate.jsx      # JD creation page
│   │       ├── JDList.jsx        # JD listing page
│   │       └── ResumeRanking.jsx # Resume ranking page
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel deployment config
├── .env                     # Environment variables
└── README.md               # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Write tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Rate Limiting with Groq API**
   - The application includes fallback mechanisms for rate-limited requests
   - Consider upgrading your Groq plan for full functionality

2. **Google Drive Integration**
   - Ensure proper service account credentials are configured
   - Check that the Drive folder is accessible to the service account
   - Mock data is used when credentials are not available

3. **Document Processing**
   - Supported formats: PDF and DOCX
   - Ensure documents are text-based (not image-based PDFs)

### Support

For issues and questions:
- Check the API documentation at `/docs`
- Review the code comments and docstrings
- Open an issue on the GitHub repository

---

Built with ❤️ using FastAPI, React, and AI-powered automation.
