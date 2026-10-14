# Guideline Learning Operations Guide

This file carries the script commands and constraints for learning track creation, preview delivery, duplicate/missed-delivery troubleshooting, and new-version migration. For the process entry point and routing, see `skills/guideline-learning/SKILL.md`.

## Track creation

First verify the complete name, issuing body, version, source link, and source revision identifier of the authoritative file. When the original text is unavailable, provide only a candidate learning map; a track that can be formally delivered cannot be built.

### 1. Save the learning goal (optional)

First restate the objective, the daily time that can be invested, the target date, and the purpose; call the following after the user confirms:

    python ../../scripts/clinical_profile.py learning-goal-save \
      --label <learning objective> --kind <exam|work_review|update_tracking|teaching|custom> \
      --daily-minutes <5-240> --target-date <YYYY-MM-DD, may be omitted> \
      --priority <0-100> --goal-id <stable slug, may be omitted> --confirm true

### 2. Create the draft track

Call the following after the user confirms the choice of this guideline:

    python ../../scripts/clinical_profile.py learning-track-create \
      --label <full guideline name> --publisher <issuing body> --version <version/year> \
      --source-url <authoritative original URL> --source-revision <version or publication date> \
      --goal-id <saved goal ID, repeatable> --track-id <stable slug, may be omitted> --confirm true

Creating a track does not mean an immediate push, nor does it mean the track is enabled.

### 3. Save the fixed section units

Split the verified sections into consecutively numbered units. Each unit must have: ordinal, title, source_anchor, at least one objectives, optional topic_tags, estimated_minutes. Save only the course structure and the source anchors; do not copy the full guideline text.

Before calling learning-track-lessons-replace, first show the user the candidate section order and obtain confirmation. That command preserves units whose delivery is confirmed and cannot rewrite units that are sending/unknown-status/delivered.

    python ../../scripts/clinical_profile.py learning-track-lessons-replace \
      --track-id <track ID> --replace-pending true --confirm true \
      --lesson-json '{"id":"<unit ID>","ordinal":1,"title":"<section topic>","source_anchor":{"section":"<section>","locator":"<subsection>"},"objectives":["<learning objective>"],"topic_tags":["<topic>"],"estimated_minutes":10}'

Repeat by appending one more --lesson-json for each unit. Numbering is consecutive from 1, and the same section unit cannot repeat within one track.

### 4. Enable/Pause

Enable after the user confirms the plan and cadence:

    python ../../scripts/clinical_profile.py learning-track-activate --track-id <track ID> --confirm true

When several tracks are active, let the user choose first; do not let a default guess take precedence. Pausing/archiving preserves history:

    python ../../scripts/clinical_profile.py learning-track-set-status --track-id <track ID> --status <paused|archived> --confirm true

## Preview and delivery

### Preview (does not count toward progress)

Read the next unit without writing any state:

    python ../../scripts/clinical_profile.py learning-next-lesson --track-id <track ID>

The response must begin directly with [Format Preview | Not Counted Toward Progress], and no text may be added before that marker, including process explanations such as "validation passed" or "pushing preview content for you". A preview does not call delivery claim, manual trigger of the scheduled task, delivery confirmation, or guideline-advance.

### Formal delivery (weak-delivery dedup protocol)

Delivery currently uses the generic agent cron and must follow the order strictly; if any step fails, stop and do not output the body:

1. Get today's date (Asia/Shanghai, YYYY-MM-DD) and run `python3 scripts/clinical_profile.py delivery-check --logical-date <today>`. When `already_sent` is true, reply "today's learning content has already been pushed" and stop; do not regenerate it.
2. Run `python3 scripts/clinical_profile.py learning-next-lesson` to read the next fixed unit. When there is no enabled track or no next unit, state that honestly and stop; do not fabricate content.
3. Generate that unit per daily-learning-template.md (exactly 3 numbered points and a source line). Use `lesson.ordinal` and `track.progress.planned_units` to decide whether it is the final unit: for a non-final unit, preview the next fixed unit's topic and learning objective; for the final unit, give 2-3 verified formal guideline/consensus/standard candidates and wait for the user to confirm the next stage. Then run `python3 scripts/validate_output.py --module daily_guideline_learning` to validate; if it fails, fix it and validate once more, and if it still fails, stop and explain why.
4. After validation passes, run `python3 scripts/clinical_profile.py delivery-record --logical-date <today> --confirm true` to record it (which also marks that unit as delivered and advances to the next unit), then output the body. The first line of the body is `[Daily Guideline Learning | {topic}] (unit {ordinal}/{total})`.

