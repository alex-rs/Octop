---
name: guideline-section-expansion
description: Expand a verified authoritative guideline section by section following the original structure and give original-text locators to help doctors understand the original text; it can also organize a guideline into a learning pathway map (learning order). Must not generate diagnosis-and-treatment plans, bedside management steps, disease SOPs, emergency action cards, individual patient advice, or drug dosage explanations.
metadata:
  octop:
    emoji: "📑"
    label:
      zh: "Section Expansion"
      en: "Section Expansion"
    summary:
      zh: "Expand guideline sections following the original structure, or organize a learning pathway map."
      en: "Expand verified guideline sections or build a learning pathway."
---

# Guideline Section Expansion and Learning Pathway Map

The two most common sentences in user feedback are "I found the guideline but cannot expand it" and "can you summarize the guideline into a process". This skill handles these two things and strictly limits them to **learning artifacts**.

## Minimal required reading set

- When the user asks only to summarize a single topic such as screening, follow-up, or quality control, this skill already embeds the learning boundaries, common source rules, and output fields; do not read `source-policy.yaml`, `compliance-boundary.md`, or `output-templates.md` any more. In the end, `validate_output.py` still validates with the full policy.
- When the user asks for a full section expansion or a learning pathway map, then read `../../references/compliance-boundary.md` and `../../references/output-templates.md` as needed.
- All of the above are definite paths; do not locate them via `glob`, `grep`, or recursive `ls`.

## First distinguish which one the user wants

| What the user says | Use |
| --- | --- |
| Expand this chapter, look closely, explain in detail, what does this section say, show the full text | Section expansion |
| Summarize the learning points of one topic in the guideline, such as screening, follow-up, quality control | Section expansion |
| How to study this guideline, learning order, summarize into a process, give me a pathway | Learning pathway map |
| How well have I mastered it, test me, weak points | guideline-learning-diagnosis skill |
| Set up continuous daily learning | guideline-learning skill |

When the user hits "summarize the learning points of one topic", jump directly to the "Topic summary fast path"; that section already gives the complete execution rules and no additional reference file is read.

When the user says "process", you **must first confirm that they mean a learning order**. If what they actually want is "what to do first and what next when encountering this kind of patient", that is a bedside management request: refuse it under the high-risk criteria of compliance-boundary.md and explain that it can be changed into a learning pathway map.

## Prerequisite: a verifiable original text is required

Both expansions and pathway maps must be bound to a verified authoritative document: full name, issuing body, version/year, authoritative original link.

- When the authoritative original text cannot be obtained, **do not expand from memory**. You may only state "no verifiable authoritative original text was obtained" and give candidate source directions.
- A full section expansion or pathway map may use only final sources within the source-policy.yaml whitelist; topic summaries follow the equivalent rules embedded in the fast path below. Aggregator platforms serve only as leads by default; only when the original body text is explicitly access-restricted, S/A formal metadata is obtained at the same time, and title/body/version/DOI/full-text completeness/current status have been verified may the B+ platform designated by source-policy.yaml serve as the body-text hosting channel.
- When the user explicitly specifies an international guideline, or a current domestic formal document does not cover the topic, read `../../references/international-guideline-source-routes.yaml`. For ordinary supplementation, choose only the single best-matching site from the WHO, NICE, ESC, ADA, and KDIGO default pool; when systems such as GINA, GOLD, ACG, and EASL are explicitly involved, go directly to the corresponding official website. If the first site genuinely does not cover the topic, add at most 1 site; do not iterate in parallel. Do not use international recommendations to silently override the current standards of mainland China.
- The version must be stated clearly. Guidelines are revised frequently, so when expanding an old version, mark which version it is.

## How to do a section expansion

A full section expansion uses the "Guideline section expansion" template in output-templates.md; a topic summary uses the field list of the fast path below directly. Key points:

1. **Give the original-text locator**: chapter number, section number, item number, or page range, so the user can return to the original text to check. This is the core value of this capability.
2. **Explain following the original structure** and do not rearrange it into your own logic; state this section's position in the overall guideline structure and its relationship with the preceding and following sections.
3. **Do structured summaries only; do not copy the full text paragraph by paragraph**. The goal is to help the user understand, not to replace the original text, and copyright issues must also be avoided.
4. Mark the evidence grade and strength of recommendation (write them if the original text has them, do not invent them if it does not).
5. Point out the easily confused places — these are the real learning pain points of doctors.
6. The ending must declare that it **does not replace the original text** and that the authoritative original text prevails.

Expanding the definitions, diagnostic criteria, differential-diagnosis frameworks, stratification concepts, examination and follow-up requirements, quality-control indicators, and conceptual relationships between sections in a guideline is allowed. These clauses **must not** be applied to a real patient to draw a conclusion, and must not be rewritten into a hospital-executable document.

### Topic summary fast path (hard performance constraints)

When the user asks for a primary-care-oriented summary of a single topic such as screening, follow-up, or quality control:

0. By default, choose only 1 current main guideline that can directly cover the question. When the user has not asked for a cross-guideline comparison, do not proactively extend to geriatric specials, primary-care specials, or other parallel documents; add a second one only when the main guideline genuinely lacks the topic. Search, fetching, B+ degradation, draft validation, and rewriting share the same cumulative tool budget, and it must not be re-counted at any stage.
1. Directly read `../../references/verified-source-entrypoints.yaml` and first match the topic by `aliases`. When it hits, directly `web_fetch` that entry's `canonical_url`; only when both the page title and DOI match may it serve as the final basis; do not use local table entries to replace original-text verification.
2. When an entry hits and the current date has not passed `recheck_after`, that original-text fetch is the real-time verification and no broad search is done. Only when the user explicitly asks about "latest/current/superseded", or `recheck_after` has passed, add 1 more currency search restricted to official domains.
   The final source line must use the `canonical_url` of the matched entry; `official_index_url` only assists in checking the volume/issue/DOI and does not replace the original-text link. When a paywall means only the abstract or a public appendix can be checked, the specific clauses that could not be checked must be marked "pending verification", and second-hand content must not be used to fill the gap.
2.1 When there is no hit in the high-frequency entry list but the topic corresponds to a professional society or specialty branch, directly read `../../references/professional-society-source-routes.yaml` and, by branch name or `aliases`, choose one most relevant official domain for the first restricted search; do not iterate over all branches in parallel. Domains marked `official_discovery_pending_fulltext_acceptance` are only used to find the complete formal original text and cannot directly serve as the final source.
3. Only when the original body text encounters 412, a CAPTCHA, JS blocking, a timeout, or unavailable body text is a controlled B+ degradation allowed: first verify the title, body, year/version, and DOI/document number using the original publisher's/formal journal's metadata page, then fetch the complete formal body text from the designated B+ platform and check completeness and current status. In the end, list two sources at the same time, "original metadata" and "body-text host"; if only the B+ page or any single field is inconsistent, stop immediately and do not generate learning points.
4. When there is no hit in the entry table, the normal target is 1 targeted search + 1 body-text fetch, and the **total tool budget for the whole user turn** has a hard cap of at most 3 `searchfree_search` calls and 3 `web_fetch` calls, including failures, timeouts, empty results, international supplementation, B+ degradation, tier-C whole-web paraphrases, post-validation link supplementation, and rewrites. At most one targeted query per tier: domestic A → international A (only when the user specifies it or there is no domestic coverage) → tier-B discovery/B+ hosting or tier-C whole-web. Do not switch to old-version files or guess URLs to keep probing. Stop searching immediately after finding 1 current formal main guideline that covers the topic.
5. When the current authoritative original text is not obtained within budget, do not generate an "original-text expansion" or claim to have mastered the original text. If a tier-C web page clearly gives the original authoritative journal/body, full title, year/version, and DOI/document-number information, a separate "background paraphrase" failure receipt may be output and disclosed per the tier-C format of `source-verify`; otherwise reply "no verifiable current authoritative original text was obtained, so no learning points are generated this time". A tier-C paraphrase must not involve precise recommendations, evidence grades, or high-risk drug information.
6. The final basis defaults to 1 document and at most 2: 1 current main guideline; add 1 specialty guideline only when the main guideline genuinely does not cover the question or the user explicitly requests a comparison. Only formal guidelines, consensus statements, standards, or quality-control documents are accepted; review articles, original research, popular-science material, reprints, conference materials, and search snippets must not serve as the final basis.
7. Commonly used domestic original-source domains include `.gov.cn`, `.nhc.gov.cn`, `.ndcpa.gov.cn`, `.chinacdc.cn`, `.cma.org.cn`, `.medjournals.cn`, `.cmda.net`, `.cpma.org.cn`, `.pmph.com`, `cs.medjournals.cn`, `bi-dmp-cs.yiigle.com`, and `rs.yiigle.com`. Tier-A international domains follow `international-guideline-source-routes.yaml`. Search results are only used to locate the original text; before drafting, first choose the original-text detail page or formal attachment link. A generic list page can only be a candidate and cannot serve as the original-text link when it cannot be matched to a specific document.
8. When there is no hit in the entry table, the first query must include the topic, "latest/current", and the professional branch/society domain matched from the registry at the same time; only when there is no professional route should `site:rs.yiigle.com` and `site:cs.medjournals.cn` be preferred. The second query checks the competent authority or formal journal platform; the third is used only to confirm a version supersession relationship or to locate the complete B+ body text after the original body text is access-restricted. The current version must be confirmed first and the content summarized afterwards; when a new version has been published, do not fall back to the old version to cobble together an answer.
9. All URLs in the draft (including those in the body and the source line) must belong to the original-source whitelist, or satisfy the paired degradation rule of "original metadata + B+ body-text host"; do not first write in a CDN, a search result, or another non-whitelisted URL and then rely on the validator to revise it repeatedly.
10. When output validation fails because of an auxiliary source domain or document type, delete that auxiliary source and redraft using the already verified main guideline; when the cumulative budget is exhausted, do not keep searching to add links. Generate a complete draft directly with the following fields: [Guideline Section Expansion | topic], basis, section, original-text locator, key points of the original text, section relationships, easily confused points, learning tips, boundary, source. Do not write a half-finished draft first, and do not read other files again just to guess the template.

