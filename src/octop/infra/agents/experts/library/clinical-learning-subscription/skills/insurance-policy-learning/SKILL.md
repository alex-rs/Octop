---
name: insurance-policy-learning
description: Generate regional medical insurance policy learning content for the primary-care doctor learning assistant. Supports a summary of the latest changes every Tuesday and Friday or on demand, and also a review of key policies over the past year or a specified interval. Outputs only summaries of the policy original text, items pending local confirmation, and authoritative sources; does not output reimbursement conclusions, payment ratios, HIS reminders, medical record requirements, or hospital execution commitments.
metadata:
  octop:
    emoji: "🏥"
    label:
      zh: "Insurance Policy Learning"
      en: "Insurance Policy Learning"
    summary:
      zh: "Summarize changes in regional insurance formal documents and flag items pending local confirmation."
      en: "Summarize local insurance policy changes for learning, not claims."
---

# Regional Medical Insurance Policy Learning

This skill has two modes:

| Mode | Coverage | Template used | Validation module |
| --- | --- | --- | --- |
| Latest changes | The past week / since the last push | Regional Insurance Policy Change Learning | `insurance_policy_learning` |
| Long-cycle review | The past year, this year, last year to date, or a user-specified interval | Insurance Policy Review Learning (Long Cycle) | `insurance_policy_retrospective` |

If the user says "only this week's changes", use the former; if they say "key policies of the past year", "what new policies are there this year", or "review it for me", use the latter. Scheduled pushes use the latest-changes mode by default; the user may additionally request a review on demand.

## Required Files

Before drafting, you must read:

- `../../USER.md` (script-generated read-only summary)
- `../../references/compliance-boundary.md`
- `../../references/source-policy.yaml`
- `../../references/output-templates.md`

## Using the Profile

Prefer calling `../../scripts/clinical_profile.py get` to obtain the structured profile; `USER.md` serves only as the script-generated read-only summary. Do not edit `USER.md` directly.

Obtain from the profile:

- Province, city, district or county
- Hospital
- Department and department system
- Hospital capability boundaries

If the regional registration is incomplete, first prompt the user to complete the region; do not generate formal insurance policy learning content.

## Region Matching

Use only policies related to the doctor's registered region:

1. Prefer formal district/county documents.
2. When there is no formal district/county document, fall back to formal city-level documents.
3. When there is no formal city-level document, fall back to formal provincial documents.
4. You must state clearly that the local application standard must be confirmed with the medical insurance office.

## Source Requirements

The final basis may only use original pages or formal attachments published by the medical insurance bureau, government departments, health commissions, or other formal institutions. WeChat official accounts, news, commercial websites, and reprint material may only serve as leads and must not serve as the final basis.

When "added, removed, expanded, narrowed, or adjusted" is involved, you must obtain both the old and the new formal documents and be able to compare them; otherwise you may only write "version differences require manual verification".

## Output Boundaries

Output only:

- Policy document title, issuing body, effective date
- Summary of the policy original text
- Items that need confirmation by the local medical insurance office
- Authoritative source link
- A note that this is not grounds for reimbursement
- The source line must be written as `Source: {document or page name}: [Link]({URL})`. The link text is fixed as "Link", and long URLs must not be exposed.

Do not output:

- Clinical action recommendations
- HIS reminders or system rules
- Medical record writing requirements
- Reimbursement conclusions, payment ratios, or payment condition commitments
- Judgments that a certain item can definitely be reimbursed at the user's hospital

## Long-Cycle Review Mode

When the user asks for a review of the past year or a specified interval:

1. **First confirm the review interval** and state it in the output (e.g. 2025-08-01 to 2026-07-31). If the user says "the past year", count back 12 months from the current date; if they say "this year", count from January 1 of the current year.
2. **Search scope** likewise follows the district/county → city → province region matching rule and may include national key policies; state in the output which levels were covered.
3. **Sort by publication date** so the user can see the policy evolution.
4. **You must mark the status of each document**: currently in force / repealed / superseded. This is a risk point specific to long-cycle review — do not present an invalid policy as currently in force. When a supersession relationship is found, state which new document supersedes it.
5. **Summarize learning tips by topic** (such as price adjustments, chronic and special disease management, payment method reform), rather than simply listing documents.
6. Give each document its own source line; if no traceable authoritative original text can be found within the interval, say so honestly rather than padding with second-hand platforms or padding with old documents.
7. Quantity control: prefer the key policies with the greatest impact on primary-care doctors and avoid listing too many documents at once; the user may ask to continue expanding.

The output boundaries of the long-cycle review are exactly the same as the latest-changes mode — still only original-text summaries and learning tips, **no reimbursement conclusions, payment ratios, or in-hospital settlement standards**, and the local confirmation note is kept at the end.

## Output Requirements

**Output language and format**: use Simplified Chinese throughout; output only the final body text, not your thinking, reasoning, search, or execution process (process statements such as I'll, Let me, search process, or retrieval logs are prohibited); stay silent while searching, and output only after the body text is generated.

The latest-changes mode uses the "Regional Insurance Policy Change Learning" template in `../../references/output-templates.md`; the long-cycle review uses the "Insurance Policy Review Learning (Long Cycle)" template.

Before sending, you must run or check by equivalent rules:

- `../../scripts/validate_output.py --module insurance_policy_learning`
- For the long-cycle review use `../../scripts/validate_output.py --module insurance_policy_retrospective`

When there are no reliable updates you may use `--allow-no-source`, but you must state clearly that no update with a traceable authoritative original text was found.
