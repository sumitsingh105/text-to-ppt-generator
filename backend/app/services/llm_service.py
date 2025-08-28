import openai
import anthropic
import google.generativeai as genai
from typing import Dict, List, Optional, Any
import json
import re
import logging
import asyncio

# Configure detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, provider: str, api_key: str):
        self.provider = provider.lower()
        self.api_key = api_key
        self._setup_client()
    
    def _setup_client(self):
        """Initialize the appropriate LLM client"""
        try:
            if self.provider == "openai":
                self.client = openai.OpenAI(api_key=self.api_key)
            elif self.provider == "anthropic":
                self.client = anthropic.Anthropic(api_key=self.api_key)
            elif self.provider == "gemini":
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel('gemini-1.5-flash')
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
            
            logger.info(f"Successfully initialized {self.provider} client")
            
        except Exception as e:
            logger.error(f"Failed to setup {self.provider} client: {str(e)}")
            raise
    
    async def process_text_to_slides(
        self,
        text: str,
        guidance: Optional[str] = None,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """Convert input text into structured slide content"""
        prompt = self._build_prompt(text, guidance, tone)
        
        logger.info(f"Processing with {self.provider}...")
        logger.debug(f"Prompt length: {len(prompt)} characters")
        
        try:
            if self.provider == "openai":
                response = await self._process_with_openai(prompt)
            elif self.provider == "anthropic":
                response = await self._process_with_anthropic(prompt)
            elif self.provider == "gemini":
                response = await self._process_with_gemini(prompt)
            
            # Log the raw response for debugging
            logger.info(f"Raw LLM response length: {len(response) if response else 0}")
            logger.debug(f"Raw LLM response (first 200 chars): {response[:200] if response else 'EMPTY'}")
            
            if not response or not response.strip():
                raise Exception("Empty response from LLM")
            
            slide_structure = self._parse_llm_response(response)
            logger.info(f"Successfully parsed {len(slide_structure.get('slides', []))} slides")
            
            return slide_structure
            
        except Exception as e:
            logger.error(f"LLM processing failed: {str(e)}")
            raise Exception(f"LLM processing failed: {str(e)}")
    
    def _build_prompt(self, text: str, guidance: Optional[str], tone: str) -> str:
        """Build a more focused prompt for better JSON responses"""
        return f"""Convert this text into a presentation structure.

Text: {text[:2000]}...

Guidance: {guidance or "Standard presentation"}
Tone: {tone}

Respond with ONLY this JSON format (no other text):
{{
    "title": "Your presentation title here",
    "slides": [
        {{
            "type": "title",
            "title": "Main Title",
            "subtitle": "Subtitle if needed",
            "speaker_notes": "Introduction notes"
        }},
        {{
            "type": "content",
            "title": "First Topic",
            "content": ["Point 1", "Point 2", "Point 3"],
            "speaker_notes": "Explanation for this slide"
        }}
    ]
}}

Create 5-10 slides total. Return ONLY valid JSON."""
    
    async def _process_with_openai(self, prompt: str) -> str:
        """Process with OpenAI GPT"""
        try:
            logger.info("Calling OpenAI API...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a JSON generator. Return only valid JSON, no other text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for more consistent JSON
                max_tokens=3000
            )
            
            result = response.choices[0].message.content
            logger.info(f"OpenAI response received: {len(result) if result else 0} characters")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"OpenAI processing failed: {str(e)}")
    
    async def _process_with_anthropic(self, prompt: str) -> str:
        """Process with Anthropic Claude"""
        try:
            logger.info("Calling Anthropic API...")
            # Anthropic calls are typically synchronous, so run in executor
            loop = asyncio.get_event_loop()
            
            def call_anthropic():
                return self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=3000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
            
            message = await loop.run_in_executor(None, call_anthropic)
            result = message.content[0].text
            logger.info(f"Anthropic response received: {len(result) if result else 0} characters")
            return result
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise Exception(f"Anthropic processing failed: {str(e)}")
    
    async def _process_with_gemini(self, prompt: str) -> str:
        """Process with Google Gemini"""
        try:
            logger.info("Calling Gemini API...")
            # Run Gemini in executor since it's synchronous
            loop = asyncio.get_event_loop()
            
            def call_gemini():
                response = self.client.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=3000,
                    )
                )
                return response.text
            
            result = await loop.run_in_executor(None, call_gemini)
            logger.info(f"Gemini response received: {len(result) if result else 0} characters")
            return result
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            if "API key" in str(e):
                raise Exception("Invalid Gemini API key. Get one from https://ai.google.dev/")
            raise Exception(f"Gemini processing failed: {str(e)}")
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response with better error handling"""
        try:
            if not response or not response.strip():
                raise ValueError("Empty response from LLM")
            
            # Clean the response more aggressively
            cleaned_response = response.strip()
            
            # Remove markdown code blocks
            cleaned_response = re.sub(r'``````', '', cleaned_response)
            cleaned_response = re.sub(r'``````', '', cleaned_response)
            
            # Remove any text before the first {
            first_brace = cleaned_response.find('{')
            if first_brace > 0:
                cleaned_response = cleaned_response[first_brace:]
                logger.info(f"Removed {first_brace} characters before JSON")
            
            # Remove any text after the last }
            last_brace = cleaned_response.rfind('}')
            if last_brace > 0 and last_brace < len(cleaned_response) - 1:
                cleaned_response = cleaned_response[:last_brace + 1]
                logger.info("Trimmed text after JSON")
            
            logger.debug(f"Cleaned response: {cleaned_response[:200]}...")
            
            # Parse JSON
            slide_structure = json.loads(cleaned_response)
            
            # Validate structure
            if not isinstance(slide_structure, dict):
                raise ValueError("Response is not a JSON object")
            
            if "slides" not in slide_structure:
                raise ValueError("No 'slides' key found in response")
            
            slides = slide_structure["slides"]
            if not isinstance(slides, list) or len(slides) == 0:
                raise ValueError("'slides' must be a non-empty array")
            
            # Fix any missing fields
            slide_structure.setdefault("title", "Generated Presentation")
            
            for i, slide in enumerate(slides):
                slide.setdefault("type", "content")
                slide.setdefault("title", f"Slide {i + 1}")
                slide.setdefault("speaker_notes", f"Notes for slide {i + 1}")
                
                if slide["type"] == "content" and "content" not in slide:
                    slide["content"] = ["Main point for this slide"]
            
            return slide_structure
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Problematic response: {response[:500]}...")
            raise Exception(f"Invalid JSON from LLM. Response started with: {response[:100]}...")
        except Exception as e:
            logger.error(f"Response parsing error: {str(e)}")
            raise Exception(f"Failed to parse LLM response: {str(e)}")
