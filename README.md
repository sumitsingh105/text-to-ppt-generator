# Text-to-PowerPoint Generator

A web application that automatically converts text content into professionally formatted PowerPoint presentations using AI. Upload your template, paste your text, and let AI create slides that match your brand's style.

## 🚀 Features

- **Multi-LLM Support**: Works with OpenAI GPT, Anthropic Claude, and Google Gemini
- **Template Style Matching**: Automatically extracts and applies colors, fonts, and layouts from uploaded templates
- **Intelligent Text Processing**: AI analyzes content and creates logical slide structures
- **Real-time Progress Tracking**: Monitor generation progress with live updates
- **Secure API Key Handling**: API keys are never stored or logged
- **Docker Deployment**: Easy deployment with Docker Compose

## 🛠️ Quick Start

### Prerequisites
- Docker and Docker Compose installed
- API key from OpenAI, Anthropic, or Google AI

### Local Deployment
Clone repository
git clone https://github.com/YOUR_USERNAME/text-to-ppt-generator.git
cd text-to-ppt-generator

Build and start services
docker-compose up --build

Access applications
Frontend: http://localhost:8502
Backend: http://localhost:8080
text

## 📁 Project Structure
text-to-ppt-generator/
├── backend/ # FastAPI backend service
│ ├── app/
│ │ └── main.py # API endpoints
│ ├── requirements.txt # Python dependencies
│ └── Dockerfile
├── frontend/ # Streamlit frontend service
│ ├── app.py # UI application
│ ├── requirements.txt # Python dependencies
│ └── Dockerfile
├── docker-compose.yml # Service orchestration
├── README.md
└── LICENSE



## 🎯 Usage

1. **Start the application** using Docker Compose
2. **Access the frontend** at http://localhost:8502
3. **Upload a PowerPoint template** (.pptx or .potx file)
4. **Paste your text content** (articles, notes, etc.)
5. **Enter your LLM API key** (OpenAI, Anthropic, or Gemini)
6. **Generate and download** your styled presentation

## 🔒 Security

- API keys are never stored or logged
- Temporary files automatically cleaned up
- Input validation and sanitization
- Secure cross-origin resource sharing (CORS)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚀 Deployment

### Local Development
See Quick Start section above.

### Cloud Deployment
- **Streamlit Community Cloud**: For frontend hosting
- **Render.com**: For backend API hosting  
- **Railway.app**: For full-stack deployment
- **Heroku**: Alternative cloud platform

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Note**: This application requires API keys from your chosen LLM provider. Keys are never stored by the application.
