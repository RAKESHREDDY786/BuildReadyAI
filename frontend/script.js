// State variables
let selectedPath = "";
let selectedLevel = "";
let selectedGoal = "";
let selectedDomain = "";
let selectedTechnology = "";
let currentPlan = null;
let currentPlanIdea = "";
let currentTaskId = null;
let assessmentsByTask = {};
let assessmentHistory = {};
const rawApiUrl = typeof window.BUILDREADY_CONFIG?.apiBaseUrl === "string" ? window.BUILDREADY_CONFIG.apiBaseUrl : "http://127.0.0.1:8000";
const API_BASE_URL = rawApiUrl.replace(/\/+$/, "");
const TASK_STATUSES = ["NOT_STARTED", "IN_PROGRESS", "NEEDS_PRACTICE", "VERIFIED"];

// DOM Elements
const pathCards = document.querySelectorAll(".path-card");
const levelCards = document.querySelectorAll(".level-card");
const goalCards = document.querySelectorAll(".goal-card");
const domainContainer = document.getElementById("domainContainer");
const technologyContainer = document.getElementById("technologyContainer");
const otherPathSection = document.getElementById("otherPathSection");
const otherPathInput = document.getElementById("otherPathInput");
const projectIdea = document.getElementById("projectIdea");
const buildBtn = document.getElementById("buildBtn");
const clearSavedPlanBtn = document.getElementById("clearSavedPlanBtn");
const resultDiv = document.getElementById("result");

const chatInput = document.getElementById("chatInput");
const chatSendBtn = document.getElementById("chatSendBtn");
const chatMessages = document.getElementById("chatMessages");
const chatContext = document.getElementById("chatContext");

// Branch-Specific Domains
const pathDomains = {
    "AIML": [
        "Python",
        "Programming Languages",
        "Math & Statistics",
        "Data & Analysis",
        "Machine Learning",
        "Deep Learning",
        "NLP",
        "Computer Vision",
        "Generative AI",
        "Data Structures & Algorithms",
        "Databases",
        "Developer Tools"
    ],
    "AI": [
        "Python",
        "Math & Statistics",
        "Artificial Intelligence Fundamentals",
        "Machine Learning",
        "NLP",
        "Computer Vision",
        "Generative AI"
    ],
    "CSE": [
        "Programming Fundamentals",
        "Programming Languages",
        "Data Structures & Algorithms",
        "Object-Oriented Programming",
        "Databases",
        "Developer Tools",
        "Operating Systems",
        "Computer Networks",
        "APIs",
        "Software Engineering & Testing"
    ],
    "Data Science": [
        "Python",
        "Statistics",
        "SQL",
        "Developer Tools",
        "Data Analysis",
        "Data Visualization",
        "Machine Learning",
        "Data Engineering"
    ],
    "Software Development": [
        "Programming Fundamentals",
        "Programming Languages",
        "Data Structures & Algorithms",
        "Object-Oriented Programming",
        "Databases",
        "Developer Tools",
        "APIs",
        "Backend Development",
        "Software Engineering",
        "Testing"
    ],
    "Web Development": [
        "HTML",
        "CSS",
        "JavaScript",
        "Web Technologies",
        "Frontend Development",
        "Backend Development",
        "APIs",
        "Databases",
        "Deployment"
    ],
    "Cybersecurity": [
        "Networking",
        "Linux",
        "Security Fundamentals",
        "Web Security",
        "Cryptography",
        "Security Tools",
        "Ethical Security Testing"
    ],
    "ECE / IoT": [
        "Electronics Fundamentals",
        "Digital Electronics",
        "Microcontrollers",
        "Embedded Systems",
        "Sensors",
        "Communication Systems",
        "IoT",
        "PCB / Hardware Design"
    ],
    "Electrical / EEE": [
        "Circuit Analysis",
        "Electrical Machines",
        "Power Systems",
        "Control Systems",
        "Power Electronics",
        "Electrical Measurements",
        "Renewable Energy",
        "Electric Vehicles",
        "Industrial Automation",
        "Embedded & Microcontrollers"
    ],
    "Mechanical": [
        "Engineering Mechanics",
        "Thermodynamics",
        "Fluid Mechanics",
        "Manufacturing",
        "Machine Design",
        "CAD / CAE",
        "Robotics & Automation",
        "Materials & Processes",
        "Automotive Systems",
        "Industrial Engineering"
    ],
    "Civil": [
        "Structural Engineering",
        "Geotechnical Engineering",
        "Transportation Engineering",
        "Water Resources",
        "Construction Engineering",
        "Surveying & Geomatics",
        "Environmental Engineering",
        "Civil CAD / BIM",
        "Urban Infrastructure",
        "Project Management"
    ],
    "Chemical": [
        "Chemical Process Fundamentals",
        "Thermodynamics",
        "Reaction Engineering",
        "Fluid & Heat Transfer",
        "Process Design",
        "Process Control",
        "Process Simulation",
        "Environmental & Sustainable Processes",
        "Materials & Polymers",
        "Industrial Safety"
    ],
    "Biotechnology": [
        "Cell Biology",
        "Genetics",
        "Molecular Biology",
        "Microbiology",
        "Bioinformatics",
        "Biochemistry",
        "Bioprocess Engineering",
        "Genomics",
        "Pharmaceutical Biotechnology",
        "Environmental Biotechnology"
    ]
};

const technologyOptionsByDomain = {
    "Python": ["Python"],
    "Programming Languages": ["Java", "JavaScript", "C", "C++", "C#", "Python"],
    "Programming Fundamentals": ["Language-agnostic", "C", "C++", "C#", "Java", "JavaScript", "Python"],
    "Data Structures & Algorithms": ["Language-agnostic", "Java", "JavaScript", "C", "C++", "C#", "Python"],
    "Databases": ["SQL"],
    "SQL": ["SQL"],
    "Developer Tools": ["Git", "GitHub"],
    "HTML": ["HTML"],
    "CSS": ["CSS"],
    "JavaScript": ["JavaScript"],
    "Web Technologies": ["HTML", "CSS", "JavaScript"],
    "Data & Analysis": ["Python", "SQL"],
    "Statistics": ["Language-agnostic", "Python"],
    "Machine Learning": ["Python"],
    "Deep Learning": ["Python"],
    "NLP": ["Python"],
    "Computer Vision": ["Python"],
    "Generative AI": ["Python"],
    "Artificial Intelligence Fundamentals": ["Language-agnostic", "Python"]
};

