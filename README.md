# OrchestIQ Grader: A Composable, Consensus-Driven Evaluation Pipeline

🏆 **Hackathon Winner Project**

**OrchestIQ Grader** is a modular, event-driven microservices architecture designed to automate and validate the grading of handwritten or template-based exam answers. By chaining a Vision Agent (OCR), an LLM Agent (Scoring), and an OPA Policy Engine (Consensus), it provides a fast, auditable, and transparent grading system, moving beyond simple single-model pipelines.

## ✨ Novelty & Key Features

This project's core innovation lies in its **Composable Orchestrator and Consensus** approach:

* **Modular Architecture:** The system is split into independent microservices (Orchestrator, Vision, LLM, OPA) communicating asynchronously via **RabbitMQ**. This ensures reliability and allows any component to be updated or scaled without affecting the others.
* **Vision-to-LLM Chain:** It first uses a **Vision Agent** (OCR/HWR) to convert the handwritten image to text, and then passes the result and confidence score to the **LLM Agent**.
* **Decoupled Consensus (OPA):** The final grading decision is not made by the LLM. Instead, the LLM's suggested grade and confidence are passed to the **Open Policy Agent (OPA)** engine. OPA applies a predefined, auditable policy to determine the final status (e.g., `COMPLETE` or `MANUAL_REVIEW`).
* **LLM Grader:** Leverages the **Groq API** and `llama-3.1-8b-instant` for fast, accurate grading and structured JSON output.

## 🏗️ Architecture Overview

The pipeline operates in 5 key steps:

1.  **Orchestrator:** Receives the exam image and rubric via the FastAPI endpoint and publishes the task to the `evaluation_tasks` queue.
2.  **Vision/HWR Agent:** Consumes the task, performs OCR/HWR using `ocr.space` (Engine 2), and sends the extracted text to the `vision_results` queue.
3.  **LLM Agent:** Consumes the text and rubric, uses the LLM to generate a score, justification, and confidence, and publishes this verdict to the `llm_results` queue.
4.  **Orchestrator (Consumer):** Listens on `llm_results`, validates the verdict against the **OPA Policy**, and determines the final grade/status (e.g., `COMPLETE`, `MANUAL_REVIEW`).
5.  **Frontend:** Polls the Orchestrator for the final status and displays the result and justification.

## 🚀 Getting Started

These instructions will get a full local development stack running via Docker Compose.

### Prerequisites

* Docker and Docker Compose installed.
* API Keys:
    * **Groq API Key**: For the LLM Agent.
    * **OCR.space API Key**: For the Vision/HWR Agent.

### Setup

1.  **Clone the Repository (if not already done):**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Configure Environment Variables:**
    Create a `.env` file in the following agent directories and populate them with your keys:

    * `llm_agent/.env`:
        ```env
        GROQ_API_KEY=YOUR_GROQ_KEY_HERE
        ```
    * `vision_hwr_agent/.env`:
        ```env
        OCRSPACE_API_KEY=YOUR_OCR_SPACE_KEY_HERE
        ```

3.  **Run the Stack:**
    Build and start all five services (Orchestrator, RabbitMQ, OPA, Vision Agent, LLM Agent):
    ```bash
    docker-compose up --build
    ```
    This will launch the services and their respective Python listeners.

### Usage

1.  **Access the Frontend:**
    Open your browser and navigate to the root directory to access the static `index.html` file (or serve it using a simple server, e.g., `python3 -m http.server 8080`).

2.  **Submit an Evaluation:**
    * Fill in the **Exam ID**, **Question Text**, and **Examiner Rubric**.
    * Upload an image of a student's answer sheet.
    * Click **"Begin Evaluation"** and watch the status messages track the task as it moves through the pipeline (Queueing -> Vision -> LLM -> Consensus).

## 🧩 Project Structure

Standard microservices layout with separate folders for each component:

```bash
.
├── consensus_service/
│   └── policy.rego     # OPA consensus rules (e.g., manual review if confidence < 0.8)
├── llm_agent/
│   └── agent.py        # Groq/Llama-3 Grader, consumes Vision result, produces LLM verdict
├── orchestrator_service/
│   └── main.py         # FastAPI API, task queuing, and OPA/Consensus handler
├── vision_hwr_agent/
│   └── agent.py        # OCR.space integration, consumes task, produces Vision verdict
├── docker-compose.yml  # Defines all 5 services: Orchestrator, RabbitMQ, OPA, Vision, LLM
└── index.html          # Simple front-end for task submission and status polling
//update
