#!/usr/bin/env bash
# SessionStart hook: on the first Claude Code session of the day (at or after
# START_HOUR local time), inject a prompt telling Claude to run the daily
# improvement cycle defined in CLAUDE.md.
#
# Source of truth for "already ran today" is ideas-log.md — the cycle appends a
# dated entry as its final step. No separate state file to drift.
#
# To change the earliest firing hour, edit START_HOUR. Set it to 0 to fire on
# the first session of the day regardless of time.

set -uo pipefail

START_HOUR=9

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
LOG="$ROOT/ideas-log.md"
TODAY="$(date +%Y-%m-%d)"
HOUR="$(date +%-H)"

# Too early in the day — a later session will pick it up.
[ "$HOUR" -lt "$START_HOUR" ] && exit 0

# Today's cycle already logged.
[ -f "$LOG" ] && grep -q "$TODAY" "$LOG" && exit 0

read -r -d '' CONTEXT <<EOF || true
Today is $TODAY and no entry for today exists in ideas-log.md, so today's
improvement cycle for the India PM Foreign Visits Tracker has not run yet.

Run it now, following the daily cycle in CLAUDE.md end to end: read
ideas-log.md, pull current repo and site state, brainstorm 5-7 candidate ideas
across different dimensions, converge on exactly one, implement it, verify the
definition of done, commit and push, append the log entry, and close with an
outcome-first summary.

Respect every guardrail in CLAUDE.md, especially: no change to the non-partisan
framing, no change to the data-provenance pipeline, and all three fallback tiers
preserved.

If the user asked for something else in this session, do their request first and
mention that the daily cycle is still pending.
EOF

jq -nc --arg ctx "$CONTEXT" \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx},
    systemMessage: "Daily improvement cycle has not run today — Claude has been prompted to run it."}'