// Update button & placeholder text depending on Goal mode
function updateGoalUI() {
    const isLearningGoal = selectedGoal.toLowerCase().includes("learn");

    if (buildBtn) {
        buildBtn.textContent = isLearningGoal
            ? "Create Learning Roadmap"
            : "Build My Project";
    }

    if (projectIdea) {
        projectIdea.placeholder = isLearningGoal
            ? "What do you want to learn? Example: 'I want to learn Python' (or leave blank for a complete roadmap)"
            : "Describe your project idea... Example: 'AI Resume Analyzer' (or leave blank to get suggested projects)";
    }

    updateChatContext();
}

function updateChatContext() {
    if (!chatContext) return;
    const parts = [];
    if (selectedPath) parts.push(selectedPath);
    if (selectedLevel) parts.push(selectedLevel);
    if (selectedDomain) parts.push(selectedDomain);
    if (selectedTechnology && selectedTechnology !== selectedDomain) parts.push(selectedTechnology);
    if (selectedGoal) parts.push(selectedGoal);

    if (parts.length > 0) {
        chatContext.textContent = `Current context: ${parts.join(" → ")}`;
    } else {
        chatContext.textContent = "Choose your path, domain, goal, and level, then ask a question.";
    }
}

async function apiRequest(path, options) {
    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, options);
    } catch (error) {
        throw new Error(`Unable to connect to BuildReady at ${API_BASE_URL}. Check that the backend is running.`);
    }

    let data = {};
    try {
        data = await response.json();
    } catch (error) {
        if (response.ok) {
            throw new Error("BuildReady returned an invalid response. Please try again.");
        }
    }

    if (!response.ok) {
        const detail = typeof data.detail === "string"
            ? data.detail
            : "The request could not be completed. Please try again.";
        throw new Error(detail);
    }
    return data;
}

// -----------------------------
// Path Selection
// -----------------------------
pathCards.forEach(function (card) {
    card.addEventListener("click", function () {
        pathCards.forEach(function (item) {
            item.classList.remove("selected");
        });

        card.classList.add("selected");
        selectedPath = card.dataset.path;

        console.log("Selected path:", selectedPath);

        if (selectedPath === "Other") {
            domainContainer.innerHTML = "";
            otherPathSection.hidden = false;
            selectedDomain = otherPathInput.value.trim();
            showTechnologiesForDomain(selectedDomain);
        } else {
            otherPathSection.hidden = true;
            otherPathInput.value = "";
            showDomainsForPath(selectedPath);
        }

        updateGoalUI();
    });
});

// -----------------------------
// Level Selection
// -----------------------------
levelCards.forEach(function (card) {
    card.addEventListener("click", function () {
        levelCards.forEach(function (item) {
            item.classList.remove("selected");
        });

        card.classList.add("selected");
        selectedLevel = card.dataset.level;

        console.log("Selected level:", selectedLevel);
        updateChatContext();
    });
});

// -----------------------------
// Goal Selection
// -----------------------------
goalCards.forEach(function (card) {
    card.addEventListener("click", function () {
        goalCards.forEach(function (item) {
            item.classList.remove("selected");
        });

        card.classList.add("selected");
        selectedGoal = card.dataset.goal;

        console.log("Selected goal:", selectedGoal);
        updateGoalUI();
    });
});

// -----------------------------
// Render Domains for Selected Path
// -----------------------------
function showDomainsForPath(path) {
    domainContainer.innerHTML = "";
    selectedDomain = "";
    technologyContainer.innerHTML = '<p class="selector-hint">Choose a domain first to see relevant technologies.</p>';
    selectedTechnology = "";

    const domains = pathDomains[path];
    if (!domains) return;

    domains.forEach(function (domain) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "domain-card";
        button.dataset.domain = domain;
        button.textContent = domain;

        button.addEventListener("click", function () {
            const allDomainCards = domainContainer.querySelectorAll(".domain-card");
            allDomainCards.forEach(function (item) {
                item.classList.remove("selected");
            });

            button.classList.add("selected");
            selectedDomain = domain;
            showTechnologiesForDomain(domain);
            console.log("Selected domain:", selectedDomain);
            updateChatContext();
        });

        domainContainer.appendChild(button);
    });
}

function showTechnologiesForDomain(domain) {
    technologyContainer.innerHTML = "";
    selectedTechnology = "";
    if (!domain) {
        technologyContainer.innerHTML = '<p class="selector-hint">Choose a domain first to see relevant technologies.</p>';
        return;
    }

    const options = technologyOptionsByDomain[domain] || [domain];
    options.forEach(function (technology, index) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "domain-card";
        button.dataset.technology = technology;
        button.textContent = technology;
        if (index === 0) {
            button.classList.add("selected");
            selectedTechnology = technology;
        }
        button.addEventListener("click", function () {
            technologyContainer.querySelectorAll(".domain-card").forEach(item => item.classList.remove("selected"));
            button.classList.add("selected");
            selectedTechnology = technology;
            updateChatContext();
        });
        technologyContainer.appendChild(button);
    });
    updateChatContext();
}

otherPathInput.addEventListener("input", function () {
    selectedDomain = otherPathInput.value.trim();
    showTechnologiesForDomain(selectedDomain);
    updateChatContext();
});

// -----------------------------
// Generate Plan / Roadmap
// -----------------------------
buildBtn.addEventListener("click", async function () {
    // Validations
    if (!selectedPath) {
        alert("Please choose an Engineering Path first.");
        return;
    }

    if (selectedPath === "Other") {
        selectedDomain = otherPathInput.value.trim();
        if (!selectedDomain) {
            alert("Please specify your custom field or topic in the text box.");
            otherPathInput.focus();
            return;
        }
    } else if (!selectedDomain) {
        alert("Please choose a Domain / Topic for " + selectedPath + ".");
        return;
    }

    if (!selectedLevel) {
        alert("Please choose your Level (Beginner, Intermediate, or Advanced).");
        return;
    }

    if (!selectedGoal) {
        alert("Please select what you want to do (Learn the Domain or Build a Project).");
        return;
    }

    let idea = projectIdea.value.trim();
    const isLearning = selectedGoal.toLowerCase().includes("learn");

    // Helpful defaults if user didn't enter custom text
    if (!idea) {
        if (isLearning) {
            idea = `I want to learn ${selectedDomain}.`;
        } else {
            idea = `Suggest a realistic and practical ${selectedDomain} project for ${selectedLevel} level.`;
        }
    }

    // Display loading message
    const actionName = isLearning ? "learning roadmap" : "project plan";
    resultDiv.innerHTML = `
        <div class="loading-box">
            🤖 BuildReady-AI is generating your personalized ${actionName}...
        </div>
    `;

    buildBtn.disabled = true;
    const originalBtnText = buildBtn.textContent;
    buildBtn.textContent = "⏳ Generating...";

    try {
        const data = await apiRequest("/generate-plan", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                idea: idea,
                path: selectedPath,
                level: selectedLevel,
                domain: selectedDomain,
                technology: selectedTechnology,
                goal: selectedGoal
            })
        });

        currentPlan = data.ai_plan;
        currentPlanIdea = idea;
        assessmentsByTask = {};
        assessmentHistory = {};
        if (currentPlan && Array.isArray(currentPlan.tasks)) {
            currentPlan.tasks.forEach(function (task, index) {
                task.status = index === 0 ? "IN_PROGRESS" : "NOT_STARTED";
            });
            currentTaskId = currentPlan.tasks.length ? currentPlan.tasks[0].id : null;
        }
        displayPlan(currentPlan, idea);
        saveCurrentPlan();

    } catch (error) {
        console.error("ERROR:", error);
        resultDiv.innerHTML = `
            <div class="error-box">
                <h3>⚠️ Service Notice</h3>
                <p>${escapeHtml(error.message || "The request could not be completed. Please try again.")}</p>
            </div>
        `;
    } finally {
        buildBtn.disabled = false;
        buildBtn.textContent = originalBtnText;
    }
});

