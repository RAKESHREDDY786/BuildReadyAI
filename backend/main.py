import hmac
import os
import logging
import re
from pathlib import Path
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from pydantic import BaseModel, Field, model_validator

import tracker

# -----------------------------
# Secure environment loading
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

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

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

# Initialise the usage tracking database at startup (creates file + table if absent).
# Never inserts demo/seed data.
tracker.init_db()

logger = logging.getLogger(__name__)

TECHNOLOGY_EXAMPLE_REQUIREMENTS = {
    "python": r"\b(?:print\s*\(|def\s+\w+|import\s+\w+)",
    "java": r"\bSystem\.out\.(?:print|println)\s*\(|\bpublic\s+class\b",
    "javascript": r"\bconsole\.log\s*\(|\b(?:const|let|var)\s+\w+|\bfunction\s+\w+",
    "c": r"#include\s*<stdio\.h>|\bprintf\s*\(|\bint\s+main\s*\(",
    "c++": r"#include\s*<iostream>|\bstd::|\bcout\s*<<|\bint\s+main\s*\(",
    "c#": r"\bConsole\.(?:WriteLine|Write)\s*\(|\busing\s+System\b",
    "sql": r"\b(?:SELECT|CREATE\s+TABLE|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b",
    "git": r"\bgit\s+(?:init|status|add|commit|log|branch|switch|merge|push|pull|clone)\b",
    "github": r"\bgithub\b|\bgh\s+(?:repo|pr)\b|\bgit\s+push\b|\bpull\s+request\b",
    "html": r"<!doctype\s+html|<html\b|<(?:head|body|h[1-6]|form|a)\b",
    "css": r"(?:\{[^}]*\b[a-z-]+\s*:\s*[^;}]+;|(?:^|\n)\s*[.#]?[a-z][\w-]*\s*\{)",
}

PYTHON_ONLY_EXAMPLE_SYNTAX = re.compile(
    r"(?m)^\s*def\s+\w+|(?<![\w.])print\s*\(|\belif\b|\bNone\b"
    r"|\bimport\s+(?:numpy|pandas|math|re|collections)\b"
)
DSA_CURRICULUM_TERMS = re.compile(
    r"\b(?:data structures?|algorithms?|complexit(?:y|ies)|big[- ]?o|"
    r"arrays?|strings?|search(?:ing)?|sort(?:ing)?|recursion|"
    r"linked lists?|stacks?|queues?|trees?|graphs?|hash(?:ing| tables?)|"
    r"dynamic programming|greedy|two pointers?|sliding windows?)\b",
    flags=re.IGNORECASE,
)
PYTHON_FUNDAMENTALS_TERMS = re.compile(
    r"\b(?:python fundamentals?|variables?|operators?|conditionals?|if[- ]else|"
    r"loops?|functions?|lists and dictionaries|collections?|file handling|"
    r"exceptions?|basic syntax|mini project)\b",
    flags=re.IGNORECASE,
)


def validate_plan_technology_examples(plan: "ProjectPlan", technology: str) -> None:
    """Reject generated example code that contradicts an explicit technology selection."""
    selected = technology.strip().casefold()
    if selected not in TECHNOLOGY_EXAMPLE_REQUIREMENTS and selected != "language-agnostic":
        return

    example_lines = [
        line.content
        for task in plan.tasks
        for example in [task.primary_example, *task.additional_examples]
        for line in example.lines
    ]
    examples = "\n".join(example_lines)
    if not examples:
        raise HTTPException(
            status_code=502,
            detail=f"The generated roadmap did not include examples for selected {technology}. Please try again.",
        )

    required_pattern = TECHNOLOGY_EXAMPLE_REQUIREMENTS.get(selected)
    if required_pattern and not re.search(required_pattern, examples, flags=re.IGNORECASE):
        raise HTTPException(
            status_code=502,
            detail=f"The generated examples did not match selected {technology}. Please generate the roadmap again.",
        )

    if selected != "python" and PYTHON_ONLY_EXAMPLE_SYNTAX.search(examples):
        raise HTTPException(
            status_code=502,
            detail=f"The generated examples included Python-specific syntax instead of selected {technology}. Please generate the roadmap again.",
        )


def validate_plan_curriculum(
    plan: "ProjectPlan",
    domain: str,
) -> None:
    """Reject a generic Python course when it does not match the selected curriculum."""
    normalized_domain = re.sub(r"[^a-z]", "", domain.casefold())
    task_text = [
        " ".join(
            filter(
                None,
                [
                    task.title,
                    task.description,
                    task.learning_objective or "",
                    task.verification_focus or "",
                    task.detailed_explanation,
                    *task.key_concepts,
                ],
            )
        )
        for task in plan.tasks
    ]
    if normalized_domain in {"dsa", "datastructuresalgorithms"}:
        matching_tasks = [
            text for text in task_text if DSA_CURRICULUM_TERMS.search(text)
        ]
        distinct_concepts = {
            match.group(0).casefold()
            for text in task_text
            for match in DSA_CURRICULUM_TERMS.finditer(text)
        }
        if len(matching_tasks) < min(6, len(plan.tasks)) or len(distinct_concepts) < 5:
            raise HTTPException(
                status_code=502,
                detail=(
                    "The generated roadmap did not cover Data Structures & Algorithms. "
                    "Please try generating it again."
                ),
            )

    valid_python_curriculum = normalized_domain in {
        "python",
        "programmingfundamentals",
        "programminglanguages",
    }
    if not valid_python_curriculum:
        python_fundamentals_tasks = sum(
            bool(PYTHON_FUNDAMENTALS_TERMS.search(" ".join(
                filter(None, [task.title, task.description, task.learning_objective or ""])
            )))
            for task in plan.tasks
        )
        if python_fundamentals_tasks >= min(6, len(plan.tasks)):
            raise HTTPException(
                status_code=502,
                detail=(
                    f"The generated roadmap substituted Python fundamentals for the selected "
                    f"{domain} curriculum. Please try generating it again."
                ),
            )


