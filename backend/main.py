import os
import re
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel

# -----------------------------
# Secure environment loading
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")
load_dotenv()  # fallback to current working directory

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(
    title="BuildReady-AI API",
    description="Backend API for BuildReady-AI: Verified Learning, Roadmap & Progress System",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Gemini Client & Model Config
# -----------------------------
GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
]

def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in ("", "your_key_here", "MY_REAL_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured in backend/.env. Please set a valid Gemini API key."
        )
    return genai.Client(api_key=api_key.strip())


# -----------------------------
# Request & Response Models
# -----------------------------
class ProjectRequest(BaseModel):
    idea: Optional[str] = ""
    path: str
    domain: str
    goal: str
    level: str


class Skill(BaseModel):
    skill: str
    why: str
    priority: str  # e.g., "High", "Core", "Recommended"


class LearningResource(BaseModel):
    topic: str
    resource_name: str
    resource_type: str


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: str = "NOT_STARTED"  # NOT_STARTED, IN_PROGRESS, NEEDS_PRACTICE, VERIFIED
    verification_focus: Optional[str] = ""


class ProjectPlan(BaseModel):
    project_overview: str
    problem: str
    target_users: List[str]
    skills_required: List[Skill]
    learning_resources: List[LearningResource]
    tasks: List[Task]
    tech_stack: List[str]
    mvp_plan: List[str]
    innovation_ideas: List[str]
    deployment_plan: List[str]
    prerequisites: List[str]
    learning_order: List[str]
    difficulty: str
    estimated_time: str
    recommended_projects: List[str]
    next_steps: List[str]


# --- Assessment & Verification Models ---
class AssessmentQuestion(BaseModel):
    id: int
    question: str
    question_type: str  # "concept", "code_or_query", "troubleshooting", "design", "output_prediction"
    hint: Optional[str] = ""


class TopicAssessment(BaseModel):
    topic_id: int
    topic_title: str
    assessment_focus: str
    difficulty: str
    questions: List[AssessmentQuestion]
    passing_criteria: str


class GenerateAssessmentRequest(BaseModel):
    topic_id: int
    topic_title: str
    topic_description: str
    path: str
    domain: str
    level: str
    goal: str
    idea: Optional[str] = ""


class AnswerSubmission(BaseModel):
    question_id: int
    question: str
    user_answer: str


class EvaluateAssessmentRequest(BaseModel):
    topic_id: int
    topic_title: str
    topic_description: str
    path: str
    domain: str
    level: str
    goal: str
    idea: Optional[str] = ""
    submissions: List[AnswerSubmission]


class AssessmentEvaluation(BaseModel):
    topic_id: int
    status: str  # "VERIFIED" or "NEEDS_PRACTICE"
    passed: bool
    score: int  # 0 to 100
    overall_feedback: str
    strengths: List[str]
    weak_areas: List[str]
    targeted_practice: str
    next_step: str


# --- Chat Models ---
class TopicState(BaseModel):
    id: int
    title: str
    status: str = "NOT_STARTED"


class ChatRequest(BaseModel):
    message: str
    path: Optional[str] = "General Engineering"
    domain: Optional[str] = "General"
    goal: Optional[str] = "Learn the Domain"
    level: Optional[str] = "Beginner"
    idea: Optional[str] = ""
    current_topic: Optional[str] = ""
    topics: Optional[List[TopicState]] = []


class TopicUpdate(BaseModel):
    topic_id: int
    status: str  # "VERIFIED", "NEEDS_PRACTICE", "IN_PROGRESS"
    topic_title: Optional[str] = ""


class ChatResponse(BaseModel):
    reply: str
    topic_update: Optional[TopicUpdate] = None


# -----------------------------
# Helper for AI errors
# -----------------------------
def raise_ai_error(error: Exception, feature_name: str):
    error_text = str(error)
    print(f"[{feature_name}] AI Error:", repr(error))

    if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
        raise HTTPException(
            status_code=429,
            detail=f"{feature_name} has reached the AI rate limit. Please try again in a few moments."
        )
    if "503" in error_text or "UNAVAILABLE" in error_text:
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again shortly."
        )
    if "404" in error_text or "NOT_FOUND" in error_text:
        raise HTTPException(
            status_code=503,
            detail="Selected AI model is currently unavailable. Please try again."
        )

    raise HTTPException(
        status_code=500,
        detail=f"An error occurred while contacting the AI service: {str(error)}"
    )