// -----------------------------
// Display Plan & Roadmap
// -----------------------------
function displayPlan(plan, customIdea) {
    plan = escapePlanStrings(plan);
    const isLearning = selectedGoal.toLowerCase().includes("learn");

    const planTitle = isLearning
        ? "Your Personalized Roadmap"
        : "Your Project Roadmap";
    const goalTitle = (customIdea || projectIdea.value || "")
        .replace(/^I want to (?:learn|build)\s+/i, "")
        .replace(/^(?:learn|build|create)\s+(?:a|an)\s+/i, "")
        .replace(/[.!?]+$/, "")
        .trim();
    const dashboardTitle = document.getElementById("dashboardTitle");
    const dashboardSubtitle = document.getElementById("dashboardSubtitle");
    const dashboardLevel = document.getElementById("dashboardLevel");
    if (dashboardTitle) {
        const topicTitle = selectedDomain || goalTitle || plan.tasks?.[0]?.title || "Your Path";
        dashboardTitle.textContent = `${topicTitle} — ${selectedPath || "BuildReady"}`;
    }
    if (dashboardSubtitle) {
        dashboardSubtitle.textContent = isLearning
            ? `Learn ${selectedDomain || goalTitle || "your domain"} from the ground up with a personalized sequence of lessons, practice, and quizzes.`
            : `Build ${customIdea || projectIdea.value || `a ${selectedDomain || "project"}`} with the skills and milestones tailored to your path.`;
    }
    if (dashboardLevel) {
        dashboardLevel.textContent = selectedLevel ? `${selectedLevel} Level` : "Select a level";
    }

    const taskTitle = isLearning
        ? "✅ Learning Stages & Tasks"
        : "✅ Build Tasks & Milestones";

    const displayGoal = escapeHtml(customIdea || projectIdea.value || (isLearning ? `Master ${selectedDomain}` : `${selectedDomain} Project`));
    const allTasksVerified = Array.isArray(plan.tasks)
        && plan.tasks.length > 0
        && plan.tasks.every(task => task.status === "VERIFIED");
    const completionHtml = allTasksVerified
        ? `
            <section class="roadmap-complete" role="status" aria-live="polite">
                <span class="roadmap-complete-icon" aria-hidden="true">✓</span>
                <div>
                    <h3>Roadmap complete!</h3>
                    <p>You passed every task assessment. Your ${isLearning ? "learning goal" : "project plan"} is ready to take forward.</p>
                </div>
            </section>
        `
        : "";

    // Badges strip
    const badgesHtml = `
        <div class="badge-row">
            <span class="badge badge-primary">Path: ${escapeHtml(selectedPath)}</span>
            <span class="badge badge-primary">Domain: ${escapeHtml(selectedDomain)}</span>
            <span class="badge badge-primary">Technology: ${escapeHtml(selectedTechnology || selectedDomain)}</span>
            <span class="badge badge-success">Level: ${escapeHtml(selectedLevel)}</span>
            ${plan.difficulty ? `<span class="badge badge-warning">Difficulty: ${plan.difficulty}</span>` : ""}
            ${plan.estimated_time ? `<span class="badge">Est. Time: ${plan.estimated_time}</span>` : ""}
        </div>
    `;

    // Prerequisites
    let prerequisitesHtml = "";
    if (plan.prerequisites && plan.prerequisites.length > 0) {
        prerequisitesHtml = `
            <div class="plan-section">
                <h3>📋 Prerequisites</h3>
                <ul>
                    ${plan.prerequisites.map(p => `<li>${p}</li>`).join("")}
                </ul>
            </div>
        `;
    }

    // Learning Order Timeline / Sequence
    let learningOrderHtml = "";
    if (plan.learning_order && plan.learning_order.length > 0) {
        learningOrderHtml = `
            <div class="plan-section">
                <h3>🧭 Suggested Learning Order</h3>
                <div class="learning-order-chain">
                    ${plan.learning_order.map((step, idx) => `
                        <span class="learning-step-badge">${idx + 1}. ${step}</span>
                        ${idx < plan.learning_order.length - 1 ? '<span class="learning-arrow">→</span>' : ''}
                    `).join("")}
                </div>
            </div>
        `;
    }

    // Skills Required Grid
    let skillsHtml = "";
    if (plan.skills_required && plan.skills_required.length > 0) {
        skillsHtml = `
            <div class="plan-section">
                <h3>🛠️ Required Skills & Tools</h3>
                <div class="cards-grid">
                    ${plan.skills_required.map(skill => `
                        <div class="skill-card">
                            <strong>${skill.skill}</strong>
                            <p>${skill.why}</p>
                            <small>Priority: ${skill.priority}</small>
                        </div>
                    `).join("")}
                </div>
            </div>
        `;
    }

    // Learning Resources Grid
    let resourcesHtml = "";
    if (plan.learning_resources && plan.learning_resources.length > 0) {
        resourcesHtml = `
            <div class="plan-section">
                <h3>📖 Recommended Free Resources</h3>
                <div class="cards-grid">
                    ${plan.learning_resources.map(res => `
                        <div class="resource-card">
                            <strong>${safeResourceUrl(res.url)
                                ? `<a href="${res.url}" target="_blank" rel="noopener noreferrer">${res.resource_name}</a>`
                                : res.resource_name}</strong>
                            <p>Topic: ${res.topic}</p>
                            <small>${res.resource_type}</small>
                        </div>
                    `).join("")}
                </div>
            </div>
        `;
    }

    // Recommended Projects
    let projectsHtml = "";
    if (plan.recommended_projects && plan.recommended_projects.length > 0) {
        projectsHtml = `
            <div class="plan-section">
                <h3>💡 Progressive Project Ideas</h3>
                <div class="cards-grid">
                    ${plan.recommended_projects.map(proj => `
                        <div class="project-idea-card">
                            <p><strong>${proj}</strong></p>
                        </div>
                    `).join("")}
                </div>
            </div>
        `;
    }

    // Next Steps
    let nextStepsHtml = "";
    if (plan.next_steps && plan.next_steps.length > 0) {
        nextStepsHtml = `
            <div class="plan-section">
                <h3>🎯 Immediate Next Steps</h3>
                <ol>
                    ${plan.next_steps.map(step => `<li>${step}</li>`).join("")}
                </ol>
            </div>
        `;
    }

    resultDiv.innerHTML = `
        <div class="plan-wrapper">
            <div class="plan-header">
                <h2>${planTitle}</h2>
                ${badgesHtml}
                <p><strong>Goal / Topic:</strong> ${displayGoal}</p>
                ${completionHtml}
            </div>

            ${prerequisitesHtml}

            <!-- Overview -->
            <div class="plan-section">
                <h3>🧠 Overview</h3>
                <p>${plan.project_overview || ""}</p>
            </div>

            <!-- Problem & Target Users (if applicable) -->
            ${plan.problem ? `
                <div class="plan-section">
                    <h3>🎯 Target Problem</h3>
                    <p>${plan.problem}</p>
                    ${plan.target_users && plan.target_users.length > 0 ? `
                        <p><strong>Target Users:</strong> ${plan.target_users.join(", ")}</p>
                    ` : ""}
                </div>
            ` : ""}

            ${learningOrderHtml}
            ${skillsHtml}

            <!-- Tasks / Roadmap -->
            <div class="plan-section">
                <h3>${taskTitle}</h3>
                <p>Complete the task learning work, then pass its assessment to verify it and unlock the next task.</p>
                <div id="taskList">
                    ${(plan.tasks || []).map((task, index) => renderTaskCard(task, index)).join("")}
                </div>
            </div>

            <!-- Tech Stack -->
            ${plan.tech_stack && plan.tech_stack.length > 0 ? `
                <div class="plan-section">
                    <h3>💻 Recommended Tools & Stack</h3>
                    <ul>
                        ${plan.tech_stack.map(tech => `<li>${tech}</li>`).join("")}
                    </ul>
                </div>
            ` : ""}

            ${projectsHtml}
            ${resourcesHtml}

            <!-- MVP Plan -->
            ${plan.mvp_plan && plan.mvp_plan.length > 0 ? `
                <div class="plan-section">
                    <h3>🚀 Core MVP Milestones</h3>
                    <ol>
                        ${plan.mvp_plan.map(step => `<li>${step}</li>`).join("")}
                    </ol>
                </div>
            ` : ""}

            <!-- Innovation Ideas -->
            ${plan.innovation_ideas && plan.innovation_ideas.length > 0 ? `
                <div class="plan-section">
                    <h3>💡 Standout / Innovation Ideas</h3>
                    <ul>
                        ${plan.innovation_ideas.map(idea => `<li>${idea}</li>`).join("")}
                    </ul>
                </div>
            ` : ""}

            <!-- Deployment Plan -->
            ${plan.deployment_plan && plan.deployment_plan.length > 0 ? `
                <div class="plan-section">
                    <h3>🌐 Deployment & Real-World Demo</h3>
                    <ol>
                        ${plan.deployment_plan.map(step => `<li>${step}</li>`).join("")}
                    </ol>
                </div>
            ` : ""}

            ${nextStepsHtml}
        </div>
    `;

    updateProgress();
}

