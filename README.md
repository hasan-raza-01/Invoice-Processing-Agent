# 📋 **LangGraph Invoice Processing Agent with HITL**

An intelligent invoice processing system built with **LangGraph**, featuring **Human-in-the-Loop (HITL)** checkpoints, **dynamic tool selection** (Bigtool), and **MCP client orchestration**.

---

## 🎯 **Features**

- ✅ **12-Stage Workflow**: Complete invoice processing from intake to completion
- 🤝 **HITL Checkpoints**: Pause workflow for human review when 2-way matching fails
- 🔄 **Resume Capability**: Seamlessly resume workflows after human decisions
- 🛠️ **Bigtool System**: Dynamic tool selection from capability-based pools
- 🔌 **MCP Integration**: Mock COMMON & ATLAS clients for deterministic and external operations
- 💾 **Checkpoint Persistence**: SQLite-based state storage with full audit logging
- 🌐 **FastAPI Backend**: Async REST API for workflow management
- 📊 **Streamlit Dashboard**: Interactive UI for human review

---

## 🏗️ **Architecture Overview**

### **Workflow Stages**

```
┌─────────────┐
│   INTAKE    │  ① Validate & persist invoice
└──────┬──────┘
       │
┌──────▼──────┐
│ UNDERSTAND  │  ② OCR extraction & parsing
└──────┬──────┘
       │
┌──────▼──────┐
│   PREPARE   │  ③ Normalize vendor & enrich data
└──────┬──────┘
       │
┌──────▼──────┐
│  RETRIEVE   │  ④ Fetch POs, GRNs, history
└──────┬──────┘
       │
┌──────▼──────┐
│MATCH_TWO_WAY│  ⑤ Compute 2-way match score
└──────┬──────┘
       │
       ├─ Match Failed ─┐
       │                 │
       │          ┌──────▼────────┐
       │          │CHECKPOINT_HITL│  ⑥ Create checkpoint & pause
       │          └──────┬────────┘
       │                 │
       │          ┌──────▼─────────┐
       │          │ HITL_DECISION  │  ⑦ Wait for human decision
       │          └──────┬─────────┘
       │                 │
       └─ Match OK ──────┘
                  │
           ┌──────▼──────┐
           │  RECONCILE  │  ⑧ Build accounting entries
           └──────┬──────┘
                  │
           ┌──────▼──────┐
           │   APPROVE   │  ⑨ Apply approval policy
           └──────┬──────┘
                  │
           ┌──────▼──────┐
           │   POSTING   │  ⑩ Post to ERP
           └──────┬──────┘
                  │
           ┌──────▼──────┐
           │    NOTIFY   │  ⑪ Send notifications
           └──────┬──────┘
                  │
           ┌──────▼──────┐
           │   COMPLETE  │  ⑫ Finalize workflow
           └─────────────┘
```
---

## Here’s a preview of the Human Review Dashboard:
![UI Screenshot](./screenshots/Human-Review-Dashboard.png)

---
### **Technology Stack**

- **Orchestration**: LangGraph
- **Backend**: FastAPI + Uvicorn
- **Frontend**: Streamlit
- **Database**: SQLite (SQLAlchemy ORM)
- **Checkpointing**: LangGraph SqliteSaver
- **LLMs**: Google Gemini + Groq (fallback)
- **OCR**: Tesseract

---

## 📁 **Repository Structure**

