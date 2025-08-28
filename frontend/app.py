import streamlit as st
import requests
import json

st.set_page_config(
    page_title="Text to PowerPoint Generator",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Text to PowerPoint Generator")
st.markdown("Transform your text into professional presentations using AI")

# Test backend connection
try:
    response = requests.get("http://backend:8000/", timeout=5)
    if response.status_code == 200:
        st.success("✅ Backend connected successfully!")
    else:
        st.error("❌ Backend connection failed")
except Exception as e:
    st.error(f"❌ Cannot connect to backend: {str(e)}")

st.markdown("---")

# Configuration sidebar
with st.sidebar:
    st.header("🔧 Configuration")
    
    llm_provider = st.selectbox(
        "AI Provider:",
        options=["openai", "anthropic", "gemini"],
        format_func=lambda x: {
            "openai": "🤖 OpenAI GPT-4",
            "anthropic": "🧠 Anthropic Claude",
            "gemini": "✨ Google Gemini"
        }[x]
    )
    
    api_key = st.text_input("API Key:", type="password", help="Never stored or logged")
    
    # Debug button
    if st.button("🔍 Test Connection", disabled=not api_key):
        with st.spinner(f"Testing {llm_provider} connection..."):
            try:
                debug_response = requests.post(
                    "http://backend:8000/debug-llm",
                    json={"llm_provider": llm_provider, "api_key": api_key},
                    timeout=30
                )
                
                if debug_response.status_code == 200:
                    debug_result = debug_response.json()
                    if debug_result["success"]:
                        st.success(f"✅ {llm_provider.upper()} connection successful!")
                        st.info(f"Generated {debug_result.get('slides_generated', 0)} test slides")
                    else:
                        st.error(f"❌ Connection failed: {debug_result.get('error', 'Unknown error')}")
                        if debug_result.get('suggestion'):
                            st.info(f"💡 {debug_result['suggestion']}")
                else:
                    st.error("❌ Debug test failed")
                    
            except Exception as e:
                st.error(f"❌ Connection test error: {str(e)}")

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 Input Content")
    
    sample_text = """Artificial Intelligence in Healthcare

AI is revolutionizing healthcare through advanced diagnostic tools, personalized treatment plans, and predictive analytics. Machine learning algorithms analyze medical images with remarkable accuracy, helping doctors detect diseases earlier than traditional methods.

Key applications include:
- Medical imaging and radiology
- Drug discovery and development
- Electronic health records analysis
- Robotic surgery assistance
- Telemedicine and remote monitoring

The future of AI in healthcare promises personalized medicine based on genetic profiles and AI-powered virtual health assistants that provide 24/7 patient support."""
    
    text_input = st.text_area(
        "Your content:",
        value=sample_text,
        height=200,
        help="Paste any text you want to convert to slides"
    )

with col2:
    st.header("⚙️ Settings")
    
    guidance = st.text_input(
        "Presentation style:",
        placeholder="e.g., 'business pitch', 'academic conference'",
        help="Guide the AI on presentation structure"
    )
    
    tone = st.selectbox(
        "Tone:",
        options=["professional", "academic", "casual", "creative", "technical"]
    )

# Generate button
if st.button("🚀 Generate Slides", type="primary", disabled=not text_input or not api_key):
    with st.spinner(f"Converting text with {llm_provider.upper()}..."):
        try:
            payload = {
                "text": text_input,
                "guidance": guidance or None,
                "tone": tone,
                "llm_provider": llm_provider,
                "api_key": api_key
            }
            
            response = requests.post(
                "http://backend:8000/process-text",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                st.success(f"✅ Generated {result['slide_count']} slides with {result['provider']}!")
                
                presentation = result['presentation']
                st.subheader(f"📋 {presentation.get('title', 'Generated Presentation')}")
                
                # Display slides
                for i, slide in enumerate(presentation.get('slides', []), 1):
                    with st.expander(f"Slide {i}: {slide.get('title', 'Untitled')} ({slide.get('type', 'content')})"):
                        
                        if slide.get('type') == 'title':
                            st.markdown(f"**Title:** {slide.get('title', '')}")
                            if slide.get('subtitle'):
                                st.markdown(f"**Subtitle:** {slide.get('subtitle')}")
                        
                        elif slide.get('type') == 'content':
                            st.markdown(f"**Title:** {slide.get('title', '')}")
                            content = slide.get('content', [])
                            if content:
                                for point in content:
                                    st.markdown(f"• {point}")
                        
                        if slide.get('speaker_notes'):
                            st.markdown(f"**Speaker Notes:** {slide.get('speaker_notes')}")
                
                # Show raw JSON in expander
                with st.expander("🔍 Raw JSON Structure"):
                    st.json(presentation)
            
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get('detail', f'HTTP {response.status_code}')
                st.error(f"❌ Processing failed: {error_msg}")
                
        except requests.exceptions.Timeout:
            st.error("⏰ Request timed out. Try with shorter text or try again.")
        except Exception as e:
            st.error(f"💥 Error: {str(e)}")

st.markdown("---")
st.markdown("🔧 **Debug tip:** Use 'Test Connection' first to verify your API key works")
