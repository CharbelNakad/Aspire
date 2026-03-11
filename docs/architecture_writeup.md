# Architecture Write-Up

## Overview

The ArcVault AI Intake & Triage Pipeline is designed as a lightweight event-driven workflow in n8n that accepts inbound support requests, classifies them with an LLM, applies deterministic routing and escalation logic, and returns a normalized structured record for downstream handling. The system is triggered by an HTTP webhook, which receives a support payload containing a request ID, source channel, and raw customer message. From there, the workflow normalizes the request into a consistent internal format, sends it to a single AI triage step for classification and enrichment, validates the AI output against an expected schema, applies deterministic queue routing rules, checks whether the case should be escalated for human review, writes the result to Google Sheets for persistence, and returns the final JSON response to the caller.

The design is intentionally simple because the assignment emphasizes clarity of reasoning and end-to-end operability over building a large platform. State is held in two places. First, the workflow execution itself carries transient state between nodes, including the normalized request, model output, and routing metadata. Second, durable state is stored in Google Sheets, split into a general processed-requests log and a dedicated escalation queue. This gives the pipeline a clear audit trail without requiring a heavier database or ticketing integration for the assessment.

## System Design

The workflow starts with a webhook trigger, which acts as the entry point for any inbound support request. A normalization step immediately reshapes the raw input into a consistent internal schema with `request_id`, `source`, `raw_message`, and a generated timestamp. That normalization step is important because it isolates downstream logic from channel-specific input differences and makes the rest of the workflow easier to reason about.

After normalization, the request is sent to a single LLM step called **AI Triage**. This model is responsible for four tasks at once: classification, priority assessment, entity extraction, and summary generation. The LLM returns a strict JSON object containing the category, priority, confidence score, core issue, extracted entities, urgency signal, and a short human-readable summary. The reason for keeping these tasks in one model call is efficiency. For a bounded schema like this one, a single-step generation approach is both fast and reliable, especially when using capable reasoning-oriented models such as GPT-5-class models. In this workflow, the prompt is narrow, the output schema is small, and the request messages are short, so the token footprint stays low and a smaller model such as `gpt-5-mini` is sufficient.

From a systems perspective, single-step generation reduces orchestration complexity, lowers latency, and avoids inconsistencies that can appear when multiple model calls independently classify, extract, and summarize the same text. If this were built around extremely cheap models with weaker schema discipline, a multi-step design could be justified: for example, one step for classification, one for schema-constrained extraction, and optionally a second model acting as a judge to verify that the classification is reasonable before routing. However, for this assessment that would add complexity without enough benefit. Because the input is short, the schema is simple, and the output is validated deterministically afterward, a single LLM call with `gpt-5-mini` is the most practical design.

After the LLM step, the workflow runs a schema validation node. This node attempts to parse the model response as JSON and checks whether required fields are present and valid. If the model output is malformed, missing required values, or uses invalid enum values, the request is immediately flagged for escalation and routed to the escalation queue. This validation layer is an important safety mechanism because it ensures the workflow never silently trusts invalid model output.

Once the result is validated, the workflow applies deterministic routing logic. Routing is intentionally not left entirely to the model. Instead, the workflow maps categories to queues in code so that operational ownership remains predictable. After routing, an escalation check examines the request for conditions that require human attention, such as outages or low-confidence model decisions. Finally, the workflow writes the resulting record to Google Sheets and responds with a finalized structured JSON object.

## Routing Logic

The routing logic is category-first and deterministic. Each valid category is mapped to a destination queue:

- **Bug Report** → Engineering
- **Feature Request** → Product
- **Billing Issue** → Billing
- **Technical Question** → General Support
- **Incident/Outage** → Engineering as nominal owner

I chose this mapping because it reflects the most likely operational owner for each class of request. Engineering owns defects and system behavior problems. Product owns requests for new features or enhancements. Billing owns invoice and charge discrepancies. General Support acts as the default operational team for implementation questions, setup help, and lower-risk troubleshooting.

There is also an override for security- or authentication-related technical questions. If a request is classified as a **Technical Question** but contains keywords such as `SSO`, `Okta`, `SAML`, `OAuth`, `MFA`, or similar access-control language, the destination queue is changed from General Support to **IT/Security**. This rule exists because authentication and identity-provider questions often require a different operational owner than general product support, even when they are not incidents.

I intentionally kept routing deterministic after classification rather than letting the LLM directly select a queue. That tradeoff gives less flexibility, but it makes the system easier to audit and safer to operate. The LLM determines the semantic class of the request; the workflow code determines queue ownership. That separation makes it easier to update routing policy without changing the prompt.

## Escalation Logic

The escalation logic is designed to identify requests that require prompt human review or extra operational caution. A case is escalated if any of the following conditions are true:

