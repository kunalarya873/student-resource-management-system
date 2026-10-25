# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

---

## 🔒 Security Architecture & Guardrails

The AMU Student Resource Management System implements multi-layered security controls:

1. **Authentication & Password Protection:**
   - Passwords hashed using Bcrypt with 12 salt rounds.
   - OTP codes hashed using SHA-256 with constant-time verification.
   - Dummy password verification executed on failed lookups to prevent user enumeration and timing attacks.
   - Maximum 5 attempts per OTP with exponential backoff / rate limit cooldowns.

2. **Access Control (RBAC):**
   - Strictly enforced Role-Based Access Control (`Administrator`, `Teacher`, `Student`).
   - Cross-tenant folder and resource isolation preventing unauthorized reading or mutation.

3. **Storage Security:**
   - File uploads partitioned by user ID (`users/{user_id}/...`) to ensure data segregation.
   - Time-bounded signed URLs for secure, authenticated file downloads.
   - Webhook validation using cryptographic HMAC secrets.

4. **Data Protection & GDPR:**
   - PII data isolation.
   - Right-to-be-Forgotten deletion cascades on user account termination.

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability within this repository, please do **NOT** open a public issue.

Instead, please send an email to the security response team at **kunalarya873@gmail.com**. Please include:
- A description of the issue and potential impact
- Detailed reproduction steps or Proof of Concept (PoC)
- Suggested remediations if available

We will acknowledge receipt within 48 hours and work towards a swift remediation and coordinated disclosure.