cors_origins_raw = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,http://127.0.0.1:3000",
)
if cors_origins_raw.strip() == "*":
    cors_origins = ["*"]
else:
    cors_origins = [
        origin.strip()
        for origin in cors_origins_raw.split(",")
        if origin.strip()
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
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
    technology: Optional[str] = ""
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
    url: Optional[str] = ""


class LessonExampleLine(BaseModel):
    content: str = Field(min_length=1, pattern=r"^[^\r\n]+$")
    explanation: str = Field(min_length=8)


class LessonExample(BaseModel):
    title: str = Field(min_length=3, max_length=80)
    lines: List[LessonExampleLine] = Field(min_length=1, max_length=12)


class LessonMistakeCorrection(BaseModel):
    mistake: str = Field(min_length=8)
    correction: str = Field(min_length=8)


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: Literal["NOT_STARTED", "IN_PROGRESS", "NEEDS_PRACTICE", "VERIFIED"] = "NOT_STARTED"
    verification_focus: Optional[str] = ""
    learning_objective: Optional[str] = ""
    concept_introduction: str = Field(min_length=20)
    why_learn: str = Field(min_length=12)
    lesson_prerequisites: List[str] = Field(min_length=1, max_length=5)
    real_world_analogy: str = Field(min_length=20)
    detailed_explanation: str = Field(min_length=80)
    key_concepts: List[str] = Field(min_length=2, max_length=6)
    simple_explanation: str = Field(min_length=20)
    syntax_rules: List[str] = Field(min_length=1, max_length=5)
    primary_example: LessonExample
    small_example: str = ""
    example_explanation: List[str] = Field(default_factory=list)
    additional_examples: List[LessonExample] = Field(min_length=1, max_length=2)
    real_world_example: str = Field(min_length=15)
    common_mistakes: List[str] = Field(min_length=1, max_length=5)
    mistake_corrections: List[LessonMistakeCorrection] = Field(min_length=1, max_length=5)
    learning_outcome: str = Field(min_length=12)
    practical_exercise: Optional[str] = ""
    assignment: str = Field(min_length=15)
    beginner_practice: str = Field(min_length=15)
    intermediate_practice: str = Field(min_length=15)
    real_world_application: str = Field(min_length=20)
    mini_challenge: str = Field(min_length=15)
    resources: List[str] = Field(default_factory=list)
    estimated_difficulty: Optional[str] = ""

    @model_validator(mode="after")
    def sync_legacy_example_fields(self):
        self.small_example = "\n".join(line.content for line in self.primary_example.lines)
        self.example_explanation = [line.explanation for line in self.primary_example.lines]
        return self


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
    options: List[str] = Field(default_factory=list)


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
    technology: Optional[str] = ""
    level: str
    goal: str
    idea: Optional[str] = ""
    verification_focus: Optional[str] = ""
    learning_objective: Optional[str] = ""
    concept_introduction: Optional[str] = ""
    lesson_prerequisites: List[str] = Field(default_factory=list)
    real_world_analogy: Optional[str] = ""
    detailed_explanation: Optional[str] = ""
    real_world_example: Optional[str] = ""
    key_concepts: List[str] = Field(default_factory=list)
    simple_explanation: Optional[str] = ""
    small_example: Optional[str] = ""
    example_explanation: List[str] = Field(default_factory=list)
    additional_examples: List[LessonExample] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    mistake_corrections: List[LessonMistakeCorrection] = Field(default_factory=list)
    practical_exercise: Optional[str] = ""
    assignment: Optional[str] = ""
    beginner_practice: Optional[str] = ""
    intermediate_practice: Optional[str] = ""
    real_world_application: Optional[str] = ""
    mini_challenge: Optional[str] = ""
    related_skills: List[str] = Field(default_factory=list)


class AnswerSubmission(BaseModel):
    question_id: int
    question: str
    user_answer: str
    options: List[str] = Field(default_factory=list)


class EvaluateAssessmentRequest(BaseModel):
    topic_id: int
    topic_title: str
    topic_description: str
    path: str
    domain: str
    technology: Optional[str] = ""
    level: str
    goal: str
    idea: Optional[str] = ""
    learning_objective: Optional[str] = ""
    concept_introduction: Optional[str] = ""
    lesson_prerequisites: List[str] = Field(default_factory=list)
    real_world_analogy: Optional[str] = ""
    detailed_explanation: Optional[str] = ""
    real_world_example: Optional[str] = ""
    key_concepts: List[str] = Field(default_factory=list)
    simple_explanation: Optional[str] = ""
    small_example: Optional[str] = ""
    example_explanation: List[str] = Field(default_factory=list)
    additional_examples: List[LessonExample] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    mistake_corrections: List[LessonMistakeCorrection] = Field(default_factory=list)
    practical_exercise: Optional[str] = ""
    assignment: Optional[str] = ""
    beginner_practice: Optional[str] = ""
    intermediate_practice: Optional[str] = ""
    real_world_application: Optional[str] = ""
    mini_challenge: Optional[str] = ""
    submissions: List[AnswerSubmission] = Field(min_length=3, max_length=5)


class QuestionEvaluation(BaseModel):
    question_id: int
    correct: bool
    feedback: str
    explanation: str


class AssessmentEvaluation(BaseModel):
    topic_id: int
    status: Literal["VERIFIED", "NEEDS_PRACTICE"]
    passed: bool
    score: int = Field(ge=0, le=100)
    overall_feedback: str
    strengths: List[str]
    weak_areas: List[str]
    targeted_practice: str
    next_step: str
    question_results: List[QuestionEvaluation] = Field(default_factory=list)


# --- Chat Models ---
class TopicState(BaseModel):
    id: int
    title: str
    status: Literal["NOT_STARTED", "IN_PROGRESS", "NEEDS_PRACTICE", "VERIFIED"] = "NOT_STARTED"


class AssessmentState(BaseModel):
    topic_id: int
    score: int
    status: Literal["VERIFIED", "NEEDS_PRACTICE"]
    overall_feedback: str
    weak_areas: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str
    path: Optional[str] = "General Engineering"
    domain: Optional[str] = "General"
    technology: Optional[str] = ""
    goal: Optional[str] = "Learn the Domain"
    level: Optional[str] = "Beginner"
    idea: Optional[str] = ""
    current_topic: Optional[str] = ""
    topics: List[TopicState] = Field(default_factory=list)
    assessment_results: List[AssessmentState] = Field(default_factory=list)


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
    logger.error("%s AI request failed (%s): %s", feature_name, type(error).__name__, error_text)

    if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
        raise HTTPException(
            status_code=429,
            detail=f"{feature_name} has reached the AI rate limit. Please try again in a few moments."
        )
    if "401" in error_text or "403" in error_text or "API_KEY_INVALID" in error_text or "Authentication failed" in error_text:
        raise HTTPException(
            status_code=401,
            detail="The AI service rejected its credentials. Check GEMINI_API_KEY in backend/.env."
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
        status_code=502,
        detail=f"{feature_name} could not complete the AI request. Please try again shortly."
    )


def call_gemini_with_fallback(client: genai.Client, contents: str, config: dict):
    last_error = None
    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            # Attach which model actually answered so callers can log it
            response._model_used = model_name
            return response
        except Exception as e:
            err_msg = str(e)
            logger.warning("Gemini model %s failed (%s); trying the next configured model.", model_name, type(e).__name__)
            last_error = e
            # If the API key itself is rejected, fallback models won't help
            if "401" in err_msg or "403" in err_msg or "API_KEY_INVALID" in err_msg or "Authentication failed" in err_msg:
                raise e
            continue
    if last_error:
        raise last_error
    raise RuntimeError("No Gemini models available.")


def _extract_tokens(response) -> tuple[int, int, int]:
    """
    Extract real token counts from a Gemini response.
    Returns (input_tokens, output_tokens, total_tokens).
    Never fabricates values — returns (0, 0, 0) when metadata is unavailable.
    """
    try:
        meta = getattr(response, "usage_metadata", None)
        if meta is None:
            return 0, 0, 0
        inp  = getattr(meta, "prompt_token_count",     None) or 0
        out  = getattr(meta, "candidates_token_count", None) or 0
        tot  = getattr(meta, "total_token_count",      None) or (inp + out)
        return int(inp), int(out), int(tot)
    except Exception:
        return 0, 0, 0


def _model_used(response) -> str:
    """Return the model name that produced a response, or empty string."""
    return getattr(response, "_model_used", "")


# -----------------------------
# Root & Health Check Endpoints
# -----------------------------
@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "gemini_configured": bool(
            os.getenv("GEMINI_API_KEY")
            and os.getenv("GEMINI_API_KEY").strip() not in ("", "your_key_here", "MY_REAL_KEY")
        )
    }


