# Customer Support Triage Agent - Runner & Testing Guide

This guide provides end-to-end instructions and copy-pasteable commands to test and run the **Customer Support Triage Multi-Agent System**.

---

## 1. Environment Setup & Activation

Navigate to the project root directory:

```powershell
cd "c:\Users\prave\OneDrive\Desktop\Personal\Udemy Course\LangGraph Multi-Agent Projects Build 5 Production-Ready AI\Projects\Project 2 Customer Support Triage Agent"
```

### Option A (Recommended): Direct Execution (No Activation Needed)
You can run any command directly through the project's virtual environment python (`.venv\Scripts\python`). This never fails with `ModuleNotFoundError` and bypasses PowerShell script execution policy restrictions:

```powershell
.venv\Scripts\python run_triage.py --mode interactive
```

---

### Option B: Activate the Virtual Environment

- **Windows (PowerShell)**:
  ```powershell
  # If PowerShell blocks script execution, run this first:
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

  # Activate virtual environment
  .\.venv\Scripts\Activate.ps1
  ```

- **Windows (Command Prompt / CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

- **Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```

> [!IMPORTANT]
> If you see `ModuleNotFoundError: No module named 'langchain_core'`, it means your terminal is running global Python instead of the virtual environment. Either run `.\.venv\Scripts\Activate.ps1` first or use `.venv\Scripts\python` directly.

---

## 2. Test Execution Commands (Start to End)

### Step 1: Run the Automated Pytest Suite
Verifies all 12 test cases across the API, agent routing rules, tools, and human-in-the-loop flows:

```powershell
.venv\Scripts\pytest -v
```
*(or `pytest -v` if environment is activated)*

**Expected output:** `12 passed`

---

### Step 2: View the Architecture & Flow Diagram
Prints the LangGraph StateGraph topology, Mermaid flowchart, and routing ASCII art:

```powershell
.venv\Scripts\python run_triage.py --mode diagram
```
*(or `python run_triage.py --mode diagram` if environment is activated)*

---

### Step 3: Run the Batch Stress-Test Suite (Recommended for Demo)
Executes all 6 real-world messy support ticket scenarios, demonstrating dynamic routing, tool invocations, and Human-in-the-Loop pauses:

```powershell
.venv\Scripts\python run_triage.py --mode batch
```
*(or `python run_triage.py --mode batch` if environment is activated)*

#### Test Scenarios Covered:
| Ticket ID | Scenario | Department | Sentiment | Priority | Human Review? | Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TIK-101** | Routine Billing Query | Billing | NEUTRAL | LOW | Auto-Resolved | Invoice confirmed, refund not needed |
| **TIK-102** | Furious $250 Refund Demand | Billing | ANGRY | HIGH | **PAUSED (HITL)** | Amount > $50 & anger triggers manager sign-off |
| **TIK-103** | Cryptic 503 Stack Trace | Technical | FRUSTRATED | HIGH | Auto-Resolved | Queries telemetry, references active incident INC-8821 |
| **TIK-104** | VIP Lawsuit & SLA Threat | Escalation | ANGRY | CRITICAL | **PAUSED (HITL)** | Pages dedicated account manager, generates dossier |
| **TIK-105** | Ambiguous Multi-Intent | Tech / Bill | NEUTRAL | LOW | Auto-Resolved | Resolves ambiguity and provides guidance |
| **TIK-106** | Routine API Doc Query | Technical | NEUTRAL | LOW | Auto-Resolved | Direct answer from Knowledge Base article KB-303 |

---

### Step 4: Run the Interactive Support Console
Allows you to enter live tickets interactively, observe agent decisions, and review/approve drafts at HITL checkpoints:

```powershell
.venv\Scripts\python run_triage.py --mode interactive
```
*(or `python run_triage.py --mode interactive` if environment is activated)*

#### Sample Prompts to Try:
1. **Auto-Resolve Flow (Billing)**:
   - **Customer ID**: `CUST-001`
   - **Customer Tier**: `pro`
   - **Message**: `"Hi support team, could you please confirm if invoice INV-2024-001 for $49 went through?"`

2. **Human-in-the-Loop Gate (High Refund & Anger)**:
   - **Customer ID**: `CUST-004`
   - **Customer Tier**: `pro`
   - **Message**: `"I was charged $250 on invoice INV-2024-099 without authorization! I demand an immediate refund or I will report fraud to my bank!"`
   - *Action*: When prompted at the red review panel, choose `[1] Approve`, `[2] Edit`, or `[3] Reject`.

3. **VIP Escalation Flow**:
   - **Customer ID**: `CUST-002`
   - **Customer Tier**: `enterprise`
   - **Message**: `"This is CTO Bob Miller. Your system outage breached our enterprise SLA. I need an immediate call with Sarah or our legal team will commence litigation."`

---

### Step 5: Run the FastAPI REST Server
Launch the production API server:

```powershell
.venv\Scripts\uvicorn src.api:app --reload --port 8000
```
*(or `uvicorn src.api:app --reload --port 8000` if environment is activated)*

- **Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Docs (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

#### Testing the API via PowerShell:

**1. Ingest a Ticket (POST /api/tickets/triage):**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/tickets/triage" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{
    "message": "I demand an immediate $250 refund on invoice INV-2024-099!",
    "customer_id": "CUST-004",
    "customer_tier": "pro"
  }' | ConvertTo-Json -Depth 4
```

**2. Check Thread State (GET /api/tickets/{thread_id}/state):**
Replace `<THREAD_ID>` with the `thread_id` returned from step 1:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/tickets/<THREAD_ID>/state" -Method Get | ConvertTo-Json -Depth 4
```

**3. Resume Paused Ticket with Human Review (POST /api/tickets/{thread_id}/resume):**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/tickets/<THREAD_ID>/resume" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{
    "decision": "approve",
    "feedback": "Approved by Customer Support Lead."
  }' | ConvertTo-Json -Depth 4
```

---

## 3. LLM Configuration Options

Settings are managed in [`.env`](file:///.env):

- **OpenRouter (Active & Configured)**:
  ```env
  LLM_PROVIDER=openrouter
  OPENROUTER_API_KEY=sk-or-v1-your-key-here
  MODEL_NAME=nvidia/nemotron-3.5-lightning:free
  MODEL_TEMPERATURE=0.0
  ```
  *(Supported models: `nvidia/nemotron-3.5-lightning:free`, `openai/gpt-4o-mini`, `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.3-70b-instruct`)*

- **Mock Mode (Zero-Cost Offline Fallback)**:
  If `OPENROUTER_API_KEY` and `OPENAI_API_KEY` are empty or removed, the system automatically runs the built-in `MockChatSupportModel` offline.

- **Direct OpenAI**:
  ```env
  LLM_PROVIDER=openai
  OPENAI_API_KEY=sk-your-openai-key-here
  MODEL_NAME=gpt-4o-mini
  ```

---

## 4. Quick Reference Cheatsheet

| Task | Direct Command (Recommended) | Activated Command |
| :--- | :--- | :--- |
| **Run All Unit Tests** | `.venv\Scripts\pytest -v` | `pytest -v` |
| **Run Specific Test File** | `.venv\Scripts\pytest tests/test_graph_flow.py -v` | `pytest tests/test_graph_flow.py -v` |
| **Run Batch Scenarios** | `.venv\Scripts\python run_triage.py --mode batch` | `python run_triage.py --mode batch` |
| **Run Interactive Console** | `.venv\Scripts\python run_triage.py --mode interactive` | `python run_triage.py --mode interactive` |
| **Inspect Mermaid Diagram** | `.venv\Scripts\python run_triage.py --mode diagram` | `python run_triage.py --mode diagram` |
| **Launch FastAPI Server** | `.venv\Scripts\uvicorn src.api:app --reload --port 8000` | `uvicorn src.api:app --reload --port 8000` |
