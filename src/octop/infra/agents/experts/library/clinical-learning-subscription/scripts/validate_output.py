#!/usr/bin/env python3
"""Validate clinical learning output: format, sources, and boundary declarations before delivery."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = PACKAGE_ROOT / "references" / "source-policy.yaml"

# Chinese has no letter case; every text check below is therefore matched
# case-insensitively so that English capitalization never changes a verdict.
_TEXT_FLAGS = re.IGNORECASE

# The body-of-text host label appears in both spellings across the reference
# documents, so both are accepted.
_BODY_HOST_RE = re.compile(r"body(?:-of)?-text host", _TEXT_FLAGS)


def _load_list_yaml(path: Path) -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    current_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_key = line[:-1].strip()
            data[current_key] = []
            continue
        if current_key and line.strip().startswith("- "):
            value = line.strip()[2:].strip().strip('"').strip("'")
            value = value.replace("\\\\", "\\")
            data[current_key].append(value)
    return data


def _domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().split("@")[-1].split(":")[0]


def _matches_domain_policy(
    domain: str,
    policy: dict[str, list[str]],
    *,
    exact_key: str,
    suffix_key: str,
) -> bool:
    if domain in set(policy.get(exact_key, [])):
        return True
    for suffix in policy.get(suffix_key, []):
        normalized = suffix.lower()
        if normalized.startswith(".") and domain.endswith(normalized):
            return True
        if domain == normalized:
            return True
    return False


def _is_primary_domain(domain: str, policy: dict[str, list[str]]) -> bool:
    if domain in set(policy.get("blocked_final_evidence_domains", [])):
        return False
    return _matches_domain_policy(
        domain,
        policy,
        exact_key="allowed_final_evidence_exact_domains",
        suffix_key="allowed_final_evidence_domain_suffixes",
    )


def _is_secondary_domain(domain: str, policy: dict[str, list[str]]) -> bool:
    if domain in set(policy.get("blocked_final_evidence_domains", [])):
        return False
    return _matches_domain_policy(
        domain,
        policy,
        exact_key="allowed_secondary_evidence_exact_domains",
        suffix_key="allowed_secondary_evidence_domain_suffixes",
    )


def _is_allowed_domain(domain: str, policy: dict[str, list[str]]) -> bool:
    return _is_primary_domain(domain, policy) or _is_secondary_domain(domain, policy)


def _is_attributed_relay_url(url: str, text: str, policy: dict[str, list[str]]) -> bool:
    """Allow an arbitrary C-tier page only when its secondary status is fully disclosed."""
    source_line = next(
        (
            line.strip()
            for line in text.splitlines()
            if line.strip().lower().startswith("source:") and url in line
        ),
        "",
    )
    if "relay page (c-tier, background only)" not in source_line.lower():
        return False

    required_markers = policy.get("attributed_relay_required_markers", [])
    if any(marker.lower() not in text.lower() for marker in required_markers):
        return False

    identity_line = next(
        (
            line.strip()
            for line in text.splitlines()
            if line.strip().lower().startswith("original source:")
        ),
        "",
    )
    if identity_line.count(" | ") < 3:
        return False
    if not re.search(r"(?:19|20)\d{2}|not provided", identity_line, _TEXT_FLAGS):
        return False
    return "doi" in identity_line.lower() or "document number" in identity_line.lower()


def _extract_markdown_links(text: str) -> list[tuple[str, str]]:
    return re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", text)


def _extract_bare_urls(text: str) -> list[str]:
    masked = re.sub(r"\[[^\]]+\]\(https?://[^)\s]+\)", "", text)
    return sorted(set(re.findall(r"https?://[^\s)]+", masked)))


def _extract_markdown_urls(text: str) -> list[str]:
    markdown_urls = [url for _, url in _extract_markdown_links(text)]
    bare_urls = _extract_bare_urls(text)
    return sorted(set(markdown_urls + bare_urls))


def _visible_length(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


_EXCLUDED_CONTENT_TYPE_PATTERNS: dict[str, str] = {
    "systematic_review": r"systematic\s+review",
    "meta_analysis": r"meta[-\s]?analysis",
    "systematic_review_and_meta_analysis": r"systematic\s+review\s+and\s+meta",
    "narrative_review": r"narrative\s+review",
    "scoping_review": r"scoping\s+review",
    "umbrella_review": r"umbrella\s+review",
    "rapid_review": r"rapid\s+review",
    "expert_review": r"expert\s+review",
    "literature_review": r"literature\s+review",
    "randomized_controlled_trial": r"randomi[sz]ed\s+controlled\s+trial|\bRCT\b",
    "observational_study": r"observational\s+stud(?:y|ies)",
    "case_report_or_case_series": r"case\s+(?:report|series)",
    "editorial_commentary_or_letter": r"editorial|commentary|letter\s+to",
    "conference_abstract": r"conference\s+abstract",
    "preprint": r"preprint",
    "retracted_or_expression_of_concern": r"retract(?:ed|ion)|expression\s+of\s+concern",
    "science_popularization": r"popular\s+science",
    "guideline_or_consensus_interpretation": (
        r"guideline\s+interpretation|consensus\s+interpretation|"
        r"standard\s+interpretation|policy\s+interpretation"
    ),
    "repost_or_excerpt": r"reprint|excerpt",
    "interview_or_media_report": r"interview|media\s+report",
    "public_health_check_education_or_interpretation": (
        r"physical\s+examination\s+knowledge|examination\s+interpretation"
    ),
    "conference_training_or_event_report": (
        r"conference\s+report|training\s+report|event\s+report"
    ),
    "marketing_or_institutional_promotion": (
        r"marketing|institutional\s+promotion|institutional\s+publicity"
    ),
}


def _extract_learning_position(text: str) -> tuple[int, int] | None:
    match = re.search(r"learning unit\s*[:：]\s*(\d+)\s*[/／]\s*(\d+)", text, _TEXT_FLAGS)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def _extract_section(text: str, heading: str) -> str:
    match = re.search(
        rf"{re.escape(heading)}\s*[:：]?\s*(.*?)(?=\n\s*(?:source|note)\s*[:：]|\Z)",
        text,
        flags=re.DOTALL | _TEXT_FLAGS,
    )
    return match.group(1).strip() if match else ""


def _final_evidence_lines(text: str) -> list[str]:
    evidence_prefix = re.compile(
        r"^\s*(?:(?:basis|guideline|source|updated document|policy document|"
        r"authoritative source)\s*[:：]|[A-C][.、]\s*)",
        _TEXT_FLAGS,
    )
    return [line.strip() for line in text.splitlines() if evidence_prefix.search(line)]


def _validate_final_evidence_content_types(
    text: str, policy: dict[str, list[str]], errors: list[str]
) -> None:
    evidence_lines = _final_evidence_lines(text)
    for line in evidence_lines:
        for content_type in policy.get("excluded_final_evidence_content_types", []):
            pattern = _EXCLUDED_CONTENT_TYPE_PATTERNS.get(content_type)
            if pattern is None:
                continue
            if re.search(pattern, line, flags=re.IGNORECASE):
                errors.append(
                    f"final evidence must not use a non-normative document type: {content_type}"
                )
                break


# Clinical safety domain module list. Only these modules get the medical
# prohibited-term list and the authoritative-source allowlist.
# Other modules (general writing/translation/programming/other skills) are
# validated as general assistant output; a doctor's non-medical work and the
# output of other skills are not downgraded or truncated by medical rules.
_DEFAULT_CLINICAL_SAFETY_MODULES = (
    "guideline_learning",
    "daily_guideline_learning",
    "guideline_section_expansion",
    "guideline_learning_pathway",
    "guideline_learning_diagnosis",
    "guideline_update_reminder",
    "professional_update_summary",
    "insurance_policy_summary",
    "insurance_policy_learning",
    "insurance_policy_retrospective",
    "exam_material_recommendation",
    "high_risk_refusal",
)

_DEFAULT_SOURCE_RESTRICTED_MODULES = tuple(
    name for name in _DEFAULT_CLINICAL_SAFETY_MODULES if name != "high_risk_refusal"
)

# A medical safety domain final draft must not carry process sentences.
# English proper nouns inside source titles are exempt.
_PROCESS_LANGUAGE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bI'll\b", "I'll"),
    (r"\bI will\b", "I will"),
    (r"\bLet me\b", "Let me"),
    (r"\bLet's\b", "Let's"),
    (r"\bNow running\b", "Now running"),
    (r"Validation passed", "Validation passed"),
    (r"Here is the answer", "Here is the answer"),
    (r"search process", "search process"),
    (r"retrieval log", "retrieval log"),
)


def _body_without_source_lines(text: str) -> str:
    """Drop Source lines so English titles in citations are not process-language hits."""
    return "\n".join(
        line for line in text.splitlines() if not line.strip().lower().startswith("source:")
    )


def _validate_process_language(text: str, errors: list[str]) -> None:
    body = _body_without_source_lines(text)
    for pattern, label in _PROCESS_LANGUAGE_PATTERNS:
        if re.search(pattern, body, flags=re.IGNORECASE):
            errors.append(f"medical output must not contain process sentences: {label}")


def _policy_modules(policy: dict[str, list[str]], key: str, fallback: tuple[str, ...]) -> set[str]:
    configured = [item for item in policy.get(key, []) if item]
    return set(configured) if configured else set(fallback)


def _validate_daily_guideline_learning(text: str, errors: list[str], warnings: list[str]) -> None:
    numbered_points = re.findall(r"(?m)^\s*[1-3][.、]\s+", text)
    if len(numbered_points) != 3:
        errors.append("the daily guideline template requires exactly 3 numbered points")
    if "learning unit" not in text.lower():
        errors.append("the daily guideline template is missing: learning unit")
    if "basis:" not in text.lower() and "guideline:" not in text.lower():
        errors.append(
            "the daily guideline template is missing: versioned guideline (basis/guideline)"
        )
    if re.search(r"self[-\s]?test", text, _TEXT_FLAGS):
        errors.append("the daily guideline template must not contain self-test questions")

    position = _extract_learning_position(text)
    if position is None:
        errors.append(
            "the daily guideline template is missing a parseable learning unit ordinal (N / total)"
        )
    else:
        ordinal, total = position
        if ordinal < 1 or total < 1 or ordinal > total:
            errors.append("the daily guideline template's learning unit ordinal is invalid")
        elif ordinal < total:
            preview = _extract_section(text, "Next unit preview") or _extract_section(
                text, "Tomorrow's preview"
            )
            if not preview:
                errors.append("a non-final unit is missing a substantive next unit preview")
            elif "—" not in preview and "learning objective" not in preview.lower():
                errors.append(
                    "a non-final unit preview must state both the next unit topic "
                    "and the learning objective"
                )
            if re.search(
                r"waiting.*(?:review|confirm\s+(?:a\s+)?new\s+track)"
                r"|all units of this track have been delivered",
                preview,
                _TEXT_FLAGS,
            ):
                errors.append(
                    "a non-final unit must not replace the next unit topic and "
                    "learning objective with a waiting status"
                )
        else:
            if "next unit preview" in text.lower() or "tomorrow's preview" in text.lower():
                errors.append("the final unit must not keep using a next unit preview")
            candidate_section = _extract_section(
                text, "Optional guidelines for the next stage (pending confirmation)"
            )
            planning_section = _extract_section(text, "next-stage planning (awaiting your choice)")
            if candidate_section:
                candidates = re.findall(r"(?m)^\s*([A-C])[.、]\s*(.+)$", candidate_section)
                if not 2 <= len(candidates) <= 3:
                    errors.append(
                        "the final unit must provide 2-3 next-stage formal guideline candidates"
                    )
                for _label, candidate in candidates:
                    if not re.search(
                        r"guideline|consensus|standard|clinical\s+pathway|quality\s+control"
                        r"|measures|notice",
                        candidate,
                        _TEXT_FLAGS,
                    ):
                        errors.append(
                            "a next-stage candidate must be a formal guideline/consensus/"
                            "normative document"
                        )
                    if not re.search(
                        r"[（(][^）)]*(?:19|20)\d{2}[^）)]*[，,][^）)]+[）)]", candidate
                    ):
                        errors.append(
                            "a next-stage candidate is missing the year/version or the issuing body"
                        )
                    if not re.search(r"\[[Ll]ink\]\(https?://[^)\s]+\)", candidate):
                        errors.append(
                            "a next-stage candidate is missing an authoritative original-text link"
                        )
                if candidate_section.lower().count("recommended connection:") < len(candidates):
                    errors.append(
                        "every next-stage candidate must state its recommended connection"
                    )
                if (
                    "no new track will be created or enabled before confirmation"
                    not in candidate_section.lower()
                ):
                    errors.append(
                        "the final unit is missing the statement that no new track will be "
                        "created or enabled before confirmation"
                    )
            elif planning_section:
                if (
                    "not enough verifiable formal guidelines were obtained"
                    not in planning_section.lower()
                ):
                    errors.append(
                        "when there are not enough candidates, state honestly that not enough "
                        "verifiable formal guidelines were obtained"
                    )
                if "learning direction" not in planning_section.lower():
                    errors.append(
                        "when there are not enough candidates, ask the user for the next-stage "
                        "learning direction"
                    )
                if (
                    "no new track will be created or enabled before confirmation"
                    not in planning_section.lower()
                ):
                    errors.append(
                        "the final unit is missing the statement that no new track will be "
                        "created or enabled before confirmation"
                    )
            else:
                errors.append(
                    "the final unit is missing either the pending next-stage guideline "
                    "candidates or a question about the learning direction"
                )

    length = _visible_length(text)
    if length > 1000:
        errors.append(f"the daily guideline template is too long: {length} characters")
    elif length < 400:
        warnings.append(f"the daily guideline template is too short: {length} characters")


def _validate_guideline_learning_diagnosis(text: str, errors: list[str]) -> None:
    """Check that a learning diagnosis reply is educational content."""
    if "[Guideline Learning Diagnosis" in text:
        required = (
            "Learning objective",
            "Learning signals",
            "Priority gaps to close",
            "Suggested starting point",
            "Next step",
            "Boundary",
        )
    elif "[Guideline Diagnostic Criteria Study" in text:
        required = ("Learning framework", "Easily confused points", "Next step", "Boundary")
    elif "[Learning Needs Pre-assessment | Guideline Pending]" in text:
        required = (
            "Learning objective",
            "Current learning signal",
            "Recommendation",
            "Next step",
            "Boundary",
        )
    else:
        errors.append("the learning diagnosis template is missing the title")
        return
    for label in required:
        if label.lower() not in text.lower():
            errors.append(f"the learning diagnosis template is missing: {label}")


def _validate_guideline_section_expansion(text: str, errors: list[str]) -> None:
    """Section expansion must be source-backed reading support, not a rewritten guideline."""
    if "[Guideline Section Expansion" not in text:
        errors.append("the section expansion template is missing the title")
        return
    for label in (
        "Basis",
        "Section",
        "Key points of the original text",
        "Learning tips",
        "Boundary",
    ):
        if label.lower() not in text.lower():
            errors.append(f"the section expansion template is missing: {label}")
    if "original-text locator" not in text.lower() and "locator" not in text.lower():
        errors.append("the section expansion template is missing: original-text locator")
    if "does not replace the original text" not in text.lower():
        errors.append(
            "the section expansion template is missing: the "
            "does-not-replace-the-original-text statement"
        )


def _validate_guideline_learning_pathway(text: str, errors: list[str]) -> None:
    """A pathway map is a learning order, not clinical triage."""
    if "[Guideline Learning Pathway" not in text:
        errors.append("the learning pathway template is missing the title")
        return
    for label in ("Basis", "Learning order", "Prerequisite knowledge", "Boundary"):
        if label.lower() not in text.lower():
            errors.append(f"the learning pathway template is missing: {label}")
    if not re.search(r"(?m)^\s*\d+[.、]\s+", text):
        errors.append("the learning pathway is missing numbered steps")
    for banned in (
        "management process",
        "diagnosis-and-treatment process",
        "resuscitation process",
        "handling process",
    ):
        if banned in text.lower():
            errors.append(
                f"the learning pathway must not be written as a clinical process: {banned}"
            )


def _validate_exam_material_recommendation(text: str, errors: list[str]) -> None:
    """The exam material list must state its scope and verification requirements."""
    if "[Exam Prep Material Recommendation" not in text:
        errors.append("the exam prep material template is missing the title")
        return
    for label in (
        "Exam objective",
        "Recommended materials",
        "Learning order",
        "Pending confirmation",
        "Boundary",
    ):
        if label.lower() not in text.lower():
            errors.append(f"the exam prep material template is missing: {label}")
    if "the official exam syllabus prevails" not in text.lower():
        errors.append(
            "the exam prep material template is missing: the "
            "official-exam-syllabus-prevails statement"
        )


def _validate_insurance_retrospective(text: str, errors: list[str]) -> None:
    """A long-cycle medical insurance review must state its window and not act as authority."""
    if "[Insurance Policy Review Study" not in text:
        errors.append("the medical insurance review template is missing the title")
        return
    for label in ("Review window", "Key policies", "Learning tips", "Pending confirmation"):
        if label.lower() not in text.lower():
            errors.append(f"the medical insurance review template is missing: {label}")


def validate(text: str, module: str, policy_path: Path, allow_no_source: bool) -> dict[str, object]:
    policy = _load_list_yaml(policy_path)
    errors: list[str] = []
    warnings: list[str] = []

    clinical_modules = _policy_modules(
        policy, "clinical_safety_modules", _DEFAULT_CLINICAL_SAFETY_MODULES
    )
    source_restricted = _policy_modules(
        policy, "source_restricted_modules", _DEFAULT_SOURCE_RESTRICTED_MODULES
    )
    in_clinical_domain = module in clinical_modules

    # General assistant output is not bound by the medical prohibited-term list.
    if in_clinical_domain:
        for pattern in policy.get("blocked_output_patterns", []):
            if re.search(pattern, text, flags=re.IGNORECASE):
                errors.append(f"hits a prohibited output pattern: {pattern}")
        _validate_process_language(text, errors)

    markdown_links = _extract_markdown_links(text)
    bare_urls = _extract_bare_urls(text)
    urls = _extract_markdown_urls(text)
    source_lines = [
        line.strip() for line in text.splitlines() if line.strip().lower().startswith("source:")
    ]
    source_required = module in source_restricted

    if source_required:
        if not urls and not allow_no_source:
            errors.append("missing source URL")
        if urls and not markdown_links:
            errors.append("the source URL must be in Markdown link format")
        if urls and not any("[link](" in line.lower() for line in source_lines):
            errors.append("the source line is missing a clickable [link](URL)")
        for label, _url in markdown_links:
            if label.lower() != "link":
                errors.append(f"source link text must be 'link': {label}")
        for url in bare_urls:
            errors.append(f"bare URL is not allowed: {url}")

        # The authoritative-source allowlist only constrains medical and policy claims;
        # general tasks may cite any legal link.
        attributed_relay_urls: list[str] = []
        for url in urls:
            domain = _domain(url)
            if not domain:
                errors.append(f"invalid URL: {url}")
                continue
            if not _is_allowed_domain(domain, policy):
                if _is_attributed_relay_url(url, text, policy):
                    attributed_relay_urls.append(url)
                else:
                    errors.append(f"source domain is not on the allowlist: {domain}")

        if attributed_relay_urls:
            if _BODY_HOST_RE.search(text):
                errors.append("a C-tier relay page must not be marked as the body-of-text host")
            if "original-text locator:" in text.lower():
                errors.append(
                    "a C-tier relay page must not claim to provide an original-text locator"
                )
            warnings.append(
                "contains a C-tier web-wide relay page: background only, not final evidence"
            )

        secondary_urls = [url for url in urls if _is_secondary_domain(_domain(url), policy)]
        if secondary_urls:
            primary_urls = [url for url in urls if _is_primary_domain(_domain(url), policy)]
            if not primary_urls:
                errors.append(
                    "a B+ body-of-text host link must also provide an S/A original-metadata link"
                )
            if "original metadata" not in text.lower():
                errors.append("a B+ controlled downgrade must be labeled: original metadata")
            if not _BODY_HOST_RE.search(text):
                errors.append("a B+ controlled downgrade must be labeled: body-of-text host")
        _validate_final_evidence_content_types(text, policy, errors)
    else:
        for url in urls:
            if not _domain(url):
                errors.append(f"invalid URL: {url}")

    if "not a basis for reimbursement" not in text.lower() and module in {
        "insurance_policy_summary",
        "insurance_policy_learning",
        "insurance_policy_retrospective",
    }:
        errors.append(
            "medical insurance content is missing the 'not a basis for reimbursement' statement"
        )

    if (
        "does not provide individual diagnosis or treatment" not in text.lower()
        and module == "high_risk_refusal"
    ):
        errors.append(
            "high-risk refusal content is missing the 'does not provide individual diagnosis "
            "or treatment' boundary statement"
        )

    if module == "daily_guideline_learning":
        _validate_daily_guideline_learning(text, errors, warnings)
    if module == "guideline_learning_diagnosis":
        _validate_guideline_learning_diagnosis(text, errors)
    if module == "guideline_section_expansion":
        _validate_guideline_section_expansion(text, errors)
    if module == "guideline_learning_pathway":
        _validate_guideline_learning_pathway(text, errors)
    if module == "exam_material_recommendation":
        _validate_exam_material_recommendation(text, errors)
    if module == "insurance_policy_retrospective":
        _validate_insurance_retrospective(text, errors)

    return {
        "ok": not errors,
        "module": module,
        "clinical_safety_domain": in_clinical_domain,
        "errors": errors,
        "warnings": warnings,
        "source_urls": urls,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate clinical learning output "
            "(check format, sources, and boundary declarations before delivery)."
        )
    )
    parser.add_argument("--module", required=True)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--text-file", type=Path)
    parser.add_argument("--allow-no-source", action="store_true")
    args = parser.parse_args()

    text = args.text_file.read_text(encoding="utf-8") if args.text_file else sys.stdin.read()

    result = validate(text, args.module, args.policy, args.allow_no_source)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
