---
name: output-format
description: Unified format validation for structured medical learning artifacts. The four hard formats and the single standard-input flow of validate_output.py. Used by guideline sections, pathway maps, diagnosis, exam prep, insurance, updates, and daily units; ordinary medical Q&A goes through the lightweight self-check of clinical-q-and-a, and general tasks are exempt.
metadata:
  octop:
    emoji: "✅"
    label:
      zh: "Output Format Check"
      en: "Output Format Check"
    summary:
      zh: "Validate the hard format of structured medical learning artifacts before sending them."
      en: "Validate structured medical learning output before sending."
---

# Output Format Validation for the Medical Safety Domain

## Scope

The output of the following modules (whether an immediate answer inside a conversation or a scheduled push) must be validated by this skill:

`guideline_learning`, `daily_guideline_learning`, `guideline_section_expansion`, `guideline_learning_pathway`, `guideline_learning_diagnosis`, `guideline_update_reminder`, `professional_update_summary`, `insurance_policy_summary`, `insurance_policy_learning`, `insurance_policy_retrospective`, `exam_material_recommendation`.

**Ordinary educational medical Q&A does not load this skill**: `clinical-q-and-a` uses its embedded short template and four self-checks, so that a brief explanation does not require loading the full template, writing a draft file, and starting the validation script. Once a question involves precise recommendations/localization, high-risk drug facts, version comparison, or insurance regulation, leave the fast path immediately and switch to the corresponding professional skill and to this skill.

**General tasks (writing/translation/programming/planning/data organization, etc.) are exempt from this skill**: no template head, no authoritative source line, and no medical disclaimer are required. When validating, use `--module general_task` for general output, and do not mistakenly use a medical module name.

**Pure source verification is exempt from this skill**: when only judging whether a file is an authoritative original text, whether it is the latest and in effect, and the revision/replacement/repeal relationships, the `source-verify` skill completes the work with its own [Source Verification] template, and neither this skill nor `validate_output.py` is called. If guideline learning content is still generated after verification, then call this skill on the learning content.

## Resource Paths

The following paths all locate the expert workspace two levels up from the current `skills/output-format/SKILL.md`; they must be used directly, and must not be located through `glob`, `grep`, or recursive `ls`, nor may the script source be read first in order to call the validator:

- `../../references/output-templates.md`
- `../../references/source-policy.yaml`
- `../../scripts/validate_output.py`

The validator receives the text to be validated from standard input or from `--text-file`. Do not run the validator without text, and do not guess parameters or template rules by reading or searching the source.

## Common Module Mapping

| Substance of the user request | module | Template requirement |
| --- | --- | --- |
| Ordinary concept explanation, clarification of common medical misconceptions | `clinical_q_and_a` | Lightweight self-check by `clinical-q-and-a`; the script flow of this skill is not executed |
| Summarizing, expanding, or explaining a chapter or section of a guideline, or a topic such as screening/follow-up | `guideline_section_expansion` | [Guideline Section Expansion]; includes basis, section, original-text localization, original-text key points, learning tips, boundary, and "does not replace the original text" |
| Organizing a whole guideline into a learning order or learning pathway | `guideline_learning_pathway` | [Guideline Learning Pathway]; includes basis, prerequisite knowledge, numbered learning order, boundary |
| Fixed daily learning unit | `daily_guideline_learning` | [Guideline Learning Unit]; exactly 3 numbered key points and the unit progress |
| Assessment of learning status or weak points | `guideline_learning_diagnosis` | [Guideline Learning Diagnosis] or [Guideline Diagnostic Criteria Study] |

Once the table above is matched, use the corresponding module directly; do not read the validator source to decide a second time.

## The Four Hard Formats (required every time)

1. **Template head**: the first line is `[{module name} | {topic}]`, for example [Guideline Section Expansion | Risk Stratification].
2. **Source line**: at the end, `Source: {file name}: [Link]({URL})`, positive example: `Source: National Health Commission official website: [Link](https://www.nhc.gov.cn/)`. When giving a journal name, DOI, or file name, you must also wrap it as a clickable link; a plain-text attribution alone is not allowed. When no authoritative link can be obtained, state explicitly "no verifiable authoritative source was obtained, manual verification is required" - never omit the source line and never fabricate a link.
3. **Boundary declaration**: one corresponding sentence per module - section expansion "does not replace the original text", exam prep "the official exam syllabus prevails", insurance "not a basis for reimbursement", and any request involving patients "no individual diagnosis or treatment".
4. **Never fabricate**: page numbers, item numbers, versions, file names, institution names - when no authoritative basis can be obtained, mark them "pending verification"; never fill them in from memory.

Detailed templates are in `../../references/output-templates.md`.

## Validation Flow

Before every medical safety domain output, follow this order strictly:

1. Generate a complete draft from the corresponding template in one pass; do not write a half-finished version first.
2. Prefer passing the complete draft to the validator through standard input, running it directly inside a single tool call:
   ```bash
   python ../../scripts/validate_output.py --module <module_name>
   ```
   Only when the currently executing tool cannot pass standard input, write to `../../outbound/.clinical-output-draft.md` and use `--text-file`; do not repeatedly read, write, or copy files just to synchronize the same draft.
   The module name must match the substance of the content (use a medical module name for medical learning content and `general_task` for general tasks).
3. Validation passes -> output the draft text directly. The draft and the final text must be in Simplified Chinese; do not output your thinking/retrieval/execution process to the user, and do not output procedural prefixes such as `I'll`, `Let me`, `Now running`, `Validation passed`, `Here is the answer.`, "validation passed", "validation complete", or "pushing preview content for you". Stay silent while retrieving and validating; do not first occupy the channel with English procedural sentences and then append the Chinese body.
4. Validation fails -> fix the draft only according to the `errors` returned by the validator and validate once more; do not read or search the validator source, and if it still fails, stop and explain why, **never bypass validation and output directly**, and never omit the [] template head or the source line.

## Hard Rules for the Source Line Format

Whenever this output queries, cites, or verifies an authoritative source, the source must be listed. Unified format:

```
Source: {file or page name}: [Link]({URL})
```

- Long URLs must not be exposed;
- The link text must not be written as other words such as "view original text", "official website", or "click here";
- Multiple sources are listed on separate lines;
- When there is no reliable source, do not fabricate a link; write only "no verifiable authoritative source was obtained or manual verification is required".

## Boundary

This skill only handles the format and validation of medical safety domain output; it does not generate medical content itself (content is generated by the respective professional skills), does not perform registration/subscription, and does not grade sources (source rules are in `../../references/source-policy.yaml` and the `source-verify` skill). General tasks and pure source verification are always exempt; never degrade general output under the pretext of format validation.
