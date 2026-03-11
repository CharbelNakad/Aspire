# ArcVault AI Triage Pipeline — Prompt Documentation

## Overview

This document captures the LLM prompt used in the ArcVault AI Intake & Triage Pipeline and explains the reasoning behind how it was structured. In this workflow there is one LLM step: **AI Triage**. The goal of the prompt is to classify inbound support requests, extract useful structured information, assess urgency, and generate a short human-readable summary for downstream routing and review.

## LLM Step 1 — AI Triage

### Prompt

```
You are an AI triage agent for ArcVault, a B2B software company. Your task is to classify, enrich, and summarize inbound customer support requests.

Analyze the support request and return exactly one valid JSON object with the following fields:

- category
- priority
- confidence_score
- core_issue
- extracted_entities
- urgency_signal
- human_summary

Allowed values:

category must be exactly one of:
- "Bug Report"
- "Feature Request"
- "Billing Issue"
- "Technical Question"
- "Incident/Outage"

priority must be exactly one of:
- "Low"
- "Medium"
- "High"

urgency_signal must be exactly one of:
- "Low"
- "Medium"
- "High"

Field requirements:

1. category
Choose the single best category using these rules:
- "Incident/Outage" = service disruption, downtime, severe degradation, dashboard/system unavailable, or multiple users affected
- "Bug Report" = broken or incorrect product behavior, typically limited in scope and not clearly a broad outage
- "Technical Question" = setup, configuration, integration, how-to, troubleshooting question, or clarification request
- "Feature Request" = request for a new capability, enhancement, or improvement
- "Billing Issue" = invoice, charge, refund, pricing, payment, or contract discrepancy

2. priority
- "High" = blocked user, revenue impact, access issue, production issue, or multiple users affected
- "Medium" = non-blocking issue with moderate business impact
- "Low" = informational, low-impact, or nice-to-have request

3. confidence_score
Return a decimal from 0.0 to 1.0:
- 0.90 to 1.00 = category is very clear from explicit evidence
- 0.70 to 0.89 = category is likely but somewhat ambiguous
- below 0.70 = ambiguous, mixed-intent, or insufficient evidence

4. core_issue
One sentence summarizing the main request or problem.

5. extracted_entities
Return an object containing only identifiers explicitly present in the message, such as:
- account_id
- invoice_number
- error_code
- provider
- product_name
- dollar_amounts
- url
- affected_users
- timestamp_reference

Do not invent or infer identifiers that are not directly supported by the message.
If none are present, return {}.

6. urgency_signal
Assess time sensitivity and operational impact:
- "High" for outages, blocked access, revenue/billing risk, or multiple affected users
- "Medium" for meaningful but not critical issues
- "Low" for low-stakes requests or informational questions

7. human_summary
Write 2 to 3 sentences for the receiving team. Include what happened, what the customer needs, and any critical supporting details.

Consistency rules:
- Return only valid JSON. No markdown, no code fences, no commentary.
- Do not add fields outside the required schema.
- Do not fabricate missing information.
- Keep category, priority, and urgency logically consistent.
- If the issue describes downtime or multiple affected users, prefer "Incident/Outage".
- If the issue is clearly a question about setup or integration, prefer "Technical Question".

Source: {{ $json.source }}
Message: {{ $json.raw_message }}
```

### Why I structured it this way

I structured this prompt to be highly constrained because the output is feeding an automation pipeline, not just a chat interface. The most important tradeoff was choosing reliability over flexibility: I used a tight schema, fixed enums, and explicit category definitions so the model would produce predictable output that downstream validation and routing logic could safely consume. I also included confidence scoring and entity extraction in the same step to keep the workflow simple and reduce latency, even though separating classification from extraction could make debugging easier. With more time, I would likely move from prompt-only schema enforcement to native structured output or JSON schema validation at the model layer, add a few-shot section with tricky edge cases like auth questions versus bugs, and tighten some entity definitions so fields like `account_id` and `product_name` are less open to interpretation.

## Design Notes

### Why combine classification, enrichment, and summarization in one step

I combined these tasks into a single LLM call to keep the workflow efficient and easy to reason about. Since the same message content drives category, urgency, summary, and entity extraction, bundling them together reduces orchestration complexity and avoids inconsistent outputs across multiple model calls. The downside is that one model miss can affect several fields at once. With more time, I would test whether splitting the flow into two stages — first classification, then summary/entity extraction — improves consistency enough to justify the added cost and complexity.

