# Python Text Extraction Backend

Extracts text from **PDF, DOCX, DOC, TXT** files and updates Supabase.

## 🚀 Local Setup

1. **Install dependencies:**
```bash
cd python-backend
pip install -r requirements.txt
```

2. **Update `.env` with Supabase credentials:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

3. **Run server:**
```bash
python main.py
```

## 🌐 Deploy to Render

1. **Push to GitHub**
2. **Go to [render.com](https://render.com)**
3. **Create New Web Service**
4. **Connect GitHub repo**
5. **Settings:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Environment Variables:**
     - `SUPABASE_URL` = your Supabase URL
     - `SUPABASE_SERVICE_KEY` = your service role key
6. **Deploy**

## 🔗 Connect to React Native App

**Update your `.env` in React Native:**
```env
PYTHON_EXTRACTION_API=https://your-render-app.onrender.com/extract-text
```

**Update `lib/ocr.ts`:**
```typescript
export async function extractTextFromFile(fileUrl: string, songId: string): Promise<string> {
  try {
    const response = await fetch(process.env.PYTHON_EXTRACTION_API!, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        file_url: fileUrl,
        song_id: songId 
      }),
    });
    
    const data = await response.json();
    return data.text || '';
  } catch (error) {
    console.error('Text extraction failed:', error);
    return '';
  }
}
```

## 📋 API Endpoints

**POST `/extract-text`**
```json
{
  "file_url": "https://supabase-storage-url/file.pdf",
  "song_id": "uuid-of-song-record"
}
```

**Response:**
```json
{
  "text": "extracted text content",
  "status": "success",
  "file_type": "pdf",
  "updated_supabase": true
}
```

## 🔧 Supabase Integration

1. **Get Service Role Key** from Supabase Dashboard → Settings → API
2. **Set Environment Variables** in Render
3. **API automatically updates** `song_scripts` table with extracted text

## 📁 Supported File Types

- **PDF** - PyMuPDF extraction
- **DOCX** - python-docx extraction  
- **DOC** - textract extraction
- **TXT** - UTF-8/Latin-1 decoding