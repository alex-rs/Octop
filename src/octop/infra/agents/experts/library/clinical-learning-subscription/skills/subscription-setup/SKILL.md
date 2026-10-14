---
name: subscription-setup
description: Creation and activation of learning subscription tasks. After the doctor completes the 5 registration items, create subscription tasks according to the user's selection (continuous daily guideline learning / professional guideline update reminders / regional insurance policy change learning). The platform's cronjob_create automatically binds delivery to the current session channel, with no WeChat binding gate. Check for duplicates before creating, and write "activated" truthfully in the receipt.
metadata:
  octop:
    emoji: "📅"
    label:
      zh: "Learning Subscription"
      en: "Learning Subscription"
    summary:
      zh: "Create guideline, update, and insurance learning subscriptions."
      en: "Create guideline, update, and insurance learning subscriptions."
---

# Learning Subscription Task Creation

## Prerequisites

- The 5 registration items are complete (title, region, hospital, department, professional rank), and `clinical_profile.py register` returns ok: true.
- When registration is not complete, go through the `doctor-registration` skill first; do not skip registration and create a subscription directly.

## Optional tasks

List the optional tasks for the user and let them choose which to enable (they may select all or only some):

1. **Continuous daily guideline learning**: every day at 07:30, generic cron + a weak-delivery deduplication protocol (no channel receipt).
2. **Professional guideline update reminders**: once every 3 days, searching authoritative sources for updates by department, subspecialty, professional-rank depth, and primary-care scenario.
3. **Regional insurance policy change learning**: every Tuesday and Friday at 09:00, summarizing changes in formal insurance documents in the registered region plus local confirmation prompts.

If the user replies "enable all / enable everything" → enable 1, 2, 3; if they name only one or several → enable only those named; "not for now / do not push yet" → keep only the registration and create no task.

## Creation flow

1. **Duplicate check**: before creating, run `cronjob_list(include_disabled=true)` to check existing tasks; do not create duplicates.
2. **Create**: call `cronjob_create` for each task the user explicitly selected.
   - **Automatic platform routing**: `cronjob_create` automatically binds the current session `session_key` and delivers through that session's channel (WeChat/QQ/dashboard/CLI, etc.). **Do not require WeChat binding, do not refuse on the grounds of a "non-WeChat session", and do not ask the user back whether they are in WeChat**.
   - Create directly; no `:weixin:` session identifier is needed, and gates such as `allow_dashboard` are not required.
3. **Confirm**: after creation, call `cronjob_list` to confirm, and write the receipt truthfully as "activated, pushed to the current session channel".
4. **Receipt**: output according to the "registration activation receipt" template in `../../references/output-templates.md`, listing the activated tasks (noting that they are pushed to the current session channel) and the tasks not activated. Stay silent throughout the duplicate check, creation, and confirmation; user-visible content must be a Simplified-Chinese final draft or a Simplified-Chinese confirmation question, and process statements such as I'll, Let me, Now running, Validation passed, or script execution logs are forbidden. When the user must first choose a guideline, ask only about the options and then stop; do not keep running tools in the same reply.

Task scheduling parameters (trigger / task_type / prompt) use the presets in `../../references/cron-presets.json`:

- Daily guideline learning: `cron:30 7 * * *`, `task_type=agent`, `fresh_thread=true`, with the prompt using the weak-delivery deduplication template (see below).
- Professional guideline update reminders: `cron:0 9 */3 * *`, `task_type=agent`.
- Regional insurance policy change learning: `cron:0 9 * * 2,5`, `task_type=agent`.

## Weak-delivery deduplication protocol for daily guideline learning

The cron prompt for daily guideline learning must use the weak-delivery deduplication template from the "continuous daily guideline learning" preset in `../../references/cron-presets.json`, strictly in order:

1. `delivery-check` performs a duplicate check by logical date — if already recorded, stop delivery for that day;
2. `learning-next-lesson` reads the next fixed unit — when there is no activated track or no next unit, explain truthfully and stop; do not fabricate content;
3. Generate the unit according to `../../references/daily-learning-template.md` (3 numbered key points + source line): a non-final unit previews the next fixed unit; the final unit gives 2-3 verified formal guideline candidates and waits for user confirmation. Reviews and research papers must not serve as the final source or next-stage candidates. Validate with `../../scripts/validate_output.py --module daily_guideline_learning`;
4. After validation passes, `delivery-record` records the entry, then output the body.

This ledger only prevents duplication and **does not represent a delivery receipt** — do not claim to the user that delivery was "confirmed". Before the user selects an authoritative guideline track, the cron run will truthfully report "no activated track yet" and stop, without pushing randomly. Once a platform adapter with channel receipts is online, daily guideline learning should migrate to strong-receipt delivery.

The final unit's candidates are only for the user to choose from; do not automatically create or activate the next track. After the user confirms a candidate, still follow the existing flow of guideline verification, chapter-plan presentation, explicit confirmation, and track creation; when there are not enough verifiable formal guidelines, ask for direction instead of filling the gap with reviews.

## Prohibitions

- Do not call `cronjob_create` for tasks the user did not explicitly select, and do not write "activated" for them in the receipt.
- Do not call `cronjob_run`, `cronjob_trigger`, or any manual execution capability for a "first push".
- Creating a subscription must not incidentally trigger a manual first push or advance the learning state (do not call `guideline-advance`).
- When a tool is unavailable or creation fails, do not claim the task is activated; explain the failure reason truthfully and keep the registration record. **Do not use "WeChat channel not bound" as the receipt**.
- Do not claim that weak delivery has "confirmed delivery".

## Boundaries

This skill only handles creation / duplicate checking / confirmation / receipt of subscription tasks. It is not responsible for doctor registration (see `doctor-registration`), does not generate learning content (see the respective medical skills), and does not perform source verification. Whether a task truly exists is determined by `cronjob_list`, not by the subscription note field in USER.md.