function escapePlanStrings(value) {
    if (typeof value === "string") return escapeHtml(value);
    if (Array.isArray(value)) return value.map(escapePlanStrings);
    if (value && typeof value === "object") {
        const escaped = {};
        Object.keys(value).forEach(function (key) {
            escaped[key] = escapePlanStrings(value[key]);
        });
        return escaped;
    }
    return value;
}

function getStatusCounts() {
    const counts = { NOT_STARTED: 0, IN_PROGRESS: 0, NEEDS_PRACTICE: 0, VERIFIED: 0 };
    (currentPlan?.tasks || []).forEach(function (task) {
        const status = TASK_STATUSES.includes(task.status) ? task.status : "NOT_STARTED";
        counts[status]++;
    });
    return counts;
}

function getActiveTask() {
    return (currentPlan?.tasks || []).find(task => task.status !== "VERIFIED") || null;
}

function restoreTaskStatuses(savedStatuses) {
    const savedById = new Map(
        Array.isArray(savedStatuses)
            ? savedStatuses.map(task => [String(task.id), task.status])
            : []
    );
    const tasks = currentPlan.tasks;

    tasks.forEach(function (task) {
        const status = savedById.get(String(task.id)) || task.status;
        task.status = TASK_STATUSES.includes(status) ? status : "NOT_STARTED";

        if (task.status === "VERIFIED") {
            const history = assessmentHistory[String(task.id)] || [];
            if (!Array.isArray(history) || !history.some(result => result.status === "VERIFIED")) {
                task.status = "NOT_STARTED";
            }
        }
    });

    const activeIndex = tasks.findIndex(task => task.status !== "VERIFIED");
    if (activeIndex === -1) return;

    tasks.forEach(function (task, index) {
        if (index < activeIndex) return;
        if (index === activeIndex) {
            task.status = task.status === "NEEDS_PRACTICE" ? "NEEDS_PRACTICE" : "IN_PROGRESS";
        } else {
            task.status = "NOT_STARTED";
        }
    });
}

