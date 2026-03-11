# ArcVault AI-Powered Intake & Triage Pipeline

An end-to-end AI automation workflow that processes unstructured customer support requests, classifies them using GPT-5.4, enriches them with structured metadata, and routes them to the correct operational queue — with automatic escalation for low-confidence or high-risk items.

Built with **n8n** (workflow orchestration), **OpenAI GPT-5.4** (classification & enrichment), and **Google Sheets** (structured output).

---

## Quick Start

### Prerequisites

- **Node.js** v18+ (for n8n) or **Docker**
- **Python** 3.9+ (for test script)
- **OpenAI API key** with access to `gpt-5.4`
- **Google Cloud** service account or OAuth2 credentials for Sheets API

### 1. Clone & Configure

```bash
git clone <repo-url>
cd Aspire
cp .env.example .env
# Edit .env with your actual API keys
```

### 2. Start n8n

**Option A — npx (quickest):**
```bash
npx n8n
```

**Option B — Docker:**
```bash
docker run -it --rm -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
```

n8n will be available at `http://localhost:5678`.

### 3. Import the Workflow

1. Open n8n at `http://localhost:5678`
2. Go to **Workflows** → **Import from File**
3. Select `n8n_workflow.json` from this repo
4. Configure credentials:
   - **OpenAI**: Add your API key in n8n credentials
   - **Google Sheets**: Add OAuth2 or Service Account credentials

### 4. Set Up Google Sheets

Create a Google Sheet with two tabs:

| Tab Name | Purpose |
|---|---|
| **Processed Requests** | Standard routed items |
| **Escalation Queue** | Low-confidence / high-risk items for human review |

Both tabs should have these column headers (Row 1):

```
ID | Source | Category | Priority | Confidence Score | Core Issue | Extracted Entities | Urgency Signal | Destination Queue | Escalation Flag | Escalation Reason | Human Summary | Raw Message | Timestamp
```

### 5. Run Test Requests

```bash
cd scripts
pip install -r requirements.txt
python send_test_requests.py
```

---

## Model Switching

The workflow supports multiple LLM providers. To switch models, update the **model configuration** in the OpenAI node or use the environment variables:

| Provider | Model Name | Use Case |
|---|---|---|
| OpenAI | `gpt-5.4` | Default — best structured output quality |
| OpenAI | `gpt-4o` | Cost-effective alternative |
| DeepSeek | `deepseek-chat` | Budget-friendly, good general performance |
| DeepSeek | `deepseek-reasoner` | Enhanced reasoning for complex triage |

---

## Workflow Architecture

```
Webhook/Form Trigger
        ↓
  Normalize Input (Set Node)
        ↓
  OpenAI Classification + Enrichment (Single LLM Call)
        ↓
  Schema Validation (Code Node)
        ↓
  Routing Logic (Code Node)
        ↓
  Escalation Check (Code Node)
       ↓                ↓
  [Normal]          [Escalated]
       ↓                ↓
  Google Sheets:    Google Sheets:
  Processed         Escalation
  Requests          Queue
       ↓                ↓
       └──── Finalize ──┘
```

---

## Project Structure

```
Aspire/
├── README.md
├── .gitignore
├── .env.example
├── n8n_workflow.json          # Importable n8n workflow
├── structured_output.json     # Final output for all 5 test cases
├── scripts/
│   ├── send_test_requests.py  # Python script to fire test requests
│   └── requirements.txt
├── docs/
│   ├── prompt_documentation.md
│   └── architecture_writeup.md
└── screenshots/               # Workflow & output screenshots
```

---

## Test Cases

| # | Source | Scenario | Expected Category | Expected Priority | Expected Queue |
|---|---|---|---|---|---|
| 1 | Email | 403 login error after update | Bug Report | High | Engineering |
| 2 | Web Form | Bulk export feature for audit logs | Feature Request | Low/Medium | Product |
| 3 | Support Portal | Invoice overcharge $1,240 vs $980 | Billing Issue | High | Billing |
| 4 | Email | SSO setup with Okta | Technical Question | Medium | IT/Security |
| 5 | Web Form | Dashboard down for multiple users | Incident/Outage | High | Escalation Queue |

---

## Key Design Decisions

1. **Single LLM call** — Classification, enrichment, confidence scoring, and summary combined into one structured response for reduced latency and better consistency.
2. **GPT-5.4** — Chosen for reliable structured JSON output and strong general reasoning.
3. **Deterministic routing** — Queue assignment handled in JavaScript code nodes, not by the LLM, for transparency and debuggability.
4. **Schema validation before routing** — LLM outputs are validated before being trusted, with invalid responses routed to human review.
5. **Rule-based escalation with AI classification** — Combines model flexibility with explainable operational guardrails.

---

## Documentation

- [Prompt Documentation](docs/prompt_documentation.md)
- [Architecture Write-Up](docs/architecture_writeup.md)
