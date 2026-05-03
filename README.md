# VAIVI - Real Time Screen-Aware Multimodal AI Copilot

A cross-platform AI system that understands your screen, processes voice and text input, and delivers real-time contextual assistance through a custom multimodal pipeline.

---

## 🔗 Demo

* **Live App**: https://your-vercel-link
* **Demo Video (90s)**: https://youtu.be/SGj-_pTr8qg
* **GitHub**: https://github.com/aravind7979/Vaivi

---

## ❓ Problem Statement

Developers and users frequently switch context between tools (browser, IDE, docs) to resolve queries, leading to:

* High cognitive overhead
* Context loss during problem-solving
* Inefficient workflows

Existing AI tools lack **real-time awareness of user context (screen, activity, voice)**.

VAIVI solves this by enabling **on-demand, screen-aware AI interaction directly within the user’s workflow**.

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

### Multimodal AI Pipeline

* Designed a custom pipeline combining **screen context, user query, and memory**
* Implemented **context aggregation + LLM orchestration** for grounded responses

### Real-Time Interaction System

* Engineered **event-driven invocation** using global hotkey (Alt+V)
* Built low-latency processing for real-time assistance within active workflows

### Cross-Platform Architecture

* Packaged desktop application using **Tauri (Rust)** for native performance
* Designed system to support **web + desktop + Android (in progress)**

### Backend & Infrastructure

* Developed **FastAPI backend deployed on AWS EC2**
* Handles image streams (Base64), audio input, and query orchestration

### Voice & Streaming

* Implemented **bidirectional voice interaction pipeline**
* Integrated real-time response streaming for improved UX

### Error Handling

* API failure fallback strategies
* Handling empty or invalid screen context
* Permission and capture edge-case handling

---

## 🛠️ Tech Stack

* Backend: Python, FastAPI
* Desktop: Tauri (Rust), JavaScript
* AI/LLM: Gemini API
* Cloud: AWS EC2
* Data Handling: Base64 image streams, audio processing
* Architecture: Multimodal RAG pipeline

---

## 🚀 Setup Instructions

git clone https://github.com/aravind7979/Vaivi
cd Vaivi

# Backend setup

pip install -r requirements.txt
uvicorn app.main:app --reload

# Run desktop app (Tauri)

npm install
npm run tauri dev

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

VAIVI is not just a chatbot-it is a **real-time AI interaction system** that integrates:

* OS-level triggers
* Screen-aware reasoning
* Multimodal inputs
* Scalable backend infrastructure

This represents a shift toward **context-aware AI systems embedded directly into user workflows**.
