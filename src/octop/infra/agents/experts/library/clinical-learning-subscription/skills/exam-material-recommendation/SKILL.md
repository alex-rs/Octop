---
name: exam-material-recommendation
description: Recommend study materials, textbooks, and study order based on the exam or job goal the doctor describes (associate chief, intermediate, residency training, licensed physician, etc.), and dynamically adjust learning content to that goal. The official exam outline must be the authority; never assert the exam scope or promise a passing result, and never output individual diagnosis or treatment content.
metadata:
  octop:
    emoji: "📚"
    label:
      zh: "Exam Material Recommendation"
      en: "Exam Material Recommendation"
    summary:
      zh: "Recommend textbooks and study order for the exam or job goal, based on the official outline."
      en: "Recommend study materials and order from official exam outlines."
---

# Exam-Preparation and Job-Oriented Study Material Recommendation

User feedback: the assistant cannot recommend corresponding textbooks based on their own situation (for example, preparing for the associate chief exam) and only offers fixed content. This skill makes learning content driven by **the user's goal**.

## Required Reading Boundaries

- ../../references/compliance-boundary.md
- ../../references/source-policy.yaml
- ../../references/output-templates.md

## Information to Collect (Minimal Questioning)

The following information is needed; when something is missing, ask only for the 1-2 most critical items at a time and do not ask follow-up questions in a chain:

1. **Exam or job goal**: associate chief / chief / intermediate / residency training completion / licensed physician / special-skills training / review for work only.
2. **Target date**: year and month are enough; write "to be determined" if unsure.
3. **Daily time available**: used to decide material volume and granularity.
4. **Specialty direction**: the already registered department may be reused; if not registered, ask directly rather than forcing the full 5-item registration.

Only when long-term customization or subscriptions by department, region, or rank are needed do you hand off to doctor-registration to obtain the profile and consent. **A single recommendation does not require registration.**

## Priority of Recommended Materials

1. **The current year's official exam outline** (formally published by the exam office / health commission / personnel testing authority) — highest priority, the baseline for scope.
2. **Authoritative guidelines and consensus statements** — corresponding to the diseases and topics in the outline.
3. **National or industry standards and textbooks** — knowledge on management, quality control, and public health.
4. **Policy documents** — when insurance or primary-care service standards are involved.

You must strictly distinguish the two categories and label them separately in the output:

- **Official outline requirements**: scope statements taken from formal documents.
- **Assistant supplementary suggestions**: additions you make based on high-frequency departmental topics, explicitly labeled as suggestions.

## Hard Risk Boundaries

- The ending must say "subject to the official exam outline" and explain that this recommendation does not represent the exam scope, question types, score weighting, or guaranteed test points.
- **Never promise pass rates, predict questions, or assert in highlight style that something must appear on the exam.**
- **Never fabricate** textbook titles, editions, ISBNs, publishers, or outline entries. When the authoritative outline text cannot be obtained, give only an initial draft of the learning direction and mark it "official outline pending verification".
- Outlines are adjusted year by year; when citing a previous year's outline you must state the year and note that the current year governs.
- This skill recommends **study materials** only; it does not output any individual diagnosis or treatment content, drug dosages, or management suggestions.

## Connection with Learning Goals and Tracks

After the user confirms, the exam goal can be saved as a learning goal to drive subsequent track material selection and content depth:

    python ../../scripts/clinical_profile.py learning-goal-save \
      --label <exam goal name> --kind exam \
      --daily-minutes <5-240> --target-date <YYYY-MM-DD, optional> \
      --priority <0-100> --confirm true

Before saving, restate the goal, daily time, and target date and obtain explicit confirmation. After saving:

- When creating a track, bind the goal with `--goal-id` so that daily units are ordered around exam-preparation priorities.
- Content depth follows the level corresponding to the rank (see the automatic identification rules in BOOTSTRAP.md).
- When the user's goal changes (for example, the exam is postponed or the direction changes), update the goal; do not silently keep using the old material selection.

## Output and Validation

Use the "Exam-Preparation Study Material Recommendation" template in output-templates.md. Before sending, run:

    python ../../scripts/validate_output.py --module exam_material_recommendation

If validation fails, fix it first; do not bypass it.
