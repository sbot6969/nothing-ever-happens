#!/bin/zsh
set -u
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
WS="/Users/sbot/.openclaw/workspace"
REPO="$WS/neh-bot"
DAY="$(date +%Y-%m-%d)"
MEM="$WS/memory/$DAY.md"
LOG="$REPO/tasks/multibot_monitor.log"
SUMMARY="$REPO/tasks/multibot_monitor_summary.txt"
OPENCLAW="${OPENCLAW_BIN:-/opt/homebrew/bin/openclaw}"
TG_CHANNEL="${MULTIBOT_MONITOR_TG_CHANNEL:-telegram}"
TG_TARGET="${MULTIBOT_MONITOR_TG_TARGET:-707939820}"
WAKE_AGENT="${MULTIBOT_MONITOR_WAKE_AGENT:-true}"
mkdir -p "$WS/memory" "$REPO/tasks"

now="$(date '+%Y-%m-%d %H:%M:%S %Z')"
since="$(date -v-30M '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date '+%Y-%m-%d %H:%M:%S')"
main_code="$(curl -sk --max-time 4 -o /dev/null -w '%{http_code}' https://127.0.0.1:8765/ || true)"
whale_https_code="$(curl -sk --max-time 4 -o /dev/null -w '%{http_code}' https://127.0.0.1:8766/ || true)"
whale_http_code="$(curl -s --max-time 4 -o /dev/null -w '%{http_code}' http://127.0.0.1:8766/ || true)"
process_snapshot="$(pgrep -af 'bot\.main|bot\.whale_copy|openclaw agent' || true)"
git_status="$(git -C "$REPO" status --short || true)"
recent_commits="$(git -C "$REPO" --no-pager log --since='30 minutes ago' --oneline --max-count=10 || true)"
agent_rows="$(grep '^|' "$REPO/docs/polymarket_multi_bot/AGENT_REGISTRY.md" 2>/dev/null | grep -v -- '---' | tail -n +2 || true)"
open_todos_count="$(grep -RhcE '^- \[ \]|^- \[blocked\]' "$REPO/docs/polymarket_multi_bot/MASTER_TODO.md" "$REPO/tasks/todo.md" 2>/dev/null | awk '{s+=$1} END{print s+0}')"

{
  echo ""
  echo "## $now — scheduled multi-bot monitor"
  echo ""
  echo "### Voice request revalidation source"
  echo "- $REPO/docs/polymarket_multi_bot/VOICE_REQUEST_2026-05-04.md"
  echo "- $REPO/docs/polymarket_multi_bot/AGENT_FLOW.md"
  echo ""
  echo "### Agent registry snapshot"
  sed -n '1,100p' "$REPO/docs/polymarket_multi_bot/AGENT_REGISTRY.md" 2>/dev/null || true
  echo ""
  echo "### Process status"
  echo "$process_snapshot"
  echo ""
  echo "### Dashboard checks"
  echo "- main https 8765: $main_code"
  echo "- whale https 8766: $whale_https_code"
  echo "- whale http 8766: $whale_http_code"
  echo ""
  echo "### Recent commits in last 30m"
  echo "${recent_commits:-none}"
  echo ""
  echo "### Git status"
  echo "$git_status"
  echo ""
  echo "### Open TODO snapshot"
  grep -nE '^- \[ \]|^- \[blocked\]' "$REPO/docs/polymarket_multi_bot/MASTER_TODO.md" "$REPO/tasks/todo.md" 2>/dev/null | head -80 || true
} >> "$LOG" 2>&1

{
  echo "🤖 Multi-bot monitor — $now"
  echo ""
  echo "За последние 30 минут:"
  if [ -n "$recent_commits" ]; then
    echo "$recent_commits" | sed 's/^/- commit: /'
  else
    echo "- новых git-коммитов нет"
  fi
  echo ""
  echo "Агенты:"
  echo "$agent_rows" | awk -F'|' 'NF>=5 {gsub(/^ +| +$/, "", $2); gsub(/^ +| +$/, "", $4); print "- " $2 ": " $4}' | head -8
  echo ""
  echo "Дашборды/процессы:"
  echo "- main 8765 HTTPS: $main_code"
  echo "- whale 8766 HTTPS: $whale_https_code"
  echo "- whale 8766 HTTP: $whale_http_code"
  echo "- bot processes: $(echo "$process_snapshot" | grep -c . | tr -d ' ')"
  echo ""
  echo "TODO открыто/blocked: $open_todos_count"
  echo "Live-финансы: заблокированы до typed-confirmation."
} > "$SUMMARY"

{
  echo ""
  echo "## $(date '+%Y-%m-%d %H:%M %Z') — scheduled multi-bot monitor tick"
  echo "- Revalidated sources: \`neh-bot/docs/polymarket_multi_bot/VOICE_REQUEST_2026-05-04.md\`, \`AGENT_FLOW.md\`, TODOs, and agent registry."
  echo "- Dashboard checks: main=$main_code, whale_https=$whale_https_code, whale_http=$whale_http_code."
  echo "- Recent commits last 30m: $(echo "$recent_commits" | grep -c . | tr -d ' ')."
  echo "- Detailed monitor log: \`neh-bot/tasks/multibot_monitor.log\`."
  echo "- Financial/live actions remain blocked pending typed confirmation."
} >> "$MEM"

if [ "$WAKE_AGENT" = "true" ]; then
  if [ -x "$OPENCLAW" ]; then
    "$OPENCLAW" system event --mode now --timeout 30000 --text "MULTIBOT_MONITOR_SUMMARY_TO_TELEGRAM target=$TG_TARGET channel=$TG_CHANNEL
$(cat "$SUMMARY")" >> "$LOG" 2>&1 || true
  else
    echo "openclaw binary not found at $OPENCLAW" >> "$LOG"
  fi
fi
