from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import requests
import fitz  # PyMuPDF for PDF
from docx import Document  # python-docx for DOCX
import textract  # textract for DOC
import io
import os
from supabase import create_client, Client
from typing import Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Church App Text Extraction API",
    description="Extract text from PDF, DOCX, DOC, and TXT files",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    logger.warning("Supabase environment variables not set. Database updates will be disabled.")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")
        supabase = None

class FileRequest(BaseModel):
    file_url: HttpUrl
    song_id: Optional[str] = None

class ExtractionResponse(BaseModel):
    text: str
    status: str
    file_type: str
    updated_supabase: bool
    char_count: int
    timestamp: str

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            if page_text.strip():
                text += f"--- Page {page_num} ---\n{page_text}\n\n"
        doc.close()
        
        if not text.strip():
            raise ValueError("No text found in PDF. PDF might be image-based.")
        
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"PDF extraction failed: {str(e)}")

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX using python-docx"""
    try:
        doc = Document(io.BytesIO(file_content))
        text = ""
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
        
        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text += cell.text + "\n"
        
        if not text.strip():
            raise ValueError("No text found in DOCX file.")
        
        return text.strip()
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"DOCX extraction failed: {str(e)}")

def extract_text_from_doc(file_content: bytes) -> str:
    """Extract text from DOC using textract"""
    temp_file = None
    try:
        # Save to temp file for textract
        temp_file = f"/tmp/temp_doc_{os.getpid()}.doc"
        with open(temp_file, "wb") as f:
            f.write(file_content)
        
        text = textract.process(temp_file).decode('utf-8')
        
        if not text.strip():
            raise ValueError("No text found in DOC file.")
        
        return text.strip()
    except Exception as e:
        logger.error(f"DOC extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"DOC extraction failed: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass

def extract_text_from_txt(file_content: bytes) -> str:
    """Extract text from TXT file with multiple encoding attempts"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            text = file_content.decode(encoding).strip()
            if text:
                return text
        except (UnicodeDecodeError, AttributeError):
            continue
    
    raise HTTPException(status_code=400, detail="Failed to decode text file with supported encodings")

async def update_supabase_record(song_id: str, text: str):
    """Background task to update Supabase"""
    if not supabase:
        logger.warning("Supabase not configured, skipping database update")
        return
    
    try:
        result = supabase.table('song_scripts').update({
            'content': text,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', song_id).execute()
        
        if result.data:
            logger.info(f"Successfully updated song_id: {song_id}")
        else:
            logger.warning(f"No record found for song_id: {song_id}")
    except Exception as e:
        logger.error(f"Supabase update error: {e}")

@app.post("/extract-text", response_model=ExtractionResponse)
async def extract_text(request: FileRequest, background_tasks: BackgroundTasks):
    """
    Extract text from uploaded file and optionally update Supabase
    
    Supported formats: PDF, DOCX, DOC, TXT
    """
    try:
        logger.info(f"Processing file: {request.file_url}")
        
        # Download file from URL
        response = requests.get(str(request.file_url), timeout=60)
        response.raise_for_status()
        file_content = response.content
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Downloaded file is empty")
        
        # Determine file type and extract text
        file_url_lower = str(request.file_url).lower()
        
        if file_url_lower.endswith('.pdf'):
            text = extract_text_from_pdf(file_content)
            file_type = "pdf"
        elif file_url_lower.endswith('.docx'):
            text = extract_text_from_docx(file_content)
            file_type = "docx"
        elif file_url_lower.endswith('.doc'):
            text = extract_text_from_doc(file_content)
            file_type = "doc"
        elif file_url_lower.endswith('.txt'):
            text = extract_text_from_txt(file_content)
            file_type = "txt"
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Supported formats: PDF, DOCX, DOC, TXT"
            )
        
        # Schedule Supabase update in background if song_id provided
        updated_supabase = False
        if request.song_id and supabase:
            background_tasks.add_task(update_supabase_record, request.song_id, text)
            updated_supabase = True
        
        logger.info(f"Successfully extracted {len(text)} characters from {file_type}")
        
        return ExtractionResponse(
            text=text,
            status="success",
            file_type=file_type,
            updated_supabase=updated_supabase,
            char_count=len(text),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except requests.RequestException as e:
        logger.error(f"File download error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to download file: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@app.get("/")
async def root():
    return {
        "service": "Church App Text Extraction API",
        "version": "1.0.0",
        "status": "operational",
        "supported_formats": ["PDF", "DOCX", "DOC", "TXT"],
        "endpoints": {
            "POST /extract-text": "Extract text from file URL",
            "GET /health": "Health check endpoint"
        },
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    supabase_status = "connected" if supabase else "disabled"
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "supabase": supabase_status
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )