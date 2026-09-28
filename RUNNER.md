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
.venv\Scripts\python run_triage.py --mode customers
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

## 2. Test Execution Commands (Step by Step)

### Step 1: Run the Automated Pytest Suite (17 Tests)
Verifies all 17 test cases across the API, agent routing rules, tools, human-in-the-loop checkpoints, and customer CRM operations:

```powershell
.venv\Scripts\pytest -v
```
*(or `pytest -v` if environment is activated)*

**Expected output:** `17 passed`

---

### Step 2: Explore the Customer CRM Directory & MRR Analytics
Inspect the 602 enterprise customer accounts, MRR metrics ($298K/mo), and SLA tiers:

```powershell
.venv\Scripts\python run_triage.py --mode customers
```
*(or `python run_triage.py --mode customers` if environment is activated)*

---

### Step 3: Submit Questions & Tickets as Any Verified Customer
Select any customer ID (e.g. `CUST-141`, `CUST-002`, `CUST-737`), view their live Customer 360 profile card, and submit custom questions/tickets grounded in their actual contract:

```powershell
.venv\Scripts\python run_triage.py --mode interactive --customer CUST-141
```

#### Sample Prompts to Try as `CUST-141`:
1. **Billing Dispute**:
   `"We were billed $250 on our last invoice without authorization. Please issue a refund immediately."`
   *(Triggers the Human-in-the-Loop checkpoint because $250 exceeds the $50 threshold!)*
2. **Infrastructure Emergency**:
   `"Our production data pipeline is throwing 503 errors and SLA guarantees are breached. What is the status of INC-8821?"`
   *(Technical specialist inspects live telemetry and provides incident status!)*

---

### Step 4: Explore the 1,000 Production Tickets Dataset
Filter and inspect the 1,000 authentic production support tickets directly from the terminal:

```powershell
.venv\Scripts\python run_triage.py --mode dataset
```

---

### Step 5: Run the Batch Stress-Test Suite
Executes the graph across messy real-world tickets, showing routing, tool calls, and HITL pauses:

```powershell
.venv\Scripts\python run_triage.py --mode batch
```

#### Test Scenarios Covered:
| Ticket ID | Scenario | Department | Sentiment | Priority | Human Review? | Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TIK-101** | Routine Billing Query | Billing | NEUTRAL | LOW | Auto-Resolved | Invoice confirmed, refund not needed |
| **TIK-102** | Furious $250 Refund Demand | Billing | ANGRY | HIGH | **PAUSED (HITL)** | Amount > $50 & anger triggers manager sign-off |
| **TIK-103** | Cryptic 503 Stack Trace | Technical | FRUSTRATED | HIGH | Auto-Resolved | Queries telemetry, references active incident INC-8821 |
| **TIK-104** | VIP Lawsuit & SLA Threat | Escalation | ANGRY | CRITICAL | **PAUSED (HITL)** | Pages dedicated account manager, generates dossier |
| **TIK-105** | Ambiguous Multi-Intent | Tech / Bill | NEUTRAL | LOW | Auto-Resolved | Resolves ambiguity and provides guidance |
| **TIK-106** | Routine API Doc Query | Technical | NEUTRAL | LOW | Auto-Resolved | Direct answer from Knowledge Base article KB-303 |

---

### Step 6: View the Architecture & Flow Diagram
Prints the LangGraph StateGraph topology, Mermaid flowchart, and routing ASCII art:

```powershell
.venv\Scripts\python run_triage.py --mode diagram
```

---

### Step 7: Run the FastAPI REST Server
Launch the production API server:

```powershell
.venv\Scripts\uvicorn src.api:app --reload --port 8000
```

- **Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Docs (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

#### Testing the API via PowerShell:

**1. Inspect Customer 360 Profile (GET /api/customers/{id}):**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/customers/CUST-141" -Method Get | ConvertTo-Json -Depth 4
```

**2. Submit a Ticket for that Customer (POST /api/customers/{id}/ticket):**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/customers/CUST-141/ticket" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{
    "subject": "Production API Latency Spike",
    "body": "Our integration endpoint is seeing 12s response times and 503 errors."
  }' | ConvertTo-Json -Depth 4
```

**3. Ingest a Raw Ticket (POST /api/tickets/triage):**
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

**4. Check Paused Thread State (GET /api/tickets/{thread_id}/state):**
Replace `<THREAD_ID>` with the `thread_id` returned from step 3:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/tickets/<THREAD_ID>/state" -Method Get | ConvertTo-Json -Depth 4
```

**5. Resume Paused Ticket with Human Review (POST /api/tickets/{thread_id}/resume):**
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

### Step 8: Open the Web Presentation & Interactive Studio
Simply open [`web/index.html`](file:///web/index.html) in your browser:
- Slide 10 features the **Interactive 1,000-Ticket Studio** with step controls (`Prev`, `Next`, `Auto Play`).
- Press `S` for Speaker Notes drawer.
- Press `P` for Pop-Out Teleprompter window for your secondary monitor.

---

## 3. Quick Reference Cheatsheet

| Task | Direct Command (Recommended) | Activated Command |
| :--- | :--- | :--- |
| **Run All 17 Unit Tests** | `.venv\Scripts\pytest -v` | `pytest -v` |
| **View Customer Directory** | `.venv\Scripts\python run_triage.py --mode customers` | `python run_triage.py --mode customers` |
| **Submit Ticket as Customer** | `.venv\Scripts\python run_triage.py --mode interactive --customer CUST-141` | `python run_triage.py --mode interactive --customer CUST-141` |
| **Explore 1,000 Tickets** | `.venv\Scripts\python run_triage.py --mode dataset` | `python run_triage.py --mode dataset` |
| **Run Batch Scenarios** | `.venv\Scripts\python run_triage.py --mode batch` | `python run_triage.py --mode batch` |
| **Inspect Architecture Diagram** | `.venv\Scripts\python run_triage.py --mode diagram` | `python run_triage.py --mode diagram` |
| **Launch FastAPI Server** | `.venv\Scripts\uvicorn src.api:app --reload --port 8000` | `uvicorn src.api:app --reload --port 8000` |
