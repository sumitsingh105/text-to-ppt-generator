from fastapi import FastAPI, HTTPException, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import logging
import os
import uuid
import tempfile
from datetime import datetime

from app.services.llm_service import LLMService
from app.services.ppt_service import PPTService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Text-to-PowerPoint Generator", version="1.0.0")

# UPDATED CORS configuration - ADD YOUR STREAMLIT URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501", 
        "http://localhost:8502", 
        "http://frontend:8501",
        "https://your-streamlit-app.streamlit.app",  # Add your actual Streamlit URL here
        "*"  # Temporarily allow all origins for testing
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# In-memory storage for generation tasks
generation_tasks = {}

class TextToSlidesRequest(BaseModel):
    text: str
    guidance: Optional[str] = None
    tone: Optional[str] = "professional"
    llm_provider: str
    api_key: str

class GenerationResponse(BaseModel):
    task_id: str
    status: str
    message: str

@app.get("/")
async def root():
    return {"message": "Text-to-PowerPoint Generator API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "features": ["LLM Integration", "PowerPoint Generation"]}

@app.post("/process-text")
async def process_text_to_slides(request: TextToSlidesRequest):
    """Convert text to slide structure using LLM"""
    try:
        if len(request.text.strip()) < 20:
            raise HTTPException(status_code=400, detail="Text must be at least 20 characters")
        
        if request.llm_provider not in ['openai', 'anthropic', 'gemini']:
            raise HTTPException(status_code=400, detail="Unsupported LLM provider")
        
        llm_service = LLMService(provider=request.llm_provider, api_key=request.api_key)
        
        logger.info(f"Processing {len(request.text)} characters with {request.llm_provider}")
        
        slide_structure = await llm_service.process_text_to_slides(
            text=request.text,
            guidance=request.guidance,
            tone=request.tone
        )
        
        return {
            "success": True,
            "message": "Text successfully converted to slide structure",
            "provider": request.llm_provider,
            "slide_count": len(slide_structure.get("slides", [])),
            "presentation": slide_structure
        }
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/generate-presentation", response_model=GenerationResponse)
async def generate_full_presentation(
    background_tasks: BackgroundTasks,
    text: str = Form(...),
    guidance: Optional[str] = Form(None),
    tone: Optional[str] = Form("professional"),
    llm_provider: str = Form(...),
    api_key: str = Form(...),
    template_file: UploadFile = File(...)
):
    """Generate complete PowerPoint presentation with template"""
    try:
        # Validate inputs
        if len(text.strip()) < 20:
            raise HTTPException(status_code=400, detail="Text must be at least 20 characters")
        
        if not template_file.filename.lower().endswith(('.pptx', '.potx')):
            raise HTTPException(status_code=400, detail="Template must be a .pptx or .potx file")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        generation_tasks[task_id] = {
            "status": "started",
            "progress": 0,
            "message": "Starting presentation generation...",
            "created_at": datetime.now(),
            "file_path": None
        }
        
        # Start background generation
        background_tasks.add_task(
            process_full_generation,
            task_id=task_id,
            text=text,
            guidance=guidance,
            tone=tone,
            llm_provider=llm_provider,
            api_key=api_key,
            template_file=template_file
        )
        
        return GenerationResponse(
            task_id=task_id,
            status="started",
            message="Generation started. Use task_id to check progress."
        )
        
    except Exception as e:
        logger.error(f"Generation start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")

@app.get("/generation-status/{task_id}")
async def get_generation_status(task_id: str):
    """Get generation status by task ID"""
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = generation_tasks[task_id]
    
    return {
        "task_id": task_id,
        "status": task_info["status"],
        "progress": task_info["progress"],
        "message": task_info["message"],
        "file_ready": task_info["status"] == "completed"
    }

@app.get("/download/{task_id}")
async def download_presentation(task_id: str):
    """Download generated presentation"""
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = generation_tasks[task_id]
    
    if task_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Generation not completed")
    
    file_path = task_info.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Generated file not found")
    
    return FileResponse(
        path=file_path,
        filename=f"generated_presentation_{task_id[:8]}.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

async def process_full_generation(
    task_id: str,
    text: str,
    guidance: Optional[str],
    tone: str,
    llm_provider: str,
    api_key: str,
    template_file: UploadFile
):
    """Background task for full presentation generation"""
    try:
        # Update status: Processing template
        generation_tasks[task_id].update({
            "status": "processing",
            "progress": 10,
            "message": "Saving template file..."
        })
        
        # Save template file
        template_path = f"temp_files/{task_id}_template.pptx"
        os.makedirs("temp_files", exist_ok=True)
        
        with open(template_path, "wb") as buffer:
            content = await template_file.read()
            buffer.write(content)
        
        # Update status: Processing with LLM
        generation_tasks[task_id].update({
            "progress": 30,
            "message": "Converting text to slides with AI..."
        })
        
        # Process text with LLM
        llm_service = LLMService(provider=llm_provider, api_key=api_key)
        slide_structure = await llm_service.process_text_to_slides(
            text=text,
            guidance=guidance,
            tone=tone
        )
        
        # Update status: Generating PowerPoint
        generation_tasks[task_id].update({
            "progress": 70,
            "message": "Creating PowerPoint presentation..."
        })
        
        # Generate PowerPoint
        ppt_service = PPTService()
        output_path = f"generated_files/{task_id}_presentation.pptx"
        os.makedirs("generated_files", exist_ok=True)
        
        await ppt_service.create_presentation_from_template(
            slide_structure=slide_structure,
            template_path=template_path,
            output_path=output_path
        )
        
        # Update status: Completed
        generation_tasks[task_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Presentation generated successfully!",
            "file_path": output_path
        })
        
        # Cleanup template file
        if os.path.exists(template_path):
            os.unlink(template_path)
        
    except Exception as e:
        logger.error(f"Generation failed for task {task_id}: {str(e)}")
        generation_tasks[task_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Generation failed: {str(e)}"
        })

@app.get("/supported-providers")
async def get_supported_providers():
    """Get list of supported LLM providers"""
    return {
        "providers": [
            {"name": "openai", "display_name": "OpenAI GPT", "model": "gpt-4o-mini"},
            {"name": "anthropic", "display_name": "Anthropic Claude", "model": "claude-3-haiku"},
            {"name": "gemini", "display_name": "Google Gemini", "model": "gemini-1.5-flash"}
        ]
    }
