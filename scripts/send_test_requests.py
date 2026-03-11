"""
ArcVault AI Triage Pipeline — Test Request Sender
Sends the 5 sample support requests to the n8n webhook endpoint
one at a time with a short delay between requests.
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'https://ferylop.app.n8n.cloud/webhook-test/arcvault-intake')

TEST_REQUESTS = [
    {
        "id": 1,
        "source": "Email",
        "message": (
            "Hi, I tried logging in this morning and keep getting a 403 error. "
            "My account is arcvault.io/user/jsmith. This started after your update last Tuesday."
        )
    },
    {
        "id": 2,
        "source": "Web Form",
        "message": (
            "We'd love to see a bulk export feature for our audit logs. "
            "We're a compliance-heavy org and this would save us hours every month."
        )
    },
    {
        "id": 3,
        "source": "Support Portal",
        "message": (
            "Invoice #8821 shows a charge of $1,240 but our contract rate is $980/month. "
            "Can someone look into this?"
        )
    },
    {
        "id": 4,
        "source": "Email",
        "message": (
            "I'm not sure if this is the right place to ask, but is there a way to set up SSO "
            "with Okta? We're evaluating switching our auth provider."
        )
    },
    {
        "id": 5,
        "source": "Web Form",
        "message": (
            "Your dashboard stopped loading for us around 2pm EST. "
            "Checked our end — it's definitely on yours. Multiple users affected."
        )
    },
]

EXPECTED_OUTPUTS = {
    1: {"category": "Bug Report",          "priority": "High",          "queue": "Engineering"},
    2: {"category": "Feature Request",     "priority": "Low/Medium",    "queue": "Product"},
    3: {"category": "Billing Issue",       "priority": "High",          "queue": "Billing"},
    4: {"category": "Technical Question",  "priority": "Medium",        "queue": "IT/Security"},
    5: {"category": "Incident/Outage",     "priority": "High",          "queue": "Escalation Queue"},
}

DELAY_BETWEEN_REQUESTS = 3


def send_request(payload: dict) -> dict | None:
    """Send a single test request to the webhook."""
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"  [ERROR] Cannot connect to {WEBHOOK_URL}")
        print(f"  Make sure n8n is running and the webhook is active.")
        return None
    except requests.exceptions.Timeout:
        print(f"  [ERROR] Request timed out after 60s")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"  [ERROR] HTTP {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        print(f"  [ERROR] Unexpected error: {e}")
        return None


def validate_response(req_id: int, result: dict) -> None:
    """Compare actual output against expected values."""
    expected = EXPECTED_OUTPUTS.get(req_id, {})
    print(f"  Category:    {result.get('category', 'N/A'):20s} (expected: {expected.get('category', '?')})")
    print(f"  Priority:    {result.get('priority', 'N/A'):20s} (expected: {expected.get('priority', '?')})")
    print(f"  Queue:       {result.get('destination_queue', 'N/A'):20s} (expected: {expected.get('queue', '?')})")
    print(f"  Confidence:  {result.get('confidence_score', 'N/A')}")
    print(f"  Escalated:   {result.get('escalation_flag', 'N/A')}")


def main():
    print("=" * 60)
    print("ArcVault AI Triage Pipeline — Test Runner")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print("=" * 60)

    results = []

    for i, payload in enumerate(TEST_REQUESTS):
        print(f"\n--- Test {payload['id']}/{len(TEST_REQUESTS)}: {payload['source']} ---")
        print(f"  Message: {payload['message'][:80]}...")

        result = send_request(payload)

        if result:
            validate_response(payload['id'], result)
            results.append(result)
        else:
            print("  [SKIPPED] No response received")
            results.append({"error": "No response", "request_id": payload['id']})

        if i < len(TEST_REQUESTS) - 1:
            print(f"\n  Waiting {DELAY_BETWEEN_REQUESTS}s before next request...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    output_path = os.path.join(os.path.dirname(__file__), '..', 'structured_output.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n{'=' * 60}")
    print(f"Done! {len(results)} results saved to structured_output.json")
    print(f"{'=' * 60}")

    return 0 if all('error' not in r for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
