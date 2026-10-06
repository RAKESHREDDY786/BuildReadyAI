import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import backend.main as api


def selector_curriculum_cases():
    root = Path(__file__).resolve().parents[1]
    script = (root / "frontend" / "script.js").read_text(encoding="utf-8")
    html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    domains_match = re.search(
        r"const pathDomains = (\{.*?\});\s*const technologyOptionsByDomain =",
        script,
        flags=re.DOTALL,
    )
    technologies_match = re.search(
        r"const technologyOptionsByDomain = (\{.*?\});\s*// Update button",
        script,
        flags=re.DOTALL,
    )
    if not domains_match or not technologies_match:
        raise AssertionError("Could not read roadmap selector configuration.")

    path_domains = json.loads(domains_match.group(1))
    technologies = json.loads(technologies_match.group(1))
    selectable_paths = re.findall(
        r'class="path-card"\s+data-path="([^"]+)"',
        html,
    )
    if not selectable_paths or any(
        path != "Other" and path not in path_domains
        for path in selectable_paths
    ):
        raise AssertionError("A selectable path has no configured domains.")
    if set(path_domains) != set(selectable_paths) - {"Other"}:
        raise AssertionError("Path-domain configuration contains an unreachable path.")

    return [
        (path, domain, technology)
        for path in selectable_paths
        if path != "Other"
        for domain in path_domains[path]
        for technology in technologies.get(domain, [domain])
    ]