### Why the prompt uses explicit decision rules

The prompt includes plain-language rules for category, priority, and urgency so the model behaves more like a deterministic triage layer than a freeform assistant. This was meant to reduce ambiguity in common support cases such as distinguishing a bug from an outage or a technical question from a feature request. The tradeoff is that the rules simplify real-world nuance; some support messages are mixed-intent and do not fit neatly into one class. With more time, I would add clearer guidance for ambiguous cases and include a fallback rule for mixed signals, such as prioritizing customer impact first and using confidence score to trigger manual review.

### Why the prompt forbids fabrication

I explicitly told the model not to invent missing information because fabricated identifiers are dangerous in operational systems. A made-up invoice number, account ID, or provider could cause misrouting or create false confidence for the receiving team. The tradeoff is that the model may sometimes return sparse entity objects, which is less impressive at first glance but safer and more production-appropriate. With more time, I would add more examples of acceptable versus unacceptable extraction so the model is even more conservative and consistent.

### Why the prompt asks for both machine-readable and human-readable output

The workflow needs structured data for routing and escalation, but it also needs a readable summary for the human team receiving the request. That is why the prompt asks for both rigid JSON fields and a short `human_summary`. The tradeoff is that this slightly increases prompt length and gives the model more to do in one pass. I accepted that cost because a good triage system should support both automation and human handoff. With more time, I would experiment with shortening the summary requirement or standardizing its format further so it is easier to scan in a spreadsheet or queue.

## What I would improve next

If I had more time, I would improve this prompt in three ways. First, I would add a small few-shot section with 3 to 5 representative examples, especially edge cases like SSO questions, login failures, and billing discrepancies. Second, I would tighten the entity extraction guidance so recurring fields are normalized more consistently. Third, I would test the prompt against a larger set of adversarial or ambiguous inputs and tune the wording based on actual failure patterns rather than only the provided sample set.

## How I would use LangSmith Playground and Experiments to optimize the prompt

Beyond manual iteration, my next step for improving this prompt would be to use LangSmith Playground and Experiments to systematically evaluate and refine it against real and synthetic support requests.

### Playground for rapid iteration

LangSmith Playground allows me to test prompt variations interactively against individual inputs without redeploying the workflow. I would use it to quickly compare how different phrasings, rule orderings, or few-shot examples affect the model's output for specific edge cases. For example, I could take a message that was previously misclassified as "Bug Report" instead of "Incident/Outage" and iterate on the category decision rules in real time until the output is correct and the reasoning is sound. Playground makes this feedback loop fast because I can adjust the prompt, swap models, and tweak parameters like temperature all in one place without touching the n8n workflow.

### Experiments for structured evaluation at scale

Once I have a candidate prompt from Playground, I would run it through LangSmith Experiments to evaluate it against a curated dataset of test cases. Each test case would include a raw support message and the expected structured output (category, priority, urgency, entities, etc.). Experiments would let me score the prompt across the full dataset using custom evaluators, for example checking whether the predicted category matches the expected category, whether the confidence score falls within a reasonable range, and whether fabricated entities appear in the output. This moves prompt improvement from guesswork to measurable comparison: I can see exactly which cases improved, which regressed, and where the prompt still falls short.

### Building a golden dataset

To support this, I would build a golden dataset of 20 to 50 representative support requests covering all five categories, a range of priorities and urgency levels, and deliberate edge cases like mixed-intent messages, vague descriptions, and messages with no extractable entities. Each entry would have a human-labeled expected output. This dataset becomes the ground truth for every future prompt change, ensuring I never improve one category at the cost of another.

### Iterative workflow

The full loop would look like this:

1. Identify failure patterns from production traces in LangSmith.
2. Reproduce those failures in Playground and iterate on the prompt.
3. Run the updated prompt through Experiments against the golden dataset.
4. Compare metrics across prompt versions to confirm net improvement.
5. Promote the best-performing version back into the n8n workflow.

This approach treats prompt engineering as an empirical process rather than a one-shot design exercise, which is critical for a production triage system where classification accuracy directly affects routing quality and response times.