# -----------------------------
# Generate Plan Endpoint
# -----------------------------
@app.post("/generate-plan")
def generate_plan(
    request: ProjectRequest,
    x_user_id: Optional[str] = Header(default="anonymous", alias="X-User-Id"),
):
    client = get_gemini_client()

    is_learning = "learn" in request.goal.lower()
    user_idea = (request.idea or "").strip()
    normalized_domain = re.sub(r"[^a-z]", "", request.domain.casefold())
    selected_focus = (request.technology or "").strip() or (
        "Language-agnostic"
        if normalized_domain in {"dsa", "datastructuresalgorithms"}
        else request.domain
    )

    if is_learning:
        mode_instructions = f"""
MODE: LEARN THE DOMAIN (Personalized Adaptive Learning Roadmap)
- The student wants to master the domain '{request.domain}' in branch '{request.path}' at level '{request.level}'.
- Selected technology/topic focus: '{selected_focus}'.
- Student's specific focus: "{user_idea if user_idea else 'Master this subject from fundamentals to practical mastery.'}"
- The selected domain defines the curriculum; the selected technology/topic focus refines its language, tools, or notation. Student Input is only a goal/application hint and must not replace either selection.
- The selected domain determines the curriculum. The selected technology/topic determines the language, tools, or notation used to teach and practice that curriculum; it must not replace the domain with a generic course (for example, DSA with Python means DSA concepts implemented in Python, not Python fundamentals).
- Make at least 6 task titles and learning objectives name distinct concepts from the selected domain. A roadmap of generic programming fundamentals is invalid unless the selected domain is Programming Fundamentals or a programming language.
- For Data Structures & Algorithms, progress through algorithm analysis and Big-O, arrays/strings, searching and sorting, linked lists, stacks/queues, trees/graphs, hashing, and recursion or dynamic programming. Use language-neutral pseudocode when the selected technology is Language-agnostic.
- Generate 8 to 12 progressive, step-by-step topics/milestones in 'tasks':
  * Set status='NOT_STARTED' for all tasks.
  * Structure each lesson from understanding to application: include 'concept_introduction' (define the concept and its place in the subject), 'simple_explanation' (what it means in everyday beginner language), 'why_learn', 1-5 task-specific 'lesson_prerequisites' (or explicitly state that none are needed), and a memorable 'real_world_analogy'.
  * Use 'detailed_explanation' to teach how the concept works and when it is useful. For programming, introduce relevant value types, syntax, naming/usage rules, and behavior rather than assuming prior knowledge. Keep this focused and readable, usually 2-4 short paragraphs rather than a textbook chapter.
  * Keep lessons substantial but focused (roughly 120-220 words before examples and practice); do not pad them with repeated definitions. Teach the selected technology/topic, not Python by default. Use Python-specific content only when the selected technology/topic is Python or the selected domain genuinely requires Python.
  * Include 2-6 task-specific 'key_concepts' and 1-5 actionable 'syntax_rules'. Provide a 'primary_example' with a title and a 'lines' array; each line object must contain exactly one 'content' line and its paired 'explanation'. Provide 1-2 distinct 'additional_examples' in the same structured format. This pairing makes line-by-line explanations exact by construction.
  * Include a project/goal-specific 'real_world_example' and 'real_world_application'. Provide 1-5 'mistake_corrections', each pairing a likely mistake with a clear correction; include the same key pitfalls concisely in 'common_mistakes'. Include a measurable 'learning_outcome'.
  * Provide progressive practice: 'beginner_practice' with guided first steps, 'intermediate_practice' that transfers or combines ideas, and a 'mini_challenge' completed without step-by-step directions. Retain 'practical_exercise' as a concise summary of that progression. Include task-specific 'resources' and 'estimated_difficulty'.
  * Include a distinct actionable task-specific 'assignment'. Include useful official documentation/tutorial URLs in task 'resources' when known; never invent URLs.
  * In 'verification_focus', specify exactly what practical or conceptual skill must be verified for that topic.
  * For Beginners: introduce every prerequisite and technical term before relying on it; begin from first principles and explain every example line.
  * For Intermediates: focus on practical implementation, patterns, tooling, and real-world scenarios.
  * For Advanced: focus on architecture, performance, edge cases, and production standards.
- In 'skills_required': specify core skills with priorities.
- In 'learning_order': list the sequential order of topics (Topic 1 -> Topic 2 -> Topic 3).
- In 'recommended_projects': list 3 progressive mini-projects.
- In 'prerequisites': what the student needs before starting.
- In 'learning_resources': official documentation and recognized tutorials, including a valid official URL when known; never invent URLs.
- In 'tech_stack': tools, software, or libraries.
- In 'mvp_plan': core milestones for domain proficiency.
- In 'next_steps': immediate first action.
"""
    else:
        mode_instructions = f"""
MODE: BUILD A PROJECT (Verified Project Milestones & Skills)
- The student is in branch '{request.path}', domain '{request.domain}', level '{request.level}'.
- Selected technology/topic focus: '{selected_focus}'.
- Project goal/idea: "{user_idea if user_idea else 'Suggest a high-impact, realistic project for this domain.'}"
- The selected domain determines the project curriculum and the selected technology/topic determines implementation syntax/tools. Student Input describes the project to support and must not cause an unrelated language or domain switch.
- Make at least 6 task titles and learning objectives name distinct concepts from the selected domain. Do not substitute a generic Python course for the selected domain.
- For Data Structures & Algorithms, include algorithm analysis and Big-O, arrays/strings, searching and sorting, linked lists, stacks/queues, trees/graphs, hashing, and recursion or dynamic programming. Use language-neutral pseudocode when the selected technology is Language-agnostic.
- Generate 8 to 12 realistic implementation milestones in 'tasks':
  * Set status='NOT_STARTED' for all tasks.
  * Give every milestone the same structured teaching: 'concept_introduction', beginner-friendly 'simple_explanation', project-specific 'why_learn', 1-5 'lesson_prerequisites' (or explicitly state none), a memorable 'real_world_analogy', and a focused 'detailed_explanation' that teaches before asking the learner to implement.
  * Keep teaching substantial but focused (roughly 120-220 words before examples and practice); do not pad with repeated definitions. Teach the selected technology/topic, not Python by default. Use Python-specific content only when the selected technology/topic is Python or the project explicitly requires Python.
  * Include 2-6 task-specific 'key_concepts', 'syntax_rules', a 'primary_example' with a title and a 'lines' array of paired 'content' and 'explanation' entries, and 1-2 distinct 'additional_examples' with the same structured format. Each entry represents one displayed example line and its explanation.
  * Include project-specific 'real_world_example' and 'real_world_application'. Add 1-5 'mistake_corrections' pairing likely errors with actionable fixes, a concise 'common_mistakes' list, and a measurable 'learning_outcome'.
  * Sequence work as 'beginner_practice' (guided), 'intermediate_practice' (less guided and combines ideas), then 'mini_challenge' (independent application). Retain a concise 'practical_exercise' summary and include task-specific 'resources' and 'estimated_difficulty'.
  * Include a distinct actionable task-specific 'assignment'. Include useful official documentation/tutorial URLs in task 'resources' when known; never invent URLs.
  * Teach the knowledge required for each code, hardware, design, or testing milestone; do not assume a complete beginner already knows unintroduced terms.
  * In 'verification_focus', specify exactly what implementation, circuit, code, or testing must be verified for that milestone.
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
- Selected Technology/Topic: {selected_focus}
- Student Level: {request.level}
- Goal Type: {request.goal}
- Student Input: {user_idea if user_idea else 'None specified'}

{mode_instructions}

CRITICAL RULES:
1. The selected Domain determines the curriculum; the selected Technology/Topic determines implementation syntax/tools within that curriculum. Student Input is context only and cannot replace either selection. Domain=Data Structures & Algorithms with Student Input='I want to learn Python' remains a DSA roadmap; with Technology=Java use Java examples for DSA, with Technology=Python use Python examples for DSA, and with Technology=Language-agnostic use language-neutral explanations and pseudocode rather than defaulting to Python.
2. Be strictly branch-aware: use the selected scope and relevant branch context. Do not infer that AIML always means Python; Java, JavaScript, C, C++, C#, SQL, Git, GitHub, HTML, CSS, and other selected topics must be taught directly when selected.
   Cybersecurity must focus on networking, Linux, and defensive security; Web Development on frontend/backend web technologies; Electrical/EEE on circuits, machines, power, and control; Chemical on process engineering and safety; Biotechnology on biology, genetics, and bioprocessing.
3. Adapt depth strictly to '{request.level}' level.
4. Every task in 'tasks' must have an integer id (1, 2, 3...) and status 'NOT_STARTED'.
5. Derive actual skills and sequence from selected scope and exact project; do not reuse a generic roadmap when the project changes.
6. Do not hallucinate URLs.
7. All fields must be informative, practical, and specific to branch, selected domain, selected technology/topic, and goal.
8. Every lesson field must be accurate, task-specific, and understandable to a complete beginner at the selected level. Teach understanding, examples/corrections, progressive practice, project application, assignment, mini challenge, then assessment. Each example line requires its paired explanation. Never fall back to generic Python content for another selected technology/topic.
"""

    # Sanitise user ID: only alphanumerics + hyphens, max 64 chars
    safe_user_id = re.sub(r"[^A-Za-z0-9\-]", "", (x_user_id or "anonymous"))[:64] or "anonymous"

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

        # --- Accumulate real token usage across all Gemini calls for this request ---
        _inp, _out, _tot = _extract_tokens(response)
        _model = _model_used(response)

        if len(plan.tasks) < 8:
            existing_topics = "\n".join(
                f"- {task.title}: {task.learning_objective or task.description}"
                for task in plan.tasks
            )
            expansion_prompt = f"""
The first roadmap response was too short ({len(plan.tasks)} tasks). Expand it into a complete
8 to 12 task roadmap for the same student and exact goal. Return the COMPLETE roadmap, not only
the additions. Preserve the useful existing progression and add distinct prerequisite and
intermediate learning tasks needed to reach the goal. Do not duplicate, rename, or split a task
without adding a genuinely new learning objective.

Existing topics to retain and build on:
{existing_topics}

Original student-specific requirements:
{prompt}
"""
            response = call_gemini_with_fallback(
                client=client,
                contents=expansion_prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ProjectPlan,
                },
            )
            plan = ProjectPlan.model_validate_json(response.text)
            ei, eo, et = _extract_tokens(response)
            _inp += ei; _out += eo; _tot += et

        task_ids = [task.id for task in plan.tasks]
        normalized_titles = [" ".join(task.title.casefold().split()) for task in plan.tasks]
        if (
            len(task_ids) < 8
            or len(set(task_ids)) != len(task_ids)
            or len(set(normalized_titles)) != len(normalized_titles)
        ):
            raise HTTPException(
                status_code=502,
                detail="The AI could not produce at least 8 distinct roadmap tasks. Please try generating the roadmap again.",
            )

        try:
            validate_plan_curriculum(plan, request.domain)
            validate_plan_technology_examples(plan, selected_focus)
        except HTTPException as scope_error:
            logger.warning(
                "Generated roadmap did not match selected domain %s or technology %s; requesting one correction.",
                request.domain,
                selected_focus,
            )
            incorrect_examples = "\n".join(
                f"- Task '{task.title}': "
                + " | ".join(line.content for line in task.primary_example.lines)
                for task in plan.tasks[:4]
            )
            correction_prompt = f"""
The previous roadmap did not honor the selected domain curriculum and/or technology/topic and must be corrected.

Authoritative selections:
- Path: {request.path}
- Domain: {request.domain}
- Technology/topic: {selected_focus}
- Level: {request.level}
- Goal type: {request.goal}
- User input (context only; it must not override selections): {user_idea}

The selected domain curriculum and technology/topic are mandatory. Keep the selected domain's concepts as the curriculum; rewrite any unrelated generic roadmap content and replace examples that use the wrong language/tool.
Invalid examples to replace:
{incorrect_examples}

Validation feedback: {scope_error.detail}
Return a complete 8 to 12 task roadmap conforming to the original schema and generation requirements below.
Do not omit any required lesson field, assignment, progressive practice, project application, or assessment preparation.

Original requirements:
{prompt}
"""
            response = call_gemini_with_fallback(
                client=client,
                contents=correction_prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ProjectPlan,
                },
            )
            plan = ProjectPlan.model_validate_json(response.text)
            ei, eo, et = _extract_tokens(response)
            _inp += ei; _out += eo; _tot += et
            task_ids = [task.id for task in plan.tasks]
            normalized_titles = [" ".join(task.title.casefold().split()) for task in plan.tasks]
            if (
                len(task_ids) < 8
                or len(set(task_ids)) != len(task_ids)
                or len(set(normalized_titles)) != len(normalized_titles)
            ):
                raise HTTPException(
                    status_code=502,
                    detail="The AI could not correct the roadmap for the selected technology/topic. Please try again.",
                )
            validate_plan_curriculum(plan, request.domain)
            validate_plan_technology_examples(plan, selected_focus)

        for index, task in enumerate(plan.tasks):
            task.status = "IN_PROGRESS" if index == 0 else "NOT_STARTED"

        display_idea = user_idea if user_idea else (
            f"{request.domain} Mastery Roadmap" if is_learning else f"{request.domain} Project"
        )

        # Record REAL token usage from this successful roadmap generation
        tracker.record_usage(
            user_id=safe_user_id,
            feature="generate-plan",
            input_tokens=_inp,
            output_tokens=_out,
            total_tokens=_tot,
            success=True,
            model_used=_model,
        )

        return {
            "project_idea": display_idea,
            "path": request.path,
            "domain": request.domain,
            "technology": selected_focus,
            "level": request.level,
            "goal": request.goal,
            "ai_plan": plan.model_dump(),
        }

    except HTTPException:
        # Record failed plan generation (no output tokens when Gemini was not reached)
        tracker.record_usage(
            user_id=safe_user_id,
            feature="generate-plan",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            success=False,
            notes="HTTPException before or during generation",
        )
        raise
    except Exception as error:
        tracker.record_usage(
            user_id=safe_user_id,
            feature="generate-plan",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            success=False,
            notes=str(error)[:200],
        )
        raise_ai_error(error, "BuildReady-AI Plan Generator")


