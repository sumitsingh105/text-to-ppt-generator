import streamlit as st
import requests

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
        st.json(response.json())
    else:
        st.error("❌ Backend connection failed")
except Exception as e:
    st.error(f"❌ Cannot connect to backend: {str(e)}")

st.markdown("---")
st.markdown("🚧 **Application is in development**")
st.markdown("Basic setup completed. Full functionality will be added next.")