## How to build a learning pathway map

Use the "Guideline learning pathway map" template in output-templates.md. Key points:

1. State clearly for each step: what to study → which section of the original text it corresponds to → estimated time → mastery marker (the user can self-check).
2. Order the steps by **cognitive dependency** (definitions first → then framework → then details → then follow-up and quality control), not by clinical timeline.
3. State the prerequisite knowledge and adjust the granularity to the time the user can invest; when there is a learning objective (such as exam preparation), trim the focus to that objective.
4. Offer "optional deep dive" so the user can choose the direction of deeper study themselves — this is exactly the "choose the scope of further learning" requested in the feedback.
5. Each step must map to a section of the original text; when it cannot, mark it as pending verification and do not pad the list.

**Hard constraints**: expressions such as "management process", "diagnosis-and-treatment process", "resuscitation process", "handling process", and "emergency action card" must not appear, and the learning order must not be written as a bedside execution order. The distinguishing criterion is — "learn the definitions before the stratification" is a learning order; "give oxygen first, then establish intravenous access" is a management process and is forbidden.

## Connection with learning tracks

After the pathway map is confirmed, the user may ask to save it as a continuous learning track. At that point switch to the guideline-learning skill and persist each step of the pathway map as a fixed learning unit (ordinal + source_anchor + objectives).

The pathway map itself is a read-only artifact: it does not create a delivery ledger and does not advance learning progress. If the user is only taking a look, write [Format Preview | Not Counted Toward Progress] as the first line of the body.

## Output and validation

Before sending or providing a formal draft, generate the complete draft in one go per the conventions of the `output-format` skill, and preferably run the validator directly through standard input within a single tool call, avoiding a synchronization round trip between writing a file and the execution environment:

    python3 ../../scripts/validate_output.py --module guideline_section_expansion

Or:

    python3 ../../scripts/validate_output.py --module guideline_learning_pathway

Do not dry-run the validator without a body, and do not read or `grep` the validator source code. When validation fails, fix it once only according to the returned `errors`; do not bypass it.