# -----------------------------
# Generate Assessment Endpoint
# -----------------------------
@app.post("/generate-assessment")
def generate_assessment(
    request: GenerateAssessmentRequest,
    x_user_id: Optional[str] = Header(default="anonymous", alias="X-User-Id"),
):
    """Generate adaptive verification questions tailored to branch, domain, topic, and level."""
    client = get_gemini_client()

    branch_guidance = ""
    path_lower = request.path.lower()
    domain_lower = request.domain.lower()
    selected_technology = (request.technology or request.domain).strip()
    technology_lower = selected_technology.lower()

    if technology_lower in {"java", "javascript", "c", "c++", "c#", "python", "html", "css"}:
        branch_guidance = f"Use {selected_technology} syntax, code examples, debugging, and output reasoning; do not substitute another programming language."
    elif technology_lower in {"sql", "git", "github"}:
        branch_guidance = f"Use {selected_technology}-specific commands, queries, workflows, and debugging; do not substitute another technology."
    elif "data structures" in domain_lower or domain_lower == "dsa":
        branch_guidance = "Assess the selected data-structure/algorithm concept, complexity when taught, and a concrete trace or implementation in the selected language."
    elif "sql" in domain_lower or "database" in domain_lower:
        branch_guidance = "Include SQL query formulation, query debugging, table joins, or result reasoning."
    elif "developer tools" in domain_lower:
        branch_guidance = "Assess the selected version-control/tool workflow using real Git or GitHub commands and repository scenarios."
    elif "ece" in path_lower or "iot" in path_lower or "hardware" in domain_lower:
        branch_guidance = "Include circuit connections, sensor pinouts, embedded code logic (Arduino/C++), or hardware troubleshooting."
    elif "aiml" in path_lower or "ai" in path_lower or "machine learning" in domain_lower:
        branch_guidance = "Include reasoning specific to the selected AI/ML domain and the concepts taught in this task; use the selected technology rather than assuming Python."
    elif "cse" in path_lower:
        branch_guidance = "Include programming, data structures, database, operating system, networking, or software engineering problems directly related to the topic."
    elif "cyber" in path_lower:
        branch_guidance = "Use a defensive security or networking scenario, Linux concepts, and safe, authorized analysis."
    elif "electrical" in path_lower or "eee" in path_lower:
        branch_guidance = "Include circuit analysis, electrical machines, power systems, measurements, or control reasoning relevant to the task."
    elif "chemical" in path_lower:
        branch_guidance = "Include process engineering, reaction or transport concepts, process safety, or practical plant reasoning relevant to the task."
    elif "biotech" in path_lower or "biotechnology" in path_lower:
        branch_guidance = "Include cell or molecular biology, genetics, bioinformatics, or bioprocess reasoning relevant to the task."
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
- Selected technology/topic: {request.technology or request.domain}
- Level: {request.level}
- Goal: {request.goal}
- Project: {request.idea if request.idea else 'General Learning'}

