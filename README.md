# 🩺 Full-Stack Medical AI Assistant

> An intelligent, full-stack Medical AI Assistant that combines **Retrieval-Augmented Generation (RAG), Agentic AI, conversational memory, and secure authentication** to provide context-aware answers from user-uploaded medical documents.

Built with **Next.js, TypeScript, Python, LangChain, LangGraph, and modern vector search technologies**, this project demonstrates how Generative AI can be integrated into a production-style full-stack application.

---

## 🚀 Overview

The **Full-Stack Medical AI Assistant** allows users to upload medical documents such as PDF reports and interact with them through a conversational AI interface.

Instead of relying only on the LLM's pre-trained knowledge, the system uses **RAG** to retrieve relevant information from the user's documents before generating an answer.

The application also maintains **conversation history**, allowing users to ask follow-up questions while preserving the context of previous interactions.

The backend is designed around an **agentic workflow using LangGraph**, enabling intelligent routing and orchestration of different AI capabilities.

---

## ✨ Key Features

### 📄 Medical Document RAG

* Upload medical PDF documents.
* Automatically process and ingest documents.
* Split documents into meaningful chunks.
* Generate embeddings for semantic search.
* Retrieve the most relevant information for each question.
* Generate answers grounded in the uploaded documents.

### 🤖 Agentic AI Workflow

* Built using **LangGraph** for stateful AI workflows.
* Uses an agent-based architecture instead of a simple single LLM call.
* Dynamically determines how a user query should be processed.
* Supports extensible AI tools and workflow components.
* Maintains state throughout multi-step interactions.

### 🧠 Conversational Memory

* Maintains chat history across conversations.
* Stores conversation data using **SQLite**.
* Enables contextual follow-up questions.
* Allows the assistant to understand previous interactions instead of treating every query independently.

### 🔐 Authentication

* Secure user authentication using **Clerk**.
* User-specific access to the application.
* Separates user sessions and conversations.

### 💬 Full-Stack AI Chat Interface

* Modern responsive frontend built with **Next.js**.
* Real-time interaction with the AI backend.
* Clean conversational interface.
* Upload documents and immediately interact with them.

### 🔎 Context-Grounded Answers

The system follows a retrieval-based workflow:

```text
User Question
      ↓
Query Processing
      ↓
Retriever / Vector Search
      ↓
Relevant Medical Context
      ↓
LangGraph / Agentic Workflow
      ↓
LLM
      ↓
Context-Aware Response
```

This reduces the chance of generating answers unrelated to the user's uploaded documents.

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │       User          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌────────────────────────────┐
                    │     Next.js Frontend      │
                    │   TypeScript + Tailwind   │
                    │          + Clerk           │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │      Python Backend        │
                    │        AI Engine           │
                    └─────────────┬──────────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
                 ▼                ▼                ▼
          ┌────────────┐   ┌─────────────┐  ┌─────────────┐
          │    RAG     │   │  LangGraph  │  │   Memory    │
          │  Pipeline  │   │   Agents    │  │   SQLite    │
          └─────┬──────┘   └──────┬──────┘  └─────────────┘
                │                 │
                ▼                 ▼
        ┌──────────────┐    ┌──────────────┐
        │ Vector Store │    │     LLM      │
        │  Embeddings  │    │  Generation  │
        └──────┬───────┘    └──────┬───────┘
               │                   │
               └─────────┬─────────┘
                         ▼
                  ┌──────────────┐
                  │ AI Response  │
                  └──────────────┘
```

---

# 🧠 RAG Pipeline

The document question-answering pipeline works in multiple stages:

### 1. Document Upload

The user uploads a medical PDF through the frontend.

### 2. Document Ingestion

The backend processes the document using the ingestion pipeline.

### 3. Chunking

The document is divided into smaller chunks so that relevant sections can be retrieved efficiently.

### 4. Embedding Generation

Each chunk is converted into a numerical vector representation.

### 5. Vector Storage

The embeddings are stored in a vector database for semantic retrieval.

### 6. Query Retrieval

When the user asks a question, the system searches for the most relevant document chunks.

### 7. Agentic Processing

The retrieved context is passed through the LangGraph workflow where the appropriate AI processing path is selected.

### 8. Response Generation

The LLM generates a response using the retrieved medical context and conversation history.

---

# 🤖 Agentic AI Workflow

Unlike a basic RAG chatbot where every question follows the same fixed pipeline, this project uses **LangGraph** to create a more flexible and stateful workflow.

```text
                  User Query
                      │
                      ▼
               ┌─────────────┐
               │   Agent /   │
               │   Router    │
               └──────┬──────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
       Retrieve     Process     Other
       Documents    Context     Tools
          │           │           │
          └───────────┼───────────┘
                      ▼
                Final Response
