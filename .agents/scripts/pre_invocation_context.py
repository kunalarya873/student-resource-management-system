#!/usr/bin/env python3
"""
Antigravity PreInvocation Sentinel Hook
Injects dynamic environment context, active workspace branch, and architectural reminders
before the model plans or acts.
"""

import json
import subprocess
import sys
from pathlib import Path


def get_git_branch():
    try:
        # Check backend repo if available
        backend_dir = (
            Path(__file__).resolve().parent.parent.parent / "nfc" / "saas-backend"
        )
        if (backend_dir / ".git").exists():
            res = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=3,
            )
            branch = res.stdout.strip()
            if branch:
                return f"branch '{branch}' in saas-backend"
    except Exception:
        pass
    return "workspace active"


def main():
    try:
        raw_input = sys.stdin.read()
        _payload = json.loads(raw_input) if raw_input.strip() else {}

        branch_info = get_git_branch()

        reminder = (
            f"⚡ [Antigravity Sentinel Active | {branch_info}]: "
            "Remember: Corex Orchestration active. Enforce GDPR data minimization, "
            "atomic database transactions, strict type safety, and zero-defect edge-case testing."
        )

        response = {"injectSteps": [{"ephemeralMessage": reminder}]}
        print(json.dumps(response))
    except Exception:
        print(json.dumps({"injectSteps": []}))


if __name__ == "__main__":
    main()
