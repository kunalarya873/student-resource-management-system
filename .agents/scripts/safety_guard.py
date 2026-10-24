#!/usr/bin/env python3
"""
Antigravity PreToolUse Safety Guard Hook
Intercepts tool calls before execution to enforce safety boundaries.
Prevents destructive commands (e.g., rm -rf, raw drop database, format disk).
"""

import json
import re
import sys

DANGEROUS_PATTERNS = [
    (
        r"rm\s+(-rf|-fr|-r\s+-f|-f\s+-r)\s+[/~]",
        "Recursive deletion of root or home directory is prohibited.",
    ),
    (r"rm\s+(-rf|-fr)\s+\*", "Blind recursive wildcard deletion is prohibited."),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb detected."),
    (
        r"DROP\s+DATABASE",
        "Direct database drop commands are prohibited. Use migration rollbacks.",
    ),
    (r"mkfs|dd\s+if=", "Low-level disk format operations are strictly forbidden."),
    (
        r"git\s+push\s+.*--force\s+(origin\s+)?(main|master)",
        "Force push to main/master is strictly blocked by safety guard.",
    ),
]


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})

        # Inspect run_command tool calls
        if tool_name == "run_command":
            cmd = args.get("CommandLine", "")
            for pattern, reason in DANGEROUS_PATTERNS:
                if re.search(pattern, cmd, re.IGNORECASE):
                    result = {
                        "decision": "deny",
                        "reason": f"🛡️ [Safety Guard Blocked]: {reason} (Command: '{cmd}')",
                    }
                    print(json.dumps(result))
                    return

        # By default, allow execution safely
        print(json.dumps({"decision": "allow", "reason": "Safety check passed."}))
    except Exception as e:
        # Fallback to allow to avoid breaking workflow on hook error, but report note
        print(
            json.dumps(
                {"decision": "allow", "reason": f"Safety hook warning: {e!s}"}
            )
        )


if __name__ == "__main__":
    main()