def call_gemini_with_fallback(client: genai.Client, contents: str, config: dict):
    last_error = None
    for model_name in GEMINI_MODELS:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except Exception as e:
            err_msg = str(e)
            print(f"Model {model_name} failed: {err_msg}")
            last_error = e
            if "404" in err_msg or "503" in err_msg or "NOT_FOUND" in err_msg or "UNAVAILABLE" in err_msg:
                continue
            raise e
    if last_error:
        raise last_error
    raise RuntimeError("No Gemini models available.")


# -----------------------------
# Root & Health Check Endpoints
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "BuildReady-AI backend is running!",
        "status": "online",
        "docs_url": "/docs"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))
    }


# -----------------------------
# Generate Plan Endpoint
# -----------------------------
@app.post("/generate-plan")
def generate_plan(request: ProjectRequest):
    client = get_gemini_client()

    is_learning = "learn" in request.goal.lower()
    user_idea = (request.idea or "").strip()

    if is_learning:
        mode_instructions = f"""
MODE: LEARN THE DOMAIN (Personalized Adaptive Learning Roadmap)
- The student wants to master the domain '{request.domain}' in branch '{request.path}' at level '{request.level}'.
- Student's specific focus: "{user_idea if user_idea else 'Master this subject from fundamentals to practical mastery.'}"
- Generate 8 to 12 progressive, step-by-step topics/milestones in 'tasks':
  * Set status='NOT_STARTED' for all tasks.
  * In 'verification_focus', specify what practical or conceptual skill must be verified for that topic.
  * For Beginners: start with foundational principles, syntax/concepts, and small practical exercises.
  * For Intermediates: focus on practical implementation, patterns, tooling, and real-world scenarios.
  * For Advanced: focus on architecture, performance, edge cases, and production standards.
- In 'skills_required': specify core skills with priorities.
- In 'learning_order': list the sequential order of topics (Topic 1 -> Topic 2 -> Topic 3).
- In 'recommended_projects': list 3 progressive mini-projects.
- In 'prerequisites': what the student needs before starting.
- In 'learning_resources': official documentation, recognized tutorials (no invented URLs).
- In 'tech_stack': tools, software, or libraries.
- In 'mvp_plan': core milestones for domain proficiency.
- In 'next_steps': immediate first action.
"""
    else:
        mode_instructions = f"""
MODE: BUILD A PROJECT (Verified Project Milestones & Skills)
- The student is in branch '{request.path}', domain '{request.domain}', level '{request.level}'.
- Project goal/idea: "{user_idea if user_idea else 'Suggest a high-impact, realistic project for this domain.'}"
- Generate 8 to 12 realistic implementation milestones in 'tasks':
  * Set status='NOT_STARTED' for all tasks.
  * In 'verification_focus', specify what implementation, circuit, code, or testing must be verified for that milestone.
- In 'skills_required': EXACT skills needed specifically to build THIS project.
- In 'learning_order': step-by-step order to learn needed skills.
- In 'prerequisites': prerequisite concepts or hardware setup.
- In 'recommended_projects': 3 related variations suitable for hackathons.
- In 'tech_stack': exact languages, frameworks, hardware components, or tools.
- In 'mvp_plan': steps to build the core working MVP.
- In 'innovation_ideas': unique features to stand out.
- In 'deployment_plan': practical deployment or physical demonstration instructions.
- In 'next_steps': immediate first milestone.
"""

    prompt = f"""
You are BuildReady-AI, an expert engineering mentor and verified learning system.

Student Context:
- Engineering Path: {request.path}
- Selected Domain: {request.domain}
- Student Level: {request.level}
- Goal Type: {request.goal}
- Student Input: {user_idea if user_idea else 'None specified'}

{mode_instructions}

CRITICAL RULES:
1. Be strictly branch-aware: ECE/IoT must focus on circuits, microcontrollers, embedded C/C++, sensors; Mechanical on CAD, kinematics, thermodynamics; Civil on structures, materials, GIS; Software/Web/AI on their respective stacks. Never confuse branches!
2. Adapt depth strictly to '{request.level}' level.
3. Every task in 'tasks' must have an integer id (1, 2, 3...) and status 'NOT_STARTED'.
4. Do not hallucinate URLs.
5. All fields must be informative and practical.
"""

    try:
        response = call_gemini_with_fallback(
            client=client,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ProjectPlan,
            },
        )

        plan = ProjectPlan.model_validate_json(response.text)

        # Mark the first task as IN_PROGRESS to give an immediate starting point
        if plan.tasks and len(plan.tasks) > 0:
            plan.tasks[0].status = "IN_PROGRESS"

        display_idea = user_idea if user_idea else (
            f"{request.domain} Mastery Roadmap" if is_learning else f"{request.domain} Project"
        )

        return {
            "project_idea": display_idea,
            "path": request.path,
            "domain": request.domain,
            "level": request.level,
            "goal": request.goal,
            "ai_plan": plan.model_dump(),
        }

    except HTTPException:
        raise
    except Exception as error:
        raise_ai_error(error, "BuildReady-AI Plan Generator")


