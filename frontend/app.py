import streamlit as st
import requests
import time
import io

st.set_page_config(
    page_title="Text to PowerPoint Generator",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Text to PowerPoint Generator")
st.markdown("Transform your text into professional presentations using AI")

# Backend URL configuration
BACKEND_URL = "https://text-to-ppt-generator.onrender.com"

# Check backend connection
try:
    response = requests.get(f"{BACKEND_URL}/", timeout=10)
    if response.status_code == 200:
        st.success("✅ Backend connected - PowerPoint generation ready!")
    else:
        st.error("❌ Backend connection failed")
except Exception as e:
    st.error(f"❌ Cannot connect to backend: {str(e)}")
    st.info(f"Trying to connect to: {BACKEND_URL}")

st.markdown("---")

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 Input Content")
    
    sample_text = """Digital Transformation in Modern Business

The business landscape is rapidly evolving through digital transformation initiatives. Companies are leveraging cloud computing, artificial intelligence, and data analytics to streamline operations and enhance customer experiences.

Key areas of transformation include:
- Cloud migration and infrastructure modernization
- Process automation and workflow optimization
- Data-driven decision making and analytics
- Customer experience digitization
- Remote work technology adoption

Organizations implementing comprehensive digital strategies report 25% higher revenue growth and 30% improvement in operational efficiency. The key to success lies in strategic planning, employee training, and gradual implementation.

Future trends include edge computing, blockchain integration, and AI-powered business intelligence systems that will further revolutionize how companies operate and compete in the digital economy."""
    
    text_input = st.text_area(
        "Your content:",
        value=sample_text,
        height=250,
        help="Paste any text, article, or document you want to convert to slides"
    )
    
    guidance = st.text_input(
        "Presentation guidance (optional):",
        placeholder="e.g., 'business presentation', 'investor pitch', 'training material'",
        help="Guide the AI on presentation style and structure"
    )

with col2:
    st.header("⚙️ Configuration")
    
    # Template upload
    st.subheader("📎 PowerPoint Template")
    template_file = st.file_uploader(
        "Upload your template:",
        type=['pptx', 'potx'],
        help="Upload a PowerPoint template that defines your desired style, colors, and fonts"
    )
    
    if template_file:
        st.success(f"✅ Template: {template_file.name}")
        file_size = len(template_file.getvalue()) / (1024 * 1024)
        st.info(f"File size: {file_size:.1f} MB")
    
    st.subheader("🤖 AI Settings")
    
    llm_provider = st.selectbox(
        "AI Provider:",
        options=["openai", "anthropic", "gemini"],
        format_func=lambda x: {
            "openai": "🤖 OpenAI GPT",
            "anthropic": "🧠 Anthropic Claude",
            "gemini": "✨ Google Gemini"
        }[x]
    )
    
    api_key = st.text_input("API Key:", type="password", help="Never stored or logged")
    
    tone = st.selectbox(
        "Tone:",
        options=["professional", "academic", "casual", "creative", "technical"]
    )

# Generate button
st.markdown("---")

if st.button("🚀 Generate PowerPoint Presentation", type="primary", 
             disabled=not text_input or not api_key or not template_file):
    
    with st.spinner("Starting presentation generation..."):
        try:
            # Prepare form data
            files = {
                'template_file': (template_file.name, template_file.getvalue(), 
                                template_file.type)
            }
            
            data = {
                'text': text_input,
                'guidance': guidance or "",
                'tone': tone,
                'llm_provider': llm_provider,
                'api_key': api_key
            }
            
            # Start generation
            response = requests.post(
                f"{BACKEND_URL}/generate-presentation",
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result['task_id']
                
                st.success("✅ Generation started!")
                st.info(f"Task ID: {task_id}")
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Poll for progress
                max_attempts = 300  # 5 minutes
                attempt = 0
                
                while attempt < max_attempts:
                    try:
                        status_response = requests.get(
                            f"{BACKEND_URL}/generation-status/{task_id}",
                            timeout=10
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            progress = status_data['progress']
                            message = status_data['message']
                            status = status_data['status']
                            
                            progress_bar.progress(progress / 100)
                            status_text.info(f"📋 {message}")
                            
                            if status == 'completed':
                                st.success("🎉 Presentation generated successfully!")
                                
                                # Download button
                                download_response = requests.get(
                                    f"{BACKEND_URL}/download/{task_id}",
                                    timeout=30
                                )
                                
                                if download_response.status_code == 200:
                                    st.download_button(
                                        label="📥 Download PowerPoint Presentation",
                                        data=download_response.content,
                                        file_name=f"generated_presentation.pptx",
                                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                        type="primary"
                                    )
                                    
                                    file_size = len(download_response.content) / (1024 * 1024)
                                    st.info(f"📊 Generated file size: {file_size:.1f} MB")
                                    
                                else:
                                    st.error("❌ Failed to download presentation")
                                
                                break
                                
                            elif status == 'failed':
                                st.error(f"❌ Generation failed: {message}")
                                break
                        
                        else:
                            st.error("❌ Failed to get status")
                            break
                        
                    except Exception as status_error:
                        st.error(f"❌ Status check error: {str(status_error)}")
                        break
                    
                    attempt += 1
                    time.sleep(1)
                
                if attempt >= max_attempts:
                    st.error("⏰ Generation timed out")
            
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"❌ Failed to start generation: {error_detail}")
                
        except Exception as e:
            st.error(f"💥 Error: {str(e)}")

# Quick test section
st.markdown("---")
with st.expander("🧪 Quick Test (Text-only Analysis)"):
    st.markdown("Test your text and AI settings without generating PowerPoint")
    
    if st.button("Test Text Processing", disabled=not text_input or not api_key):
        with st.spinner("Testing..."):
            try:
                test_payload = {
                    "text": text_input,
                    "guidance": guidance,
                    "tone": tone,
                    "llm_provider": llm_provider,
                    "api_key": api_key
                }
                
                test_response = requests.post(
                    f"{BACKEND_URL}/process-text",
                    json=test_payload,
                    timeout=60
                )
                
                if test_response.status_code == 200:
                    result = test_response.json()
                    st.success(f"✅ Would generate {result['slide_count']} slides")
                    
                    with st.expander("Preview slide structure"):
                        st.json(result['presentation'])
                else:
                    st.error("❌ Test failed")
                    
            except Exception as e:
                st.error(f"Test error: {str(e)}")

st.markdown("---")
st.markdown("💡 **Tips:** Upload a professional template, provide clear guidance, and use concise but detailed text for best results!")
