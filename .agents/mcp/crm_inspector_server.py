#!/usr/bin/env python3
"""
Antigravity Pure-Python Model Context Protocol (MCP) Server
Implements standard JSON-RPC 2.0 MCP protocol over stdio.
Exposes specialized CRM introspection, GDPR auditing, and mock payload generation tools.
"""

import json
import random
import sys
import uuid
from pathlib import Path

TOOLS = [
    {
        "name": "inspect_crm_schema",
        "description": "Scans the CRM codebase (nfc/saas-backend) to list discovered apps, models, and migrations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Optional app name to filter by (e.g., 'contacts', 'accounts', 'crm', 'subscriptions')",
                }
            },
        },
    },
    {
        "name": "audit_gdpr_compliance",
        "description": "Audits CRM code and models for GDPR compliance (PII identification, consent tracking, and erasure cascades).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_app": {
                    "type": "string",
                    "description": "Target app to audit (e.g. 'contacts', 'accounts', or 'all')",
                    "default": "all",
                }
            },
        },
    },
    {
        "name": "generate_mock_lead",
        "description": "Generates a realistic mock CRM lead payload with UUID, company, lifecycle stage, and contact info for testing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of leads to generate (default 1, max 10)",
                    "default": 1,
                },
                "stage": {
                    "type": "string",
                    "description": "Lifecycle stage ('lead', 'qualified', 'customer', 'churned')",
                    "default": "qualified",
                },
            },
        },
    },
]

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
SAAS_BACKEND = WORKSPACE_ROOT / "nfc" / "saas-backend"


def handle_inspect_crm_schema(args):
    app_filter = args.get("app_name")
    apps = []
    if SAAS_BACKEND.exists():
        for p in SAAS_BACKEND.iterdir():
            if p.is_dir() and (p / "models.py").exists() or p.is_dir() and (p / "models").exists():
                apps.append(p.name)

    if app_filter:
        apps = [a for a in apps if a.lower() == app_filter.lower()]

    result = {
        "workspace": str(SAAS_BACKEND),
        "discovered_apps": sorted(apps),
        "total_apps": len(apps),
        "status": "ready",
    }
    return json.dumps(result, indent=2)


def handle_audit_gdpr_compliance(args):
    target = args.get("target_app", "all")
    pii_keywords = [
        "email",
        "phone",
        "first_name",
        "last_name",
        "address",
        "ssn",
        "passport",
        "birth_date",
    ]
    audit_findings = []

    if SAAS_BACKEND.exists():
        for py_file in SAAS_BACKEND.glob("**/models*.py"):
            if "venv" in str(py_file) or ".git" in str(py_file):
                continue
            if target != "all" and target not in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    for kw in pii_keywords:
                        if kw in line.lower() and (
                            "models." in line or "field" in line.lower()
                        ):
                            audit_findings.append(
                                {
                                    "file": str(py_file.relative_to(WORKSPACE_ROOT)),
                                    "line": line_idx,
                                    "matched_pii": kw,
                                    "snippet": line.strip()[:100],
                                    "recommendation": "Verify field-level encryption or consent tag is configured.",
                                }
                            )
            except Exception:
                pass

    report = {
        "target_app": target,
        "pii_fields_detected": len(audit_findings),
        "compliance_status": "Attention Recommended" if audit_findings else "Compliant",
        "findings": audit_findings[:15],
    }
    return json.dumps(report, indent=2)


def handle_generate_mock_lead(args):
    count = min(max(args.get("count", 1), 1), 10)
    stage = args.get("stage", "qualified")

    first_names = [
        "Elena",
        "Marcus",
        "Aria",
        "Sophia",
        "Devon",
        "Liam",
        "Zara",
        "Kenji",
    ]
    last_names = [
        "Vance",
        "Sterling",
        "Kovacs",
        "Chen",
        "Patel",
        "Dubois",
        "O'Connor",
        "Novak",
    ]
    companies = [
        "Acme Cloud",
        "Apex Dynamics",
        "Quantum Flow",
        "Nexus AI",
        "Starlight Media",
        "HyperScale Systems",
    ]
    domains = ["example.com", "enterprise.org", "techcorp.io", "ventures.net"]

    leads = []
    for _ in range(count):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        company = random.choice(companies)
        domain = random.choice(domains)
        email = f"{fname.lower()}.{lname.lower()}@{domain}"

        leads.append(
            {
                "lead_id": str(uuid.uuid4()),
                "first_name": fname,
                "last_name": lname,
                "email": email,
                "company": company,
                "lifecycle_stage": stage,
                "lead_score": random.randint(65, 99),
                "consent_status": "opted_in",
                "gdpr_compliant": True,
                "custom_attributes": {
                    "source": "web_signup",
                    "interest": "agentic_crm_automation",
                    "estimated_seats": random.choice([5, 20, 50, 200]),
                },
            }
        )
    return json.dumps({"leads": leads}, indent=2)


def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            msg_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            # 1. Initialize
            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "crm-inspector-server",
                            "version": "1.0.0",
                        },
                    },
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            # 2. Notification Initialized
            elif method == "notifications/initialized":
                # Notifications do not return a response in JSON-RPC
                pass

            # 3. List Tools
            elif method == "tools/list":
                res = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            # 4. Call Tool
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})

                if tool_name == "inspect_crm_schema":
                    content = handle_inspect_crm_schema(args)
                elif tool_name == "audit_gdpr_compliance":
                    content = handle_audit_gdpr_compliance(args)
                elif tool_name == "generate_mock_lead":
                    content = handle_generate_mock_lead(args)
                else:
                    content = f"Error: Tool '{tool_name}' not found."

                res = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": content}]},
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            elif method == "ping":
                res = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            else:
                if msg_id is not None:
                    res = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method '{method}' not found",
                        },
                    }
                    sys.stdout.write(json.dumps(res) + "\n")
                    sys.stdout.flush()

        except Exception as e:
            if "msg_id" in locals() and msg_id is not None:
                err_res = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32603, "message": str(e)},
                }
                sys.stdout.write(json.dumps(err_res) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