# -----------------------------
# Generate Assessment Endpoint
# -----------------------------
@app.post("/generate-assessment")
def generate_assessment(request: GenerateAssessmentRequest):
    """Generate adaptive verification questions tailored to branch, domain, topic, and level."""
    client = get_gemini_client()

    branch_guidance = ""
    path_lower = request.path.lower()
    domain_lower = request.domain.lower()

    if "ece" in path_lower or "iot" in path_lower or "hardware" in domain_lower:
        branch_guidance = "Include circuit connections, sensor pinouts, embedded code logic (Arduino/C++), or hardware troubleshooting."
    elif "sql" in domain_lower or "database" in domain_lower:
        branch_guidance = "Include SQL query formulation, query debugging, table joins, or result reasoning."
    elif "python" in domain_lower or "software" in path_lower or "programming" in domain_lower or "web" in path_lower:
        branch_guidance = "Include code writing, syntax verification, output prediction, or practical problem solving."
    elif "cad" in domain_lower or "mechanical" in path_lower:
        branch_guidance = "Include CAD constraint design, modeling workflow, finite element reasoning, or mechanical tolerances."
    elif "civil" in path_lower:
        branch_guidance = "Include structural load calculations, soil/material properties, or code compliance."
    else:
        branch_guidance = "Include conceptual understanding, application scenarios, and a practical task relevant to the domain."

    prompt = f"""
You are BuildReady-AI, creating a targeted verification assessment for a student.

Student Context:
- Path: {request.path}
- Domain: {request.domain}
- Level: {request.level}
- Goal: {request.goal}
- Project: {request.idea if request.idea else 'General Learning'}

Topic to Verify:
- Topic ID: {request.topic_id}
- Title: {request.topic_title}
- Description: {request.topic_description}

Assessment Requirements:
1. Create 3 to 4 focused verification questions that prove whether the student has genuinely learned this topic.
2. {branch_guidance}
3. Tailor questions strictly to '{request.level}' level.
4. Mix conceptual reasoning with practical execution (e.g. writing a code snippet, explaining a circuit, writing a query, or solving a scenario).
5. Specify passing criteria clearly (e.g. 'Must correctly explain core concepts and provide working syntax/logic for the practical problem').
"""

    try:
        response = call_gemini_with_fallback(
            client=client,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": TopicAssessment,
            },
        )

        assessment = TopicAssessment.model_validate_json(response.text)
        assessment.topic_id = request.topic_id
        assessment.topic_title = request.topic_title

        return assessment.model_dump()

    except HTTPException:
        raise
    except Exception as error:
        raise_ai_error(error, "Assessment Generator")