```

This architecture makes the system easier to extend with additional tools and specialized agents.

---

# 🛠️ Tech Stack

## Frontend

* **Next.js**
* **TypeScript**
* **React**
* **Tailwind CSS**
* **Clerk Authentication**

## Backend

* **Python**
* **LangChain**
* **LangGraph**
* **RAG**
* **Vector Database**
* **SQLite**

## AI / Generative AI

* Large Language Models (LLMs)
* Embeddings
* Semantic Search
* Retrieval-Augmented Generation
* Agentic AI
* Stateful AI Workflows

---

# 📂 Project Structure

```text
Full-Stack-Medical-AI-Assistant
│
├── backend
│   │
│   ├── uploaded_files/
│   │
│   ├── main.py
│   ├── ingest_data.py
│   ├── chat_history.py
│   └── requirements.txt
│
├── med-ai-frontend
│   │
│   ├── app/
│   ├── clerk-nextjs/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── .gitignore
└── README.md
```

---

# ⚙️ Getting Started

## 1. Clone the Repository

```bash
git clone https://github.com/sameeryellamandala/Full-Stack-Medical-AI-Assistant.git

cd Full-Stack-Medical-AI-Assistant
```

---

## 2. Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create a `.env` file in the appropriate backend/frontend directories and add the required API keys and configuration values.

Example:

```env
LLM_API_KEY=your_api_key
VECTOR_DB_API_KEY=your_api_key
CLERK_SECRET_KEY=your_secret_key
```

**Never commit `.env` files or API keys to GitHub.**

---

## 4. Start the Backend

Run the Python backend using the project's configured server command.

For example:

```bash
python main.py
```

---

## 5. Start the Frontend

Open another terminal:

```bash
cd med-ai-frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Then open:

```text
http://localhost:3000
```

---

# 💡 Example Use Case

A user uploads a medical report:

```text
Blood_Test_Report.pdf
```

The system processes and indexes the document.

The user can then ask:

```text
"What is my hemoglobin level?"
```

The RAG pipeline retrieves the relevant section from the uploaded document and provides a response based on that context.

The user can continue:

```text
"Is that within the normal range?"
```

Because conversation history is maintained, the assistant can understand that **"that" refers to the previously discussed hemoglobin value**.

---

//output 
<img width="1897" height="993" alt="Screenshot 2026-09-12 102925" src="https://github.com/user-attachments/assets/f6b8aeb1-0bc8-49e3-b955-76e93f6552b8" />
<img width="1911" height="1045" alt="Screenshot 2026-09-12 102948" src="https://github.com/user-attachments/assets/42da07ac-d271-491a-ac62-f347ffe291ae" />

<img width="1548" height="852" alt="Screenshot 2026-09-12 102853" src="https://github.com/user-attachments/assets/586f570f-0d83-4aef-aa29-92ff488c4c14" />
<img width="1902" height="997" alt="Screenshot 2026-09-12 102913" src="https://github.com/user-attachments/assets/9de17237-4b14-498b-a404-23b6a245723d" />




# 🔒 Security & Privacy

This project is designed with user-specific access and authentication in mind.

* Authentication handled through Clerk.
* User conversations are separated through application-level session handling.
* API keys are stored through environment variables.
* Sensitive configuration should never be committed to the repository.
* Medical information should be treated as sensitive data.

> **Disclaimer:** This project is intended for educational and demonstration purposes. It is not a substitute for professional medical diagnosis, treatment, or medical advice.

---

# 🎯 Why This Project?

This project demonstrates the combination of several modern Generative AI concepts into a complete application:

```text
LLMs
 │
 ├── RAG
 │    ├── Document Ingestion
 │    ├── Chunking
 │    ├── Embeddings
 │    └── Vector Search
 │
 ├── Agentic AI
 │    ├── LangGraph
 │    ├── State Management
 │    └── Workflow Routing
 │
 ├── Memory
 │    └── Conversation History
 │
 └── Full-Stack Engineering
      ├── Next.js
      ├── Python
      ├── Authentication
      └── Database
```

The goal is to demonstrate how **Generative AI, RAG, Agentic AI, and full-stack development** can be combined to build a practical AI application.

---


# 🚧 Future Improvements

* [ ] Multi-document reasoning
* [ ] Improved retrieval using hybrid search
* [ ] Better document metadata filtering
* [ ] Source/page citations in responses
* [ ] Streaming AI responses
* [ ] More specialized medical AI agents
* [ ] Improved evaluation and RAG metrics
* [ ] Production deployment
* [ ] Automated testing
* [ ] Observability and AI tracing

---

# 👨‍💻 Author

**Sameer Yellamandala**

B.Tech Computer Science Student | Generative AI Developer

Interested in:

* 🤖 Generative AI
* 🧠 LLMs
* 🔍 RAG Systems
* 🦾 Agentic AI
* 🕸️ LangChain & LangGraph
* 💻 Data Structures & Algorithms
* 🚀 Full-Stack AI Applications


**Repository:**
https://github.com/sameeryellamandala/Full-Stack-Medical-AI-Assistant