Honest stance: the ledger only prevents duplication and does not mean the channel really accepted the content — never tell the user "delivery confirmed". When creating the task, use the prompt of the "Daily Guideline Continuous Learning" preset in cron-presets.json (the above protocol is already embedded there).

### Strong-receipt state machine (migration target)

After a platform delivery adapter with real channel receipts goes live, formal delivery must obey the state machine: read the track → atomically claim the next unit → generate and validate safely → the channel actually sends → receive the channel receipt → confirm delivery and unlock the next unit.

- The platform delivery service must atomically claim the fixed unit and deduplicate by task identifier/logical date/target channel; the model cannot supply or forge these inputs.
- Only a sending adapter with real channel receipts may mark a delivery as accepted and unlock the next unit; the expert package workspace does not store a trusted delivery ledger, nor does it expose delivery lifecycle commands to the model.
- Delivery must not be self-confirmed by the model/an ordinary cron/the fact that content was generated; guideline-advance must not be called again.
- A failed send may be recorded as retryable; an interrupted send or an unclear receipt must be marked unknown and reconciled first, and must not be blindly resent or skipped.
- Confirmed delivery only means the content was accepted by the channel; it does not mean the user has read/mastered it or has clinical competence.

The current weak-delivery mode only prevents duplication and does not represent a delivery receipt; it is a transitional scheme before strong receipts go live.

### Next-stage recommendation at the end of a cycle

The last fixed unit should give the next-stage suggestion in the same body, so that after the unit advances the next cron run is not unable to recommend anything because of "no next unit":

1. Silently search for and verify 2-3 formal guidelines/consensus statements/standards that clearly connect to the current track, and write the full name, year/version, issuing body, authoritative original link, and recommended connection.
2. All review articles (including systematic reviews, meta-analyses, narrative, scoping, umbrella, rapid, expert, and other literature reviews) as well as research papers may only be used internally to discover formal guidelines, and must not become the current unit's source, a next-stage candidate, or a new track's source.
3. Candidates are marked only as "pending confirmation". After the user replies A/B/C or proposes another direction, the candidate sections must still be shown and confirmed following the "track creation" process; tracks must not be created or enabled automatically in the final unit.
4. When there are not at least 2 verifiable formal guidelines, state honestly that "not enough verifiable formal guidelines were obtained", ask the user which learning direction they wish to continue, and do not pad the list with review articles or research papers.

## Duplicate/missed-delivery troubleshooting and new-version migration

### Duplicate content

The root cause of duplication is almost always that the fixed unit was not advanced and the content was regenerated instead. Handling order:

1. Run `python ../../scripts/clinical_profile.py get` and read the track's unit list, each unit's ordinal, and its status.
2. Check whether there are duplicate ordinals, whether the same source_anchor was split into several units, or whether several active tracks are bound to the same guideline.
3. Explain the current progress to the user (which unit out of how many) and the completed units, and point out where the duplication occurs.
4. When adjustment is needed, use learning-track-lessons-replace to correct undelivered units and preserve units whose delivery is confirmed; units that are sending/unknown-status/delivered must not be rewritten.

Never use "resend a different unit" to cover up duplication. Until delivery of the same unit is confirmed, it must not be resent as new content.

### Missed delivery

Daily guideline learning currently uses weak delivery (a generic cron run counts as delivered, with no channel receipt). When the user reports a missed delivery:

- First run `python3 scripts/clinical_profile.py delivery-check --logical-date <that day>` to check the ledger: if there is a record but the user did not receive it, the cron ran but the channel did not deliver — state honestly that this is a limitation of weak delivery; if there is no record, the run did not happen that day.
- You may resend that day's unit for the user: generate the day's unit in the current conversation per the template (the ledger already has a record, so do not call delivery-record again to double-record; mark the first line of the resent body with [Daily Learning Resend]).
- Do not attribute it to "it was sent but the user did not see it", and do not call guideline-advance to advance.
- When missed deliveries recur, state honestly that delivery can only be guaranteed once a platform delivery adapter with channel receipts is live.

### Migrating to a new guideline version

When a new version of a guideline is found, do not silently overwrite the old track, the old learning units, or the existing delivery ledger. First give the old/new versions, the delivered units, the affected sections, and the new planning needs; after the user confirms, create a new draft track, preserve the old track's history, and then re-verify and plan the new units.
