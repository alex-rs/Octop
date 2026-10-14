---
name: source-verify
description: Fast or full verification of medical sources. Ordinary educational medical Q&A uses fast verification against a single authoritative body of text; requests about the latest version, precise recommendations, high-risk drugs, insurance regulation, or cross-version changes escalate to full verification. It only organizes the learning basis; it does not generate diagnosis or treatment, prescriptions, emergency handling, insurance reimbursement conclusions, or HIS execution advice.
metadata:
  octop:
    emoji: "🔍"
    label:
      zh: "Source Verify"
      en: "Source Verify"
    summary:
      zh: "Verify authoritative medical original texts, version currency, and revision/replacement relationships."
      en: "Verify authoritative medical sources, versions, and replacements."
---

# Unified Source Verification

## Routing Boundary

When purely judging whether a file is an authoritative original text, whether it is the latest and in effect, and the revision/replacement/repeal relationships, use only this skill and the [Source Verification] template below, and do not call the `output-format` skill or `../../scripts/validate_output.py`. If the user also asks for guideline learning content, first complete source verification, then hand the verified sources to the corresponding medical learning skill, and run `output-format` validation only on the learning content.

## First Choose the Verification Tier

### Fast Verification (default)

Applies to ordinary educational medical Q&A, concept explanations, clarification of common misconceptions, and general learning summaries, when none of the full-verification triggers below apply.

- The goal is to obtain **1** current authoritative normative text sufficient to cover the question; do not actively gather multiple documents to "corroborate" one another.
- The minimum checks are: authoritative institution/official publication domain, normative document type, full title, issuing institution, year/version, and whether the body of text can support this claim.
- When the official original-text page already states the above identity, finding a second source is not mandatory; when the original text has no DOI/recommendation grade, write "not stated" truthfully, and do not keep searching just to fill in fields.
- When a verified entry point that has not passed its `recheck_after` is matched, fetch the body of text directly and check its identity; when the user has not asked about "latest/current/replacement", do not add a currency search.
- Stop immediately once one document satisfies identity, body of text, and coverage scope.

### Full Verification (escalate on demand)

Escalate only when any of the following occurs: the user explicitly asks about latest/current/replacement/repeal, cross-version changes, precise recommendations or evidence grades, or chapter/table/page/item localization; indications, contraindications, dosage, pregnancy or pediatric use, serious adverse reactions, invasive or emergency content; or drug approval, regulation, insurance, or legal status. Full verification retains version status, unique identifiers, precise localization, and the necessary same-document identity verification requirements.

The verification tier only removes unnecessary steps; it does not change the bottom line that "second-hand summaries must not be used to fill in precise clinical facts".

## Read Files On Demand

Fast verification reads only `../../references/verified-source-entrypoints.yaml` first. If an entry is matched, fetch from its direct entry point; do not pre-read the full allowlist or the compliance notes.

Read the corresponding file in these cases:

- Entry point not matched, or a judgment about domain/document type/B+ or C-tier eligibility is needed: `../../references/source-policy.yaml`
- The request approaches individual diagnosis or treatment, prescriptions, or another medical boundary: `../../references/compliance-boundary.md`
- The target is issued by a Chinese professional society or subsociety and the entry point is not matched: `../../references/professional-society-source-routes.yaml`

The above are fixed paths; read them directly. Do not call `glob`, `grep`, or recursive `ls` to locate these files.

When the user explicitly specifies an international guideline, or current Chinese formal documents do not cover the target topic, then read
`../../references/international-guideline-source-routes.yaml`; do not pre-read that table for ordinary Chinese topics.

## Order of Using Verified Entry Points

1. First match the user topic against the `aliases` of `verified-source-entrypoints.yaml`. Only move to regular online search when there is no match.
2. On a match, `web_fetch` the entry's `canonical_url` directly; fast verification checks at least the title, issuing institution, year/version, and coverage of the body of text; when the entry provides a DOI, check the DOI too. In full verification, a conflicting unique identifier means the entry must not be used.
3. When the current date has passed `recheck_after`, or the user explicitly asks about "latest/current/replacement", add 1 currency search restricted to official domains; without evidence of a new formal original text, do not rewrite the entry's version status based only on a search snippet.
4. `version_relation` is the verified expression boundary. When it says "no repeal/replacement statement obtained", you must truthfully output "no formal repeal or replacement has been confirmed"; do not infer on your own.
5. The final original-text link of a matched entry must use that entry's `canonical_url`; `official_index_url` is only for auxiliary checks of volume/issue/DOI and must not replace the original-text link. When the full text is restricted by subscription, you may explain that the verifiable scope is limited, but you must still give the `canonical_url`.