function renderTaskCard(task, index) {
    const status = TASK_STATUSES.includes(task.status) ? task.status : "NOT_STARTED";
    const canTakeAssessment = status === "IN_PROGRESS" || status === "NEEDS_PRACTICE";
    const isActive = String(task.id) === String(currentTaskId) && canTakeAssessment;
    const hasAssessmentResult = (assessmentHistory[String(task.id)] || []).length > 0;
    const latestResult = hasAssessmentResult
        ? assessmentHistory[String(task.id)][assessmentHistory[String(task.id)].length - 1]
        : null;
    const assessment = assessmentsByTask[String(task.id)];
    const statusLabels = {
        VERIFIED: "Completed",
        IN_PROGRESS: "In Progress",
        NEEDS_PRACTICE: "Needs Practice",
        NOT_STARTED: "Not Started"
    };
    const statusLabel = statusLabels[status];
    const resources = Array.isArray(task.resources) ? task.resources : [];
    const keyConcepts = Array.isArray(task.key_concepts) ? task.key_concepts : [];
    const syntaxRules = Array.isArray(task.syntax_rules) ? task.syntax_rules : [];
    const exampleExplanation = Array.isArray(task.example_explanation) ? task.example_explanation : [];
    const commonMistakes = Array.isArray(task.common_mistakes) ? task.common_mistakes : [];
    const lessonPrerequisites = Array.isArray(task.lesson_prerequisites) ? task.lesson_prerequisites : [];
    const additionalExamples = Array.isArray(task.additional_examples) ? task.additional_examples : [];
    const mistakeCorrections = Array.isArray(task.mistake_corrections) ? task.mistake_corrections : [];
    const missingLesson = "This saved roadmap does not include task-specific lesson content. Generate a new roadmap to get the complete learning sequence.";
    const renderExample = function (title, example, explanations) {
        const exampleLines = example && typeof example === "object" && Array.isArray(example.lines)
            ? example.lines
            : null;
        const exampleCode = exampleLines
            ? exampleLines.map(line => line.content || "").join("\n")
            : example;
        const lineExplanations = exampleLines
            ? exampleLines.map(line => line.explanation || "")
            : explanations;
        return `
            <div class="lesson-example-card">
                <h6>${title}</h6>
                <pre class="lesson-example"><code>${exampleCode || missingLesson}</code></pre>
                ${Array.isArray(lineExplanations) && lineExplanations.length
                    ? `<ol class="lesson-line-explanations">${lineExplanations.map(line => `<li>${line}</li>`).join("")}</ol>`
                    : ""}
            </div>
        `;
    };
    const lessonHtml = `
        <section class="task-learning" aria-label="Learn this task first">
            <h5>📚 Learn This First</h5>
            <div class="lesson-block">
                <h6>1. Concept introduction</h6>
                <p>${task.concept_introduction || task.simple_explanation || missingLesson}</p>
                <h6>What does it mean?</h6>
                <p>${task.simple_explanation || missingLesson}</p>
                <h6>Why does it matter?</h6>
                <p>${task.why_learn || missingLesson}</p>
                <h6>What should you know first?</h6>
                ${lessonPrerequisites.length
                    ? `<ul>${lessonPrerequisites.map(item => `<li>${item}</li>`).join("")}</ul>`
                    : `<p>${missingLesson}</p>`}
                <h6>Real-world analogy</h6>
                <p>${task.real_world_analogy || missingLesson}</p>
                <h6>Detailed explanation</h6>
                <p>${task.detailed_explanation || missingLesson}</p>
                <h6>Key concepts</h6>
                ${keyConcepts.length ? `<ul>${keyConcepts.map(item => `<li>${item}</li>`).join("")}</ul>` : `<p>${missingLesson}</p>`}
                <h6>Rules / syntax</h6>
                ${syntaxRules.length ? `<ul>${syntaxRules.map(item => `<li>${item}</li>`).join("")}</ul>` : `<p>${missingLesson}</p>`}
                <h6>2. Examples with line-by-line explanations</h6>
                ${renderExample("Example 1", task.small_example, exampleExplanation)}
                ${additionalExamples.map((example, exampleIndex) => renderExample(
                    example.title || `Example ${exampleIndex + 2}`,
                    example
                )).join("")}
                <h6>Common mistakes and corrections</h6>
                ${mistakeCorrections.length
                    ? `<ul class="lesson-corrections">${mistakeCorrections.map(item => `<li><strong>Mistake:</strong> ${item.mistake}<br><strong>Correction:</strong> ${item.correction}</li>`).join("")}</ul>`
                    : commonMistakes.length
                        ? `<ul>${commonMistakes.map(item => `<li>${item}</li>`).join("")}</ul>`
                        : `<p>${missingLesson}</p>`}
                <h6>After this lesson, you can</h6>
                <p>${task.learning_outcome || missingLesson}</p>
            </div>
        </section>
    `;
    const practiceHtml = `
        <section class="task-practice" aria-label="Practice this task">
            <h5>3. 🛠️ Practice and apply</h5>
            <div class="practice-level">
                <h6>Beginner practice — guided</h6>
                <p>${task.beginner_practice || task.practical_exercise || missingLesson}</p>
            </div>
            <div class="practice-level">
                <h6>Intermediate practice — combine ideas</h6>
                <p>${task.intermediate_practice || missingLesson}</p>
            </div>
            <div class="practice-level">
                <h6>Assignment</h6>
                <p>${task.assignment || task.practical_exercise || missingLesson}</p>
            </div>
            <div class="practice-level">
                <h6>Real-world / project application</h6>
                <p>${task.real_world_application || task.real_world_example || missingLesson}</p>
            </div>
            <div class="practice-level practice-challenge">
                <h6>Mini challenge</h6>
                <p>${task.mini_challenge || missingLesson}</p>
            </div>
        </section>
    `;
    const detailsHtml = `
        ${task.verification_focus ? `<p><strong>Assessment focus:</strong> ${task.verification_focus}</p>` : ""}
        ${task.estimated_difficulty ? `<p><strong>Difficulty:</strong> ${task.estimated_difficulty}</p>` : ""}
        ${resources.length ? `<p><strong>Resources:</strong> ${resources.map(renderTaskResource).join(" · ")}</p>` : ""}
    `;

    let actionHtml = "";
    if (isActive) {
        if (assessment && assessment.readyForSubmission && Array.isArray(assessment.questions)) {
            actionHtml = renderAssessmentForm(task, assessment);
        } else {
            const buttonText = status === "NEEDS_PRACTICE"
                ? "🎯 Retake Quiz"
                : "🎯 Take Quiz";
            actionHtml = `<button type="button" class="assessment-button" data-action="take-assessment" data-task-id="${task.id}">${buttonText}</button>`;
        }
    } else if (status === "NOT_STARTED" || status === "IN_PROGRESS") {
        const lockMessage = status === "NOT_STARTED"
            ? "Complete and verify the previous task to unlock this assessment."
            : "Only the current task can be assessed. Complete earlier tasks to continue.";
        actionHtml = `<p class="task-locked">${lockMessage}</p>`;
    }

    return `
        <article class="task-card status-border-${status.toLowerCase()}" id="taskCard_${task.id}">
            <div class="task-heading">
                <h4>${index + 1}. ${task.title}</h4>
                <span class="status-badge status-${status.toLowerCase()}">${statusLabel}</span>
            </div>
            <p>${task.description}</p>
            ${lessonHtml}
            ${practiceHtml}
            ${actionHtml}
            ${latestResult ? renderAssessmentResult(latestResult) : ""}
            ${detailsHtml}
        </article>
    `;
}

