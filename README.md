# AI-Driven Workflow Automation Agent

## Overview

**AI-Driven Workflow Automation Agent** is a local, LLM-powered automation system that performs end-to-end candidate screening and interview scheduling. It parses resumes, evaluates candidates against configurable criteria, generates interview availability, communicates via email, and schedules interviews on a calendar using structured LLM outputs.

The system is designed to run **entirely locally** using **Ollama** for inference and relies on explicit schemas (via Pydantic) to ensure deterministic, machine-parseable LLM responses.

---

## What AI_Agent Does

AI_Agent automates the following workflow:

1. **Resume ingestion** (PDF)
2. **LLM-based resume parsing** into structured candidate data
3. **Rule-based candidate filtering**
4. **Calendar availability analysis**
5. **LLM-generated interview date/time proposals**
6. **Email communication with candidates**
7. **Interview scheduling and confirmation**

All LLM interactions return strict JSON conforming to predefined schemas.

---

## Repository Structure

```
AI_Agent/
├── AI_Agent.py          # Main orchestration logic
├── Email.py             # Email sending and SMTP handling
├── Calendar.py          # Calendar ingestion and scheduling logic
├── calendar.json        # Calendar data source
├── resumes/             # Input resumes (PDF format)
    ├── *.pdf
```

---

## Requirements

### System Requirements

* Python 3.10+
* Ollama installed locally

### Python Dependencies

Key dependencies include:

* `ollama`
* `pydantic`
* `pypdf`
* `aiosmtpd`
* `tkinter` (standard library)

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## LLM Setup (Required)

AI_Agent uses **Ollama** with the `llama3` model.

### Start Ollama

```bash
ollama serve
```

Or allow AI_Agent to start it automatically (threaded) via:

```python
AIAgent().start_server()
```

Ensure the `llama3` model is available:

```bash
ollama pull llama3
```

---

## Running AI_Agent

From inside the `AI_Agent/` directory:

```bash
python AI_Agent.py
```

The agent will:

1. Read all PDFs in `./resumes/`
2. Extract structured candidate data using the LLM
3. Filter candidates based on education, experience, location, and projects
4. Generate interview dates/times excluding unavailable calendar dates
5. Email qualified candidates and schedule interviews

---

## Resume Parsing

Resumes are parsed using an LLM prompt and validated against the `DataExtraction` schema, which includes:

* Name, email, address
* Education and work history
* Projects
* Boolean flags (e.g., `has_masters`, `has_five_years_work_experience`, `is_located_in_the_US`)

This ensures consistent downstream filtering.

---

## Candidate Filtering Logic

A candidate passes if **any** of the following are true:

* Has a Master’s or Doctorate and is located in the U.S.
* Has a Master’s or Doctorate and ≥5 years of work experience
* Has ≥5 years of work experience and multiple projects

Filtering is deterministic and rule-based after extraction.

---

## Calendar and Scheduling

* Calendar availability is loaded from `calendar.json`
* Existing dates are treated as unavailable
* The LLM generates new weekday-only interview dates and times
* Responses are validated against strict schemas before use

---

## Email Automation

AI_Agent:

* Generates congratulatory interview emails via the LLM
* Sends messages using SMTP
* Parses candidate replies to confirm date/time selection
* Updates the calendar upon confirmation

Email logic is implemented in `Email.py`.

---

## Design Principles

* **Local-first inference** (no cloud LLM dependency)
* **Schema-enforced LLM outputs**
* **Deterministic control logic** around probabilistic models
* **Separation of concerns** (resume parsing, filtering, scheduling, email)

