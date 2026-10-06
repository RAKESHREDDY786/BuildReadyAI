# BuildReady-AI

> Personalized Engineering Roadmaps & Project Planning Assistant powered by Google Gemini.

BuildReady-AI is an engineering-aware mentor designed for students and hackathon participants. Instead of generic chatbot responses, BuildReady-AI structures guidance by:

**Engineering Path → Mode → Specific Goal → Required Skills → Personalized Roadmap → Assessment → Verified Progress**

---

## 🌟 Key Features

1. **Branch-Aware Engineering Paths**:
   - Includes AIML, AI, CSE, Data Science, Software Development, Web Development, Cybersecurity, ECE / IoT, Electrical / EEE, Mechanical, Civil, Chemical, Biotechnology, and custom ("Other").
   - Each branch displays its own tailored domains and a dependent Technology / Topic Focus selector. AIML includes a dedicated Data Structures & Algorithms domain, language choices, SQL, and Git/GitHub; CSE and related paths expose Java, JavaScript, C, C++, C#, Python, SQL, Git, and GitHub; Web Development exposes HTML, CSS, and JavaScript.
   - The selected Domain determines the curriculum; Technology / Topic Focus determines the language, tools, or notation used within that curriculum. Free-text goals provide context only and cannot replace either selection (for example, choosing DSA with Python selected still teaches DSA in Python, while choosing DSA with a language-neutral focus uses pseudocode).

2. **Adaptive Student Levels**:
   - **Beginner**: Prerequisites, foundational concepts, step-by-step small exercises.
   - **Intermediate**: Practical development, architectural patterns, and real-world tools.
   - **Advanced**: Scalability, optimization, system design, and production implementations.

3. **Two Tailored Modes**:
   - **Learn the Domain**: Step-by-step progressive learning stages, milestones, and curated free resources for the selected technology/topic, not Python by default.
   - **Build a Project**: Project-specific skills analysis (required, recommended, learning order, tech stack, MVP plan, innovation ideas, and demo/deployment guide) constrained by the selected technology/topic.

4. **Assessment-Verified Progress**:
   - Each task presents a structured, task-specific lesson: concept introduction and explanation, why it matters, prerequisites, analogy, detailed teaching, key concepts and syntax, multiple line-explained examples, mistake corrections, progressive beginner/intermediate practice, real-world application, an assignment, and a mini challenge before its quiz.
   - Example code and its explanation are stored as paired line objects, so displayed code lines cannot drift out of alignment with their explanations.
   - Roadmap tasks use `NOT_STARTED`, `IN_PROGRESS`, `NEEDS_PRACTICE`, and `VERIFIED` statuses. Passing a task quiz marks it completed and unlocks the next task; passing all task quizzes displays a roadmap completion banner.
   - The quiz is based on the taught task concepts and choices are included during answer evaluation; a passing result verifies the task and unlocks the next one.
   - The progress bar, circular graph, and status counts are calculated from verified task statuses.
   - Roadmaps, generated assessments, assessment results, and statuses are saved in browser `localStorage`.
5. **Ask BuildReady (Contextual AI Mentor)**:
   - Built-in mentor assistant powered by Google Gemini that receives the student's branch, domain, level, goal, task statuses, and recent assessment results.

---

## 🚀 Quick Start Guide

### 1. Configure the Environment
Ensure your `.env` file exists in `backend/.env` (or in the root directory):
```env
GEMINI_API_KEY=your_gemini_api_key_here
CORS_ALLOW_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```
Templates are provided in the root and backend `.env.example` files. Never put the Gemini key in frontend files.

### 2. Start the Backend
Activate your Python virtual environment and run Uvicorn:
```powershell
# From project root:
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# Or using the backend module path:
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```
- Open Swagger API documentation at: **http://127.0.0.1:8000/docs**
- Open the app directly from FastAPI at: **http://127.0.0.1:8000/**
- For Live Server development, use: **http://127.0.0.1:5500/frontend/index.html**

### 3. Deploy from GitHub with Vercel
1. Import the existing `RAKESHREDDY786/BuildReadyAI` repository in Vercel and keep the project root set to the repository root.
2. Add `GEMINI_API_KEY` as a Vercel environment variable for Production and Preview. Enter the key in Vercel only; never commit it.
3. Deploy the `main` branch. FastAPI serves the app at `/`, the API on the same origin, and API documentation at `/docs`.
4. The frontend automatically uses the same origin when hosted, so a separate public backend URL or CORS allowlist is not needed for the Vercel deployment. On localhost it continues to call `http://127.0.0.1:8000`.

For a local FastAPI deployment, set `GEMINI_API_KEY` in `backend/.env` or the root `.env`. Keep both `.env` files out of Git.

## 🔐 Founder Dashboard

The founder-only usage dashboard lives at `/founder-dashboard.html` and calls `GET /founder/stats`, `/founder/users`, and `/founder/events` with the `X-Founder-Key` header.

- Set `FOUNDER_SECRET_KEY` to a long random value in `backend/.env` locally, and in the Render service's **Environment** settings for production (`render.yaml` declares it with `sync: false`, so Render never stores it in Git). Redeploy after changing it.
- The endpoints return `503` when `FOUNDER_SECRET_KEY` is unset or still set to the `.env.example` placeholder, `403` for a missing or wrong key, and `200` for the configured key. There is no built-in default key.

---

## 📡 API Endpoints

- `GET /` — Backend status check
- `GET /health` — Health check and Gemini configuration status
- `POST /generate-plan` — Generates a personalized structured learning roadmap or project plan
- `POST /generate-assessment` — Creates 3–5 assessment questions for one roadmap task
- `POST /evaluate-assessment` — Evaluates answers and returns a score, feedback, and verified/practice-needed status
- `POST /chat` — Context-aware AI mentoring via Ask BuildReady

The plan, assessment, evaluation, and chat requests support an optional `technology` field. Existing API callers that omit it remain compatible; the selected domain is used as the focus, except DSA defaults to language-neutral pseudocode. Add selector choices in `frontend/script.js` (`pathDomains` and `technologyOptionsByDomain`); add a syntax signature to `TECHNOLOGY_EXAMPLE_REQUIREMENTS` in `backend/main.py` when the new choice has recognizable example syntax. This keeps extension work configuration-driven and protects the existing learning workflow.

## Current MVP Limits and Deployment

- Plan, assessment, and progress persistence is browser-local; there is no database or cross-device account storage.
- AI endpoints require a valid Gemini API key and network access to the configured Gemini models.
- Vercel deployments use browser-local progress and need a configured `GEMINI_API_KEY` environment variable. Keep the key in Vercel settings, not in frontend files or Git.
