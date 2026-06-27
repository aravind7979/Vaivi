# VAIVI - Real Time Screen-Aware Multimodal AI Copilot

A cross-platform AI system that understands your screen, processes voice and text input, and delivers real-time contextual assistance through a custom multimodal pipeline.

---

## 🔗 Demo

* **Live App**: https://vaivi.vercel.app
* **Demo Video (90s)**: https://youtu.be/SGj-_pTr8qg
* **GitHub**: https://github.com/aravind7979/Vaivi

---

## ❓ Problem Statement

Developers and users frequently switch context between tools (browser, IDE, docs) to resolve queries, leading to:

* High cognitive overhead
* Context loss during problem-solving
* Inefficient workflows

Existing AI tools lack **real-time awareness of user context (screen, activity, voice)**.

VAIVI solves this by enabling **on-demand, screen-aware AI interaction directly within the user's workflow**.

---

## 🏗️ System Architecture

User Trigger (Alt+V)
→ Screen Capture (Selected Region / Window / Full Screen)
→ Audio/Text Input
→ Context Processing (Screen + Query + Memory)
→ Multimodal RAG Pipeline
→ LLM (Gemini)
→ Response Engine
→ Output (Text / Voice)

---

## ⚙️ Key Features

* Real-time **screen-aware reasoning** using captured visual context
* Multimodal input: **screen + voice + text**
* **Global shortcut (Alt+V)** for instant invocation across applications
* Context selection: **tab / window / full screen**
* Low-latency **voice interaction pipeline** with response playback
* Streaming responses with smooth UI rendering

---

## 🧠 Engineering Highlights

### Cloud-Native & Distributed Systems
* **Stateless Architecture**: Migrated from a monolithic stateful server to a fully stateless distributed backend.
* **Orchestration**: Containerized the entire backend stack (Gateway, API, Workers) using **Docker Compose**.
* **Distributed Caching**: Implemented **Redis (Upstash)** for sub-millisecond session state, user profiles, and chat caching using Cache-Aside and Write-Through patterns.
* **Asynchronous Workers**: Built a robust **Celery** + Redis Message Queue pipeline to offload heavy AI operations (like vector embedding extraction), ensuring a non-blocking and highly responsive API.
* **Managed Data & Vectors**: Migrated local SQLite and local FAISS indexes to managed **AWS RDS PostgreSQL** and remote **Qdrant Cloud** for true horizontal scalability.
* **Gateway Layer**: Designed an **Nginx** reverse proxy to handle request routing and shield internal microservices.

### Multimodal AI Pipeline
* Designed a custom pipeline combining **screen context, user query, and memory**
* Implemented **context aggregation + LLM orchestration** for grounded responses

### Real-Time Interaction System
* Engineered **event-driven invocation** using global hotkey (Alt+V)
* Built low-latency processing for real-time assistance within active workflows

### Cross-Platform Architecture & CI/CD
* **Automated Deployments**: Engineered a seamless CI/CD pipeline using GitHub Actions to automatically deploy frontend changes to **Vercel** and orchestrate zero-downtime backend builds on **AWS EC2**.
* **Secure Desktop Auto-Updater**: Packaged the desktop application using **Tauri (Rust)** and engineered a cryptographically signed auto-update pipeline leveraging GitHub Releases.
* Designed system to support **web + desktop + Android (in progress)**

### Voice & Streaming
* Implemented **bidirectional voice interaction pipeline**
* Integrated real-time response streaming for improved UX

### Error Handling
* Fault-tolerant Redis fallback strategies to ensure uninterrupted session validation
* Handling empty or invalid screen context
* Permission and capture edge-case handling

---

## 🛠️ Tech Stack

* **Infrastructure**: AWS EC2, AWS RDS (PostgreSQL), Docker, Docker Compose, Nginx, GitHub Actions
* **Backend**: Python, FastAPI, Celery, Upstash Redis, Qdrant Cloud
* **Frontend/Desktop**: HTML/Vanilla CSS/JS, Tauri (Rust), Vercel
* **AI/LLM**: Google Gemini API, Sentence Transformers (MiniLM)
* **Architecture**: Stateless Distributed Microservices, Asynchronous Message Queues, Multimodal RAG

---

## 🚀 Setup Instructions

### 1. Backend Orchestration (Docker Compose)
The entire backend stack is fully containerized and orchestrated via Docker Compose. It launches an **Nginx Gateway (port 80)**, **FastAPI API Server**, and a **Celery Worker** (handling asynchronous title generation and memory extraction).

1. Clone the repository:
   ```bash
   git clone https://github.com/aravind7979/Vaivi
   cd Vaivi
   ```
2. Create `backend/.env` with your API keys:
   ```env
   # SQLite is used by default if DATABASE_URL is not set
   REDIS_URL="rediss://..."      # Upstash Redis Connection String
   GEMINI_API_KEY="AIzaSy..."    # Google Gemini API Key
   QDRANT_URL="https://..."      # Qdrant Cloud URL
   QDRANT_API_KEY="..."          # Qdrant Cloud API Key
   ```
3. Start the stack:
   ```bash
   docker compose up -d --build
   ```
4. Verify health checks (wait 20-30 seconds):
   ```bash
   docker compose ps
   ```

### 2. Frontend web app
Open the static site locally using a simple Python server:
```bash
cd website
python -m http.server 3000
# Open http://localhost:3000 in your browser!
```

### 3. Tauri Desktop client (Rust)
To run the desktop application wrapper:
```bash
cd desktop
npm install
npm run tauri dev
```

---

## ⚖️ Trade-offs & Design Decisions

* Screen-based context vs static input
  → Enables real-time reasoning but introduces capture and latency constraints

* External LLM (Gemini) vs local models
  → Chose Gemini for higher reasoning capability and faster development

* Multimodal pipeline complexity vs performance
  → Balanced context richness with near real-time responsiveness

---

## 🔮 Future Work

* Complete Android integration (MediaProjection pipeline)
* Local LLM support for offline inference
* Persistent long-term memory system
* Enhanced context understanding (object-level screen parsing)

---

## 📌 Why This Project Matters

VAIVI is not just a chatbot—it is a **real-time AI interaction system** that integrates:

* OS-level triggers
* Screen-aware reasoning
* Multimodal inputs
* Scalable backend infrastructure

This represents a shift toward **context-aware AI systems embedded directly into user workflows**.
