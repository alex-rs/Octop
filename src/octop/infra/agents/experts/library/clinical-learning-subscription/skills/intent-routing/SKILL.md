---
name: intent-routing
description: Intent recognition and skill routing at the request entry point. Judge the intent progressively: general tasks first (do them directly), then high-risk clinical (refuse), then distinguish pure source verification from medical learning, and finally registration/subscription. Pure source verification goes through source-verify first; when the original path is restricted, it then enters medical-source-failover. Only medical learning calls the corresponding skill + output-format validation.
metadata:
  octop:
    emoji: "🧭"
    label:
      zh: "Intent Routing"
      en: "Intent Routing"
    summary:
      zh: "Identify and dispatch general tasks, high-risk clinical, source verification, and medical learning."
      en: "Route general, clinical, source-verify, and learning requests."
---

# Intent Recognition and Routing

Judge each request progressively in the following order; on a hit, execute immediately and do not continue downward:

1. **General tasks** (writing/summarizing/translation/programming/planning/data/creative/chat) → complete them directly; do not call medical skills, do not require registration, and do not apply medical rules.
2. **A high-risk clinical diagnosis or management request is detected** (individual diagnosis, prescription dosages, emergency management, disease SOPs, reimbursement conclusions, HIS rules) → refuse that request; you may suggest switching to authoritative guideline learning, and after refusing do not add diagnosis-and-treatment steps or medication details.
3. **Pure source verification** (whether it is an authoritative original text, whether it is the latest valid version, version comparison, revision/supersession/repeal relationships) → first call `source-verify`; when it hits blocking, a timeout, a redirect, a paywall, or incomplete body text, let it continue by calling `medical-source-failover`. It still outputs per the [Source Verification] template and does not call `output-format` or `validate_output.py`. If learning content is also required, then move to the next category.
4. **Ordinary educational medical Q&A** (concept explanations, common misconceptions, "is this statement accurate", with no request for precise recommendations/locators and no high-risk drug facts) → the `clinical-q-and-a` fast path; by default, verify only one domestic authoritative body of text, use the embedded short template and lightweight self-check, and do not call section expansion, subagents, or full format validation.
5. **Structured medical learning** (guideline learning/section expansion/pathway maps/learning diagnosis/exam prep/medical insurance/guideline updates) → call the corresponding skill, find information from authoritative guidelines and cite the source, and pass `output-format` validation before output; when progress/tracks/diagnosis/subscription/regional customization must be saved, confirm registration first.
6. **Registration/subscription** (register/update/disable/enable push) → `doctor-registration` (registration) / `subscription-setup` (subscription, which requires prior registration).

## Judgment points

- Look at the **substantive purpose** of the output, not whether a particular word appears: ordinary text such as `delivery`/`import`/`5 g of data`/`iv` (a variable name) does not trigger medical interception.
- Medical words appearing inside a general task are only ordinary text; the safety domain is enabled only when medical learning/medical insurance is genuinely asked about or when the request lands on individual diagnosis and treatment.
- Switch naturally when the topic changes; there is no requirement to "re-enter a mode"; the routing result is used only internally, and the user side only sees the normal output of the corresponding skill.
