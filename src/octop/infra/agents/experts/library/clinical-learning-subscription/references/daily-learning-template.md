# Hard Template for the Daily Guideline Learning Unit

Used for formal guideline subscriptions that have channel-receipt capability, or to generate a draft awaiting delivery. Default 600-900 characters; for busy outpatient settings prefer the short version, and do not write it as a review article. It does not restrict the on-demand learning diagnosis, diagnostic-criteria learning, or educational quizzes performed in the guideline-learning-diagnosis skill.

Example structure:

    [Guideline Learning Unit | {department/topic}]
    Track: {user-readable track name}
    Basis: {full name of the authoritative guideline} ({version/year}, {issuing body})
    Learning unit: {ordinal} / {total_units}
    Section: {fixed section anchor}
    Linked goal: {exam/work review/update tracking/teaching; write "general learning" when not linked}
    Topic: {topic of this unit}

    1. {Point one: state the learning point only, do not write patient management orders}
    2. {Point two: highlight primary-care recognition, follow-up, quality control, or learning value}
    3. {Point three: state the boundaries or the points that need confirmation from local policy}

    {For a non-final unit:
    Next unit preview:
    {next fixed unit topic} — {next unit learning objective}}

    {For the final unit:
    Optional guidelines for the next stage (pending confirmation):
    A. "{full name of the formal guideline/consensus/standard}"({year/version}, {issuing body}): [link]({verified authoritative original URL})
       Recommended connection: {its knowledge connection with the current track}
    B. "{full name of the formal guideline/consensus/standard}"({year/version}, {issuing body}): [link]({verified authoritative original URL})
       Recommended connection: {its knowledge connection with the current track}
    {Optional C, at most 3 items}
    Reply A/B/C, or tell me another learning direction. No new track will be created or enabled before confirmation.}

    Source: {file name}: [link]({authoritative original URL})
    Note: This content is compiled from authoritative guidelines and is intended for doctors' learning; it does not provide individual diagnosis or treatment or prescription dosages, and for emergency management it only offers guideline-level educational suggestions, not a basis for action.

## Hard Rules

- Must be exactly 3 numbered points.
- A non-final unit must contain a substantive next unit preview that states the next fixed unit topic and learning objective; do not replace it with status statements such as "waiting for review" or "waiting to confirm a new track".
- The final unit must not keep outputting an empty next unit preview. It should provide 2-3 verified formal guideline candidates for the next stage, including the full name, year/version, issuing body, authoritative original link, and recommended connection, and must clearly state "pending confirmation" and that "no new track will be created or enabled before confirmation".
- When there are not at least 2 verifiable formal guideline candidates at the end of a cycle, do not fill the gap with a review article, a meta-analysis, or a research paper. Rewrite it as "next-stage planning (awaiting your choice)", explain that "not enough verifiable formal guidelines were obtained", and ask the user which direction they wish to continue; do not create or enable a new track.
- Do not set self-test questions, and do not write prompts such as announcing the answer afterwards; this rule applies only to daily subscription content.
- Must display the fixed guideline version, learning unit ordinal, and section anchor; do not display the internal track ID, delivery ledger, token, hash, session_key, or channel receipt.
- Default 600-900 characters, at most no more than 1000 characters.
- Do not output drug dosages, routes of administration, frequencies, treatment courses, loading doses, emergency action cards, disease SOPs, medical-insurance reimbursement conclusions, or HIS recommendations.
- The source must be written as Source: file name: [link](URL); the link text is fixed as link, and long bare URLs must not appear.
- Systematic reviews, meta-analyses, narrative/scoping/umbrella/rapid/expert reviews, and other literature reviews may only be used internally to discover original guidelines and must not appear in the final sources, next-stage candidates, or learning track sources.
- The old guideline-advance must not be called.
- Only after the sending adapter receives a real channel receipt may delivery be confirmed internally and the next unit unlocked. Content generation, preview, cron execution, or draft validation do not count as delivery.
- The single-day receipt may be used only when there is a real channel receipt, stating that today's learning content has been accepted by the channel and the subscription remains enabled; do not write that the learning task is complete, the learning subscription is complete, the user has mastered the content, or day N of learning is complete.

## Preview Template Rules

When the user asks to see the effect, to preview, or to test the push, add the following as the first line of the body:

    [Format Preview | Not Counted Toward Progress]

A preview response must begin directly with the above marker, and no title, greeting, colon, or process explanations such as "validation passed" or "pushing the preview of unit N for you" may appear before the marker. A preview only reads the next unit; it does not claim a delivery, does not call the manual trigger of the scheduled task, and does not change any learning state.
