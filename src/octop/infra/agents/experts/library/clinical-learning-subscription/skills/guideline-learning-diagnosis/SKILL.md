---
name: guideline-learning-diagnosis
description: >-
  Use when the user asks to assess their mastery of a specific guideline, create a guideline study / exam-preparation
  plan, sort out weak sections, do an educational quiz, or study the diagnostic criteria, differential framework,
  and workflow relationships in a guideline. This skill only performs learning diagnosis and teaches diagnostic criteria;
  it does not make disease diagnosis, treatment, prescription, dosage, emergency management, or insurance reimbursement judgments for any patient.
metadata:
  octop:
    emoji: "🧩"
    label:
      zh: "Learning Diagnosis"
      en: "Learning Diagnosis"
    summary:
      zh: "Assess guideline mastery and explain diagnostic criteria, without individual case management."
      en: "Assess guideline mastery and teach diagnostic criteria, not cases."
---

# Guideline Learning Diagnosis and Diagnostic Criteria Study

## First Distinguish the Three Types of Diagnosis

When the user says "diagnosis", first classify it into one of the following by context; the names are similar and must not be conflated:

| Type | Allowed | How to handle |
| --- | --- | --- |
| Learning diagnosis / learning assessment | Allowed | Assess learning goals, knowledge coverage, weak sections, and review paths. |
| Studying diagnostic criteria in a guideline | Allowed | Explain definitions, criteria elements, differential frameworks, risk notes, and workflow relationships, with the original source. |
| Diagnosis or management of a specific patient | Not allowed | Do not derive diagnosis, testing, or treatment conclusions from cases, symptoms, examinations, or imaging; redirect to general learning material and authoritative sources. |

If the user's intent is still unclear, ask only one clarifying question: do you want to assess your mastery of the guideline, or to study the diagnostic criteria in the guideline? Do not ask for patient-identifiable information.

## Required Reading Boundaries

Before handling a medical learning request, read and comply with:

- ../../USER.md (if present, a read-only summary used only for personalized learning)
- ../../references/compliance-boundary.md
- ../../references/source-policy.yaml
- ../../references/learning-diagnosis-template.md
- ../../references/learning-track-template.md

An ordinary, one-off learning assessment does not require completing the 5-item doctor registration. Only when the user asks to save learning goals, tracks, continuous progress, a WeChat subscription, or department/region personalization do you obtain the necessary consent and minimal information.

## Workflow A: Learning Diagnosis

### 1. Collect the Minimum Necessary Information

Prefer extracting from content the user already provided; ask only when something is missing:

1. Learning goal: review for work, rank/exam, update tracking, or teaching.
2. Guideline/topic: full title, version/year, or at least the topic.
3. Current learning signals: self-assessment, sections already studied, or answers to this quiz.
4. Daily time available and target date (only when a plan is needed).

Do not ask for patient names, medical records, examination reports, prescriptions, imaging, or real case details. Do not disclose existing profile fields such as department, hospital, or region in unrelated general tasks.

### 2. Verify the Learning Basis

When the user asks to base the work on a guideline, first confirm it per the source-verify rules: full document title, issuing body, version/year, scope of application, authoritative original link, and whether alternative versions exist.

- When no verifiable guideline is available, output an initial assessment of the learning need and state clearly that the guideline is still to be selected; you may not claim the basis comes from the latest guideline.
- When a guideline is confirmed, link each learning conclusion to the most relevant section or topic, and keep the source line in the body text.
- Do not copy or expand a complete copyright-restricted guideline; prefer a learning map, section locations, summaries, and links to the official or authorized original text.

### 3. Form the Learning Diagnosis

Express learning signals using only the following wording: suggest starting with a fundamentals review, suggest consolidation, ready to move to the next level, insufficient evidence, retest pending. Do not write competence-certification conclusions such as pass/fail, able to practice independently, or lacking clinical competence.

A learning diagnosis includes at least:

- This round's scope, the learning goal, and the basis version.
- Existing learning signals: state clearly which come from the user's self-assessment and which from this round's answers.
- No more than 3 concepts/sections to prioritize, with a reason for each priority.
- One actionable next step: expand a section, view the learning workflow diagram, do the next question set, or form a candidate learning track.

If the user asks for a quiz: at most 3-5 questions per round, testing the guideline's scope of application, concept distinctions, section structure, evidence understanding, or update points. Do not use real patient cases, drug dosages, prescriptions, emergency actions, or questions about what to do next for this patient. Give educational explanations tied to the source immediately after answering; do not treat the accuracy rate as proof of clinical competence.

### 4. All Save Actions Are Optional

By default, do not persist this self-assessment, the answers, the learning diagnosis, or the candidate plan. When the user explicitly says to save this learning diagnosis, save the learning goal, or save the plan, first restate the fields that will be saved and confirm they contain no patient information.

To save only the diagnosis summary, use:

    python ../../scripts/clinical_profile.py learning-diagnosis-save \
      --goal <learning goal> --self-assessed-level <needs_foundation|developing|confident> \
      --available-minutes-per-day <5-240> --priority-topic <priority topic, repeatable> \
      --recommended-start <which section or task to start from> --confirm true

If a guideline has been verified, also append --guideline-title and --source-url. When there is no verifiable source, do not fabricate a link.

To save a learning goal, first use the guideline-learning skill's learning-goal-save. A learning goal can be linked to multiple tracks, but the diagnosis itself does not automatically create a track, nor does it automatically start delivery.

Only when the user explicitly confirms the version, section scope, cadence, and intent to save do you call the guideline-learning skill to create a track, save units, and enable it. Candidate track output must clearly state that it is not saved, not enabled, and not pushing.

To delete a learning diagnosis summary at the user's request, use:

    python ../../scripts/clinical_profile.py learning-diagnosis-clear --confirm true

## Workflow B: Studying Diagnostic Criteria in a Guideline

Without involving any specific patient, the diagnostic-related sections of a guideline can be broken down into:

1. Document version, scope of application, and term definitions.
2. The relationships among the diagnostic elements/criteria listed in the guideline; express conceptual relationships with a learning workflow diagram or a hierarchy, not a clinical action card.
3. Educational explanations of differential frameworks, risk notes, referral recognition, or quality requirements.
4. Easily confused concepts and their corresponding locations in the original text.

Do not write the workflow diagram as step-by-step management instructions for a real patient, and do not output specific examinations or management, drug regimens, dosages, dosing frequency, or emergency action cards. Every guideline-based explanation must include the authoritative source and version; when the source is uncertain, state clearly that it cannot be verified.

## Output and Validation

Use the structure in learning-diagnosis-template.md. Before sending a formal guideline-based learning diagnosis or diagnostic criteria explanation, run:

    python ../../scripts/validate_output.py --module guideline_learning_diagnosis

If you are still collecting goals, the user has not yet selected a guideline, or there is no verifiable authoritative original text, you may use --allow-no-source, but the first line must clearly read "Initial learning need assessment | Guideline to be selected", and it must not be presented as a guideline-based conclusion.

On the doctor-facing side, output only learning-oriented conclusions, learning paths, and sources; do not show internal scores, tool calls, status JSON, or script paths.
