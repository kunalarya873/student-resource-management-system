#!/usr/bin/env python3
"""
Antigravity PostToolUse Quality & Audit Hook
Runs after tool execution (file modifications or test runs) to track mutations
and log activity to .agents/logs/audit.log.
"""

import json
import sys
import time
from pathlib import Path


def main():
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}

        log_dir = Path(__file__).resolve().parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "audit.log"

        step_idx = payload.get("stepIdx", "unknown")
        conv_id = payload.get("conversationId", "unknown")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(
                f"[{timestamp}] Conversation: {conv_id} | Step: {step_idx} | Tool executed successfully.\n"
            )

        # PostToolUse contract expects an empty JSON object {}
        print(json.dumps({}))
    except Exception:
        print(json.dumps({}))


if __name__ == "__main__":
    main()
