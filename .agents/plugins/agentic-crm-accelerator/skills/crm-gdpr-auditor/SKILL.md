---
name: crm-gdpr-auditor
description: Audit CRM models, serializers, and APIs for GDPR compliance, PII field exposure, consent tracking, and Right-to-be-Forgotten deletion cascades.
---

# CRM GDPR Auditor Skill

This skill guides the agent through an automated and manual privacy audit of all data flows within the CRM platform.

## When to Use
* Adding or modifying contact, lead, user, or billing models.
* Reviewing customer data export or deletion API endpoints.
* Preparing for SOC2 or GDPR regulatory compliance verification.

## Procedure

### Step 1: Scan for Personal Data (PII)
Check models and schemas for unencrypted personal identifiers:
* Full name, email addresses, physical addresses.
* Phone numbers, IP addresses, browser user-agents.
* Government or tax identifiers.

### Step 2: Verify Consent Record
Ensure every personal record contains consent metadata:
* `consent_timestamp`: ISO 8601 UTC timestamp.
* `consent_source`: E.g., `web_form`, `api_sync`, `manual_entry`.
* `consent_scope`: Explicit permission flags (e.g. `marketing_emails`, `telephony`).

### Step 3: Verify Erasure Cascade
Audit the deletion handler for Right-to-be-Forgotten:
1. Ensure the user can invoke `DELETE /api/v1/privacy/erasure/`.
2. Confirm related records are either hard-deleted or anonymized:
   ```python
   # Correct Anonymization Pattern
   contact.email = f"anonymized_{contact.id}@deleted.local"
   contact.first_name = "ANONYMIZED"
   contact.last_name = "ANONYMIZED"
   contact.phone_number = None
   contact.save()
   ```
3. Verify that third-party CRM connectors (Salesforce/HubSpot) receive an asynchronous deletion notification.