Topic to Verify:
- Topic ID: {request.topic_id}
- Title: {request.topic_title}
- Description: {request.topic_description}
- Learning objective: {request.learning_objective or 'Use the topic description'}
- Concept introduction: {request.concept_introduction or 'Use the task title and description'}
- Prerequisites taught: {', '.join(request.lesson_prerequisites) if request.lesson_prerequisites else 'None specified'}
- Real-world analogy taught: {request.real_world_analogy or 'None specified'}
- Detailed explanation taught: {request.detailed_explanation or 'Use the task lesson'}
- Key concepts taught: {', '.join(request.key_concepts) if request.key_concepts else 'Derive exact concepts from the task lesson'}
- Simple explanation taught: {request.simple_explanation or 'Use the task description and learning objective'}
- Small example taught: {request.small_example or 'Derive an example from the task lesson'}
- Small example explanation: {request.example_explanation}
- Additional examples taught: {[example.model_dump() for example in request.additional_examples]}
- Common mistakes taught: {', '.join(request.common_mistakes) if request.common_mistakes else 'Identify mistakes directly related to this task'}
- Mistakes and corrections taught: {[item.model_dump() for item in request.mistake_corrections]}
- Beginner practice: {request.beginner_practice or request.practical_exercise or 'Create a guided practice task'}
- Intermediate practice: {request.intermediate_practice or 'Create a progressively harder task based on the lesson'}
- Assignment: {request.assignment or 'No separate assignment specified'}
- Real-world application: {request.real_world_application or request.real_world_example or 'Apply the concept to the stated goal'}
- Mini challenge: {request.mini_challenge or 'Create a concise independent challenge'}
- Practice sequence summary: {request.practical_exercise or 'Use the beginner and intermediate practice tasks'}
- Verification focus: {request.verification_focus or 'Verify the core skills for this topic'}
- Relevant project/learning skills: {', '.join(request.related_skills) if request.related_skills else 'Derive relevant skills from the topic and goal'}