## Fast Routing for Professional Societies

When a high-frequency entry point is not matched and the target file is formulated/published by a professional society, association, or specialty subsociety, read
`../../references/professional-society-source-routes.yaml` directly, first match by subsociety name and `aliases`,
and then run a domain-restricted search; do not start with a broad search without a domain.

- For Chinese Medical Association subsocieties, first match the registered dedicated `*.cma.org.cn` subdomain; when there is no dedicated subdomain, use the official specialty subsociety directory to confirm identity, then search restricted to `cma.org.cn`, `medjournals.cn`, or `rs.yiigle.com`.
- A `conditional_final` route must still pass formal document type, completeness, and version verification; a domain match alone does not constitute final evidence.
- An `official_discovery_pending_fulltext_acceptance` route can only locate publication information and the formal original text, and must not go directly into the final source line; you must continue to obtain the S/A formal original text or complete that site's full document identity acceptance.
- Stop immediately after finding one complete current formal document sufficient to cover the question; do not traverse other society websites.

## Source Tiering

- Normative original text on S/A-tier authoritative domains: after passing document type and version verification, it can serve as the final learning basis.
- All international A-tier sources retain evidence eligibility, but the default pool is fixed at WHO, NICE, ESC, ADA, and KDIGO. An ordinary international supplement calls only the 1 best-matching website, and when the first site truly does not cover the topic, at most 1 more may be added. When the question clearly belongs to a specific system such as GINA, GOLD, ACG, AGA, ASGE, ESGE, EASL, AASLD, or ECCO, go directly to that official source; do not traverse the default pool first, and do not silently override current Chinese regulations.
- Designated B+ professional platforms: by default they still only serve as leads; only when the S/A original text shows 412, a CAPTCHA, JS blocking, a timeout, or an unobtainable body of text may they serve as the formal full-text hosting channel. You must also obtain the S/A original publisher or formal journal metadata link, and complete six checks: title, formulating institution, year/version, DOI/document number, full-text completeness, and current version.
- B-tier lead sources: used only to find candidate documents; they must be traced back to the S/A original text, and the B+ downgrade does not apply to them.
- C-tier web-wide relay: when neither A nor B yields a usable original text or a complete identity chain, a web-wide search is allowed and a clearly attributed background relay may be output, but it is not final evidence. You must also state "relay page (C-tier, background only)", the original journal/institution, the full title of the original article or guideline, the year/version, the DOI/document number (if the page does not give one, truthfully write that it is not provided), and "no verifiable original text was obtained". No precise recommendations, evidence grades, indications, contraindications, dosage, serious adverse reactions, pregnancy/pediatric medication, or emergency/invasive handling may be extracted from it.

Specific domains and prohibited patterns follow `../../references/source-policy.yaml`.

## Chinese Context and Controlled Downgrade Order

For general learning requests from primary-care doctors in mainland China, look first by default for current Chinese formal guidelines/consensus/standards; when the user explicitly specifies an international document or China has no coverage, then use international formal documents within the requested scope. Do not silently override current Chinese documents with international recommendations.

When the original page or attachment shows `401`, `403`, `412`, `429`, a CAPTCHA, a paywall, a timeout, a relocation, an empty-shell page, or an incomplete body/PDF, read `../medical-source-failover/SKILL.md` and, as it requires, read the corresponding Chinese source registry, circuit-breaker, and document identity verification files. That skill is only responsible for finding a trusted access path to the same target document; it does not change this skill's judgment on document type, version, and final evidence eligibility. If the two rule sets differ, apply the stricter one; when only L5 metadata, abstracts, interpretations, screenshots, or an incomplete body of text can be obtained, precise extraction must stop.

Search strictly in the following order, and stop as soon as one succeeds:

1. The S/A original text in verified entry points;
2. The Chinese S/A original text located by regular search;
3. When the user specifies an international guideline or China has no coverage, search official international A-tier formal guidelines;
4. Use B-tier platforms to discover the original source; after the original text is clearly access-restricted, dual verification with the S/A formal metadata page + the designated B+ complete body of text may be used;
5. Only when the original text is still unobtainable, run one web-wide C-tier search. A clearly disclosed background relay may be output, but it must not be called "authoritative original text", "original-text key points", "formal basis", or "body-of-text host".

### Tool Budget and Stop Conditions

- Normal target: 1 targeted `searchfree_search` + 1 `web_fetch`; when a verified entry point is matched, usually only 1 `web_fetch` is needed.
- Hard cap for the whole user turn: at most 3 searches + 3 fetches, counting failures, timeouts, B+ downgrades, C-tier relays, link patching, and draft rewrites alike, and it cannot be reset.
- At the same stage, access only one best-matching domain, executed in order; do not search multiple Chinese subsocieties or international institutions in parallel by default.
- Internationally, usually 1 site and absolutely at most 2. For a specific guideline system, go directly to the corresponding official website rather than running the default five sites first.
- Stop immediately after finding one authoritative normative document that is current, has a confirmed identity, has a verifiable body of text, and covers the question.

A-tier authority and access priority must be kept separate. `nhc.gov.cn`, `gov.cn`, `nmpa.gov.cn`, `cmde.org.cn`, `rs.yiigle.com`, `csco.org.cn`, and similar sites retain A-tier eligibility even when access is unstable, but must not be the first broad search target for an unmatched topic. Prefer verified specific direct pages, `cs.medjournals.cn`, `bi-dmp-cs.yiigle.com`, `cjournal.hep.com.cn`, same-origin attachments, official reprints, or formal journal versions. Access these low-priority main sites directly only when the entry table already has an exact `canonical_url`, or when drug regulation/insurance/legal facts must go back to that competent authority; after a clear block, switch according to the circuit-breaker rules instead of waiting on the same address repeatedly.

### C-tier Relay Output Format

```text
Source: relay page (C-tier, background only): [Link]({any legal public web URL})
Original source: {original journal or institution} | {full title of the original article/guideline} | {year or version} | {DOI/document number; if not provided, explicitly write not provided}
Verification status: no verifiable original text was obtained; the following is only this page's relay of the original source and is not an authoritative basis.
```

When a page only says "from an authoritative journal" without giving an identifiable journal/institution, title, or year/version, it does not meet the relay disclosure requirement. Multiple reprinted pages must not be counted as multiple independent pieces of evidence.

## Dedicated Layer for Drug Information

For drug indications, contraindications, dosage, and adverse reactions, check the National Medical Products Administration, CDE, the Center for Drug Reevaluation/National Center for ADR Monitoring of the NMPA, and official approved package inserts first. The generic name, dosage form, strength, route of administration, approval number, marketing authorization holder/manufacturer, and package insert version must match; CDE technical guidelines, insurance payment restrictions, guideline relays, and C-tier pages cannot replace the approved package insert of a specific product.

During a B+ downgrade, do not bypass CAPTCHAs or anti-automation limits, and do not retry the same failed address indefinitely. The final verification result must list two lines at the same time:

```text
Source: original metadata ({formal institution/journal}): [Link]({S/A URL})
Source: body-of-text host (original text access restricted): [Link]({B+ URL})
```

When there is only a B+ page without an independent S/A metadata link, or when any of title/institution/version/DOI is inconsistent, the only possible conclusion is "usable as a lead only". "Guideline interpretations", "consensus interpretations", editorial summaries, news, interviews, conference reports, case discussions, and popular science must not serve as the final basis even when they sit on a B+ domain.

All search and fetch budgets accumulate over the whole user turn, and B+ downgrades, validation failures, and draft rewrites must not reset the budget. Stop immediately when one current formal guideline is enough to cover the user's question; do not proactively expand to a second or third guideline for the sake of being "more complete"; add a second one only when the user explicitly asks for a cross-guideline comparison or when the main guideline truly does not cover the question. When output validation fails because of a link domain, prefer deleting the auxiliary source that failed and keeping the verified main guideline; do not use the draft rewrite as an excuse to start a new round of searching.

