**PROJECT NAME:** [LifeBuddy] (e.g., "The Recipe Curator AI")

**OVERALL GOAL (The Why):**
To develop a web-based, and later mobile, application that [A concise, one-sentence description of what the app does and the core problem it solves].

**TARGET USER/AUDIENCE:**
[Who is the primary user? e.g., "Small business owners," "Home cooks," "Students studying advanced physics."]

**CORE FEATURES (The What):**
1. [Feature 1, e.g., "AI-powered text generation based on user input."]
2. [Feature 2, e.g., "Secure user registration and authentication."]
3. [Feature 3, e.g., "Vector search capability for document retrieval."]
4. [Feature 4, e.g., "Dashboard to visualize usage metrics."]
5. [Add more features as needed.]

**TECHNOLOGY STACK (The How):**
* **Primary Language:** Python
* **Containerization:** Docker
* **Database:** PostgreSQL with pgVector extension
* **AI/ML:** Local AI (Specify which one if known, e.g., Llama 3, or "TBD - will start with an open-source model")
* **Web Framework (Initial):** [e.g., FastAPI, Flask, Django, Streamlit]
* **Frontend (Initial):** [e.g., HTML/CSS/JavaScript, React, or "Simple Jinja templates rendered by Python."]

**CURRENT STATUS & BASE DOCUMENT:**
* **Current Code/State:** [Describe what you have, e.g., "Only a project idea and the database schema laid out," or "A basic FastAPI 'Hello World' with Dockerfile," or "I have a Python script for the AI but no web integration."]

* **Base Document Content Summary:** [A brief summary of your foundational document. Include key entities, relationships, or business logic. *You will provide the actual document content in the next interaction.*]

**REQUEST FOR AI AGENT (Me):**
Act as a Senior Software Architect and Lead Developer. Your task is to help me build, migrate, and maintain this application. For each request, you must provide:

1.  **Code Recommendations/Changes:** Full, executable code blocks for new files or explicit diffs for existing files.

2.  **Database Updates:** SQL commands (DDL/DML) required for schema changes.

3.  **Architectural Context:** A brief explanation of *why* the changes are necessary and how they fit into the overall structure.

**FIRST IMMEDIATE TASK:**
[What is the very first piece of code we need to create? e.g., "Define the initial `docker-compose.yml` to spin up PostgreSQL/pgVector and a basic Python service.", or "Provide the initial SQL schema for User and Document tables."]