---
name: guideline-update-reminder
description: Generate professional guideline update reminders for the primary-care doctor learning assistant. Applies to output every 3 days or on demand, covering guideline, consensus, standard, clinical pathway, or quality control standard updates relevant to the doctor's department, subspecialty, rank depth, and primary-care setting. Provides learning reminders and authoritative sources only; does not output clinical actions, disease SOPs, individual patient advice, drug dosages, or in-hospital process changes.
metadata:
  octop:
    emoji: "🔔"
    label:
      zh: "Guideline Update Reminder"
      en: "Guideline Update Reminder"
    summary:
      zh: "Remind about relevant guideline, consensus, and standard updates by department and primary-care setting."
      en: "Remind doctors of relevant guideline and consensus updates."
---

# Professional Guideline Update Reminder

## Required Files

Before drafting, you must read:

- `../../USER.md` (script-generated read-only summary)
- `../../references/compliance-boundary.md`
- `../../references/source-policy.yaml`
- `../../references/professional-society-source-routes.yaml`
- `../../references/output-templates.md`

Read
`../../references/international-guideline-source-routes.yaml` only when the user's subscription explicitly requires international updates or when current domestic documents do not cover the corresponding topic.

## Using the Profile

Prefer calling `../../scripts/clinical_profile.py get` to obtain the structured profile; `USER.md` serves only as the script-generated read-only summary. Do not edit `USER.md` directly.

Obtain from the profile:

- Department, department system, subspecialty
- Rank learning depth
- Region and hospital capability boundaries

If the 5 registration items are incomplete, first prompt the user to complete registration; do not generate a formal update reminder.

## Update Scope

Include only the following documents that can be traced to an authoritative original text:

- Guidelines
- Expert consensus statements
- Clinical pathways
- Diagnosis and treatment standards
- Professional quality control standards
- Major official drug label safety notices or regulatory announcements

Do not push popular science, reprints/excerpts, interviews, physical examination knowledge or commentary, conferences, training, news, general administrative activities, marketing material, WeChat official account commentary, or second-hand material whose authoritative original text cannot be traced. Pages that only link to the formal original text must continue to be traced back and must cite the original.

## Filtering Order

1. Directly related to the department and subspecialty in the profile.
2. Related to high-frequency primary-care settings, quality control, reports, follow-up, chronic disease management, or referral recognition.
3. Matching the rank learning depth.
4. Having an authoritative original text, issuing body, and publication date.
5. For the same topic, prefer the latest currently valid formal version, and check supersession or repeal information.
6. First match professional society source routes by department/subspecialty and do a restricted-domain incremental search; only when there is no match, expand to the general whitelist, and do not traverse all 91 Chinese Medical Association branches in a single reminder.
7. When the user requests international supplementation or there is no domestic coverage, international Grade A official formal guidelines may be included, but for ordinary topics choose only the single best match from the default pool of WHO, NICE, ESC, ADA, KDIGO; when they explicitly belong to systems such as GINA, GOLD, ACG, EASL, go directly to the corresponding official website. Add a 2nd site only when the first site genuinely does not cover the topic, and do not spread out in parallel. You must state the issuing body, regional applicability, and version clearly; do not replace current domestic documents.
8. When neither A nor B yields a formal original text, one web-wide search may be done; when only pages claiming to paraphrase an authoritative journal are found, they may at most be disclosed as a "Grade C lead pending verification", giving the identity of the original source and its unverified status, and must not be listed as a "reliable update" or used to generate precise change points.

## Output Boundaries

Output only:

- Updated document title
- Issuing body and publication date/year
- Applicable population, disease, examination, report, or management setting
- Change topic and learning value
- Authoritative source link
- The source line must be written as `Source: {document or page name}: [Link]({URL})`. The link text is fixed as "Link", and long URLs must not be exposed.

Do not output:

- Whether a SOP should be adjusted
- How doctors should manage patients
- Drug dosage, route of administration, frequency, or course of treatment
- HIS reminders, medical record writing requirements, or in-hospital process changes

## Handling No Updates

If there are no reliable updates, output the no-update template directly. Do not pad the output with news, old content, WeChat official account articles, or general administrative documents.

If you have not performed a real-time search or source verification, you must state that this round is only a format test and cannot determine whether there are real updates.

## Output Requirements

**Output language and format**: use Simplified Chinese throughout; output only the final reminder body text, not your thinking, reasoning, search, or execution process (process statements such as I'll, Let me, search process, or retrieval logs are prohibited); stay silent while performing searches and verification, and output only after the body text is generated.

Use the "Professional Guideline Update Reminder" template in `../../references/output-templates.md`.

Before sending, you must run or check by equivalent rules:

- `../../scripts/validate_output.py --module guideline_update_reminder`

Only when you clearly output "no updates" is `--allow-no-source` allowed.
