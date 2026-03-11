# ArcVault AI Intake & Triage Pipeline

This repository is organized as a reviewer guide for the deliverables requested in `AI_Engineer_Technical_Intermediate-Senior.docx`. It contains the working n8n workflow export, prompt documentation, architecture write-up, structured output examples, screenshots, and a demo video for the ArcVault AI-powered intake and triage pipeline assessment.

## Quick Review Links

- Assessment brief: `AI_Engineer_Technical_Intermediate-Senior.docx`
- Demo video: [Loom walkthrough](https://www.loom.com/share/23ad722fd454492a9121ae79abfef391)
- Workflow export: `n8n_workflow.json`
- Structured outputs: `structured_output.json`
- Prompt documentation: `docs/prompt_documentation.md`
- Architecture write-up: `docs/architecture_writeup.md`
- Test runner: `scripts/send_test_requests.py`
- Environment template: `.env.example`

## Deliverables Map

### 1. Working Workflow

The assignment asks for a working end-to-end workflow and a way to review it in action.

- The complete n8n workflow export is in `n8n_workflow.json`.
- The end-to-end walkthrough video is here: [Loom walkthrough](https://www.loom.com/share/23ad722fd454492a9121ae79abfef391).
- Supporting screenshots are included in `screenshots/`:
  - `screenshots/n8n_workflow.png`
  - `screenshots/normal_queue.png`
  - `screenshots/escalation_queue.png`

### 2. Structured Output File

The structured output deliverable is included in `structured_output.json`.

- It contains the required output fields from the brief:
  - `category`
  - `priority`
  - `confidence_score`
  - `core_issue`
  - `extracted_entities`
  - `urgency_signal`
  - `destination_queue`
  - `escalation_flag`
  - `escalation_reason`
  - `human_summary`
- The file includes the five required sample inputs from the assessment and additional test cases used to pressure-test routing and escalation behavior.

### 3. Prompt Documentation

The prompt documentation requested in the brief is in `docs/prompt_documentation.md`.

- It includes the full LLM prompt used in the `AI Triage` step.
- It explains why the prompt was structured that way.
- It documents tradeoffs made for reliability, schema consistency, and routing alignment.
- It notes what would be improved with more time.

### 4. Architecture Write-Up

The architecture write-up requested in the brief is in `docs/architecture_writeup.md`.

It covers:

- system design and component flow
- where state is held
- routing logic and queue mapping
- escalation logic and fallback behavior
- production-scale improvements for reliability, latency, and cost
- a Phase 2 extension plan

## What The Workflow Does

The pipeline is designed around the six required workflow stages from the assessment:

1. Ingest an inbound support request through an n8n webhook.
2. Classify the message with an LLM into one of the required support categories.
3. Enrich the message with extracted entities, a core issue, urgency, and a human summary.
4. Route the request to a destination queue using deterministic logic.
5. Persist a structured JSON record for downstream use.
6. Escalate low-confidence or high-risk cases to a dedicated escalation queue.

## Assessment Requirement Coverage

Below is a direct mapping from the assignment brief to the repository artifacts.

| Assessment requirement | Repo artifact |
| --- | --- |
| Working workflow | `n8n_workflow.json` |
| Demo / walkthrough | [Loom walkthrough](https://www.loom.com/share/23ad722fd454492a9121ae79abfef391) |
| Screenshots of workflow / outputs | `screenshots/n8n_workflow.png`, `screenshots/normal_queue.png`, `screenshots/escalation_queue.png` |
| Structured output records | `structured_output.json` |
| LLM prompt(s) and explanation | `docs/prompt_documentation.md` |
| Architecture write-up | `docs/architecture_writeup.md` |
| Original assignment brief | `AI_Engineer_Technical_Intermediate-Senior.docx` |

## Repository Guide

### Core Files

- `n8n_workflow.json`: exported workflow containing ingestion, AI triage, validation, routing, escalation, persistence, and webhook response steps
- `structured_output.json`: saved example output records from processed requests
- `scripts/send_test_requests.py`: helper script that sends the assessment inputs and extra test cases to the webhook and rewrites `structured_output.json`

### Documentation

- `docs/prompt_documentation.md`: prompt text plus rationale and tradeoffs
- `docs/architecture_writeup.md`: system design, routing, escalation, and production-thinking write-up

### Visual Assets

- `screenshots/n8n_workflow.png`: workflow overview
- `screenshots/normal_queue.png`: standard processed-request output view
- `screenshots/escalation_queue.png`: escalated-request output view

## How To Review This Submission

For the fastest review path:

1. Watch the [Loom walkthrough](https://www.loom.com/share/23ad722fd454492a9121ae79abfef391).
2. Open `n8n_workflow.json` to inspect the workflow implementation.
3. Review `structured_output.json` to see the generated records.
4. Read `docs/prompt_documentation.md` for the LLM prompt and reasoning.
5. Read `docs/architecture_writeup.md` for the design and tradeoff discussion.
6. Open the files in `screenshots/` for quick visual confirmation of the workflow and outputs.

## Notes

- The scenario, company, and customer requests are synthetic and were provided as part of the technical assessment.
- The routing and escalation behavior intentionally combine LLM output with deterministic rules to keep the workflow auditable and safer for downstream operational use.
- Sensitive values are not hardcoded in the workflow documentation; environment setup is documented in `.env.example`.