## Hard Document Type Threshold

An authoritative website does not mean every page on it is an authoritative basis. Once the domain qualifies, the document type must also be judged.

- The final basis accepts only formal guidelines/consensus, standards/clinical pathways/quality control standards, and formal policy or regulatory documents and attachments. Guidelines/consensus published in formal journals may be included according to their normative document type, but they do not automatically become the final basis just because they were "published in a journal".
- Systematic reviews, meta-analyses, narrative reviews, scoping reviews, umbrella reviews, rapid reviews, expert reviews, and other literature reviews must not appear in the final "source", the next-stage guideline candidates, or the sources of a formal learning track; at most they may be used internally to find formal guidelines, while continuing to trace back to the normative original text.
- Research or academic discussion such as randomized controlled trials, observational studies, case reports/series, editorials/letters, conference abstracts, and preprints must not replace the normative original text required by this product.
- Popular science, reprints/excerpts, interviews/media reports, public-facing physical examination knowledge or examination interpretations, conference/training/event reports, and marketing or institutional publicity must not serve as the final basis even on allowlisted websites.
- When a news, interview, or policy interpretation page links to the formal original text, that page only serves as a discovery lead; you must continue to trace back to and cite the formal original text or attachment.
- Do not judge by title keywords alone; for example, the formal "Health Examination Management Measures" should not be wrongly excluded because it contains "examination".

## Currency Rules

- For the same topic, prefer the latest and currently effective formal version rather than simply choosing the result with the largest web page year.
- The year is based on the document's formal publication date, revision date, or version identifier; do not treat a web page update time as the document version.
- You must check whether there is update, revision, replacement, or repeal information. An older version may be used only when it is still effective, when there is no new version, or for historical comparison, and the reason must be stated clearly.

## Full Verification Flow

1. Discover candidate documents.
2. Trace back to the original text or formal attachment of the guideline/consensus on official pages, society websites, or formal journals; try the original body of text first and do not jump straight to B+.
3. Check the document type first, excluding reviews, primary research, popular science, reprints, interviews, physical examination interpretations, and other non-normative texts.
4. Check the full name, issuing institution, publication date/year, version, and scope of application.
5. Determine whether there is a subsequent update, revision, replacement document, or repeal notice, and prefer the latest effective version.
6. When changes between old and new are involved, you must obtain both the new and the old original texts.
7. Insurance content must go back to the formal catalog, policy attachment, or formal document of the local medical insurance bureau.
8. In the output, list only the normative core sources directly related to the learning conclusion; when a B+ downgrade is used, list both the original metadata and the body-of-text host link, and state clearly that the original text is access-restricted; at the end of a cycle, 2-3 verified formal guideline candidates may be listed when recommending the next stage.

Fast verification does not mechanically execute the 8 steps above: output is allowed after "authoritative institution/official domain + normative document type + title/institution/year-version + body-of-text coverage" is complete. Enter the full flow only when a full-verification trigger is hit, or when an identity conflict, a version doubt, or an incomplete body of text is found.

## Prohibitions

Do not fabricate file names, document numbers, institutions, years, links, version relationships, insurance payment conditions, drug dosages, or your own hospital's capabilities.

When no actual search has been performed, you may only write "no verifiable authoritative source was obtained" or "manual verification is required". When the A/B/C ordered search has been performed but the original text is inaccessible, a C-tier background relay may be disclosed in the format above; do not disguise it as a confirmed update, an authoritative original text, or a formal basis.

When the search yields only reviews or research papers, treat it as "no verifiable formal guideline was obtained" as well, and do not use them to fill in the final source or the next-stage candidates.

## Output Requirements

The doctor-facing side outputs only a concise verification conclusion:

```text
[Source Verification]
Verification target: {file or topic}
Conclusion: {usable as a learning basis / usable as a lead only / not recommended for use}
Reason: {document type, institution, year, original-text accessibility, whether it is the latest effective version}
Source: {file name}: [Link]({URL})
Boundary: this verification is only for judging the learning basis; it does not provide diagnosis or treatment, prescriptions, insurance reimbursement, or in-hospital execution advice.
```
