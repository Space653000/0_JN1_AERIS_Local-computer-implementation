"""PreToolUse guard: refuse Edit/Write/NotebookEdit under protected paths.

.aeris/core-reference/ is a read-only git-worktree mirror of the canonical
Core repo (Space653000/0_JN1_AERIS); writing there breaks
`aeris_runtime core verify` and desyncs from the design authority. This
session already made that mistake once by hand -- this hook makes it
mechanically impossible instead of relying on memory/documentation alone.
"""
import json
import sys

PROTECTED_PREFIXES = (
    ".aeris/core-reference/",
)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    file_path = str(payload.get("tool_input", {}).get("file_path", "")).replace("\\", "/")
    if any(prefix in file_path for prefix in PROTECTED_PREFIXES):
        sys.stderr.write(
            "BLOCKED: " + file_path + " is under a read-only Core-repo mirror "
            "(.aeris/core-reference/). Editing it desyncs the local Core cache "
            "from the canonical design authority and breaks "
            "`aeris_runtime core verify`. If a new Implementation-owned asset "
            "is needed, add it under ui/web/ instead.\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