1. **Schema validation fails**: If the LLM output cannot be parsed or does not conform to the required schema, the request is escalated immediately.
2. **Low confidence**: If the model confidence score is below `0.70`, the case is considered ambiguous and escalated for manual review.
3. **Incident/Outage classification**: Any request classified as an outage is escalated because service disruption and multi-user impact should receive immediate human attention.
4. **Outage indicators in text**: Even if the model classification were imperfect, keyword checks such as `multiple users affected`, `service down`, or `stopped loading` add another safeguard for operationally urgent issues.
5. **Large billing discrepancy**: Billing cases with a discrepancy above a defined threshold are escalated because they may represent higher-risk revenue or contract issues.

The core design principle here is that escalation logic should be conservative in the face of operational risk. I did not want the pipeline to over-trust model output for cases involving outages, access issues, or ambiguous intent. At the same time, I avoided escalating everything by default, because a triage pipeline should reduce manual load, not simply re-label all requests for humans. The current rules are a middle ground: ordinary requests stay with their functional owner, while ambiguous or high-impact cases are promoted to an escalation queue.

## Production-Scale Changes

At production scale, I would keep the general architecture but replace several assessment-oriented components with more robust infrastructure. Google Sheets is a convenient persistence layer for a take-home exercise, but in production I would write records to a database and/or a ticketing system such as Jira, Zendesk, Linear, or ServiceNow. I would also introduce retries, dead-letter queues, structured application logging, metrics, and alerting around webhook failures, LLM timeouts, schema-validation failures, and downstream write errors.

For reliability, I would make the workflow idempotent using request IDs so duplicate webhook deliveries do not create duplicate triage records. I would also separate synchronous and asynchronous paths. The webhook could return quickly with an accepted status while background workers handle enrichment, routing, and downstream integrations, which would improve resilience under load.

For cost and latency, I would continue using a single-step generation design for the first pass because the schema is small and the input messages are short. That keeps both token usage and orchestration overhead low. If traffic scaled significantly, I would add prompt caching, model selection tiers, and perhaps a fast-path rules engine for very obvious cases before invoking the LLM. I would also benchmark whether even smaller or cheaper models can meet quality targets on this narrow schema. If they cannot, I would rather keep one strong, inexpensive model call than introduce a fragile multi-step chain that is harder to maintain.

Another production improvement would be stronger structured-output enforcement. Depending on model and platform support, I would move from prompt-only JSON instructions to native structured outputs or JSON Schema validation at the model interface. That would reduce parsing errors and make downstream automation more reliable.

## Phase 2: What I Would Build with Another Week

If I had another week, I would extend the system from triage into the first stage of assisted resolution. The most valuable Phase 2 addition would be an engineering-agent workflow for bug handling. After a request is classified as a bug or incident and enough context is available, an internal software-engineering agent could read the codebase and relevant documentation, generate a technical diagnosis, propose a remediation plan, and prepare implementation artifacts for a human engineer.

I would structure this as a supervised multi-agent workflow rather than a fully autonomous coding loop. A **solution-analysis agent** would first inspect the issue, summarize probable root causes, and identify the subsystems most likely involved. That agent could then call focused sub-agents for narrower tasks: one for code investigation, one for implementation drafting, one for test generation, and one for regression-risk review. The output would not go directly to production. Instead, it would produce a draft branch or PR, along with a clear explanation of the proposed change, impacted files, assumptions, and tests.

A code-review agent such as CodeRabbit or a similar review layer could then evaluate the generated changes for correctness, style, and risk before handing the work off for human review and manual validation. The goal would not be to remove engineers from the loop, but to reduce time-to-diagnosis and accelerate repetitive implementation work. Human approval, manual testing, and automated CI would remain required before any merge.

Beyond engineering automation, I would also add three practical Phase 2 improvements. First, I would integrate the triage output into a real ticketing system so queue ownership, SLAs, and status transitions are tracked in one place. Second, I would create an evaluation harness with labeled historical examples to measure classification accuracy, routing correctness, and escalation precision over time. Third, I would add an operations dashboard showing request volumes, top categories, escalation rates, and model confidence trends so the workflow can be monitored and tuned continuously.

## Conclusion

This architecture intentionally balances LLM flexibility with deterministic operational safeguards. The LLM is used where it adds the most value — understanding messy customer language and producing structured triage data — while code-based validation, routing, and escalation preserve reliability and auditability. For the scope of this assessment, a single-step AI triage design is the right tradeoff: it is simple, efficient, and strong enough for a small schema using a cost-effective model such as `gpt-5-mini`. With more time, the same foundation could evolve into a more production-ready support-operations platform and, eventually, into a supervised engineering-assistance system that helps move issues from triage toward resolution.