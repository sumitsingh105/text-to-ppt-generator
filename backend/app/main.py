from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.llm_service import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Text-to-PowerPoint Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:8502", "http://frontend:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class TextToSlidesRequest(BaseModel):
    text: str
    guidance: Optional[str] = None
    tone: Optional[str] = "professional"
    llm_provider: str
    api_key: str

class DebugRequest(BaseModel):
    llm_provider: str
    api_key: str

@app.get("/")
async def root():
    return {"message": "Text-to-PowerPoint Generator API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "features": ["LLM Integration", "Debug Mode"]}

@app.post("/debug-llm")
async def debug_llm_connection(request: DebugRequest):
    """Debug endpoint to test LLM connection with simple text"""
    try:
        llm_service = LLMService(
            provider=request.llm_provider,
            api_key=request.api_key
        )
        
        # Simple test text
        test_text = """
        Machine learning is transforming business operations through automation, 
        predictive analytics, and intelligent decision-making systems.
        """
        
        result = await llm_service.process_text_to_slides(
            text=test_text,
            guidance="simple business presentation",
            tone="professional"
        )
        
        return {
            "success": True,
            "provider": request.llm_provider,
            "test_result": "Connection successful",
            "slides_generated": len(result.get("slides", [])),
            "sample_slide": result.get("slides", [{}])[0] if result.get("slides") else None
        }
        
    except Exception as e:
        logger.error(f"Debug test failed: {str(e)}")
        return {
            "success": False,
            "provider": request.llm_provider,
            "error": str(e),
            "suggestion": "Check your API key and try again"
        }

@app.post("/process-text")
async def process_text_to_slides(request: TextToSlidesRequest):
    """Convert text to slide structure using LLM"""
    try:
        if len(request.text.strip()) < 20:
            raise HTTPException(status_code=400, detail="Text must be at least 20 characters")
        
        if request.llm_provider not in ['openai', 'anthropic', 'gemini']:
            raise HTTPException(status_code=400, detail="Unsupported LLM provider")
        
        llm_service = LLMService(
            provider=request.llm_provider,
            api_key=request.api_key
        )
        
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