# -----------------------------
# Evaluate Assessment Endpoint
# -----------------------------
@app.post("/evaluate-assessment")
def evaluate_assessment(request: EvaluateAssessmentRequest):
    """Evaluate student answers to verify whether the topic is COMPLETED/VERIFIED or NEEDS_PRACTICE."""
    client = get_gemini_client()

    submissions_text = "\n\n".join([
        f"Question {sub.question_id}: {sub.question}\nStudent's Answer:\n\"{sub.user_answer.strip() if sub.user_answer.strip() else '[No Answer Provided]'}\""
        for sub in request.submissions
    ])

    prompt = f"""
You are BuildReady-AI, a rigorous but fair engineering evaluator.

Context:
- Path: {request.path}
- Domain: {request.domain}
- Level: {request.level}
- Topic: {request.topic_title} ({request.topic_description})

Student's Submitted Answers:
{submissions_text}

EVALUATION RULES:
1. Evaluate each answer for genuine comprehension and technical correctness.
2. If the student answers are empty, superficial, or contain phrases like 'i don't know', 'idk', or are fundamentally incorrect:
   - status: 'NEEDS_PRACTICE'
   - passed: False
   - score: 0 to 50
   - Identify specific 'weak_areas' and provide targeted remedial guidance in 'targeted_practice'.
3. If the student demonstrates solid conceptual and practical grasp appropriate for '{request.level}':
   - status: 'VERIFIED'
   - passed: True
   - score: 70 to 100
   - Highlight their 'strengths' and suggest 'next_step'.
4. If score >= 65, set status='VERIFIED' and passed=True. Otherwise status='NEEDS_PRACTICE' and passed=False.
5. Provide constructive, encouraging, actionable feedback.
"""

    try:
        response = call_gemini_with_fallback(
            client=client,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": AssessmentEvaluation,
            },
        )

        evaluation = AssessmentEvaluation.model_validate_json(response.text)
        evaluation.topic_id = request.topic_id

        return evaluation.model_dump()

    except HTTPException:
        raise
    except Exception as error:
        raise_ai_error(error, "Assessment Evaluator")


# -----------------------------
# Ask BuildReady Chatbot Endpoint
# -----------------------------
@app.post("/chat")
def chat(request: ChatRequest):
    """Context-aware AI mentor connected directly to student roadmap and topic verification."""
    client = get_gemini_client()

    topics_summary = ""
    if request.topics:
        topics_summary = "\n".join([
            f"- Topic #{t.id} '{t.title}': Status = {t.status}"
            for t in request.topics
        ])

    prompt = f"""
You are BuildReady, a friendly, encouraging, and deeply knowledgeable engineering mentor AI.
You are directly connected to the student's active learning roadmap.

Student Context:
- Engineering Path: {request.path}
- Domain / Topic: {request.domain}
- Level: {request.level}
- Goal: {request.goal}
- Project Idea: {request.idea if request.idea else 'None'}
- Current Active Topic: {request.current_topic if request.current_topic else 'Not specified'}

Roadmap Topics & Statuses:
{topics_summary if topics_summary else 'No active roadmap loaded yet'}

Student's Message:
"{request.message}"

MENTOR GUIDELINES & ROADMAP INTERACTION:
1. Maintain student context ({request.path}, {request.domain}, {request.level}).
2. If the student asks a technical or conceptual question:
   - Teach clearly with simple analogies and code/hardware examples matched to their level ({request.level}).
3. If the student claims to have completed a topic (e.g. 'I finished Functions', 'I completed Arduino setup', 'Verify my topic'):
   - Ask 2 to 3 targeted verification questions or practical challenges to test their knowledge.
4. If the student is replying to verification questions:
   - Evaluate their answers.
   - If they show genuine understanding, congratulate them and append EXACTLY:
     [STATUS_UPDATE: topic_id=<id>, status=VERIFIED]
   - If they gave incorrect or superficial answers, explain what was missing, give guidance, and append:
     [STATUS_UPDATE: topic_id=<id>, status=NEEDS_PRACTICE]
   (Replace <id> with the matching topic number from the roadmap).
5. If the student asks for practice on a weak topic, provide targeted exercises.
6. Keep answers concise, clear, and inspiring.
"""

    try:
        response = call_gemini_with_fallback(
            client=client,
            contents=prompt,
            config={
                "temperature": 0.7,
            },
        )

        reply_raw = response.text.strip() if response.text else "I am here to guide and verify your learning. What would you like to explore?"

        # Extract [STATUS_UPDATE: topic_id=X, status=STATUS]
        status_match = re.search(
            r"\[STATUS_UPDATE:\s*topic_id=(\d+),\s*status=(VERIFIED|NEEDS_PRACTICE|IN_PROGRESS)\]",
            reply_raw,
            re.IGNORECASE
        )

        topic_update = None
        clean_reply = reply_raw

        if status_match:
            tid = int(status_match.group(1))
            st = status_match.group(2).upper()
            topic_update = {
                "topic_id": tid,
                "status": st
            }
            # Remove the tag from the user-facing message
            clean_reply = re.sub(r"\[STATUS_UPDATE:.*?\]", "", reply_raw).strip()

        return {
            "reply": clean_reply,
            "topic_update": topic_update
        }

    except HTTPException:
        raise
    except Exception as error:
        raise_ai_error(error, "Ask BuildReady")