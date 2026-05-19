# 🩺 Full-Stack Medical AI Assistant

A robust, full-stack Generative AI application designed to process medical documents and provide context-aware, 
intelligent responses.
Built with a modern Next.js frontend and a Python-powered AI backend, featuring a complete RAG (Retrieval-Augmented Generation) pipeline.

## ✨ Key Features
* **Intelligent Medical QA:** Upload and query medical PDFs to get precise, context-backed answers.
* **RAG Pipeline:** Automated data ingestion, chunking, and vectorization of user-uploaded documents (`ingest_data.py`).
* **Persistent Memory:** Maintains context across conversations using a local SQLite chat history database.
* **Secure Authentication:** User management and secure access powered by Clerk.
* **Seamless Full-Stack Integration:** Next.js frontend communicating seamlessly with the Python AI engine.

## 🛠️ Tech Stack
**Frontend:**
* Next.js (App Router)
* TypeScript
* Tailwind CSS
* Clerk (Authentication)

**Backend & AI:**
* Python
* Langchain/Langgraph / RAG Workflows
* Vector Database Integration
* SQLite (Chat History)

## 📂 Project Structure
```text
📦 full-stack-medical-ai-assistant
 ┣ 📂 backend                 # Python AI Engine & API
 ┃ ┣ 📂 uploaded_files        # Directory for ingested medical PDFs
 ┃ ┣ 📜 main.py               # Main backend server
 ┃ ┣ 📜 ingest_data.py        # RAG document processing pipeline
 ┃ ┣ 📜 chat_history.py       # Conversation memory management
 ┃ ┗ 📜 requirements.txt      # Python dependencies
 ┣ 📂 med-ai-frontend         # Next.js Web Application
 ┃ ┣ 📂 app                   # Frontend routing and UI
 ┃ ┣ 📂 clerk-nextjs          # Auth implementation
 ┃ ┗ 📜 package.json          # Node dependencies
 ┗ 📜 .gitignore              # Root Git configuration

