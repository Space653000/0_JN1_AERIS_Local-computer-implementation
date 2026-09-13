"""Claude Code statusLine: show AERIS's live overall_percent/truth_state in
the CLI status bar so progress is visible ambiently without opening a
browser or re-asking Claude. Must never hang or error the status bar --
a short timeout and a graceful fallback are the whole point.
"""
import json
import sys
import urllib.request

TIMEOUT_S = 0.8


def main() -> int:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/api/v1/progress", timeout=TIMEOUT_S) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        state = d.get("truth_state", "UNKNOWN")
        percent = d.get("overall_percent")
        aligned = d.get("runtime_candidate_aligned")
        percent_str = f"{percent}%" if percent is not None else "--%"
        align_str = "" if aligned else " (STALE runtime)"
        print(f"AERIS {percent_str} | {state}{align_str}")
    except Exception:
        print("AERIS: local supervisor not reachable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
