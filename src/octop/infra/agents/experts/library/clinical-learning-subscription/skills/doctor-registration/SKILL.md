---
name: doctor-registration
description: Use when a doctor provides or updates the five registration items (title, region, hospital, department, rank), changes department/region/rank, or asks to deactivate or delete subscription data. This skill only covers writing/updating/clearing registration data; creating subscription tasks after registration is handled by the subscription-setup skill. It does not enable diagnosis, treatment, disease SOPs, emergency action cards, individual patient advice, drug dosage, HIS decision support, or insurance reimbursement conclusions.
metadata:
  octop:
    emoji: "🪪"
    label:
      zh: "Doctor Registration"
      en: "Doctor Registration"
    summary:
      zh: "Register or update the five items: title, region, hospital, department, and rank."
      en: "Register or update title, region, hospital, department, and rank."
---

# Doctor Registration, Update, and Deactivation

## Required Reading Boundaries

Before registering, updating, or clearing registration, you must read and comply with:

- ../../USER.md (script-generated read-only summary, if present)
- ../../references/compliance-boundary.md

Registration, updating, and clearing must all call ../../scripts/clinical_profile.py. Do not edit USER.md directly, and do not look for any other USER.md on your own. Creating subscription tasks is outside the scope of this skill and is handled by the `subscription-setup` skill.

## Registration Fields

Collect only the following 5 items of doctor information:

- Title: a surname, nickname, or "Dr. X" is acceptable; a real name is not required.
- Region: province / city / district or county.
- Hospital.
- Department.
- Current rank.

Do not request patient information. Do not turn questions about hospital capabilities, equipment availability, or bed capacity into a mandatory registration form.

Learning goals, learning diagnosis summaries, and learning tracks may be saved separately after the user confirms; they do not require these 5 items. Register only when the user needs subscriptions customized or enabled by region, hospital, department, or rank.

## Consent and Privacy

Before saving registration information, you must obtain the doctor's explicit consent to process these 5 items. If the user has already supplied the fields but has not explicitly consented, ask for confirmation first; do not write to state or generate a receipt directly.

Registration information is written to structured state through the profile script, which then automatically generates USER.md. If the script refuses to write, do not tell the user that registration is complete. Do not write patient information into any profile.

Recommended commands:

    python ../../scripts/clinical_profile.py get
    python ../../scripts/clinical_profile.py register --display-name <title> --region <region> --hospital <hospital> --department <department> --title <rank> --consent-confirmed true
    python ../../scripts/clinical_profile.py clear --confirm true

If the current working directory is not the skill directory, use the script at the root of the expert package; do not pass file path arguments.

## Progressive Completion Rules

Registration may be completed over multiple turns. Ask about only one missing field per turn; do not list the full table at once unless the user explicitly asks to complete everything in one go.

Recommended order:

1. Title: How should I address you going forward? A surname, nickname, or "Dr. X" works; a real name is not needed.
2. Region: Which region's insurance policies do you mainly follow? Just give the province / city / district or county.
3. Hospital: How is your hospital recorded? An abbreviation is fine.
4. Department: Which department do you mainly work in now?
5. Rank: What is your current rank? For example resident, attending, associate chief, chief, or roles such as quality control / insurance / medical records.

Handling rules:

- First call the script's get command or read the script-generated USER.md to determine the existing state; if consent state and all 5 items are already complete, go directly to change handling and do not ask again.
- If the user has not yet explicitly consented to processing the 5 items, ask only about consent first and do not ask about other fields.
- If the user has consented but the information is incomplete, ask only about the next missing field.
- If the user provides several items at once, extract the known fields and ask only about the next missing field or confirm consent.
- If the user provides patient information, ignore it and note that this assistant does not store patient personal information.

## After Registration Is Complete

Once all 5 items are complete and the user has explicitly consented, call `register`. The script handles region normalization, department system identification, rank depth mapping, and USER.md generation; do not expose the script's output JSON in your reply.

After the registration receipt is given, route according to the user's intent (routed by the `intent-routing` skill):

- The user wants to enable a subscription task (daily guideline learning / guideline update reminders / insurance learning) → hand off to the `subscription-setup` skill for creation.
- The user wants learning diagnosis, section expansion, exam material selection, insurance Q&A, or other intents → `intent-routing` routes to the corresponding skill.
- Subsequent delivery reads region, hospital, department, and rank depth from the script-generated USER.md by default; do not repeatedly ask for the 5 registration items.

## Prohibitions

Do not create, imply, or claim to have enabled the following capabilities:

- Disease diagnosis and treatment SOPs.
- Emergency action cards.
- Patient consultations or individual patient advice.
- Drug dosage, route of administration, frequency, or course-of-treatment generation.
- HIS decision support or pop-up rules.
- Insurance reimbursement conclusions, payment ratio commitments, or judgments about whether a hospital can reimburse.

## Output Requirements

The registration receipt uses the template in ../../references/output-templates.md. Only after register returns ok: true may you output "recorded". Every receipt must include the medical learning boundary statement: learning and policy summaries are based on authoritative guidelines and do not provide individual diagnosis or treatment or prescription dosages; emergency management and insurance reimbursement are only educational suggestions at the guideline/policy level and are not grounds for action or reimbursement; the user's ordinary general tasks can be handled directly and do not require registration.
