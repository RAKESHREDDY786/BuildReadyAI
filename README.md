# BuildReady-AI

> Personalized Engineering Roadmaps & Project Planning Assistant powered by Google Gemini.

BuildReady-AI is an engineering-aware mentor designed for students and hackathon participants. Instead of generic chatbot responses, BuildReady-AI structures guidance by:

**Engineering Path → Relevant Domain → Project / Learning Goal → Project-Specific Skills → Personalized Roadmap → Contextual AI Guidance**

---

## 🌟 Key Features

1. **Branch-Aware Engineering Paths**:
   - Supports 12 distinct paths: AI / ML, Data Science, Software Development, Web Development, Cybersecurity, ECE / IoT, Electrical / EEE, Mechanical, Civil, Chemical, Biotechnology, and custom ("Other").
   - Each branch displays its own tailored domains rather than generic AI/ML lists.

2. **Adaptive Student Levels**:
   - **Beginner**: Prerequisites, foundational concepts, step-by-step small exercises.
   - **Intermediate**: Practical development, architectural patterns, and real-world tools.
   - **Advanced**: Scalability, optimization, system design, and production implementations.

3. **Two Tailored Modes**:
   - **Learn the Domain**: Step-by-step progressive learning stages, milestones, and curated free resources.
   - **Build a Project**: Project-specific skills analysis (required, recommended, learning order, tech stack, MVP plan, innovation ideas, and demo/deployment guide).

4. **Interactive Progress Tracking**:
   - Task checklists with real-time percentage indicators (progress bar and circular dial).
   - Saved state in `localStorage` with a "Clear Saved Plan" option.

5. **Ask BuildReady (Contextual AI Mentor)**:
   - Built-in mentor assistant powered by Google Gemini that understands the student's selected branch, domain, level, goal, and project.

---

## 🚀 Quick Start Guide

### 1. Configure the Environment
Ensure your `.env` file exists in `backend/.env` (or in the root directory):
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(A template is provided in `.env.example`)*

### 2. Start the Backend
Activate your Python virtual environment and run Uvicorn:
```powershell
# From project root:
uvicorn main:app --reload --port 8000

# Or using the backend module path:
uvicorn backend.main:app --reload --port 8000
```
- Open Swagger API documentation at: **http://127.0.0.1:8000/docs**
- Backend root check: **http://127.0.0.1:8000/**

### 3. Open the Frontend
Open the frontend using VS Code Live Server or any static web server:
- URL: **http://127.0.0.1:5500/frontend/index.html**

---

## 📡 API Endpoints

- `GET /` — Backend status check
- `GET /health` — Health check and Gemini configuration status
- `POST /generate-plan` — Generates a personalized structured learning roadmap or project plan
- `POST /chat` — Context-aware AI mentoring via Ask BuildReady