function getTaskLessonContext(task) {
    return {
        concept_introduction: task.concept_introduction || "",
        lesson_prerequisites: task.lesson_prerequisites || [],
        real_world_analogy: task.real_world_analogy || "",
        detailed_explanation: task.detailed_explanation || "",
        real_world_example: task.real_world_example || "",
        example_explanation: task.example_explanation || [],
        additional_examples: task.additional_examples || [],
        mistake_corrections: task.mistake_corrections || [],
        beginner_practice: task.beginner_practice || "",
        intermediate_practice: task.intermediate_practice || "",
        assignment: task.assignment || "",
        real_world_application: task.real_world_application || "",
        mini_challenge: task.mini_challenge || ""
    };
}

function renderAssessmentForm(task, assessment) {
    const questionsHtml = assessment.questions.map(function (question, index) {
        const options = Array.isArray(question.options)
            ? question.options
            : Array.isArray(question.choices) ? question.choices : [];
        const answerControl = options.length
            ? `<div class="assessment-options">${options.map(function (option) {
                const optionText = typeof option === "string" ? option : option.text || option.label || option.value || "";
                return `<label><input type="radio" name="answer-${question.id}" value="${escapeHtml(optionText)}" required> ${escapeHtml(optionText)}</label>`;
            }).join("")}</div>`
            : `<textarea name="answer-${question.id}" rows="3" required placeholder="Write your answer"></textarea>`;

        return `
            <fieldset class="assessment-question">
                <legend>${index + 1}. ${escapeHtml(question.question)}</legend>
                <small>${escapeHtml(question.question_type || "short answer")}</small>
                ${question.hint ? `<p class="assessment-hint">Hint: ${escapeHtml(question.hint)}</p>` : ""}
                ${answerControl}
            </fieldset>
        `;
    }).join("");

    return `
        <section class="assessment-panel" aria-label="Task assessment">
            <h5>🎯 Quiz: ${escapeHtml(assessment.topic_title || task.title)}</h5>
            <p>${escapeHtml(assessment.assessment_focus || "")}</p>
            <p><strong>Passing criteria:</strong> ${escapeHtml(assessment.passing_criteria || "Demonstrate practical understanding of the task.")}</p>
            <form class="assessment-form" data-task-id="${task.id}">
                ${questionsHtml}
                <button type="button" class="assessment-button" data-action="submit-assessment" data-task-id="${task.id}">Submit Quiz</button>
            </form>
        </section>
    `;
}

function renderAssessmentResult(result) {
    const questionResults = Array.isArray(result.question_results) ? result.question_results : [];
    const correctCount = questionResults.filter(item => item.correct).length;
    const questionsHtml = questionResults.map(function (item, index) {
        const correct = Boolean(item.correct);
        return `
            <div class="question-result ${correct ? "answer-correct" : "answer-incorrect"}">
                <strong>Question ${index + 1}: ${correct ? "Correct" : "Needs improvement"}</strong>
                <p>${escapeHtml(item.feedback || "")}</p>
                <small>${escapeHtml(item.explanation || "")}</small>
            </div>
        `;
    }).join("");

    return `
        <section class="assessment-result">
            <h5>Latest Assessment: ${Number(result.score) || 0}/100 (${correctCount}/${questionResults.length} correct) — ${escapeHtml(result.status || "NEEDS_PRACTICE")}</h5>
            <p>${escapeHtml(result.overall_feedback || "")}</p>
            ${result.weak_areas?.length ? `<p><strong>Needs improvement:</strong> ${result.weak_areas.map(escapeHtml).join(", ")}</p>` : ""}
            ${result.targeted_practice ? `<p><strong>Practice guidance:</strong> ${escapeHtml(result.targeted_practice)}</p>` : ""}
            ${result.next_step ? `<p><strong>Next step:</strong> ${escapeHtml(result.next_step)}</p>` : ""}
            ${questionsHtml}
        </section>
    `;
}

async function generateAssessment(taskId) {
    const task = currentPlan?.tasks.find(item => String(item.id) === String(taskId));
    if (
        !task
        || String(currentTaskId) !== String(task.id)
        || !["IN_PROGRESS", "NEEDS_PRACTICE"].includes(task.status)
    ) return;

    try {
        const assessment = await apiRequest("/generate-assessment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topic_id: task.id,
                topic_title: task.title,
                topic_description: task.description,
                verification_focus: task.verification_focus || "",
                learning_objective: task.learning_objective || "",
                ...getTaskLessonContext(task),
                key_concepts: task.key_concepts || [],
                simple_explanation: task.simple_explanation || "",
                small_example: task.small_example || "",
                common_mistakes: task.common_mistakes || [],
                practical_exercise: task.practical_exercise || "",
                path: selectedPath,
                domain: selectedDomain,
                technology: selectedTechnology,
                level: selectedLevel,
                goal: selectedGoal,
                idea: currentPlanIdea,
                related_skills: (currentPlan?.skills_required || []).map(skill => skill.skill)
            })
        });
        assessment.questions = normalizeAssessmentQuestions(assessment);
        if (assessment.questions.length < 3 || assessment.questions.length > 5) {
            throw new Error("The generated assessment did not contain 3–5 questions. Please try again.");
        }
        assessment.readyForSubmission = true;
        assessmentsByTask[String(task.id)] = assessment;
        displayPlan(currentPlan, currentPlanIdea);
        saveCurrentPlan();
    } catch (error) {
        displayPlan(currentPlan, currentPlanIdea);
        window.alert(error.message || "Could not generate the assessment. Please try again.");
    }
}

function normalizeAssessmentQuestions(assessment) {
    const questions = Array.isArray(assessment.questions) ? assessment.questions : [];
    const isPlaceholderQuestion = function (text) {
        return /^(?:q(?:uestion)?\s*\d+\s*[:.)-]?\s*)?(?:concept|practical|code|question|multiple choice)$/i.test(text.trim());
    };

    return questions.map(function (question, index) {
        const nestedQuestion = question.question && typeof question.question === "object"
            ? question.question
            : {};
        const candidates = [
            question.question,
            question.question_text,
            question.prompt,
            question.text,
            question.stem,
            question.title,
            nestedQuestion.text,
            nestedQuestion.prompt,
            nestedQuestion.question_text
        ];
        const prompt = candidates.find(function (candidate) {
            return typeof candidate === "string"
                && candidate.trim().length >= 4
                && !isPlaceholderQuestion(candidate);
        });
        if (!prompt) {
            throw new Error(`Assessment question ${index + 1} is missing its question text. Please generate the assessment again.`);
        }
        return {
            ...question,
            id: question.id ?? index + 1,
            question: prompt.trim(),
            options: Array.isArray(question.options)
                ? question.options
                : Array.isArray(question.choices) ? question.choices : []
        };
    });
}

