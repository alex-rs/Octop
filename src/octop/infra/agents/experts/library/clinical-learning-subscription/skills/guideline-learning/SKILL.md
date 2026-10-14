---
name: guideline-learning
description: Guideline learning process constraints. Determine the request type → read state → create a track/preview/deliver/troubleshoot migration per the process; for the operation commands and detailed rules see references/learning-operations.md. Use authoritative sources for topic selection, and pass output-format validation before output. Does not generate diagnosis and treatment/prescription/emergency SOP/individual patient advice.
metadata:
  octop:
    emoji: "📘"
    label:
      zh: "Guideline Learning"
      en: "Guideline Learning"
    summary:
      zh: "Create, preview, and deliver authoritative guideline learning content by track."
      en: "Create, preview, and deliver guideline learning tracks."
---

# Guideline Learning Process

## Required reading

- ../../USER.md
- ../../references/source-policy.yaml
- ../../references/output-templates.md
- ../../references/daily-learning-template.md

When performing track creation/preview delivery/duplicate or missed delivery troubleshooting/new-version migration, also read `../../references/learning-operations.md` (the operation commands and detailed rules; not required reading every time).

## Request routing

- Assess mastery/educational quizzes/learning maps/diagnostic-criteria learning → `guideline-learning-diagnosis`
- Expand a section/learning order/pathway map → `guideline-section-expansion`
- Exam material selection → `exam-material-recommendation`
- Learning track/preview/delivery/duplicate or missed delivery/new-version migration → this skill, executed per the corresponding process in learning-operations.md

## Reading state

Before any save/claim/send/status decision, first call:

    python ../../scripts/clinical_profile.py get

Do not treat which day it is, a chat summary, or an old current_guideline as real progress. Read learning.tracks, learning.goals, and delivery_ledger; show the user only the track/version/next unit/understandable progress, and do not show ledger IDs/tokens/hashes/channel session information. A personalized goal track may be saved after confirmation and does not require mandatory registration; registration is required only for customization by department/region/professional title or for enabling a subscription.

## Process constraints

1. **Create a track**: first verify the guideline's full name/body/version/source link/source revision; only after the user confirms, save the goal → draft track → fixed section units → enable. For the commands and detailed rules see learning-operations.md.
2. **Preview**: read the next unit without writing state; the response must begin directly with [Format Preview | Not Counted Toward Progress], and no text may be added before that marker; do not call delivery claim/manual trigger/guideline-advance.
3. **Formal delivery**: weak-delivery dedup protocol (delivery-check for dedup → read the unit → validate → delivery-record to book it → output); the ledger only prevents duplication and does not represent delivery, so never claim that delivery is confirmed. The strong-receipt state machine is the migration target. For detailed rules see learning-operations.md.
4. **Duplicates/missed delivery/migration**: read the real state first and then handle it; do not resend based on an impression; for a new version, give the migration plan first and do not overwrite the old track before confirmation. For detailed rules see learning-operations.md.

## Topic selection and source boundaries

Topic selection priority: common high-frequency primary-care needs of this department > high-risk recognition and referral knowledge (learning content only, no action cards) > examination/reporting/quality control/chronic disease/standards > verified recent updates.

The final basis uses only authoritative sources allowed by source-policy.yaml; when the user explicitly specifies an international guideline or there is no domestic coverage, use a tier-A international formal guideline per `international-guideline-source-routes.yaml`, and do not silently override current domestic standards. The learning content must include at least one authoritative original-text link `Source: name: [link](URL)`; when neither A nor B can be found, one tier-C whole-web paraphrase may be disclosed per the `source-verify` rules, but it can only serve as background pending verification and must not be used to create a formal guideline track, expand the original text, or generate precise recommendations. Educational explanations of the scope of application/learning objectives/core concepts/risk awareness/quality control/reporting and follow-up are allowed; individual diagnosis and treatment/drug dosages/emergency action cards/disease SOPs/hospital processes/HIS are forbidden.

## Output language and validation

**Output language and format**: use Simplified Chinese throughout; output only the final body, not the thinking, reasoning, retrieval, or execution process (process statements such as I'll, Let me, Now running, Validation passed, Here is the answer., search narration, and retrieval logs are forbidden). Perform retrieval, skill reading, script runs, and validation silently; when you need to confirm options with the user, also ask only in Simplified Chinese, stop immediately after asking, and do not carry tool process sentences.

Before sending or providing a formal draft, run `python ../../scripts/validate_output.py --module daily_guideline_learning`, and fix failures first without bypassing them. The validation result is for internal control only; after it passes, output the body directly, and do not output process explanations such as "validation passed" or "pushing preview content for you" to the user. The four hard format rules and the validation process are in the `output-format` skill.
