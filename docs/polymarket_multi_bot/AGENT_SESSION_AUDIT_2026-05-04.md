# Agent session audit — 2026-05-04 23:50 CEST

Source: local OpenClaw session stores under `/Users/sbot/.openclaw/agents/*/sessions`. A `.jsonl.lock` file is treated as the reliable running indicator; stale `status: running` fields without a lock are considered done/stale.

## Result

- `backend-dev`
  - `cross-reviewer-multibot`: done
  - `research-agent-multibot`: done
  - `quant-math-agent-multibot`: done
  - `research-dev-multibot`: done
  - `4f58a665-367a-4a56-9fc9-07c349d96ea0`: stale status says running, but no lock; treated as done/stale
- `frontend-dev`
  - `a0202c55-2e71-4276-8d2d-69b06083d536`: stale status says running, but no lock; treated as done/stale
- `research-agent`
  - `research-agent-real-multibot`: done
- `quant-math-agent`
  - `quant-math-agent-real-multibot`: done
- `security-reviewer`
  - `security-reviewer-multibot`: done
  - `7d946b21-df12-4ea8-adcc-f14a1c19802f`: stale status says running, but no lock; treated as done/stale
- `cross-reviewer`
  - no dedicated session store; cross review was run as `backend-dev:cross-reviewer-multibot` and is done.

## Action taken

Updated the monitor session-summary logic to report `running` only when a session lock exists, preventing stale old agent sessions from showing as active forever.
