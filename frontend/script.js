// State variables
let selectedPath = "";
let selectedLevel = "";
let selectedGoal = "";
let selectedDomain = "";
let currentPlan = null;

// DOM Elements
const pathCards = document.querySelectorAll(".path-card");
const levelCards = document.querySelectorAll(".level-card");
const goalCards = document.querySelectorAll(".goal-card");
const domainContainer = document.getElementById("domainContainer");
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
    "AI / ML": [
        "Python",
        "Math & Statistics",
        "Data & Analysis",
        "Machine Learning",
        "Deep Learning",
        "NLP",
        "Computer Vision",
        "Generative AI"
    ],
    "Data Science": [
        "Python",
        "Statistics",
        "SQL",
        "Data Analysis",
        "Data Visualization",
        "Machine Learning",
        "Data Engineering"
    ],
    "Software Development": [
        "Programming Fundamentals",
        "Data Structures & Algorithms",
        "Object-Oriented Programming",
        "Databases",
        "APIs",
        "Backend Development",
        "Software Engineering",
        "Testing"
    ],
    "Web Development": [
        "HTML",
        "CSS",
        "JavaScript",
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
    if (selectedGoal) parts.push(selectedGoal);

    if (parts.length > 0) {
        chatContext.textContent = `Current context: ${parts.join(" → ")}`;
    } else {
        chatContext.textContent = "Choose your path, domain, goal, and level, then ask a question.";
    }
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
            console.log("Selected domain:", selectedDomain);
            updateChatContext();
        });

        domainContainer.appendChild(button);
    });
}

