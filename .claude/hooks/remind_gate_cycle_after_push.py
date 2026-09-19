"""PostToolUse reminder: after `git push` to this repo, the local runtime
candidate_sha immediately falls behind HEAD until the supervisor is
restarted, and Progress Truth correctly (by design) goes FAIL_CLOSED until
it is. This session hit that exact confusion twice in one day -- pushed a
commit, checked /progress in the browser, and got a false "it's broken"
signal that was actually just a stale runtime pointing at the previous
commit. This hook makes the required next step impossible to forget instead
of relying on memory.
"""
import json
import re
import sys

PUSH_PATTERN = re.compile(r"\bgit\s+push\b")


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    command = str(payload.get("tool_input", {}).get("command", ""))
    if PUSH_PATTERN.search(command):
        sys.stderr.write(
            "REMINDER: a `git push` just happened. The running local "
            "supervisor still has the PREVIOUS commit's candidate_sha, so "
            "/api/v1/progress and /progress will correctly (by design) show "
            "FAIL_CLOSED / mismatched-with-source until it is restarted. "
            "Run `scripts/aeris-gate-cycle.ps1` now to realign before "
            "checking or reporting progress -- do not interpret a stale "
            "runtime as a regression.\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
