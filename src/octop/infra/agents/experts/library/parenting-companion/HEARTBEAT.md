# Heartbeat — Parenting Companion Scheduled Tasks

> This file defines everything the "AI wakes up and does on its own".
> Any proactive contact **must first pass** the "checks to complete before speaking" in `PROACTIVE.md` — if it is outside the user's preferred window → `[SKIP]`.

## Task List

| Trigger condition | Frequency | Action | Does it disturb the user |
|---------|------|------|-------------|
| Daily 0:00 | Once daily | Run `scripts/check_memory_freshness.sh` to reconcile | Fix silently only when discrepancies are found, **send no message** |
| Xth day of each month (X = the child's "monthly age day") | Once monthly | Summarize the month's development, compare against WHO curves | Disturbs, but only inside the user's preferred window |
| 24 hours after a vaccine | Triggers once when met | Ask about the reaction | Disturbs (inside the window) |
| Fever case still open, ≥6 hours with no new reading | Triggers once when met | Ask for the latest temperature | Disturbs (inside the window) |
| Day 3 of an allergen trial with no allergy flag | Triggers once when met | Prompt "this can go on the safe list" | Disturbs (inside the window) |
| ≤7 days until the next vaccine | One reminder | Remind about booking | Disturbs (inside the window) |

## Detailed Rules

### 1. Daily 0:00 reconciliation (must run, **silent**)

**Purpose**: stop the AI from writing specialized files and forgetting to sync MEMORY.md.

**Steps**:
1. Call `execute_shell_command` to run `bash scripts/check_memory_freshness.sh`
2. Parse the output:
   - Exit code 0 = in sync, finish (send no message)
   - Exit code 2 = a specialized file is newer than `MEMORY.md`
3. If exit code is 2:
   - Read the latest record from each new file
   - Use `edit_file` to update the matching index line in `MEMORY.md`
   - `append_file` one line to `memory/{today}.md`:
     ```
     [00:00] Ran reconciliation: found N out-of-sync items, fixed → MEMORY.md
     ```
   - **Send no message** to the parent (it is midnight)

### 2. Monthly-age summary (once monthly)

**Condition**: today's date = the "day" of the child's birth date (for example, born on 6/19 → triggers on the 19th of every month).

**Check the time first**:
- Is the current time inside the contact window in `USER.md`? If not → `[SKIP]` and try again the next day
- Is it a do-not-disturb period? If yes → `[SKIP]`

**Actions**:
1. Call `execute_shell_command + date` to compute the exact current age in months
2. Read the latest height and weight from `memory/child/PROFILE.md` for this month
3. Read the new milestones from `MILESTONES.md` for this month
4. Read the newly passed / newly allergic foods from `FEEDING.md` for this month
5. Use `web_search + web_fetch` to verify the WHO growth-curve comparison
6. Generate a short monthly report (within 200 words + sources ✅ verified)
7. Send it to the parent through the `lastDispatch` channel

### 3. Vaccine-reaction follow-up (conditional trigger)

**Conditions**:
- The latest vaccination entry in `HEALTH/vaccines.md` is 24-30 hours old
- The day's work log `memory/{today}.md` has **no** record of asking about that vaccine's reaction

**Actions**:
- Must check the contact window
- Send one gentle message of concern (≤50 words):
  ```
  {child_name} had {vaccine_name} yesterday — any reaction today? Fever, rash, drowsiness, or a change in appetite are all fine to tell me.
  ```
- Write a log entry noting "asked about the {vaccine_name} reaction" to avoid repeating it

### 4. Fever case follow-up (conditional trigger)

**Conditions**:
- `HEALTH/records.md` has a fever record with the status "monitoring"
- The last temperature reading is ≥37.5°C
- It has been ≥6 hours since the last reading

**Actions**:
- Must check the contact window
- Ask for the latest temperature:
  ```
  {child_name}'s last temperature was {temp}°C {hours} hours ago — how is it now?
  ```
- After the reply, update `records.md` using the 5-step flow

**Auto-close**: temperature <37.3 for 12 consecutive hours → change the status to "closed" in `records.md`.

### 5. Day-3 allergen-trial prompt (conditional trigger)

**Conditions**:
- A food in "pending allergen trial" in `FEEDING.md` reaches day 3
- No allergy flag in the meantime

**Actions**:
- Ask the parent whether to add it to the safe list:
  ```
  {child_name} has been eating {food} for 3 days now and no allergic reaction has shown up. Can I update it to "passed"?
  ```
- After confirmation, use `edit_file` to change the status from "pending allergen trial" to "✅ passed"

### 6. Next vaccination booking reminder

**Condition**: the earliest vaccine in the "planned" section of `HEALTH/vaccines.md` is ≤7 days away, and no reminder has been sent this week.

**Action**: send one reminder:
```
{child_name}, there are {days} days left before the {vaccine_name} shot — remember to book at the community clinic in advance.
```

---

## Common prerequisite: PROACTIVE check

Every "disturb the user" task **must first** complete the global `PROACTIVE.md` "checks to complete before speaking" list:

1. ✅ `Current time (authoritative)` in the system prompt has been read
2. ✅ The proactive-contact preference in `USER.md` has been checked
3. ✅ The current time is inside the preferred window
4. ✅ No holiday / do-not-disturb period is hit
5. ✅ The daily contact-frequency cap has not been exceeded

Any single failure → `[SKIP]`.

---

## Collaboration Between Heartbeats

- Every action triggered by HEARTBEAT writes a log entry to `memory/{today}.md`, prefixed with `[HH:MM heartbeat]`
- User replies to heartbeat messages still go through the full 5-step flow (identify → write specialized file → sync index → write log → tag)
- The heartbeat log must not repeat specialized-file content the user has already seen — the log records only what the "AI itself did"
