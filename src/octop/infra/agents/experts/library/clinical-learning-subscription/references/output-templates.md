# Output Templates

## Ordinary medical Q&A (lightweight fast path)

Ordinary concept explanations and common misconceptions are handled by `clinical-q-and-a` and are not expanded into a section template:

    [Clinical Learning Q&A | {topic}]
    Conclusion: {accurate/inaccurate/needs conditional understanding}
    Explanation: {2-4 concise points}
    Evidence note: {guideline/consensus; keep the grade if the original text has one, otherwise write "not stated"}
    Boundary: This answer is for medical learning and communication reference; it does not provide individual diagnosis or treatment or prescription advice.
    Source: {formal document name}: [link]({authoritative original URL})

The fast path uses only one authoritative normative body of text sufficient to cover the question, and checks four things within the same reasoning turn: conclusion, boundary, source, and not going beyond the original text; it does not write a draft file or launch the format validation script. Precise recommendations/locators, high-risk drug facts, version comparisons, medical-insurance regulation, or individual management requests must not use this template.

## Registration activation receipt

Used when the user explicitly selects tasks and the tasks are actually created successfully (the platform cronjob_create automatically binds the current session channel, so no WeChat binding is needed):

    [Learning Subscription Enabled]
    Form of address/Hospital: recorded (not shown repeatedly by default in later pushes)
    Region: {province-city-district/county}
    Identified specialty: {department system} / {subspecialty}
    Content depth: {level corresponding to professional title}

    Enabled tasks:
    {list only the tasks the user explicitly selected and that were actually created successfully, noting "pushed to the current session channel" for each}

    Not enabled:
    {list the tasks the user did not select; write "none" when all are enabled}

    Note: The schedules for the above tasks have been created and the platform delivers automatically through the current session channel (WeChat/QQ/dashboard/CLI, etc.). Daily guideline learning uses the generic cron + weak-delivery dedup protocol (no channel receipt; the cron run prevails; deduplicated by logical date); before you select an authoritative guideline track it will not push knowledge points at random, and after selection it starts from unit 1.
    Medical learning boundary: This assistant performs medical guideline learning and policy summaries based on authoritative guidelines; it does not provide individual diagnosis or treatment or prescription dosages; for emergency management and medical-insurance reimbursement it only offers guideline/policy-level educational suggestions, not a basis for individual action or reimbursement; other general tasks may be raised directly.

When the tool is unavailable or creation fails, do not claim that the task is enabled; state the failure reason honestly and keep the registration record, and do not use "WeChat channel not bound" as a receipt.