Assessment Requirements:
1. Create 3 to 5 focused verification questions that prove whether the student has genuinely learned this topic.
2. {branch_guidance}
3. Tailor questions strictly to '{request.level}' level.
4. The 'question' field MUST contain the complete student-facing question, not the category, question type, or a placeholder such as 'concept'. Never return a question whose text is only 'concept', 'practical', 'code', or another type label.
5. Ask concrete, answerable, topic-specific questions using only the concepts and skills taught above, including the examples, practice, and assignment. Use the selected technology/topic, never default to Python unless Python is selected or explicitly required by the selected domain.
6. Mix conceptual reasoning with practical execution (e.g. writing a code snippet, explaining a circuit, writing a query, or solving a scenario).
7. For multiple-choice questions, include 3 or 4 choices in 'options'; for other questions, options may be empty.
8. Specify passing criteria clearly (e.g. 'Must correctly explain core concepts and provide working syntax/logic for the practical problem').
"""

    safe_user_id = re.sub(r"[^A-Za-z0-9\-]", "", (x_user_id or "anonymous"))[:64] or "anonymous"

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
        question_ids = [question.id for question in assessment.questions]
        question_texts = [" ".join(question.question.casefold().split()) for question in assessment.questions]
        if (
            not 3 <= len(question_ids) <= 5
            or len(set(question_ids)) != len(question_ids)
            or any(
                len(text) < 4
                or re.fullmatch(
                    r"(?:q(?:uestion)?\s*\d+\s*[:.)-]?\s*)?(?:concept|practical|code|question|multiple choice)",
                    text,
                )
                for text in question_texts
            )
        ):
            raise ValueError("Assessment questions must have unique IDs and meaningful, topic-specific question text.")

        inp, out, tot = _extract_tokens(response)
        tracker.record_usage(
            user_id=safe_user_id,
            feature="generate-assessment",
            input_tokens=inp,
            output_tokens=out,
            total_tokens=tot,
            success=True,
            model_used=_model_used(response),
        )
        return assessment.model_dump()

    except HTTPException:
        tracker.record_usage(
            user_id=safe_user_id,
            feature="generate-assessment",
            input_tokens=0, output_tokens=0, total_tokens=0,
            success=False,
        )
        raise
    except Exception as error:
        tracker.record_usage(
            user_id=safe_user_id,
            feature="generate-assessment",
            input_tokens=0, output_tokens=0, total_tokens=0,
            success=False, notes=str(error)[:200],
        )
        raise_ai_error(error, "Assessment Generator")


# -----------------------------
# Evaluate Assessment Endpoint
# -----------------------------
@app.post("/evaluate-assessment")
def evaluate_assessment(
    request: EvaluateAssessmentRequest,
    x_user_id: Optional[str] = Header(default="anonymous", alias="X-User-Id"),
):
    """Evaluate student answers to verify whether the topic is COMPLETED/VERIFIED or NEEDS_PRACTICE."""
    submitted_ids = [submission.question_id for submission in request.submissions]
    if len(set(submitted_ids)) != len(submitted_ids):
        raise HTTPException(status_code=422, detail="Assessment question IDs must be unique.")
    client = get_gemini_client()

    submissions_text = "\n\n".join([
        f"Question {sub.question_id}: {sub.question}\n"
        f"Available choices: {', '.join(sub.options) if sub.options else 'No multiple-choice options'}\n"
        f"Student's Answer:\n\"{sub.user_answer.strip() if sub.user_answer.strip() else '[No Answer Provided]'}\""
        for sub in request.submissions
    ])

    prompt = f"""
