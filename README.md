# AI-Driven Workflow Automation Agent

A fully local, end-to-end recruiting workflow automation system that combines deterministic software engineering with LLM-assisted reasoning to simulate a real recruiting pipeline.

The agent parses resumes, filters candidates, generates interview schedules, sends email invitations, processes replies, and maintains a persistent calendar — all without external services.

Designed as a deterministic AI orchestration prototype demonstrating structured LLM integration, schema-constrained extraction, and workflow automation.

---

## Core Capabilities

The system automates an entire recruiting workflow:

### Resume ingestion
- Reads PDFs from a directory.
- Converts to text via `pypdf`.

### Structured data extraction
- Uses an Ollama-hosted LLaMA model.
- Constrained to a strict Pydantic schema.
- Extracts name, location, education, work history, projects.

### Profile normalization
Computes derived attributes such as:
- US location
- Degree level
- Experience thresholds
- Project presence

### Deterministic candidate filtering
- Applies rule-based eligibility criteria.
- Ensures reproducible, explainable decisions.

### Interview slot generation
- Generates weekday business-hour slots.
- Avoids calendar conflicts.
- Structured JSON output.

### Email drafting and delivery
- Generates invite emails with LLM.
- Sends via local SMTP server.
- Simulates inbox using GUI.

### Reply interpretation
- Parses candidate responses.
- Validates chosen slot.
- Updates persistent calendar.

### Calendar management
- Stores scheduled interviews in JSON.
- Displays via lightweight GUI.

---

## Architecture Overview

### Design Goals
- Fully local execution
- Deterministic workflow control
- Schema-validated LLM output
- Transparent decision logic
- Modular prompt-driven architecture

### High-Level Pipeline

```
PDF Resumes
     ↓
Text Extraction
     ↓
LLM Resume Parser → Structured Candidate Profiles
     ↓
Normalization + Derived Features
     ↓
Deterministic Filtering
     ↓
Interview Slot Generator
     ↓
Invite Email Drafting
     ↓
SMTP Delivery → Inbox GUI
     ↓
Reply Parsing
     ↓
Calendar Scheduling
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| LLM runtime | Ollama + LLaMA 3 |
| Language | Python 3.10+ |
| Data modeling | Pydantic |
| PDF parsing | pypdf |
| Email simulation | aiosmtpd |
| GUIs | Tkinter |
| Persistence | JSON files |

---

## Project Structure

```
AI_Agent.py
prompts/
    parser.txt
    dates.txt
    congratulations.txt
    response.txt
resumes/
email_dir/
calendar_dir/
requirements.txt
```

### Key Files

**AI_Agent.py**  
Main orchestration script controlling the full workflow.

**prompts/**  
Modular LLM prompts for parsing, scheduling, and response handling.

**resumes/**  
Input PDF resumes.

**email_dir/**  
Simulated inbox storage.

**calendar_dir/**  
JSON-backed interview calendar.

---

## Installation

### System Requirements
- Python 3.10+
- Ollama installed
- LLaMA model pulled locally

### Python Dependencies

```
pip install -r requirements.txt
```

---

## Running the Agent

From the project root:

```
python AI_Agent.py
```

### Execution Flow
1. Starts Ollama server if not running.
2. Loads prompts from `prompts/`.
3. Parses resumes.
4. Filters candidates.
5. Generates interview slots.
6. Sends invite emails via local SMTP.
7. Opens inbox GUI.
8. Parses replies and schedules interviews.
9. Saves results to calendar JSON.

---

## Deterministic Filtering Logic

Candidates pass if **any** rule is satisfied:

- Masters or PhD + US location  
- Bachelor + ≥5 years experience  
- Masters/PhD + (≥3 years experience OR projects)

This demonstrates hybrid AI + rule-based decision systems.

---

## LLM Integration Strategy

| Task | LLM Role |
|------|----------|
| Resume parsing | Extract structured candidate data |
| Slot generation | Produce business-hour availability |
| Email drafting | Natural-language communication |
| Reply parsing | Interpret candidate choices |

All outputs are constrained by schema validation to prevent hallucination.

---

## Engineering Highlights
- Schema-constrained LLM extraction
- Deterministic workflow orchestration
- Persistent state via JSON
- Local SMTP + GUI simulation
- Modular prompt architecture
- Fully offline operation
---

## Educational Value

This project demonstrates:
- Practical LLM system integration
- AI-assisted workflow automation
- Structured data extraction from unstructured documents
- Hybrid deterministic + AI system design
- Prompt engineering with validation
---