def plan_payload():
    payload = {
        "project_overview": "A beginner AIML path for the supplied goal.",
        "problem": "",
        "target_users": [],
        "skills_required": [
            {"skill": "Python", "why": "Core implementation language.", "priority": "Core"}
        ],
        "learning_resources": [],
        "tasks": [
            {
                "id": 1,
                "title": "Python fundamentals",
                "description": "Learn variables and basic expressions.",
                "status": "NOT_STARTED",
                "verification_focus": "Use variables and expressions correctly.",
                "learning_objective": "Understand values and variables.",
                "practical_exercise": "Write a short temperature converter.",
                "resources": ["Python tutorial"],
                "estimated_difficulty": "Beginner",
            },
            {
                "id": 2,
                "title": "Python conditions",
                "description": "Make decisions with if and else.",
                "status": "NOT_STARTED",
                "verification_focus": "Select a branch from a condition.",
                "learning_objective": "Understand conditional logic.",
                "practical_exercise": "Write a pass/fail checker.",
                "resources": [],
                "estimated_difficulty": "Beginner",
            },
            {
                "id": 3,
                "title": "Python operators",
                "description": "Use arithmetic and comparison operators.",
                "status": "NOT_STARTED",
                "verification_focus": "Apply operators.",
                "learning_objective": "Understand expressions.",
                "practical_exercise": "Calculate a score.",
                "resources": [],
                "estimated_difficulty": "Beginner",
            },
            {
                "id": 4,
                "title": "Python loops",
                "description": "Repeat work with loops.",
                "status": "NOT_STARTED",
                "verification_focus": "Use loops.",
                "learning_objective": "Understand iteration.",
                "practical_exercise": "Print a sequence.",
                "resources": [],
                "estimated_difficulty": "Beginner",
            },
            {
                "id": 5,
                "title": "Python functions",
                "description": "Create reusable functions.",
                "status": "NOT_STARTED",
                "verification_focus": "Define and call functions.",
                "learning_objective": "Understand function inputs and outputs.",
                "practical_exercise": "Create a calculator function.",
                "resources": [],
                "estimated_difficulty": "Beginner",
            },
            {
                "id": 6,
                "title": "Python collections",
                "description": "Use lists and dictionaries.",
                "status": "NOT_STARTED",
                "verification_focus": "Choose suitable collections.",
                "learning_objective": "Store related data.",
                "practical_exercise": "Create a contact list.",
                "resources": [],
                "estimated_difficulty": "Beginner",
            },
            {
                "id": 7,
                "title": "Python files and exceptions",
                "description": "Read files and handle errors.",
                "status": "NOT_STARTED",
                "verification_focus": "Handle file errors.",
                "learning_objective": "Use file operations safely.",
                "practical_exercise": "Read a text file.",
                "resources": [],
                "estimated_difficulty": "Beginner",
            },
            {
                "id": 8,
                "title": "Python mini project",
                "description": "Apply Python foundations.",
                "status": "NOT_STARTED",
                "verification_focus": "Combine core skills.",
                "learning_objective": "Build a small application.",
                "practical_exercise": "Create a command-line quiz.",
                "resources": [],
                "estimated_difficulty": "Beginner",
            },
        ],
        "tech_stack": ["Python"],
        "mvp_plan": [],
        "innovation_ideas": [],
        "deployment_plan": [],
        "prerequisites": [],
        "learning_order": ["Python fundamentals", "Python conditions"],
        "difficulty": "Beginner",
        "estimated_time": "2 weeks",
        "recommended_projects": [],
        "next_steps": ["Practice variables."],
    }
    lessons = [
        {
            "why_learn": "Variables let a program reuse and update inputs such as a student's name or score.",
            "key_concepts": ["assignment", "strings", "integers", "print()"],
            "simple_explanation": "A variable is a named reference to a value; Python chooses its type from the assigned value.",
            "syntax_rules": ["Assign with name = value", "Put string values in quotes"],
            "small_example": 'name = "Ada"\nprint(name)',
            "example_explanation": [
                'name = "Ada" stores the text in a variable.',
                "print(name) displays the stored text.",
            ],
            "real_world_example": "An AIML script stores a dataset path in a variable so it can reuse that location.",
            "common_mistakes": ["Leaving quotes off text values", "Using a variable before assigning it"],
            "learning_outcome": "Create named values and display them with print().",
        },
        {
            "why_learn": "Conditions let a program choose a response based on a user's score.",
            "key_concepts": ["if", "else", "Boolean conditions", "indentation"],
            "simple_explanation": "A condition is a true-or-false test that decides which indented block runs.",
            "syntax_rules": ["End if/else headers with a colon", "Indent each branch consistently"],
            "small_example": "score = 80\nif score >= 50:\n    print('pass')\nelse:\n    print('retry')",
            "example_explanation": [
                "score = 80 stores the score to test.",
                "The if line checks whether score is at least 50.",
                "The indented print runs when the condition is true.",
                "The else branch handles scores below 50.",
            ],
            "real_world_example": "A resume analyzer can use a condition to flag a resume below a required keyword-match score.",
            "common_mistakes": ["Using = instead of == for equality", "Forgetting the colon or indentation"],
            "learning_outcome": "Write an if/else statement that handles both outcomes.",
        },
        {
            "why_learn": "Operators calculate results and compare values before an AIML program makes a decision.",
            "key_concepts": ["arithmetic", "comparison", "precedence", "expressions"],
            "simple_explanation": "Operators combine values into a calculated result or a true-or-false comparison.",
            "syntax_rules": ["Use +, -, *, / for arithmetic", "Use ==, <, > for comparisons"],
            "small_example": "score = 8 + 2\nprint(score > 5)",
            "example_explanation": [
                "8 + 2 evaluates to 10 and is assigned to score.",
                "score > 5 compares the value with 5 and print displays True.",
            ],
            "real_world_example": "A model evaluation script can compare accuracy with a minimum target.",
            "common_mistakes": ["Confusing = with ==", "Overlooking operator precedence"],
            "learning_outcome": "Calculate a value and compare it using the appropriate operator.",
        },
        {
            "why_learn": "Loops process every item in a dataset without writing the same operation repeatedly.",
            "key_concepts": ["for", "range()", "iteration", "loop body"],
            "simple_explanation": "A loop repeats an indented block for each item or each number in a sequence.",
            "syntax_rules": ["Write for item in sequence:", "Indent statements inside the loop"],
            "small_example": "for score in [7, 9]:\n    print(score)",
            "example_explanation": [
                "The loop takes each score from the list in order.",
                "The indented print runs once for each score.",
            ],
            "real_world_example": "An AIML data-cleaning script can loop over rows to check each label.",
            "common_mistakes": ["Forgetting indentation", "Accidentally looping over the wrong collection"],
            "learning_outcome": "Use a for loop to process each item in a short collection.",
        },
        {
            "why_learn": "Functions package repeated calculations so project code stays reusable and testable.",
            "key_concepts": ["def", "parameters", "return", "function call"],
            "simple_explanation": "A function is a named block that can accept inputs and return a result.",
            "syntax_rules": ["Start a definition with def name(parameters):", "Use return to send back a value"],
            "small_example": "def double(value):\n    return value * 2\nprint(double(3))",
            "example_explanation": [
                "def double(value) creates a function with one input.",
                "return value * 2 sends the calculated result back.",
                "double(3) calls the function and print displays 6.",
            ],
            "real_world_example": "A resume analyzer can use a function to normalize text for every uploaded resume.",
            "common_mistakes": ["Forgetting to call the function", "Printing instead of returning a result"],
            "learning_outcome": "Define a small function that accepts an input and returns a result.",
        },
        {
            "why_learn": "Collections keep related records together for searching and analysis.",
            "key_concepts": ["lists", "dictionaries", "indexing", "keys"],
            "simple_explanation": "A list stores ordered values; a dictionary stores values under named keys.",
            "syntax_rules": ["Lists use square brackets", "Dictionaries use key: value pairs in braces"],
            "small_example": "skills = ['Python', 'NLP']\nprofile = {'name': 'Ada'}",
            "example_explanation": [
                "skills stores two ordered skill strings in a list.",
                "profile stores the name value under the 'name' key.",
            ],
            "real_world_example": "A resume analyzer can store extracted skills in a list and candidate details in a dictionary.",
            "common_mistakes": ["Using an index to access a dictionary", "Misspelling dictionary keys"],
            "learning_outcome": "Choose a list or dictionary and retrieve a stored value.",
        },
        {
            "why_learn": "Files let an application load data, while exception handling makes failures understandable.",
            "key_concepts": ["open()", "with", "read()", "try/except"],
            "simple_explanation": "File operations read or write saved data; exceptions let code handle errors safely.",
            "syntax_rules": ["Use with open(path) to close files safely", "Handle expected errors in except blocks"],
            "small_example": "try:\n    with open('notes.txt') as file:\n        text = file.read()\nexcept FileNotFoundError:\n    text = ''",
            "example_explanation": [
                "try begins code that may fail.",
                "with opens the file and closes it when the block ends.",
                "read() loads the text from the file.",
                "except handles a missing file by using empty text.",
            ],
            "real_world_example": "A resume analyzer can read an uploaded text file and report a helpful message if it is missing.",
            "common_mistakes": ["Not handling a missing file", "Opening a file without closing it"],
            "learning_outcome": "Read a text file safely and handle a missing-file error.",
        },
        {
            "why_learn": "A small complete program combines Python building blocks into something a user can run.",
            "key_concepts": ["input", "functions", "conditions", "looping"],
            "simple_explanation": "A mini project connects input, processing, and output into one useful program.",
            "syntax_rules": ["Convert input text before numeric calculations", "Keep each program step in a clear function or block"],
            "small_example": "answer = input('2 + 2 = ')\nif answer == '4':\n    print('Correct')",
            "example_explanation": [
                "input asks the user for an answer and returns text.",
                "The condition compares that text with the expected answer.",
                "The matching branch prints feedback.",
            ],
            "real_world_example": "A command-line quiz can ask AIML learners Python questions and track their responses.",
            "common_mistakes": ["Comparing input text with a number", "Leaving out feedback for an incorrect answer"],
            "learning_outcome": "Build and run a short interactive program that checks a response.",
        },
    ]
    for index, (task, lesson) in enumerate(zip(payload["tasks"], lessons)):
        lesson["small_example"] = "\n".join(
            f"example_line_{index + 1} = {index + 1}"
            for index in range(len(lesson["example_explanation"]))
        )
        lesson["primary_example"] = {
            "title": "Core example",
            "lines": [
                {"content": code, "explanation": explanation}
                for code, explanation in zip(
                    lesson["small_example"].splitlines(),
                    lesson["example_explanation"],
                )
            ],
        }
        lesson.update({
            "concept_introduction": f"{task['title']} introduces the ideas needed to understand this step in Python.",
            "lesson_prerequisites": ["Be able to read a short Python statement."],
            "real_world_analogy": f"Think of {task['title'].lower()} like organizing labeled notes so each one can be found and used.",
            "detailed_explanation": (
                f"{lesson['simple_explanation']} Start with one small input, observe how Python handles it, "
                "then change one part and predict the result before running the code."
            ),
            "additional_examples": [{
                "title": "A second small example",
                "lines": [
                    {
                        "content": "value = 2",
                        "explanation": "Assign the integer 2 to the name value.",
                    },
                    {
                        "content": "print(value)",
                        "explanation": "Display the value stored under that name.",
                    },
                ],
            }],
            "mistake_corrections": [{
                "mistake": lesson["common_mistakes"][0],
                "correction": "Check the value and syntax carefully, then test the corrected version with a small example.",
            }],
            "beginner_practice": f"Guided: follow the example and change one value while practicing {task['title'].lower()}.",
            "intermediate_practice": f"Extend the example to use two inputs and explain how {task['title'].lower()} processes them.",
            "real_world_application": f"Apply {task['title'].lower()} to organize or process information for the student's selected AIML project.",
            "mini_challenge": f"Create a small independent example of {task['title'].lower()} and predict its result.",
        })
        task.update(lesson)
        task["assignment"] = f"Complete a small {task['title'].lower()} exercise and document its result."
    return payload


def dsa_plan_payload():
    payload = plan_payload()
    topics = [
        ("Algorithm analysis and Big-O", "Analyze time and space complexity for simple operations.", ["algorithms", "complexity"]),
        ("Arrays and strings", "Store, access, and traverse arrays and strings.", ["arrays", "strings"]),
        ("Searching and sorting", "Compare linear search, binary search, and sorting strategies.", ["searching", "sorting"]),
        ("Linked lists", "Trace nodes and links in a singly linked list.", ["linked lists", "nodes"]),
        ("Stacks and queues", "Choose stacks and queues for ordered data processing.", ["stacks", "queues"]),
        ("Trees and traversals", "Explore tree structure and traversal algorithms.", ["trees", "traversal"]),
        ("Graphs and graph search", "Represent graphs and trace breadth-first and depth-first search.", ["graphs", "breadth-first search"]),
        ("Hashing and dynamic programming", "Use hash tables and dynamic programming to solve problems.", ["hashing", "dynamic programming"]),
    ]
    for task, (title, description, concepts) in zip(payload["tasks"], topics):
        task["title"] = title
        task["description"] = description
        task["learning_objective"] = f"Understand and apply {title.lower()} to solve algorithm problems."
        task["verification_focus"] = f"Explain and trace {title.lower()} correctly."
        task["key_concepts"] = concepts
        task["detailed_explanation"] = (
            f"{description} Compare the choices and explain when each approach is useful."
        )
        for example in [task["primary_example"], *task["additional_examples"]]:
            for line in example["lines"]:
                line["content"] = "for each item in collection"
    return payload


def scoped_plan_payload(domain):
    topics_by_domain = {
        "Databases": [
            ("Relational database foundations", "Organize records into related tables and define keys."),
            ("SQL query structure", "Select columns from tables and filter matching rows."),
            ("Sorting and aggregation", "Sort records and summarize groups with SQL functions."),
            ("Joins and relationships", "Combine related rows with inner and outer joins."),
            ("Data changes and transactions", "Insert, update, and delete rows safely."),
            ("Schema design and normalization", "Design consistent tables and reduce duplicate data."),
            ("Indexes and query performance", "Use indexes and inspect query plans."),
            ("Database project", "Build a small data-backed application using SQL."),
        ],
        "Developer Tools": [
            ("Version control foundations", "Track changes and inspect project history with Git."),
            ("Repositories and branches", "Create repositories and isolate work with branches."),
            ("Staging and commits", "Stage selected changes and record clear commits."),
            ("Remote collaboration", "Connect to a remote repository and synchronize changes."),
            ("Pull requests and reviews", "Propose changes and respond to code review."),
            ("Conflict resolution", "Resolve merge conflicts and verify the resulting history."),
            ("GitHub project workflows", "Use issues and project boards to coordinate work."),
            ("Team workflow project", "Collaborate on a small project using Git and GitHub."),
        ],
        "Generative AI": [
            ("Generative AI foundations", "Explain how generative models create text and other outputs."),
            ("Tokens and context windows", "Trace how tokenization and context limits affect prompts."),
            ("Prompt design", "Write clear prompts with constraints and structured outputs."),
            ("Model APIs", "Send requests to a generative model and handle its responses."),
            ("Embeddings and semantic search", "Represent text as vectors and retrieve similar content."),
            ("Retrieval-augmented generation", "Ground model responses in retrieved source material."),
            ("Evaluation and safety", "Evaluate output quality and identify unsafe or unsupported responses."),
            ("Generative AI application", "Combine prompts, retrieval, and evaluation in a small application."),
        ],
    }
    payload = plan_payload()
    for task, (title, description) in zip(payload["tasks"], topics_by_domain[domain]):
        task["title"] = title
        task["description"] = description
        task["learning_objective"] = f"Understand and apply {title.lower()}."
    return payload