You are BuildReady-AI, a rigorous but fair engineering evaluator.

Context:
- Path: {request.path}
- Domain: {request.domain}
- Selected technology/topic: {request.technology or request.domain}
- Level: {request.level}
- Goal: {request.goal}
- Project: {request.idea if request.idea else 'General Learning'}
- Topic: {request.topic_title} ({request.topic_description})
- Learning objective: {request.learning_objective or 'Use the topic description'}
- Concept introduction: {request.concept_introduction or 'Use the task title and description'}
- Prerequisites taught: {', '.join(request.lesson_prerequisites) if request.lesson_prerequisites else 'None specified'}
- Real-world analogy taught: {request.real_world_analogy or 'None specified'}
- Detailed explanation taught: {request.detailed_explanation or 'Use the task lesson'}
- Key concepts taught: {', '.join(request.key_concepts) if request.key_concepts else 'Derive from the task description'}
- Simple explanation taught: {request.simple_explanation or 'Use the topic description'}
- Small example taught: {request.small_example or 'Derive from the topic description'}
- Small example explanation: {request.example_explanation}
- Additional examples taught: {[example.model_dump() for example in request.additional_examples]}
- Common mistakes taught: {', '.join(request.common_mistakes) if request.common_mistakes else 'Identify mistakes relevant to this topic'}
- Mistakes and corrections taught: {[item.model_dump() for item in request.mistake_corrections]}
- Beginner practice: {request.beginner_practice or request.practical_exercise or 'Apply the topic to a guided task'}
- Intermediate practice: {request.intermediate_practice or 'Apply the topic in a progressively harder task'}
- Assignment: {request.assignment or 'No separate assignment specified'}
- Real-world application: {request.real_world_application or 'Apply the topic to the stated goal'}
- Mini challenge: {request.mini_challenge or 'Apply the topic independently'}
- Practice sequence summary: {request.practical_exercise or 'Use the beginner and intermediate practice tasks'}

Student's Submitted Answers:
{submissions_text}

EVALUATION RULES:
1. Evaluate each answer for genuine comprehension and technical correctness against the selected technology/topic, learning objective, concepts, explanation, examples, practice, and assignment taught above. Do not introduce Python conventions unless Python is selected or explicitly required.
2. For a multiple-choice question, compare the student's selected answer with the supplied choices and determine the technically correct choice yourself. Mark an objectively incorrect selection incorrect; do not award credit just because it is related to the topic.
3. Evaluate only the named task and exact submitted questions. Do not use feedback or examples from another topic or project.
4. If the student answers are empty, superficial, or contain phrases like 'i don't know', 'idk', or are fundamentally incorrect:
   - status: 'NEEDS_PRACTICE'
   - passed: False
   - score: 0 to 50
   - Identify specific 'weak_areas' and provide targeted remedial guidance in 'targeted_practice'.
5. If the student demonstrates solid conceptual and practical grasp appropriate for '{request.level}':
   - status: 'VERIFIED'
   - passed: True
   - score: 70 to 100
   - Highlight their 'strengths' and suggest 'next_step'.
