---
name: clinical-q-and-a
description: Quickly answer ordinary educational medical questions and common misconceptions. By default, use one current domestic authoritative guideline/consensus to complete a lightweight verification and answer immediately; not for individual diagnosis or treatment, prescription dosages, precise recommendation locators, high-risk drug facts, medical-insurance regulation, or cross-version comparisons.
metadata:
  octop:
    emoji: "💬"
    label:
      zh: "Clinical Q&A"
      en: "Clinical Q&A"
    summary:
      zh: "Quickly clarify educational medical questions and common misconceptions from one authoritative source."
      en: "Answer educational medical questions from one authoritative source."
---

# Ordinary Medical Q&A Fast Path

Used for general educational questions such as "is this statement accurate", "how do I explain a common misconception to a patient", or "what is the relationship between a disease and a risk". The goal is a reliable, concise answer as quickly as possible, without expanding ordinary Q&A into guideline section research.

## Immediately route out when not applicable

- Diagnosis, management, prescribing, or emergency action for a specific patient: refuse according to the safety boundary, and do not give substitute steps.
- Indications, contraindications, dosages, pregnancy/children, serious adverse reactions, invasive procedures, regulatory or insurance status: route to `source-verify` for full verification and to the corresponding professional skill.
- The user asks for the latest version, version comparisons, recommendation grades, evidence grades, or chapter/table/page/item locators: route to `source-verify` for full verification.
- The user wants to expand a section of the original text or a learning pathway: route to `guideline-section-expansion`.

## Quick evidence gathering

1. Domestic authoritative guidelines, consensus statements, or standards take priority. By default, find only **1** current formal body of text sufficient to cover the question; do not call subagents and do not collect a second or third "corroborating" source.
2. First read `../../references/verified-source-entrypoints.yaml` and match the alias; when it hits and `recheck_after` has not passed, fetch `canonical_url` directly, verify the title, issuing body, year/version, and the body text supporting this explanation, then stop and do not search for the "latest" anymore.
3. When there is no hit, run 1 search restricted to domestic authoritative domains and fetch the single best-matching body of text. Prefer `cs.medjournals.cn`, `bi-dmp-cs.yiigle.com`, `cjournal.hep.com.cn`, known same-origin attachments, or official reprints; heavily blocked main sites such as `nhc.gov.cn`, `gov.cn`, `nmpa.gov.cn`, `cmde.org.cn`, `rs.yiigle.com`, and `csco.org.cn` are not the first broad targets unless there is already a precise direct link or the fact must be confirmed by that competent authority. Only when the target is published by a professional branch but the route is uncertain may you read `../../references/professional-society-source-routes.yaml`; do not iterate over all branches.
4. Only when there is no domestic coverage or the user explicitly requires international evidence may you read `../../references/international-guideline-source-routes.yaml`: the default pool is fixed as WHO, NICE, ESC, ADA, and KDIGO, and you visit only the single best-matching site; when systems such as GINA, GOLD, ACG, and EASL are explicitly involved, go directly to the corresponding official website. If the first site genuinely does not cover the topic, add at most 1 site, executed sequentially, not in parallel.
5. The normal budget is 1 search + 1 fetch; the hard cap for the whole turn is 3 searches + 3 fetches, and failures, degradations, and rewrites all count. Stop immediately once an authoritative document is obtained that is the latest, has a definite identity, has verifiable body text, and covers the question.
6. Call `medical-source-failover` only when the original text is blocked. Only one most appropriate alternative path for the same document is allowed; for an explicit CAPTCHA, login wall, or 403/412, do not retry the original address.

Quick verification only requires: an authoritative body/formal domain, a normative document type, a title, an issuing body, a year/version, and body text that can support the current claim. When the official text does not state a DOI or evidence grade, say so honestly and do not keep searching to fill in the field. Search snippets, interpretations, and reprints cannot support precise clinical facts.

## Answer structure and lightweight self-check

Output directly; do not load `output-format`, do not write a draft file, and do not run `validate_output.py`:

```text
[Clinical Learning Q&A | {topic}]
Conclusion: {first answer accurate/inaccurate/needs conditional understanding}
Explanation: {2-4 concise points, write only what the original text can support}
Evidence note: {guideline/consensus; keep the grade if the original text has one, otherwise write "not stated"}
Boundary: This answer is for medical learning and communication reference; it does not provide individual diagnosis or treatment or prescription advice.
Source: {formal document name}: [link]({authoritative original URL})
```

Before sending, check only four things within the same reasoning turn: there is a conclusion, there is a boundary, there is one authoritative original-text source, and nothing goes beyond the body of text or falls into individual diagnosis and treatment. If something is missing, fix the wording directly and do not open another round of retrieval. If no authoritative body of text was obtained, switch to a short failure receipt and do not fill it in from memory.
