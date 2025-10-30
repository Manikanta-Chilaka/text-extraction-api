from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import fitz  # PyMuPDF for PDF
from docx import Document  # python-docx for DOCX
import textract  # textract for DOC
import io
import os
from supabase import create_client, Client
from typing import Optional

app = FastAPI(title="Church App Text Extraction API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

class FileRequest(BaseModel):
    file_url: str
    song_id: Optional[str] = None

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF extraction failed: {str(e)}")

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX using python-docx"""
    try:
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DOCX extraction failed: {str(e)}")

def extract_text_from_doc(file_content: bytes) -> str:
    """Extract text from DOC using textract"""
    try:
        # Save to temp file for textract
        temp_file = "/tmp/temp_doc_file.doc"
        with open(temp_file, "wb") as f:
            f.write(file_content)
        text = textract.process(temp_file).decode('utf-8')
        os.remove(temp_file)
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DOC extraction failed: {str(e)}")

def extract_text_from_txt(file_content: bytes) -> str:
    """Extract text from TXT file"""
    try:
        return file_content.decode('utf-8').strip()
    except UnicodeDecodeError:
        try:
            return file_content.decode('latin-1').strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"TXT extraction failed: {str(e)}")

@app.post("/extract-text")
async def extract_text(request: FileRequest):
    """Extract text from uploaded file and optionally update Supabase"""
    try:
        # Download file from URL
        response = requests.get(request.file_url, timeout=30)
        response.raise_for_status()
        file_content = response.content
        
        # Determine file type and extract text
        file_url_lower = request.file_url.lower()
        
        if file_url_lower.endswith('.pdf'):
            text = extract_text_from_pdf(file_content)
        elif file_url_lower.endswith('.docx'):
            text = extract_text_from_docx(file_content)
        elif file_url_lower.endswith('.doc'):
            text = extract_text_from_doc(file_content)
        elif file_url_lower.endswith('.txt'):
            text = extract_text_from_txt(file_content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Supported: PDF, DOCX, DOC, TXT")
        
        # Update Supabase record if song_id provided
        if request.song_id:
            result = supabase.table('song_scripts').update({
                'content': text
            }).eq('id', request.song_id).execute()
            
            if not result.data:
                raise HTTPException(status_code=404, detail="Song record not found")
        
        return {
            "text": text,
            "status": "success",
            "file_type": file_url_lower.split('.')[-1],
            "updated_supabase": bool(request.song_id)
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Church App Text Extraction API",
        "supported_formats": ["PDF", "DOCX", "DOC", "TXT"],
        "endpoints": {
            "POST /extract-text": "Extract text from file URL"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))