6. If score >= 65, set status='VERIFIED' and passed=True. Otherwise status='NEEDS_PRACTICE' and passed=False.
7. Set 'question_results' with one entry per submitted question. Include question_id, correct, specific feedback, and an explanation of the expected reasoning.
8. Keep 'passed' and 'status' consistent with the 65 point threshold and provide constructive, encouraging, actionable feedback tied to this task.
"""

    safe_user_id = re.sub(r"[^A-Za-z0-9\-]", "", (x_user_id or "anonymous"))[:64] or "anonymous"

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
        submitted_ids = set(submitted_ids)
        evaluated_ids = {item.question_id for item in evaluation.question_results}
        if (
            submitted_ids != evaluated_ids
            or len(evaluation.question_results) != len(request.submissions)
            or len(evaluated_ids) != len(evaluation.question_results)
        ):
            raise ValueError("Evaluation must provide feedback for every submitted question.")
        evaluation.passed = evaluation.score >= 65
        evaluation.status = "VERIFIED" if evaluation.passed else "NEEDS_PRACTICE"

        inp, out, tot = _extract_tokens(response)
        tracker.record_usage(
            user_id=safe_user_id,
            feature="evaluate-assessment",
            input_tokens=inp,
            output_tokens=out,
            total_tokens=tot,
            success=True,
            model_used=_model_used(response),
        )
        return evaluation.model_dump()

    except HTTPException:
        tracker.record_usage(
            user_id=safe_user_id,
            feature="evaluate-assessment",
            input_tokens=0, output_tokens=0, total_tokens=0,
            success=False,
        )
        raise
    except Exception as error:
        tracker.record_usage(
            user_id=safe_user_id,
            feature="evaluate-assessment",
            input_tokens=0, output_tokens=0, total_tokens=0,
            success=False, notes=str(error)[:200],
        )
        raise_ai_error(error, "Assessment Evaluator")


# -----------------------------
# Ask BuildReady Chatbot Endpoint
# -----------------------------
@app.post("/chat")
def chat(
    request: ChatRequest,
    x_user_id: Optional[str] = Header(default="anonymous", alias="X-User-Id"),
):
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
- Selected technology/topic: {request.technology or request.domain}
- Level: {request.level}
- Goal: {request.goal}
- Project Idea: {request.idea if request.idea else 'None'}
- Current Active Topic: {request.current_topic if request.current_topic else 'Not specified'}

Roadmap Topics & Statuses:
{topics_summary if topics_summary else 'No active roadmap loaded yet'}

Recent Assessment Results:
{chr(10).join([f"- Topic #{result.topic_id}: {result.score}/100, {result.status}. Feedback: {result.overall_feedback}; areas to practice: {', '.join(result.weak_areas) or 'none listed'}" for result in request.assessment_results]) if request.assessment_results else 'No assessment results yet'}

Student's Message:
"{request.message}"

MENTOR GUIDELINES & ROADMAP INTERACTION:
1. Maintain student context ({request.path}, {request.domain}, {request.technology or request.domain}, {request.level}); selected technology/domain take precedence over unrelated words in the goal.
2. If the student asks a technical or conceptual question:
   - Teach clearly with simple analogies and code/hardware examples matched to their level ({request.level}).
3. Explain the next learning step using the roadmap and respect task order and statuses.
4. If asked about a failed assessment, refer to its recorded score, feedback, and weak areas; provide targeted practice.
5. You may recommend that a task be started or practiced, but NEVER claim a task is VERIFIED or change its status; only the assessment endpoint can verify a task.
6. If asked whether the student is ready, base the answer on verified roadmap tasks and clearly identify remaining work.
7. Keep answers concise, clear, and inspiring.
"""

    safe_user_id = re.sub(r"[^A-Za-z0-9\-]", "", (x_user_id or "anonymous"))[:64] or "anonymous"

    try:
        response = call_gemini_with_fallback(
            client=client,
            contents=prompt,
            config={
                "temperature": 0.7,
            },
        )

        reply_raw = response.text.strip() if response.text else "I am here to guide and verify your learning. What would you like to explore?"

        inp, out, tot = _extract_tokens(response)
        tracker.record_usage(
            user_id=safe_user_id,
            feature="chat",
            input_tokens=inp,
            output_tokens=out,
            total_tokens=tot,
            success=True,
            model_used=_model_used(response),
        )
        return {
            "reply": reply_raw,
            "topic_update": None
        }

    except HTTPException:
        tracker.record_usage(
            user_id=safe_user_id,
            feature="chat",
            input_tokens=0, output_tokens=0, total_tokens=0,
            success=False,
        )
        raise
    except Exception as error:
        tracker.record_usage(
            user_id=safe_user_id,
            feature="chat",
            input_tokens=0, output_tokens=0, total_tokens=0,
            success=False, notes=str(error)[:200],
        )
        raise_ai_error(error, "Ask BuildReady")


# =============================================================================
# FOUNDER-ONLY DASHBOARD ENDPOINTS
# =============================================================================
# Protected by a secret key sent as the X-Founder-Key header.
# Set FOUNDER_SECRET_KEY in backend/.env locally or in the Render environment (never committed to git).
# The frontend dashboard page reads ONLY from these endpoints.
# Normal students never see or call these endpoints.

FOUNDER_KEY_PLACEHOLDERS = {"change-this-to-a-long-random-secret"}


def _normalize_founder_key(value: Optional[str]) -> str:
    return (value or "").strip().strip('"').strip("'").strip()


def _check_founder_key(key: Optional[str]) -> None:
    """Raise 503 if no founder secret is configured, 403 if the provided key does not match."""
    expected = _normalize_founder_key(os.getenv("FOUNDER_SECRET_KEY"))
    if not expected or expected in FOUNDER_KEY_PLACEHOLDERS:
        raise HTTPException(
            status_code=503,
            detail="Founder dashboard is not configured. Set FOUNDER_SECRET_KEY on the server.",
        )

    provided = _normalize_founder_key(key)
    if not provided or not hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Invalid founder secret key.")


@app.get("/founder/stats")
def founder_stats(
    period: str = "all",
    x_founder_key: Optional[str] = Header(default=None, alias="X-Founder-Key"),
):
    """
    Founder-only: return aggregated real usage statistics.
    period must be one of: today | 7d | 30d | all
    Protected by X-Founder-Key header — never exposed to students.
    """
    _check_founder_key(x_founder_key)
    if period not in ("today", "7d", "30d", "all"):
        period = "all"
    return tracker.get_summary(period)


@app.get("/founder/users")
def founder_users(
    period: str = "all",
    x_founder_key: Optional[str] = Header(default=None, alias="X-Founder-Key"),
):
    """
    Founder-only: return per-user real usage statistics.
    Returns an empty list when no data has been recorded — no fake users.
    Protected by X-Founder-Key header.
    """
    _check_founder_key(x_founder_key)
    if period not in ("today", "7d", "30d", "all"):
        period = "all"
    return tracker.get_per_user_stats(period)


@app.get("/founder/events")
def founder_events(
    limit: int = 50,
    x_founder_key: Optional[str] = Header(default=None, alias="X-Founder-Key"),
):
    """
    Founder-only: return the most recent raw usage events (up to 100).
    Useful for debugging and verifying that real token values are being captured.
    """
    _check_founder_key(x_founder_key)
    limit = min(max(1, limit), 100)
    return tracker.get_recent_events(limit)


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend-assets")