```
Invoice-Processing-Agent/
├── src/invoice_agent/
│   ├── agent/
│   │   ├── langgraph_workflow.py    # LangGraph workflow definition
│   │   └── workflow_executor.py     # Start/resume helpers
│   ├── nodes/
│   │   ├── workflow_nodes_1.py      # Stages 1-5
│   │   └── workflow_nodes_2.py      # Stages 6-12
│   ├── mcp/
│   │   ├── common_client.py         # COMMON server mock
│   │   └── atlas_client.py          # ATLAS server mock
│   ├── bigtool/
│   │   ├── bigtool_picker.py        # Tool selection engine
│   │   └── tools/                   # OCR, ERP, email, enrichment tools
│   ├── database/
│   │   ├── models.py                # SQLAlchemy models
│   │   └── checkpoint_store.py      # Checkpoint persistence
│   ├── models/
│   │   ├── invoice_models.py        # Pydantic models
│   │   ├── state_models.py          # WorkflowState TypedDict
│   │   └── api_models.py            # API request/response
│   ├── api/
│   │   ├── main.py                  # FastAPI app
│   │   └── routes/                  # Workflow & review endpoints
│   ├── frontend/
│   │   └── app.py                   # Streamlit dashboard
│   └── utils/
│       ├── logger.py                # Logging setup
│       └── exceptions.py            # Custom exceptions
├── config/
│   └── workflow.json                 # Workflow configuration
├── data/sample_invoices/             # Sample test data
├── scripts/
│   ├── setup_db.py                   # Database initialization
│   └── run_demo.py                   # Demo script
├── pyproject.toml                    # Dependencies (uv)
└── README.md                         # This file
```

---

## 🚀 **Getting Started**

### **Prerequisites**

- Python 3.11+
- `uv` package manager ([astral.sh/uv](https://astral.sh/uv))

### **Installation**

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd Invoice-Processing-Agent
   ```

2. **Create virtual environment**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Setup environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Update `.env` with your API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

5. **Initialize database**:
   ```bash
   python scripts/setup_db.py
   ```

---

## 💻 **Usage**

### **Option 1: Run with Docker (Recommended)**

```bash
docker-compose up --build
```

- **API**: http://localhost:8000
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

### **Option 2: Run Locally**

**Terminal 1 - API Server**:
```bash
uvicorn invoice_agent.api.main:app --reload
```

**Terminal 2 - Streamlit Dashboard**:
```bash
streamlit run src/invoice_agent/frontend/app.py
```

---

## 🧪 **Running the Demo**

```bash
python scripts/run_demo.py
```

This will process 3 sample invoices:
1. **Perfect Match** → Auto-completes
2. **Match Failure** → Creates HITL checkpoint
3. **New Vendor** → Enrichment + completion

---

## 🔌 **API Endpoints**

### **Workflow Management**

**Start Workflow**:
```bash
POST /workflow/start
Content-Type: application/json

{
  "invoice_payload": {
    "invoice_id": "INV-001",
    "vendor_name": "ACME Corp",
    "amount": 2000.00,
    ...
  }
}
```

**Response**:
```json
{
  "workflow_id": "uuid",
  "status": "RUNNING",
  "current_stage": "MATCH_TWO_WAY",
  "checkpoint_id": "CKPT-xxxx",
  "review_url": "http://localhost:8501/review/CKPT-xxxx"
}
```

### **Human Review**

**List Pending Reviews**:
```bash
GET /human-review/pending
```

**Submit Decision**:
```bash
POST /human-review/decision
Content-Type: application/json

{
  "checkpoint_id": "CKPT-xxxx",
  "decision": "ACCEPT",
  "reviewer_id": "reviewer_001",
  "notes": "Approved after verification"
}
```

---

## 📊 **Bigtool Capabilities**

The Bigtool system dynamically selects tools from pools:

- **OCR**: Tesseract (mock Google Vision, AWS Textract available)
- **Enrichment**: Vendor DB (mock Clearbit, PDL available)
- **ERP Connector**: Mock ERP (SAP, NetSuite stubs available)
- **Email**: Mock Email (SendGrid, SES stubs available)
- **Storage**: Local filesystem (S3, GCS stubs available)

---

## 🗄️ **Database Schema**

**Tables**:
- `checkpoints`: Workflow state snapshots
- `human_review_queue`: Pending HITL items
- `audit_logs`: Complete workflow audit trail

## 🙏 **Acknowledgments**

Built for Analytos.ai coding task using:
- LangGraph by Langchain
- FastAPI
- Streamlit
- SQLAlchemy
- Google Gemini & Groq

---

**🔥 Ready to process invoices intelligently with human oversight!**