## Daily guideline learning unit

    [Guideline Learning Unit | {department}]
    Track: {user-readable name}
    Basis: {full guideline name} ({version/year}, {issuing body})
    Learning unit: {ordinal} / {total_units}
    Section: {section anchor}
    Linked goal: {learning objective or "general learning"}
    Topic: {today's learning topic}

    1. {educational learning point one, no management orders}
    2. {educational learning point two, highlighting primary-care learning value}
    3. {educational learning point three, stating boundaries or local confirmation items}

    {For a non-final unit:
    Next unit preview:
    {next fixed unit topic} — {next unit learning objective}}

    {For the final unit:
    Optional guidelines for the next stage (pending confirmation):
    A. "{full name of the formal guideline}"({year/version}, {issuing body}): [link]({authoritative original URL})
       Recommended connection: {the connection with the current track}
    B. "{full name of the formal guideline}"({year/version}, {issuing body}): [link]({authoritative original URL})
       Recommended connection: {the connection with the current track}
    Reply A/B, or tell me another learning direction. No new track will be created or enabled before confirmation.}

    Source: {file name}: [link]({URL})
    Note: This content is for doctors' continuing learning and does not provide individual diagnosis or treatment, prescription dosages, or emergency management advice.

Daily learning units default to 600-900 characters, no more than 1000 characters. See daily-learning-template.md for the detailed constraints. The final unit recommends only 2-3 verified formal guidelines/consensus statements/standards; review articles and research papers are not used as final sources or candidates. When there are not enough candidates, ask about the learning direction and do not pad the list with low-credibility sources. The first line of a preview is marked [Format Preview | Not Counted Toward Progress] and will not create a delivery ledger or advance. Only a real channel receipt allows delivery to be confirmed internally, and confirmed delivery does not equal mastery.

## Professional guideline update reminder

    [Professional Guideline Update Alert | {department}]
    Updated document: {full name}
    Issuing body: {body}
    Publication date: {date or year}
    Scope of application: {populations/diseases/tests/management scenarios involved}
    Changed topics:
    1. {changed topic, no prescriptive clinical actions}
    2. {changed topic}
    Primary-care learning relevance: {explain which knowledge points are worth learning, without patient management advice}
    Source: {file name}: [link]({URL})

When there is no reliable update:

    [Professional Guideline Update Alert | {department}]
    In this cycle, no updates were found to guidelines, consensus statements, standards, clinical pathways, or quality-control documents that are directly related to {region} {department} and traceable to an authoritative original text.

## Learning about regional medical-insurance policy changes

    [Insurance Policy Change Study | {region}]
    Policy document: {full name}
    Issuing body: {body}
    Effective date: {date}
    Summary:
    1. {change or requirement at the level of the policy text}
    2. {change or requirement at the level of the policy text}
    Pending confirmation: this hospital's catalog, settlement mapping, and the medical insurance office's implementation rules.
    Source: {file name}: [link]({URL})
    Note: Actual implementation is governed by the local medical insurance bureau, the hospital medical insurance office, and the hospital's formal settlement rules; this summary is not a basis for reimbursement.

## Guideline section expansion

Used when the user asks to expand, look closely at, or explain a section in detail. The purpose is to help the user understand the original text, not to replace it.

    [Guideline Section Expansion | {section name}]
    Basis: {full guideline name} ({version/year}, {issuing body})
    Section: {chapter/section number and title}
    Original-text locator: {chapter number / subsection number / item number or page range}

    Key points of the original text:
    1. {what this section says, stated following the original structure}
    2. {key definitions, elements, or stratification concepts}
    3. {levels of evidence, strength of recommendations, or quality indicators (if the original text has them)}

    Section relationships: {this section's relationship with the preceding and following sections, explaining its position in the guideline structure}
    Easily confused points: {places that are easily confused or misapplied when reading this section}
    Learning tips: {how to study this section, and what must be mastered first}
    Boundary: This section expansion is for learning the original structure and concepts; it does not replace the original text and is not a basis for individual diagnosis or treatment; please rely on the authoritative original text.
    Source: {file name}: [link]({URL})

Constraints: Only structured summaries and precise locators; do not copy the full guideline text paragraph by paragraph; the expansion must not be rewritten into a hospital-executable process, an action card, or management steps. When the authoritative original text cannot be obtained, only state that it is pending verification and do not expand from memory.

## Guideline learning pathway map

Used when the user says "summarize the guideline into a process" or "how should I study this guideline". First confirm that the user wants a learning order rather than a bedside management order.

    [Guideline Learning Pathway | {guideline}]
    Basis: {full guideline name} ({version/year}, {issuing body})
    Applicable learning objective: {learning objective or "general learning"}
    Prerequisite knowledge: {what is recommended to have mastered before studying this guideline}

    Learning order:
    1. {what to study first} — corresponding original text: {section/item} — estimated {N} minutes — mastery marker: {self-checkable learning outcome}
    2. {what to study second} — corresponding original text: {section/item} — estimated {N} minutes — mastery marker: {...}
    3. {what to study third} — corresponding original text: {section/item} — estimated {N} minutes — mastery marker: {...}

    Optional deep dive: {advanced or special-topic directions for the user to choose from}
    Boundary: This pathway map only sets out a learning order; it is not for bedside execution and does not constitute a basis for individual diagnosis or treatment; clinical execution is governed by the hospital's formal documents and the opinions of supervising physicians.
    Source: {file name}: [link]({URL})

Constraints: It is forbidden to write the content as bedside execution steps or resuscitation sequences (expressions such as "management process", "diagnosis-and-treatment process", "resuscitation process", "handling process", and "emergency action card" must not appear). Each step must map to a section of the original text; when it cannot, mark it as pending verification. After the user confirms, it may be used to create the fixed units of a learning track.

## Exam-preparation study material recommendations

Used when the user states an exam or position goal (associate chief physician, intermediate, residency training, licensed physician, etc.).

    [Exam Prep Material Recommendation | {exam or role target}]
    Exam objective: {objective name} | target time: {YYYY-MM or undetermined}
    Time available: {minutes per day or "pending confirmation"}

    Recommended materials:
    1. {material name} ({type: official syllabus/guideline/textbook/standard}, {version/year}, {issuing body}) — purpose: {why it is recommended}
    2. {material name} (...) — purpose: {...}
    3. {material name} (...) — purpose: {...}

    Learning order: {suggested sequence and the reason}
    Pending confirmation: this year's official exam syllabus, formal notices from the exam office, and local registration requirements.
    Boundary: The official exam syllabus prevails; this recommendation does not represent the exam scope, question types, score weighting, or must-test points, and does not promise a passing result.
    Source: {file name}: [link]({URL})

Constraints: A distinction must be made between "official syllabus requirements" and "the assistant's supplementary suggestions". Do not fabricate textbook versions, ISBNs, or bibliographies; when the authoritative syllabus cannot be obtained, give only a draft of the learning direction and mark it as pending verification.

## Medical-insurance policy retrospective learning (long cycle)

Used when the user asks for a review of medical-insurance policy over the past year, the current year, or a specified period; keep it distinct from the weekly change push.

    [Insurance Policy Review Study | {region}]
    Review window: {YYYY-MM-DD to YYYY-MM-DD}
    Retrieval scope: {national/provincial/municipal/district-county level description}

    Key policies:
    1. {full name of the policy document} ({issuing body}, published {date}, effective {date}) | status: {currently in force/repealed/superseded}
       Key points: {requirements or changes at the level of the original text}
       Source: {file name}: [link]({URL})
    2. {full name of the policy document} (...) | status: {...}
       Key points: {...}
       Source: {file name}: [link]({URL})

    Learning tips: {what these policies mean for primary-care doctors' learning, grouped by topic}
    Pending confirmation: this hospital's catalog, settlement mapping, and the medical insurance office's implementation rules.
    Note: Actual implementation is governed by the local medical insurance bureau, the hospital medical insurance office, and the hospital's formal settlement rules; this summary is not a basis for reimbursement.

Constraints: Sort by publication date; the repealed or superseded status must be marked, and lapsed policies must not be presented as currently in force. When no traceable original text is found within the window, state that honestly and do not fill the gap from second-hand platforms.

## Hard rules for source format

Whenever this output queries, cites, or verifies an authoritative source, whether for a scheduled push or for answering a question, the sources must be listed. The unified format is:

    Source: {file or page name}: [link]({URL})

Long bare URLs must not appear, and the link text must not be written as other words such as view original, official website, or click here. Multiple sources are listed on separate lines. When there is no reliable source, do not fabricate links; write only that no verifiable authoritative source was obtained or that manual verification is required.