async function submitAssessment(taskId) {
    const task = currentPlan?.tasks.find(item => String(item.id) === String(taskId));
    const assessment = assessmentsByTask[String(taskId)];
    const form = resultDiv.querySelector(`.assessment-form[data-task-id="${taskId}"]`);
    if (
        !task
        || !assessment
        || !form
        || String(currentTaskId) !== String(task.id)
        || !["IN_PROGRESS", "NEEDS_PRACTICE"].includes(task.status)
    ) return;

    const submissions = assessment.questions.map(function (question) {
        const selected = form.querySelector(`input[name="answer-${question.id}"]:checked`);
        const textAnswer = form.querySelector(`textarea[name="answer-${question.id}"]`);
        return {
            question_id: question.id,
            question: question.question,
            user_answer: selected ? selected.value.trim() : (textAnswer?.value || "").trim(),
            options: Array.isArray(question.options)
                ? question.options.map(option => typeof option === "string"
                    ? option
                    : option.text || option.label || option.value || "")
                : []
        };
    });
    if (submissions.some(answer => !answer.user_answer)) {
        window.alert("Please answer every question before submitting.");
        return;
    }

    const submitButton = form.querySelector('[data-action="submit-assessment"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Evaluating...";
    }

    try {
        const evaluation = await apiRequest("/evaluate-assessment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topic_id: task.id,
                topic_title: task.title,
                topic_description: task.description,
                path: selectedPath,
                domain: selectedDomain,
                technology: selectedTechnology,
                level: selectedLevel,
                goal: selectedGoal,
                idea: currentPlanIdea,
                learning_objective: task.learning_objective || "",
                ...getTaskLessonContext(task),
                key_concepts: task.key_concepts || [],
                simple_explanation: task.simple_explanation || "",
                small_example: task.small_example || "",
                common_mistakes: task.common_mistakes || [],
                practical_exercise: task.practical_exercise || "",
                submissions: submissions
            })
        });
        if (!["VERIFIED", "NEEDS_PRACTICE"].includes(evaluation.status)) {
            throw new Error("The evaluator returned an invalid task status. Please retry the assessment.");
        }

        task.status = evaluation.passed === true && Number(evaluation.score) >= 65 && evaluation.status === "VERIFIED"
            ? "VERIFIED"
            : "NEEDS_PRACTICE";
        evaluation.status = task.status;
        evaluation.passed = task.status === "VERIFIED";
        assessment.readyForSubmission = false;
        const history = assessmentHistory[String(task.id)] || [];
        history.push(evaluation);
        assessmentHistory[String(task.id)] = history;

        const taskIndex = currentPlan.tasks.indexOf(task);
        if (task.status === "VERIFIED") {
            const nextTask = currentPlan.tasks.slice(taskIndex + 1).find(item => item.status !== "VERIFIED");
            if (nextTask) {
                nextTask.status = "IN_PROGRESS";
                currentTaskId = nextTask.id;
            } else {
                currentTaskId = null;
            }
        } else {
            currentTaskId = task.id;
        }

        assessmentsByTask[String(task.id)] = null;
        displayPlan(currentPlan, currentPlanIdea);
        saveCurrentPlan();
    } catch (error) {
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = "Submit Answers";
        }
        window.alert(error.message || "Could not evaluate the assessment. Your answers are still available to retry.");
    }
}

resultDiv.addEventListener("click", function (event) {
    const button = event.target.closest("[data-action]");
    if (!button) return;

    if (button.dataset.action === "take-assessment") {
        button.disabled = true;
        button.textContent = "Generating assessment...";
        generateAssessment(button.dataset.taskId);
    } else if (button.dataset.action === "submit-assessment") {
        submitAssessment(button.dataset.taskId);
    }
});

// -----------------------------
// Progress Tracker
// -----------------------------
function updateProgress() {
    if (!currentPlan || !Array.isArray(currentPlan.tasks)) return;
    const counts = getStatusCounts();
    const total = currentPlan.tasks.length;

    if (total === 0) return;

    const progress = Math.round((counts.VERIFIED / total) * 100);

    const progressFill = document.getElementById("progressFill");
    const progressText = document.getElementById("progressText");
    const currentTaskSummary = document.getElementById("currentTaskSummary");
    const progressCircle = document.getElementById("progressCircle");
    const progressNumber = document.getElementById("progressNumber");
    const progressTaskCount = document.getElementById("progressTaskCount");

    if (progressFill) progressFill.style.width = `${progress}%`;
    if (progressText) progressText.textContent = `Overall Progress: ${progress}% (${counts.VERIFIED}/${total} verified)`;
    if (progressTaskCount) {
        progressTaskCount.textContent = `${total} ${total === 1 ? "task" : "tasks"} total`;
    }
    const activeTask = getActiveTask();
    if (currentTaskSummary) {
        currentTaskSummary.textContent = activeTask
            ? `Current task: ${activeTask.title} — ${activeTask.status}`
            : "All required tasks are verified. Your learning/project goal is ready.";
    }
    if (progressCircle) progressCircle.style.background = `conic-gradient(#2563eb ${progress}%, #e2e8f0 0)`;
    if (progressNumber) progressNumber.textContent = `${progress}%`;

    const summary = document.getElementById("progressSummary");
    if (summary) {
        const labels = {
            VERIFIED: "Completed",
            IN_PROGRESS: "In Progress",
            NEEDS_PRACTICE: "Needs Practice",
            NOT_STARTED: "Not Started"
        };
        summary.innerHTML = TASK_STATUSES.map(function (status) {
            return `<span class="status-summary status-${status.toLowerCase()}"><i aria-hidden="true"></i>${labels[status]} <strong>${counts[status]}</strong></span>`;
        }).join("");
    }

    const continueRoadmapButton = document.getElementById("continueRoadmap");
    if (continueRoadmapButton) {
        continueRoadmapButton.addEventListener("click", function () {
            const activeTask = getActiveTask();
            const target = activeTask
                ? document.getElementById(`taskCard_${activeTask.id}`)
                : document.getElementById("taskList");
            if (target) {
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            } else {
                document.getElementById("selectionPanel")?.scrollIntoView({ behavior: "smooth" });
            }
        });
    }

    const askBuildReadyButton = document.getElementById("askBuildReady");
    if (askBuildReadyButton) {
        askBuildReadyButton.addEventListener("click", function () {
            document.getElementById("chatInput")?.focus();
            document.getElementById("chatbot")?.scrollIntoView({ behavior: "smooth", block: "center" });
        });
    }

    saveCurrentPlan();
}

