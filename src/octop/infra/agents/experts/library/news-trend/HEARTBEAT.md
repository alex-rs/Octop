---
summary: "Hotspot Reporter heartbeat task list"
read_when:
  - Heartbeat cycle triggers
  - Manually bootstrap the workspace
---

# Heartbeat Task List

<!-- Empty file = no heartbeat API call is triggered. If you want the agent to patrol periodically, add entries below. -->
<!-- Keep it lean. Every line burns tokens. -->

## Periodic Patrol

| Task | Frequency | Description |
|------|-----------|-------------|
| Check USERS.md push settings | Every heartbeat | Users with push enabled → run hotspot briefings at their configured interval and time |
| Refresh core-topic hotspots | Every 4 hours | Read the core topics in USERS.md, call the 60s API to quickly scan for major breaking events |
| Financial data snapshot | Trading days 09:30, 15:00 | Call `/v2/gold-price` + `/v2/exchange-rate`, record to `logs/` |
| DailyHotApi availability probe | Once per day | `node scripts/fetch_dailyhot.mjs weibo` to verify the module works; log it if it fails |

## Trigger Rules

```
Heartbeat triggers → read this file
  → check each task in turn to see whether its execution time has arrived
    → yes → run the task, write the results to logs/
    → no → skip
  → check USERS.md push settings
    → enabled and push time reached → run the scheduled briefing
    → not enabled or time not reached → skip
```

## Notes

- Heartbeat tasks only do lightweight checks and data collection; they do not push to the user proactively (unless push settings are enabled)
- Each heartbeat should consume as few tokens as possible; avoid triggering deep analysis during a patrol
- Breaking-event detection: if heat around a core topic spikes (appearing on 3+ platforms at the same time), log it and proactively mention it in the next user conversation