def curriculum_plan_payload(path, domain, technology):
    normalized_domain = re.sub(r"[^a-z]", "", domain.casefold())
    if normalized_domain in {"dsa", "datastructuresalgorithms"}:
        payload = dsa_plan_payload()
    else:
        payload = plan_payload()
        payload["project_overview"] = f"A focused {domain} curriculum for {path}."
        payload["skills_required"] = [
            {"skill": domain, "why": f"Core knowledge for {domain}.", "priority": "Core"}
        ]
        payload["tech_stack"] = [technology]
        for index, task in enumerate(payload["tasks"], start=1):
            task["title"] = f"{domain} concept {index}"
            task["description"] = f"Study concept {index} within {domain} for the {path} track."
            task["learning_objective"] = f"Understand and apply concept {index} within {domain}."
            task["verification_focus"] = f"Demonstrate concept {index} within {domain}."
            task["key_concepts"] = [f"{domain} concept {index}", f"{domain} application"]
            task["detailed_explanation"] = (
                f"This lesson teaches concept {index} within {domain} and how it applies "
                f"to the selected {path} track."
            )

    example_by_technology = {
        "language-agnostic": "for each item in collection",
        "python": 'print("selected topic")',
        "java": 'System.out.println("selected topic");',
        "javascript": 'console.log("selected topic");',
        "c": "#include <stdio.h>",
        "c++": "#include <iostream>",
        "c#": 'Console.WriteLine("selected topic");',
        "sql": "SELECT id FROM records;",
        "git": "git status",
        "github": "git push origin main",
        "html": "<html><body>selected topic</body></html>",
        "css": ".card { color: blue; }",
    }
    sample = example_by_technology.get(technology.casefold(), f"{domain}: concept")
    for task in payload["tasks"]:
        for example in [task["primary_example"], *task["additional_examples"]]:
            for line in example["lines"]:
                line["content"] = "process selected concept"
        task["primary_example"]["lines"][0]["content"] = sample

    payload["learning_order"] = [task["title"] for task in payload["tasks"]]
    return payload


def assessment_payload():
    return {
        "topic_id": 1,
        "topic_title": "Python fundamentals",
        "assessment_focus": "Variables and expressions",
        "difficulty": "Beginner",
        "questions": [
            {
                "id": 1,
                "question": "What is a variable?",
                "question_type": "concept",
                "options": ["A named reference to a value", "A loop"],
            },
            {
                "id": 2,
                "question": "Predict the output.",
                "question_type": "output_prediction",
                "options": ["25", "age"],
            },
            {
                "id": 3,
                "question": "Write an expression.",
                "question_type": "code_or_query",
                "options": ["2 + 2", "print"],
            },
        ],
        "passing_criteria": "Explain the concept and solve the practical questions.",
    }


def evaluation_payload(score, status, passed):
    return {
        "topic_id": 1,
        "status": status,
        "passed": passed,
        "score": score,
        "overall_feedback": "Review the individual feedback.",
        "strengths": ["Understands basic values."],
        "weak_areas": ["Practice expressions."],
        "targeted_practice": "Complete two short coding exercises.",
        "next_step": "Continue to the next roadmap task.",
        "question_results": [
            {
                "question_id": question_id,
                "correct": True,
                "feedback": "Good explanation.",
                "explanation": "Variables refer to stored values.",
            }
            for question_id in (1, 2, 3)
        ],
    }


class BuildReadyWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(api.app)
        self.client_patcher = patch.object(api, "get_gemini_client", return_value=object())
        self.client_patcher.start()
        self.addCleanup(self.client_patcher.stop)

    def mock_model_json(self, payload, prompt_capture=None):
        def respond(**kwargs):
            if prompt_capture is not None:
                prompt_capture.append(kwargs["contents"])
            return type("GeminiResponse", (), {"text": json.dumps(payload)})()

        return patch.object(api, "call_gemini_with_fallback", side_effect=respond)

    def test_health_and_request_validation(self):
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertIn("BuildReady-AI", home.text)
        frontend_styles = self.client.get("/style.css")
        self.assertEqual(frontend_styles.status_code, 200)
        frontend_script = self.client.get("/script.js")
        self.assertEqual(frontend_script.status_code, 200)
        self.assertIn("apiBaseUrl", frontend_script.text)
        frontend_config = self.client.get("/config.js")
        self.assertEqual(frontend_config.status_code, 200)

        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertIn("gemini_configured", health.json())
        invalid_request = self.client.post("/generate-plan", json={})
        self.assertEqual(invalid_request.status_code, 422)

    def test_plan_assessment_and_verification_flow(self):
        with self.mock_model_json(plan_payload(), []) as generate:
            plan_response = self.client.post(
                "/generate-plan",
                json={
                    "path": "AIML",
                    "domain": "Python",
                    "goal": "Learn a skill",
                    "level": "Beginner",
                    "idea": "Learn Python",
                },
            )
        self.assertEqual(plan_response.status_code, 200)
        plan = plan_response.json()["ai_plan"]
        self.assertEqual(len(plan["tasks"]), 8)
        self.assertEqual(
            [task["status"] for task in plan["tasks"]],
            ["IN_PROGRESS"] + ["NOT_STARTED"] * 7,
        )
        task = plan["tasks"][0]
        for generated_task in plan["tasks"]:
            examples = [generated_task["primary_example"], *generated_task["additional_examples"]]
            self.assertGreaterEqual(len(examples), 2)
            for example in examples:
                self.assertTrue(example["lines"])
                self.assertTrue(all(line["content"].strip() and line["explanation"].strip() for line in example["lines"]))
        self.assertTrue(task["key_concepts"])
        self.assertTrue(task["simple_explanation"])
        self.assertTrue(task["why_learn"])
        self.assertTrue(task["syntax_rules"])
        self.assertTrue(task["small_example"])
        self.assertEqual(len(task["example_explanation"]), len(task["small_example"].splitlines()))
        self.assertTrue(task["concept_introduction"])
        self.assertTrue(task["lesson_prerequisites"])
        self.assertTrue(task["real_world_analogy"])
        self.assertTrue(task["detailed_explanation"])
        self.assertEqual(len(task["additional_examples"]), 1)
        self.assertTrue(task["mistake_corrections"][0]["correction"])
        self.assertTrue(task["beginner_practice"])
        self.assertTrue(task["intermediate_practice"])
        self.assertTrue(task["real_world_application"])
        self.assertTrue(task["mini_challenge"])
        self.assertTrue(task["real_world_example"])
        self.assertTrue(task["common_mistakes"])
        self.assertTrue(task["learning_outcome"])
        self.assertEqual(
            len({item["real_world_example"] for item in plan["tasks"]}),
            len(plan["tasks"]),
        )
        self.assertIn("Learn Python", generate.call_args.kwargs["contents"])
        self.assertIn("content' line and its paired 'explanation'", generate.call_args.kwargs["contents"])
        self.assertIn("mini_challenge", generate.call_args.kwargs["contents"])
        self.assertIn("mistake_corrections", generate.call_args.kwargs["contents"])
        self.assertIn("selected Domain determines the curriculum", generate.call_args.kwargs["contents"])
        self.assertEqual(plan_response.json()["technology"], "Python")
        self.assertTrue(task["assignment"])

        assessment_request = {
            "topic_id": task["id"],
            "topic_title": task["title"],
            "topic_description": task["description"],
            "verification_focus": task["verification_focus"],
            "learning_objective": task["learning_objective"],
            "key_concepts": task["key_concepts"],
            "simple_explanation": task["simple_explanation"],
            "small_example": task["small_example"],
            "concept_introduction": task["concept_introduction"],
            "lesson_prerequisites": task["lesson_prerequisites"],
            "real_world_analogy": task["real_world_analogy"],
            "detailed_explanation": task["detailed_explanation"],
            "real_world_example": task["real_world_example"],
            "example_explanation": task["example_explanation"],
            "additional_examples": task["additional_examples"],
            "common_mistakes": task["common_mistakes"],
            "mistake_corrections": task["mistake_corrections"],
            "practical_exercise": task["practical_exercise"],
            "assignment": task["assignment"],
            "beginner_practice": task["beginner_practice"],
            "intermediate_practice": task["intermediate_practice"],
            "real_world_application": task["real_world_application"],
            "mini_challenge": task["mini_challenge"],
            "path": "AIML",
            "domain": "Python",
            "technology": "Python",
            "level": "Beginner",
            "goal": "Learn a skill",
            "idea": "Learn Python",
            "related_skills": ["Python", "Data types"],
        }
        assessment_prompts = []
        with self.mock_model_json(assessment_payload(), assessment_prompts):
            assessment_response = self.client.post("/generate-assessment", json=assessment_request)
        self.assertEqual(assessment_response.status_code, 200)
        assessment = assessment_response.json()
        self.assertEqual(len(assessment["questions"]), 3)
        self.assertTrue(all(question["question"] != question["question_type"] for question in assessment["questions"]))
        self.assertIn("Python", assessment_prompts[0])
        self.assertIn(", ".join(task["key_concepts"]), assessment_prompts[0])
        self.assertIn(task["small_example"], assessment_prompts[0])
        self.assertIn(task["detailed_explanation"], assessment_prompts[0])
        self.assertIn(task["beginner_practice"], assessment_prompts[0])
        self.assertIn(task["mini_challenge"], assessment_prompts[0])
        self.assertIn(task["assignment"], assessment_prompts[0])
        self.assertIn("The 'question' field MUST contain the complete student-facing question", assessment_prompts[0])

        evaluation_request = {
            **{key: assessment_request[key] for key in (
                "topic_id", "topic_title", "topic_description", "path", "domain", "technology", "level", "goal", "idea"
            )},
            **{key: assessment_request[key] for key in (
                "learning_objective", "key_concepts", "simple_explanation", "small_example",
                "common_mistakes", "practical_exercise"
            )},
            **{key: assessment_request[key] for key in (
                "concept_introduction", "lesson_prerequisites", "real_world_analogy",
                "detailed_explanation", "real_world_example", "example_explanation", "additional_examples",
                "mistake_corrections", "beginner_practice", "intermediate_practice",
                "real_world_application", "mini_challenge"
            )},
            "assignment": assessment_request["assignment"],
            "submissions": [
                {
                    "question_id": question["id"],
                    "question": question["question"],
                    "user_answer": question["options"][-1],
                    "options": question["options"],
                }
                for question in assessment["questions"]
            ],
        }
        evaluation_prompts = []
        with self.mock_model_json(evaluation_payload(82, "NEEDS_PRACTICE", False), evaluation_prompts):
            passed_response = self.client.post("/evaluate-assessment", json=evaluation_request)
        self.assertEqual(passed_response.status_code, 200)
        self.assertIn(", ".join(task["key_concepts"]), evaluation_prompts[0])
        self.assertIn(task["detailed_explanation"], evaluation_prompts[0])
        self.assertIn(task["intermediate_practice"], evaluation_prompts[0])
        self.assertIn("Available choices: A named reference to a value, A loop", evaluation_prompts[0])
        self.assertIn("Mark an objectively incorrect selection incorrect", evaluation_prompts[0])
        passed_result = passed_response.json()
        self.assertEqual(passed_result["status"], "VERIFIED")
        self.assertTrue(passed_result["passed"])
        self.assertEqual(passed_result["score"], 82)
        self.assertTrue(passed_result["question_results"][0]["correct"])

        with self.mock_model_json(evaluation_payload(50, "VERIFIED", True)):
            failed_response = self.client.post("/evaluate-assessment", json=evaluation_request)
        self.assertEqual(failed_response.status_code, 200)
        self.assertEqual(failed_response.json()["status"], "NEEDS_PRACTICE")
        self.assertFalse(failed_response.json()["passed"])

    def test_project_prompt_uses_specific_branch_and_goal(self):
        prompts = []
        with self.mock_model_json(scoped_plan_payload("Generative AI"), prompts):
            response = self.client.post(
                "/generate-plan",
                json={
                    "path": "AIML",
                    "domain": "Generative AI",
                    "goal": "Build a Project",
                    "level": "Beginner",
                    "idea": "Build an AI Resume Analyzer",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Build an AI Resume Analyzer", prompts[0])
        self.assertIn("AIML", prompts[0])
        self.assertIn("Derive actual skills and sequence from selected scope", prompts[0])

    def test_selected_scope_takes_precedence_over_free_text_goal(self):
        cases = [
            ("AIML", "Data Structures & Algorithms", "Language-agnostic", "Language-agnostic"),
            ("CSE", "Programming Languages", "Java", "Java"),
            ("CSE", "Databases", "SQL", "SQL"),
            ("Software Development", "Developer Tools", "GitHub", "GitHub"),
        ]
        example_for_focus = {
            "Language-agnostic": "for each item in collection",
            "Java": 'System.out.println("selected");',
            "SQL": "SELECT id FROM records;",
            "GitHub": "git push origin main",
        }
        for path, domain, technology, expected_focus in cases:
            with self.subTest(technology=technology):
                prompts = []
                response_plan = (
                    dsa_plan_payload()
                    if domain == "Data Structures & Algorithms"
                    else scoped_plan_payload(domain)
                    if domain in {"Databases", "Developer Tools"}
                    else plan_payload()
                )
                for task in response_plan["tasks"]:
                    examples = [task["primary_example"], *task["additional_examples"]]
                    for example in examples:
                        for line in example["lines"]:
                            line["content"] = "for each item in collection"
                    examples[0]["lines"][0]["content"] = example_for_focus[technology]
                with self.mock_model_json(response_plan, prompts):
                    response = self.client.post(
                        "/generate-plan",
                        json={
                            "path": path,
                            "domain": domain,
                            "technology": technology,
                            "goal": "Learn the Domain",
                            "level": "Beginner",
                            "idea": "I want to learn Python",
                        },
                    )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["technology"], expected_focus)
                self.assertIn(f"Selected technology/topic focus: '{expected_focus}'", prompts[0])
                self.assertIn("Student Input is context only", prompts[0])
                self.assertIn("Never fall back to generic Python content", prompts[0])

    def test_every_selectable_path_domain_and_goal_preserves_curriculum_scope(self):
        cases = selector_curriculum_cases()
        self.assertEqual(len(cases), 175)
        self.assertEqual(len(set(cases)), 175)
        self.assertEqual(len({(path, domain) for path, domain, _ in cases}), 121)

        model_responses = [
            type(
                "GeminiResponse",
                (),
                {"text": json.dumps(curriculum_plan_payload(path, domain, technology))},
            )()
            for path, domain, technology in cases
            for _goal in ("Learn the Domain", "Build a Project")
        ]
        prompts = []

        def generate_response(**kwargs):
            prompts.append(kwargs["contents"])
            return model_responses.pop(0)

        with patch.object(api, "call_gemini_with_fallback", side_effect=generate_response):
            for path, domain, technology in cases:
                for goal in ("Learn the Domain", "Build a Project"):
                    with self.subTest(path=path, domain=domain, goal=goal):
                        response = self.client.post(
                            "/generate-plan",
                            json={
                                "path": path,
                                "domain": domain,
                                "technology": technology,
                                "goal": goal,
                                "level": "Beginner",
                                "idea": "I want to learn Python",
                            },
                        )
                        self.assertEqual(response.status_code, 200, response.text)
                        result = response.json()
                        self.assertEqual(result["path"], path)
                        self.assertEqual(result["domain"], domain)
                        self.assertEqual(result["technology"], technology)
                        self.assertIn(f"- Engineering Path: {path}", prompts[-1])
                        self.assertIn(f"- Selected Domain: {domain}", prompts[-1])
                        self.assertIn(f"- Goal Type: {goal}", prompts[-1])
                        self.assertIn("curriculum", prompts[-1].casefold())
        self.assertEqual(len(model_responses), 0)

    def test_python_fallback_is_rejected_for_every_non_python_curriculum(self):
        generic_python_plan = api.ProjectPlan.model_validate(plan_payload())
        valid_python_domains = {
            "python",
            "programmingfundamentals",
            "programminglanguages",
        }
        for path, domain, _technology in selector_curriculum_cases():
            normalized_domain = re.sub(r"[^a-z]", "", domain.casefold())
            with self.subTest(path=path, domain=domain):
                if normalized_domain in valid_python_domains:
                    api.validate_plan_curriculum(generic_python_plan, domain)
                else:
                    with self.assertRaises(api.HTTPException):
                        api.validate_plan_curriculum(generic_python_plan, domain)

    def test_custom_other_topics_keep_scope_and_reject_python_fallback(self):
        for custom_topic in ("Robotics Hardware", "Environmental Engineering"):
            with self.subTest(topic=custom_topic):
                generic_python_plan = api.ProjectPlan.model_validate(plan_payload())
                with self.assertRaises(api.HTTPException):
                    api.validate_plan_curriculum(generic_python_plan, custom_topic)

                for goal in ("Learn the Domain", "Build a Project"):
                    prompt_capture = []
                    with self.mock_model_json(
                        curriculum_plan_payload("Other", custom_topic, custom_topic),
                        prompt_capture,
                    ):
                        response = self.client.post(
                            "/generate-plan",
                            json={
                                "path": "Other",
                                "domain": custom_topic,
                                "technology": custom_topic,
                                "goal": goal,
                                "level": "Beginner",
                                "idea": "I want to learn Python",
                            },
                        )
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(response.json()["domain"], custom_topic)
                    self.assertIn(f"- Selected Domain: {custom_topic}", prompt_capture[0])

    def test_custom_other_retries_and_rejects_python_fundamentals(self):
        prompts = []
        with self.mock_model_json(plan_payload(), prompts) as generate:
            response = self.client.post(
                "/generate-plan",
                json={
                    "path": "Other",
                    "domain": "Robotics Hardware",
                    "technology": "Robotics Hardware",
                    "goal": "Learn the Domain",
                    "level": "Beginner",
                    "idea": "I want to learn Python",
                },
            )
        self.assertEqual(response.status_code, 502)
        self.assertIn("substituted Python fundamentals", response.json()["detail"])
        self.assertEqual(generate.call_count, 2)
        self.assertIn("- Selected Domain: Robotics Hardware", prompts[0])

    def test_python_fundamentals_roadmap_is_rejected_for_dsa_and_regenerated(self):
        prompts = []
        corrected_plan = dsa_plan_payload()
        for task in corrected_plan["tasks"]:
            for example in [task["primary_example"], *task["additional_examples"]]:
                for line in example["lines"]:
                    line["content"] = "values = [1, 2, 3]"
            task["primary_example"]["lines"][0]["content"] = 'print("DSA")'
        responses = [
            type("GeminiResponse", (), {"text": json.dumps(plan_payload())})(),
            type("GeminiResponse", (), {"text": json.dumps(corrected_plan)})(),
        ]

        def generate_response(**kwargs):
            prompts.append(kwargs["contents"])
            return responses.pop(0)

        with patch.object(api, "call_gemini_with_fallback", side_effect=generate_response):
            response = self.client.post(
                "/generate-plan",
                json={
                    "path": "AIML",
                    "domain": "Data Structures & Algorithms",
                    "technology": "Python",
                    "goal": "Learn the Domain",
                    "level": "Beginner",
                    "idea": "I want to learn Python",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(prompts), 2)
        self.assertIn("Data Structures & Algorithms", prompts[0])
        self.assertIn("selected Domain determines the curriculum", prompts[0])
        self.assertIn("Selected technology/topic focus: 'Python'", prompts[0])
        self.assertIn("selected domain curriculum", prompts[1])
        task_titles = [task["title"] for task in response.json()["ai_plan"]["tasks"]]
        self.assertIn("Arrays and strings", task_titles)
        self.assertIn("Trees and traversals", task_titles)

    def test_python_fundamentals_are_rejected_for_other_domains(self):
        plan = api.ProjectPlan.model_validate(plan_payload())
        with self.assertRaises(api.HTTPException) as raised:
            api.validate_plan_curriculum(plan, "Cybersecurity")
        self.assertEqual(raised.exception.status_code, 502)
        self.assertIn("substituted Python fundamentals", raised.exception.detail)

    def test_selected_language_rejects_python_example_fallback(self):
        plan = api.ProjectPlan.model_validate(plan_payload())
        with self.assertRaises(api.HTTPException) as raised:
            api.validate_plan_technology_examples(plan, "Java")
        self.assertEqual(raised.exception.status_code, 502)

    def test_wrong_language_plan_gets_one_technology_correction(self):
        incorrect_plan = plan_payload()
        corrected_plan = plan_payload()
        for task in corrected_plan["tasks"]:
            for example in [task["primary_example"], *task["additional_examples"]]:
                for line in example["lines"]:
                    line["content"] = "value = 1"
            task["primary_example"]["lines"][0]["content"] = 'System.out.println("Java");'

        responses = [incorrect_plan, corrected_plan]
        prompts = []

        def generate_response(**kwargs):
            prompts.append(kwargs["contents"])
            return type("GeminiResponse", (), {"text": json.dumps(responses.pop(0))})()

        with patch.object(api, "call_gemini_with_fallback", side_effect=generate_response) as model_call:
            response = self.client.post(
                "/generate-plan",
                json={
                    "path": "CSE",
                    "domain": "Programming Languages",
                    "technology": "Java",
                    "goal": "Learn the Domain",
                    "level": "Beginner",
                    "idea": "I want to learn Python",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(model_call.call_count, 2)
        self.assertIn("Authoritative selections:", prompts[1])
        self.assertIn("Technology/topic: Java", prompts[1])
        self.assertEqual(response.json()["technology"], "Java")

    def test_assessment_and_evaluation_keep_selected_technology(self):
        request = {
            "topic_id": 1,
            "topic_title": "Java variables",
            "topic_description": "Declare and use Java variables.",
            "path": "CSE",
            "domain": "Programming Languages",
            "technology": "Java",
            "level": "Beginner",
            "goal": "Learn the Domain",
            "idea": "I want to learn Python",
            "key_concepts": ["Java types", "variable declarations"],
        }
        assessment_prompts = []
        with self.mock_model_json(assessment_payload(), assessment_prompts):
            assessment_response = self.client.post("/generate-assessment", json=request)
        self.assertEqual(assessment_response.status_code, 200)
        self.assertIn("Use Java syntax", assessment_prompts[0])
        self.assertIn("Selected technology/topic: Java", assessment_prompts[0])
        self.assertIn("never default to Python", assessment_prompts[0])

        evaluation_request = {
            **request,
            "submissions": [
                {
                    "question_id": index + 1,
                    "question": question["question"],
                    "user_answer": "A named reference to a value",
                    "options": question["options"],
                }
                for index, question in enumerate(assessment_response.json()["questions"])
            ],
        }
        evaluation_prompts = []
        with self.mock_model_json(evaluation_payload(50, "NEEDS_PRACTICE", False), evaluation_prompts):
            evaluation_response = self.client.post("/evaluate-assessment", json=evaluation_request)
        self.assertEqual(evaluation_response.status_code, 200)
        self.assertIn("Selected technology/topic: Java", evaluation_prompts[0])
        self.assertIn("Do not introduce Python conventions unless Python is selected", evaluation_prompts[0])

    def test_short_roadmap_is_regenerated_as_unique_steps(self):
        short_plan = plan_payload()
        short_plan["tasks"] = short_plan["tasks"][:2]
        responses = [
            type("GeminiResponse", (), {"text": json.dumps(short_plan)})(),
            type("GeminiResponse", (), {"text": json.dumps(plan_payload())})(),
        ]
        with patch.object(api, "call_gemini_with_fallback", side_effect=responses) as model_call:
            response = self.client.post(
                "/generate-plan",
                json={
                    "path": "AIML",
                    "domain": "Python",
                    "goal": "Learn a skill",
                    "level": "Beginner",
                    "idea": "Learn Python",
                },
            )
        self.assertEqual(response.status_code, 200)
        tasks = response.json()["ai_plan"]["tasks"]
        self.assertEqual(len(tasks), 8)
        self.assertEqual(len({task["title"] for task in tasks}), 8)
        self.assertEqual(model_call.call_count, 2)

    def test_structured_lesson_examples_keep_line_explanations_aligned(self):
        with self.assertRaises(ValueError):
            api.LessonExampleLine(
                content="print(1)\nprint(2)",
                explanation="This one explanation cannot represent two separate code lines.",
            )

        lesson_plan = plan_payload()
        task = lesson_plan["tasks"][2]
        task["small_example"] = "unrelated legacy text"
        task["example_explanation"] = ["unrelated legacy explanation"]
        task["primary_example"]["lines"] = [
            {"content": "score = 8 + 2", "explanation": "Add 8 and 2, then store the result in score."},
            {"content": "print(score > 5)", "explanation": "Compare score with 5 and display the Boolean result."},
        ]
        with self.mock_model_json(lesson_plan) as model_call:
            response = self.client.post(
                "/generate-plan",
                json={
                    "path": "AIML",
                    "domain": "Python",
                    "goal": "Learn Python",
                    "level": "Beginner",
                    "idea": "Learn Python",
                },
            )

        self.assertEqual(response.status_code, 200)
        plan = response.json()["ai_plan"]
        repaired_task = plan["tasks"][2]
        self.assertEqual(
            repaired_task["small_example"].splitlines(),
            [line["content"] for line in repaired_task["primary_example"]["lines"]],
        )
        self.assertEqual(
            repaired_task["example_explanation"],
            [line["explanation"] for line in repaired_task["primary_example"]["lines"]],
        )
        self.assertEqual(model_call.call_count, 1)
        self.assertIn("Each example line requires its paired explanation", model_call.call_args.kwargs["contents"])

    def test_assessment_rejects_placeholder_question_text(self):
        invalid_assessment = assessment_payload()
        invalid_assessment["questions"][0]["question"] = "concept"
        with self.mock_model_json(invalid_assessment):
            response = self.client.post(
                "/generate-assessment",
                json={
                    "topic_id": 1,
                    "topic_title": "Python variables",
                    "topic_description": "Learn Python variable assignment.",
                    "path": "AIML",
                    "domain": "Python",
                    "level": "Beginner",
                    "goal": "Learn",
                },
            )
        self.assertEqual(response.status_code, 502)
        self.assertNotIn('"questions"', response.text)

    def test_chat_receives_roadmap_and_assessment_context(self):
        prompts = []
        with self.mock_model_json({"reply": "Practice variables next."}, prompts):
            response = self.client.post(
                "/chat",
                json={
                    "message": "What should I practice?",
                    "path": "AIML",
                    "domain": "Python",
                    "technology": "Java",
                    "goal": "Learn a skill",
                    "level": "Beginner",
                    "current_topic": "Python fundamentals",
                    "topics": [{"id": 1, "title": "Python fundamentals", "status": "NEEDS_PRACTICE"}],
                    "assessment_results": [{
                        "topic_id": 1,
                        "score": 42,
                        "status": "NEEDS_PRACTICE",
                        "overall_feedback": "Expressions need work.",
                        "weak_areas": ["Expressions"],
                    }],
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("NEEDS_PRACTICE", prompts[0])
        self.assertIn("Selected technology/topic: Java", prompts[0])
        self.assertIn("42/100", prompts[0])
        self.assertIn("Expressions", prompts[0])

    def test_provider_errors_are_not_returned_to_clients(self):
        with patch.object(api, "call_gemini_with_fallback", side_effect=RuntimeError("private provider detail")):
            response = self.client.post(
                "/generate-plan",
                json={
                    "path": "AIML",
                    "domain": "Python",
                    "goal": "Learn",
                    "level": "Beginner",
                },
            )
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private provider detail", response.text)

    def test_cors_allows_local_frontend_and_rejects_unknown_origin(self):
        allowed = self.client.options(
            "/generate-plan",
            headers={
                "Origin": "http://localhost:5500",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.headers.get("access-control-allow-origin"), "http://localhost:5500")
        self.assertNotIn("access-control-allow-origin", self.client.get(
            "/health", headers={"Origin": "https://untrusted.example"}
        ).headers)


    def test_founder_endpoints_require_configured_secret(self):
        endpoints = ["/founder/stats", "/founder/users", "/founder/events"]
        with patch.dict("os.environ", {"FOUNDER_SECRET_KEY": "test-founder-key"}):
            for endpoint in endpoints:
                self.assertEqual(
                    self.client.get(endpoint, headers={"X-Founder-Key": "test-founder-key"}).status_code,
                    200,
                )
                self.assertEqual(
                    self.client.get(endpoint, headers={"X-Founder-Key": " 'test-founder-key' "}).status_code,
                    200,
                )
                self.assertEqual(self.client.get(endpoint, headers={"X-Founder-Key": "wrong"}).status_code, 403)
                self.assertEqual(self.client.get(endpoint).status_code, 403)
                self.assertEqual(self.client.get(endpoint, headers={"X-Founder-Key": "  "}).status_code, 403)
                self.assertEqual(
                    self.client.get(
                        endpoint, headers={"X-Founder-Key": "change-this-to-a-long-random-secret"}
                    ).status_code,
                    403,
                )

    def test_founder_endpoints_reject_unset_or_placeholder_secret(self):
        for configured in ("", "change-this-to-a-long-random-secret"):
            with patch.dict("os.environ", {"FOUNDER_SECRET_KEY": configured}):
                response = self.client.get(
                    "/founder/stats", headers={"X-Founder-Key": "change-this-to-a-long-random-secret"}
                )
                self.assertEqual(response.status_code, 503)

    def test_frontend_assets_are_revalidated_after_deploy(self):
        for path in ("/", "/founder-dashboard.html", "/config.js", "/founder-dashboard.js", "/style.css"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertEqual(response.headers.get("cache-control"), "no-cache", path)
        self.assertNotIn("cache-control", self.client.get("/health").headers)

    def test_frontend_scripts_do_not_redeclare_shared_globals(self):
        root = Path(__file__).resolve().parents[1] / "frontend"
        declaration = re.compile(r"^(?:const|let|class)\s+([A-Za-z_$][\w$]*)", flags=re.MULTILINE)
        config_globals = set(declaration.findall((root / "config.js").read_text(encoding="utf-8")))
        for page_script in ("script.js", "founder-dashboard.js"):
            page_globals = set(declaration.findall((root / page_script).read_text(encoding="utf-8")))
            self.assertFalse(config_globals & page_globals, f"{page_script} redeclares a config.js global")


if __name__ == "__main__":
    unittest.main()