// -----------------------------
// LocalStorage Persistence
// -----------------------------
function saveCurrentPlan() {
    if (!currentPlan) return;

    const counts = getStatusCounts();
    const savedData = {
        version: 2,
        plan: currentPlan,
        idea: currentPlanIdea || projectIdea.value,
        path: selectedPath,
        domain: selectedDomain,
        technology: selectedTechnology,
        goal: selectedGoal,
        level: selectedLevel,
        taskStatuses: currentPlan.tasks.map(task => ({ id: task.id, status: task.status })),
        assessmentsByTask: assessmentsByTask,
        assessmentHistory: assessmentHistory,
        currentTaskId: currentTaskId,
        progress: counts
    };

    localStorage.setItem("buildReadySavedPlan", JSON.stringify(savedData));
    if (clearSavedPlanBtn) clearSavedPlanBtn.hidden = false;
}

function restoreSavedPlan() {
    const savedText = localStorage.getItem("buildReadySavedPlan");
    if (!savedText) return;

    try {
        const savedData = JSON.parse(savedText);
        if (!savedData.plan || !Array.isArray(savedData.plan.tasks)) return;

        currentPlan = savedData.plan;
        currentPlanIdea = savedData.idea || "";
        selectedPath = savedData.path || "";
        selectedDomain = savedData.domain || "";
        const savedTechnology = savedData.technology || savedData.domain || "";
        selectedTechnology = savedTechnology;
        selectedGoal = savedData.goal || "";
        selectedLevel = savedData.level || "";
        assessmentsByTask = savedData.assessmentsByTask && typeof savedData.assessmentsByTask === "object"
            ? savedData.assessmentsByTask
            : {};
        assessmentHistory = savedData.assessmentHistory && typeof savedData.assessmentHistory === "object"
            ? savedData.assessmentHistory
            : {};

        if (projectIdea) projectIdea.value = savedData.idea || "";

        // Highlight matching path
        pathCards.forEach(function (card) {
            if (card.dataset.path === selectedPath) {
                card.classList.add("selected");
            }
        });

        // Show domains or other input
        if (selectedPath === "Other") {
            otherPathSection.hidden = false;
            otherPathInput.value = selectedDomain;
        } else if (selectedPath) {
            showDomainsForPath(selectedPath);
            const domainCards = domainContainer.querySelectorAll(".domain-card");
            domainCards.forEach(function (btn) {
                if (btn.dataset.domain === selectedDomain) {
                    btn.classList.add("selected");
                }
            });
        }
        showTechnologiesForDomain(selectedDomain);
        technologyContainer.querySelectorAll(".domain-card").forEach(function (button) {
            const isSelected = button.dataset.technology === savedTechnology;
            button.classList.toggle("selected", isSelected);
            if (isSelected) selectedTechnology = button.dataset.technology;
        });

        // Highlight level
        levelCards.forEach(function (card) {
            if (card.dataset.level === selectedLevel) {
                card.classList.add("selected");
            }
        });

        // Highlight goal
        goalCards.forEach(function (card) {
            if (card.dataset.goal === selectedGoal) {
                card.classList.add("selected");
            }
        });

        updateGoalUI();
        restoreTaskStatuses(savedData.taskStatuses);
        const activeTask = getActiveTask();
        currentTaskId = activeTask ? activeTask.id : null;
        displayPlan(currentPlan, currentPlanIdea);

        if (clearSavedPlanBtn) clearSavedPlanBtn.hidden = false;

    } catch (e) {
        console.error("Could not restore saved plan:", e);
        resultDiv.textContent = "The saved roadmap could not be restored. Clear the saved plan and generate a new one.";
    }
}

if (clearSavedPlanBtn) {
    clearSavedPlanBtn.addEventListener("click", function () {
        localStorage.removeItem("buildReadySavedPlan");
        currentPlan = null;
        currentPlanIdea = "";
        currentTaskId = null;
        assessmentsByTask = {};
        assessmentHistory = {};
        if (projectIdea) projectIdea.value = "";
        resultDiv.innerHTML = "";
        clearSavedPlanBtn.hidden = true;
    });
}

// -----------------------------
// Ask BuildReady Chatbot
// -----------------------------
function addChatMessage(message, messageType) {
    const messageBox = document.createElement("div");
    messageBox.className = `chat-message ${messageType}`;

    const sender = messageType === "user-message" ? "You" : "BuildReady";
    messageBox.innerHTML = `<strong>${sender}:</strong> ${escapeHtml(message)}`;

    chatMessages.appendChild(messageBox);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function safeResourceUrl(value) {
    return typeof value === "string" && /^https?:\/\/[^\s"'<>]+$/i.test(value.trim())
        ? value.trim()
        : "";
}

function renderTaskResource(resource) {
    const text = String(resource || "");
    const match = text.match(/https?:\/\/[^\s"'<>]+/i);
    if (!match) return text;
    const href = safeResourceUrl(match[0]);
    if (!href) return text;
    return text.replace(
        match[0],
        `<a href="${href}" target="_blank" rel="noopener noreferrer">${match[0]}</a>`
    );
}

async function sendChatMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    if (!selectedPath || !selectedDomain || !selectedGoal || !selectedLevel) {
        addChatMessage(
            "Please choose your path, domain, goal, and level above first so I can tailor my advice to your context!",
            "bot-message"
        );
        return;
    }

    addChatMessage(message, "user-message");
    chatInput.value = "";

    updateChatContext();

    const thinkingBox = document.createElement("div");
    thinkingBox.className = "chat-message bot-message";
    thinkingBox.innerHTML = "<strong>BuildReady:</strong> <em>Thinking...</em>";
    chatMessages.appendChild(thinkingBox);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const data = await apiRequest("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                path: selectedPath,
                domain: selectedDomain,
                technology: selectedTechnology,
                goal: selectedGoal,
                level: selectedLevel,
                idea: currentPlanIdea || (projectIdea ? projectIdea.value.trim() : ""),
                current_topic: getActiveTask()?.title || "",
                topics: (currentPlan?.tasks || []).map(task => ({
                    id: task.id,
                    title: task.title,
                    status: task.status
                })),
                assessment_results: Object.entries(assessmentHistory).flatMap(([topicId, history]) => {
                    const result = history[history.length - 1];
                    return result ? [{
                        topic_id: Number(topicId),
                        score: result.score,
                        status: result.status,
                        overall_feedback: result.overall_feedback,
                        weak_areas: result.weak_areas || []
                    }] : [];
                })
            })
        });

        thinkingBox.remove();
        addChatMessage(data.reply, "bot-message");

    } catch (error) {
        thinkingBox.remove();
        addChatMessage(error.message || "BuildReady could not reply. Please try again.", "bot-message");
    }
}

if (chatSendBtn) {
    chatSendBtn.addEventListener("click", sendChatMessage);
}

if (chatInput) {
    chatInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            sendChatMessage();
        }
    });
}

// Initial restore on page load
restoreSavedPlan();