otherPathInput.addEventListener("input", function () {
    selectedDomain = otherPathInput.value.trim();
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
        const response = await fetch("http://127.0.0.1:8000/generate-plan", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                idea: idea,
                path: selectedPath,
                level: selectedLevel,
                domain: selectedDomain,
                goal: selectedGoal
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Backend request failed.");
        }

        currentPlan = data.ai_plan;
        displayPlan(currentPlan, idea);
        saveCurrentPlan();

    } catch (error) {
        console.error("ERROR:", error);

        let errorMessage = error.message;
        if (errorMessage === "Failed to fetch" || error.name === "TypeError") {
            errorMessage = "Unable to connect to BuildReady backend at http://127.0.0.1:8000. Please ensure the backend server is running.";
        }

        resultDiv.innerHTML = `
            <div class="error-box">
                <h3>⚠️ Service Notice</h3>
                <p>${errorMessage}</p>
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
    const isLearning = selectedGoal.toLowerCase().includes("learn");

    const planTitle = isLearning
        ? "📚 Your BuildReady Learning Roadmap"
        : "🚀 Your BuildReady Project Plan";

    const taskTitle = isLearning
        ? "✅ Learning Stages & Tasks"
        : "✅ Build Tasks & Milestones";

    const displayGoal = customIdea || projectIdea.value || (isLearning ? `Master ${selectedDomain}` : `${selectedDomain} Project`);

    // Badges strip
    const badgesHtml = `
        <div class="badge-row">
            <span class="badge badge-primary">Path: ${selectedPath}</span>
            <span class="badge badge-primary">Domain: ${selectedDomain}</span>
            <span class="badge badge-success">Level: ${selectedLevel}</span>
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
                            <strong>${res.resource_name}</strong>
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
            </div>

            <!-- Progress Tracking -->
            <div class="progress-card">
                <div class="progress-info">
                    <h3>📊 Progress Tracker</h3>
                    <div class="progress-bar">
                        <div id="progressFill" class="progress-fill" style="width: 0%"></div>
                    </div>
                    <p id="progressText">0% complete — 0/${(plan.tasks || []).length} tasks completed</p>
                </div>
                <div class="progress-circle" id="progressCircle">
                    <span id="progressNumber">0%</span>
                </div>
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
                <p>Check off tasks as you complete them to track your progress:</p>
                <div id="taskList">
                    ${(plan.tasks || []).map(task => `
                        <div class="task-card" id="taskCard_${task.id}">
                            <label>
                                <input
                                    type="checkbox"
                                    class="task-checkbox"
                                    data-task-id="${task.id}"
                                    onchange="updateProgress()"
                                >
                                <strong>${task.id}. ${task.title}</strong>
                            </label>
                            <p>${task.description}</p>
                        </div>
                    `).join("")}
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

// -----------------------------
// Progress Tracker
// -----------------------------
function updateProgress() {
    const checkboxes = document.querySelectorAll(".task-checkbox");
    const total = checkboxes.length;

    if (total === 0) return;

    let completed = 0;
    checkboxes.forEach(function (box) {
        const taskId = box.dataset.taskId;
        const card = document.getElementById("taskCard_" + taskId);
        if (box.checked) {
            completed++;
            if (card) card.classList.add("completed");
        } else {
            if (card) card.classList.remove("completed");
        }
    });

    const progress = Math.round((completed / total) * 100);

    const progressFill = document.getElementById("progressFill");
    const progressText = document.getElementById("progressText");
    const progressCircle = document.getElementById("progressCircle");
    const progressNumber = document.getElementById("progressNumber");

    if (progressFill) progressFill.style.width = `${progress}%`;
    if (progressText) progressText.textContent = `${progress}% complete — ${completed}/${total} tasks completed`;
    if (progressCircle) progressCircle.style.background = `conic-gradient(#2563eb ${progress}%, #e2e8f0 0)`;
    if (progressNumber) progressNumber.textContent = `${progress}%`;

    saveCurrentPlan();
}

// -----------------------------
// LocalStorage Persistence
// -----------------------------
function saveCurrentPlan() {
    if (!currentPlan) return;

    const completedTaskIds = Array.from(
        document.querySelectorAll(".task-checkbox:checked")
    ).map(function (cb) {
        return cb.dataset.taskId;
    });

    const savedData = {
        plan: currentPlan,
        idea: projectIdea.value,
        path: selectedPath,
        domain: selectedDomain,
        goal: selectedGoal,
        level: selectedLevel,
        completedTaskIds: completedTaskIds
    };

    localStorage.setItem("buildReadySavedPlan", JSON.stringify(savedData));
    if (clearSavedPlanBtn) clearSavedPlanBtn.hidden = false;
}

function restoreSavedPlan() {
    const savedText = localStorage.getItem("buildReadySavedPlan");
    if (!savedText) return;

    try {
        const savedData = JSON.parse(savedText);
        if (!savedData.plan) return;

        currentPlan = savedData.plan;
        selectedPath = savedData.path || "";
        selectedDomain = savedData.domain || "";
        selectedGoal = savedData.goal || "";
        selectedLevel = savedData.level || "";

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
        displayPlan(currentPlan, savedData.idea);

        // Restore checked tasks
        if (savedData.completedTaskIds && Array.isArray(savedData.completedTaskIds)) {
            savedData.completedTaskIds.forEach(function (taskId) {
                const cb = document.querySelector(`.task-checkbox[data-task-id="${taskId}"]`);
                if (cb) cb.checked = true;
            });
            updateProgress();
        }

        if (clearSavedPlanBtn) clearSavedPlanBtn.hidden = false;

    } catch (e) {
        console.error("Could not restore saved plan:", e);
    }
}

if (clearSavedPlanBtn) {
    clearSavedPlanBtn.addEventListener("click", function () {
        localStorage.removeItem("buildReadySavedPlan");
        currentPlan = null;
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
        const response = await fetch("http://127.0.0.1:8000/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                path: selectedPath,
                domain: selectedDomain,
                goal: selectedGoal,
                level: selectedLevel,
                idea: projectIdea ? projectIdea.value.trim() : ""
            })
        });

        const data = await response.json();

        thinkingBox.remove();

        if (!response.ok) {
            throw new Error(data.detail || "BuildReady could not reply.");
        }

        addChatMessage(data.reply, "bot-message");

    } catch (error) {
        thinkingBox.remove();
        let errorMsg = error.message;
        if (errorMsg === "Failed to fetch" || error.name === "TypeError") {
            errorMsg = "Unable to connect to the BuildReady backend at http://127.0.0.1:8000. Please ensure the backend is running.";
        }
        addChatMessage(errorMsg, "bot-message");
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