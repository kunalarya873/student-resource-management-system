# Plugin Rule: CRM Webhook Integrations & Resiliency

When implementing or modifying CRM webhooks (HubSpot, Salesforce, Stripe, custom inbound webhooks):

## 1. Signature Verification
* **HMAC Validation**: Always verify webhook signatures (e.g., `X-HubSpot-Signature-v3` or `Stripe-Signature`) using constant-time comparison (`hmac.compare_digest`) before reading payload contents.
* Reject expired timestamps (>300 seconds delta) to prevent replay attacks.

## 2. Asynchronous Queue Handoff
* Never execute long-running database mutations directly inside synchronous webhook view endpoints.
* Acknowledge receipt with HTTP 200/202 within <500ms and dispatch the processing payload into a background queue (Celery/BullMQ/Convex actions).

## 3. Idempotency Safeguards
* Check the inbound event ID (`X-Event-ID` or `webhook_id`) in an idempotency table before processing.
* If already processed or in-flight, return the recorded response and skip duplicate execution.
