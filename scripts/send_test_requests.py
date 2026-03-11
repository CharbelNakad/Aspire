"""
ArcVault AI Triage Pipeline — Test Request Sender
Sends realistic sample support requests to the n8n webhook endpoint
one at a time with a short delay between requests.
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'https://ferylop.app.n8n.cloud/webhook/arcvault-intake')

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
    {
        "id": 6,
        "source": "Chat",
        "message": (
            "Hey team, I'm the new IT coordinator here and I might be missing something obvious, "
            "but I can't get MFA enrollment to finish for three new hires. It keeps bouncing them "
            "back to the start after they scan the QR code."
        )
    },
    {
        "id": 7,
        "source": "Email",
        "message": (
            "Good afternoon, I'm 72 and not especially technical, so apologies if this is a simple fix. "
            "Since yesterday I haven't been able to download the monthly archive report I normally send to our board. "
            "The button spins for a while and then nothing happens."
        )
    },
    {
        "id": 8,
        "source": "Support Portal",
        "message": (
            "Our finance team noticed we were billed for 42 active seats this month, but we reduced that to 35 in January. "
            "Could you review the account before we close out the quarter? I can send the admin screenshot if helpful."
        )
    },
    {
        "id": 9,
        "source": "Web Form",
        "message": (
            "I'm a college intern helping our compliance manager and I had a feature idea: "
            "it would be really helpful if archived records could be tagged by project code so we can find them faster during audits."
        )
    },
    {
        "id": 10,
        "source": "Phone Transcript",
        "message": (
            "Caller reports that password reset emails are arriving about 25 minutes late. "
            "This is affecting several branch employees who are locked out right before opening and need immediate access to customer files."
        )
    },
    {
        "id": 11,
        "source": "Email",
        "message": (
            "We're in the middle of a security review and need to confirm whether ArcVault supports SCIM provisioning with Microsoft Entra ID. "
            "If it does, is there any setup guide beyond the basic SSO documentation?"
        )
    },
    {
        "id": 12,
        "source": "Chat",
        "message": (
            "Not trying to be dramatic, but the activity feed has been frozen for almost an hour and our ops team uses that screen all day. "
            "New uploads are going through, they just aren't showing up in the timeline unless we hard refresh."
        )
    },
    {
        "id": 13,
        "source": "Support Portal",
        "message": (
            "One of our case managers works part-time and swears she didn't delete anything, "
            "but a client folder appears to be missing two consent forms from last week. "
            "Can someone help us figure out whether they were removed or just not synced?"
        )
    },
    {
        "id": 14,
        "source": "Web Form",
        "message": (
            "I'm 24 and usually use the mobile app more than the desktop site. "
            "After the last iPhone update, uploading photos into a record fails on the second image every time. "
            "The first one works, then the app just sits there."
        )
    },
    {
        "id": 15,
        "source": "Email",
        "message": (
            "Could you please consider adding a read-only auditor role? "
            "Right now we have to choose between giving outside reviewers too much access or sitting with them during every review session."
        )
    },
]

EXPECTED_OUTPUTS = {
    1: {"category": "Bug Report",          "priority": "High",          "queue": "Engineering"},
    2: {"category": "Feature Request",     "priority": "Low/Medium",    "queue": "Product"},
    3: {"category": "Billing Issue",       "priority": "High",          "queue": "Billing"},
    4: {"category": "Technical Question",  "priority": "Medium",        "queue": "IT/Security"},
    5: {"category": "Incident/Outage",     "priority": "High",          "queue": "Escalation Queue"},
    6: {"category": "Bug Report",          "priority": "High",          "queue": "Engineering"},
    7: {"category": "Bug Report",          "priority": "Medium",        "queue": "Engineering"},
    8: {"category": "Billing Issue",       "priority": "High",          "queue": "Billing"},
    9: {"category": "Feature Request",     "priority": "Low/Medium",    "queue": "Product"},
    10: {"category": "Incident/Outage",    "priority": "High",          "queue": "Escalation Queue"},
    11: {"category": "Technical Question", "priority": "Medium",        "queue": "IT/Security"},
    12: {"category": "Incident/Outage",    "priority": "High",          "queue": "Escalation Queue"},
    13: {"category": "Bug Report",         "priority": "High",          "queue": "Engineering"},
    14: {"category": "Bug Report",         "priority": "Medium",        "queue": "Engineering"},
    15: {"category": "Feature Request",    "priority": "Low/Medium",    "queue": "Product"},
}

DELAY_BETWEEN_REQUESTS = 3


def preview_text(text: str, limit: int = 240) -> str:
    """Return a single-line preview of text for console logging."""
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[:limit] + "..."


def normalize_response_body(body: object) -> dict | None:
    """Normalize the webhook payload into a single result object."""
    if isinstance(body, dict):
        return body

    # n8n may return a single-item array from Respond to Webhook.
    if isinstance(body, list):
        if len(body) == 1 and isinstance(body[0], dict):
            return body[0]
        print(f"  [ERROR] Expected one result object, received a list with {len(body)} item(s)")
        return None

    print(f"  [ERROR] Expected a JSON object, received {type(body).__name__}")
    return None


def send_request(payload: dict) -> dict | None:
    """Send a single test request to the webhook."""
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        print(f"  HTTP Status: {response.status_code}")
        response.raise_for_status()

        raw_body = response.text.strip()
        print(f"  Response Body: {preview_text(raw_body) if raw_body else '[empty body]'}")

        if not raw_body:
            print("  [ERROR] Webhook returned an empty response body")
            return None

        try:
            parsed_body = response.json()
        except json.JSONDecodeError as e:
            print(f"  [ERROR] Response was not valid JSON: {e}")
            return None

        print(f"  Parsed JSON Type: {type(parsed_body).__name__}")
        return normalize_response_body(parsed_body)
    except requests.exceptions.ConnectionError:
        print(f"  [ERROR] Cannot connect to {WEBHOOK_URL}")
        print(f"  Make sure n8n is running and the webhook is active.")
        return None
    except requests.exceptions.Timeout:
        print(f"  [ERROR] Request timed out after 60s")
        return None
    except requests.exceptions.HTTPError as e:
        response_text = e.response.text.strip() if e.response is not None else ""
        print(f"  [ERROR] HTTP {e.response.status_code}: {preview_text(response_text) if response_text else '[empty body]'}")
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

        if result is not None:
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
