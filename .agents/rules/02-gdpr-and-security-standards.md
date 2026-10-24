# Rule 02: GDPR Compliance & Security Standards

Every agent operating within this CRM ecosystem must strictly comply with data privacy regulations (GDPR, CCPA) and security hygiene:

## 1. PII & Data Minimization
* **Explicit Consent**: Contacts, leads, and customer profiles must record consent provenance (`consent_given_at`, `consent_source`, `consent_version`).
* **Field Masking & Encryption**: Sensitive personal identifiers (phone numbers, financial details, auth credentials) must be encrypted at rest and masked in logs (`k***@domain.com`).
* **Audit Trail**: Every read, update, or export of customer PII must emit an immutable audit log with actor ID, timestamp, and accessed fields.

## 2. Right-to-be-Forgotten & Erasure Cascades
* Deletion requests must execute a complete erasure cascade:
  1. Anonymize personal identifier columns in transactional tables.
  2. Permanently delete file attachments and cached representations.
  3. Propagate erasure events to external CRM connectors (e.g., Salesforce, HubSpot).
  4. Retain only cryptographically hashed, non-identifiable records if mandated by legal retention policies.

## 3. Secret Management & Authentication
* **Zero Hardcoded Secrets**: Never commit tokens, API keys, private keys, or passwords. Always use environment variables (`django-environ` / secret manager).
* **RBAC / ABAC Enforcement**: Every endpoint must explicitly verify user permissions (`IsAuthenticated`, `HasTenantAccess`, `HasRole('crm_admin')`). Object-level authorization checks are mandatory.
