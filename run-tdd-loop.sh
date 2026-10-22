#!/usr/bin/env bash
set -euo pipefail

PROGRESS_FILE="TASK_PROGRESS.md"
TASKS_DIR="tasks"

# Ensure progress file exists
touch "$PROGRESS_FILE"

echo "=== Starting Automated TDD Agent Loop ==="

while true; do
  # Determine if unfinished tasks remain
  TOTAL_TASKS=$(find "$TASKS_DIR" -name "task-0*.md" | wc -l | tr -d ' ')

  PROMPT=$(
    cat <<'EOF'
You are an autonomous executor operating in strict TDD mode.
Inspect `@tasks/task-0*.md` and `TASK_PROGRESS.md` to see which tasks are already completed.

EXECUTION PROTOCOL:
1. Identify the first incomplete ticket in `@tasks/`.
   - If ALL tasks are complete, output exactly `ALL_TASKS_COMPLETED` and stop immediately.
2. Complete up to 2 tickets in strict sequential order:
   - Write failing tests first.
   - Implement the solution until tests pass.
   - Run the full test suite.
   - Commit: `git add -A && git commit -m "[task-id]: [concise summary]"`
   - Append completed task ID and 3 bullets to `TASK_PROGRESS.md`.
3. Stop after finishing at most 2 tickets so the orchestrator can refresh your context.
   - When finished with the batch, output: `BATCH_COMPLETE`
EOF
  )

  echo "Spawning fresh Claude session..."

  # Run Claude Code in print/headless mode with full permissions for tests & git
  # Adjust danger flags as needed for your environment:
  OUTPUT=$(claude -p "$PROMPT" --dangerously-skip-permissions 2>&1 | tee /dev/tty)

  if echo "$OUTPUT" | grep -q "ALL_TASKS_COMPLETED"; then
    echo "=== All tasks in $TASKS_DIR are finished! ==="
    break
  fi

  echo "=== Batch finished. Resetting context and launching next session in 3s... ==="
  sleep 3
done
