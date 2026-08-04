#!/usr/bin/env bash
# SessionStart hook: report whether today's improvement cycle has landed in this
# checkout. Purely informational.
#
# The cloud routine "India PM Visits Tracker — daily improvement cycle"
# (trig_01243CJJJ6D8U4yaxFgphCD9) owns the daily run and pushes to main at
# ~03:36 UTC / ~09:06 IST. This hook deliberately does NOT ask Claude to run the
# cycle — that would duplicate the routine's work whenever the local checkout is
# simply behind origin.
#
# Source of truth is ideas-log.md, which the cycle appends to as its final step.

set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
LOG="$ROOT/ideas-log.md"
TODAY="$(date +%Y-%m-%d)"

# Today's entry is already here — nothing worth saying.
[ -f "$LOG" ] && grep -q "$TODAY" "$LOG" && exit 0

jq -nc --arg msg "No ideas-log.md entry for $TODAY in this checkout. The daily routine pushes at ~09:06 IST — run 'git pull' to see it, or ask Claude to run today's cycle if it did not fire." \
  '{systemMessage: $msg}'
