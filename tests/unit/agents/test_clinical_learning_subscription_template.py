"""Regression tests for the clinical learning + general assistant template."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest
from octop_harness.subagents.loader import parse_agent_markdown

from octop.infra.agents.experts.catalog import default_library_root

_ROOT = default_library_root() / "clinical-learning-subscription"


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_template_exposes_general_and_guideline_learning_entrypoints() -> None:
    manifest = json.loads((_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["id"] == "clinical-learning-subscription"
    assert {"SOUL.md", "AGENTS.md", "BOOTSTRAP.md"} <= set(manifest["prompt_files"])
    titles = {item["title"]["zh"] for item in manifest["quick_prompts"]}
    assert {"指南学习诊断", "指南学习地图", "处理其他任务"} <= titles
    assert {"预览下一学习单元", "创建学习轨道", "检查指南新版迁移"} <= titles

    soul = (_ROOT / "SOUL.md").read_text(encoding="utf-8")
    assert "other ordinary tasks" in soul
    assert "studying diagnostic criteria from guidelines" in soul
    assert "a specific patient" in soul
    assert "platform-owned delivery service" in soul
    assert (_ROOT / "references" / "learning-track-template.md").is_file()

    failover_root = _ROOT / "skills" / "medical-source-failover"
    failover_skill = (failover_root / "SKILL.md").read_text(encoding="utf-8")
    assert "Degrade the access path, never the document identity" in failover_skill
    assert (failover_root / "references" / "domestic-source-registry.md").is_file()
    assert (failover_root / "references" / "failover-policy.md").is_file()
    assert (failover_root / "references" / "document-identity.md").is_file()
    assert not (failover_root / "agents").exists()

    intent_routing = (_ROOT / "skills" / "intent-routing" / "SKILL.md").read_text(encoding="utf-8")
    source_verify = (_ROOT / "skills" / "source-verify" / "SKILL.md").read_text(encoding="utf-8")
    assert "medical-source-failover" in intent_routing
    assert "../medical-source-failover/SKILL.md" in source_verify


def test_learning_diagnostic_summary_is_opt_in_and_can_be_cleared(tmp_path: Path) -> None:
    profile = _load_module(_ROOT / "scripts" / "clinical_profile.py", "clinical_profile_test")

    state = profile.save_learning_diagnosis(
        goal="副高考试复习",
        guideline_title="高血压防治指南",
        source_url="https://www.nhc.gov.cn/example",
        self_assessed_level="developing",
        available_minutes_per_day=20,
        priority_topics=["诊断标准", "分层概念", "诊断标准"],
        recommended_start="先学习适用范围与定义章节",
        confirm=True,
        root=tmp_path,
    )

    diagnostic = state["learning_diagnosis"]
    assert diagnostic["status"] == "saved"
    assert diagnostic["priority_topics"] == ["诊断标准", "分层概念"]
    assert "the original answering process is not saved" in (tmp_path / "USER.md").read_text(
        encoding="utf-8"
    )

    cleared = profile.clear_learning_diagnosis(confirm=True, root=tmp_path)
    assert cleared["learning_diagnosis"]["status"] == "not_started"
    assert cleared["profile"]["consent_confirmed"] is False


def test_learning_diagnostic_rejects_unconfirmed_or_patient_like_storage(tmp_path: Path) -> None:
    profile = _load_module(
        _ROOT / "scripts" / "clinical_profile.py", "clinical_profile_rejection_test"
    )

    try:
        profile.save_learning_diagnosis(
            goal="继续学习",
            guideline_title="",
            source_url="",
            self_assessed_level="developing",
            available_minutes_per_day=20,
            priority_topics=["诊断标准"],
            recommended_start="第一章",
            confirm=False,
            root=tmp_path,
        )
    except ValueError as exc:
        assert "explicit confirmation" in str(exc)
    else:
        raise AssertionError("expected explicit-confirmation rejection")

    try:
        profile.save_learning_diagnosis(
            goal="patient case review",
            guideline_title="",
            source_url="",
            self_assessed_level="developing",
            available_minutes_per_day=20,
            priority_topics=["诊断标准"],
            recommended_start="第一章",
            confirm=True,
            root=tmp_path,
        )
    except ValueError as exc:
        assert "patient" in str(exc)
    else:
        raise AssertionError("expected patient-like content rejection")


def test_learning_diagnostic_validator_requires_educational_structure_and_source() -> None:
    validator = _load_module(
        _ROOT / "scripts" / "validate_output.py", "clinical_output_validator_test"
    )
    text = """[Guideline Learning Diagnosis | Assessment Only]
Basis: Primary-Care Hypertension Management Guideline (2024, National Health Commission)
Learning objective: exam preparation for the associate senior title
Learning signals: recommend consolidation (basis: this session's answers)
Priority gaps to close: diagnostic criteria
Suggested starting point: study the definition section first
Next step: expand that section
Source: example page: [link](https://www.nhc.gov.cn/example)
Boundary: This result only reflects the learning signals of this session; it is not a patient diagnosis, a clinical competence certification, or diagnosis-and-treatment advice.
"""

    result = validator.validate(
        text,
        module="guideline_learning_diagnosis",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is True


def test_daily_learning_validator_requires_fixed_unit_structure() -> None:
    validator = _load_module(
        _ROOT / "scripts" / "validate_output.py", "clinical_daily_validator_test"
    )
    text = """[Guideline Learning Unit | General Practice]
Track: Hypertension learning track
Basis: Hypertension Prevention and Treatment Guideline (2024, National Health Commission)
Learning unit: 1 / 2
Section: Chapter 1, 1.1
Topic: Scope of application and core definitions
1. Study the scope of application and core concepts, and do not apply learning items to a specific patient.
2. Focus on the relationships between concepts and on quality awareness, and do not write them as management orders.
3. Hospital policies and local execution rules must be confirmed by formal documents.
Next unit preview:
Risk stratification framework — learn to recognize the core concepts of risk stratification.
Source: example page: [link](https://www.nhc.gov.cn/example)
Note: This content is for doctors' continuing learning and does not provide individual diagnosis or treatment, prescription dosages, or emergency management advice.
"""
    result = validator.validate(
        text,
        module="daily_guideline_learning",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is True


def test_clinical_validator_rejects_english_process_phrases() -> None:
    validator = _load_module(
        _ROOT / "scripts" / "validate_output.py", "clinical_process_language_test"
    )
    text = """[Guideline Learning Unit | General Practice]
Track: Hypertension learning track
Basis: Hypertension Prevention and Treatment Guideline (2024, National Health Commission)
Learning unit: 1 / 2
Section: Chapter 1, 1.1
Topic: Scope of application and core definitions
1. Study the scope of application and core concepts, and do not apply learning items to a specific patient.
2. Focus on the relationships between concepts and on quality awareness, and do not write them as management orders.
3. Hospital policies and local execution rules must be confirmed by formal documents.
Let me search for the next unit.
Next unit preview:
Risk stratification framework — learn to recognize the core concepts of risk stratification.
Source: example page: [link](https://www.nhc.gov.cn/example)
Note: This content is for doctors' continuing learning and does not provide individual diagnosis or treatment, prescription dosages, or emergency management advice.
"""
    result = validator.validate(
        text,
        module="daily_guideline_learning",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is False
    assert any("Let me" in err for err in result["errors"])


def test_clinical_validator_ignores_english_in_source_titles() -> None:
    validator = _load_module(
        _ROOT / "scripts" / "validate_output.py", "clinical_source_title_language_test"
    )
    text = """[Guideline Learning Unit | General Practice]
Track: Hypertension learning track
Basis: Hypertension Prevention and Treatment Guideline (2024, National Health Commission)
Learning unit: 1 / 2
Section: Chapter 1, 1.1
Topic: Scope of application and core definitions
1. Study the scope of application and core concepts, and do not apply learning items to a specific patient.
2. Focus on the relationships between concepts and on quality awareness, and do not write them as management orders.
3. Hospital policies and local execution rules must be confirmed by formal documents.
Next unit preview:
Risk stratification framework — learn to recognize the core concepts of risk stratification.
Source: Let me explain hypertension: [link](https://www.nhc.gov.cn/example)
Note: This content is for doctors' continuing learning and does not provide individual diagnosis or treatment, prescription dosages, or emergency management advice.
"""
    result = validator.validate(
        text,
        module="daily_guideline_learning",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is True


def test_daily_learning_final_unit_requires_confirmed_next_stage_choices() -> None:
    validator = _load_module(
        _ROOT / "scripts" / "validate_output.py", "clinical_final_daily_validator_test"
    )
    text = """[Guideline Learning Unit | General Practice]
Track: Pediatric medication track
Basis: Pediatric Medication Notice (2023, National Health Commission)
Learning unit: 6 / 6
Section: Health education
Topic: Parent guidance
1. Study the core information in parent communication.
2. Study how follow-up supports continuity of medication.
3. Local execution follows formal institutional policies.

Optional guidelines for the next stage (pending confirmation):
A. "Primary-Care Child Health Guideline"(2025, National Health Commission): [link](https://www.nhc.gov.cn/next-a)
   Recommended connection: continue with child health.
B. "Pediatric Medication Quality Control Standard"(2024, Chinese Medical Association): [link](https://www.cma.org.cn/next-b)
   Recommended connection: move on to institutional quality control.
Reply A/B, or tell me another learning direction. No new track will be created or enabled before confirmation.

Source: Pediatric medication notice: [link](https://www.nhc.gov.cn/example)
Note: For doctors' continuing learning only; no individual diagnosis or treatment, prescription dosages, or emergency advice.
"""
    result = validator.validate(
        text,
        module="daily_guideline_learning",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is True


def test_daily_learning_final_unit_rejects_canned_waiting_preview() -> None:
    validator = _load_module(
        _ROOT / "scripts" / "validate_output.py", "clinical_canned_final_validator_test"
    )
    text = """[Guideline Learning Unit | General Practice]
Track: Pediatric rational medication learning track
Basis: Notice on Further Strengthening the Management of Pediatric Clinical Medication (2023, National Health Commission)
Learning unit: 6 / 6
Section: Health education and follow-up
Topic: Parent guidance and medication follow-up
1. Study the core information in parent communication.
2. Focus on the follow-up system and continuity of medication.
3. Local execution rules are governed by formal policies.
Next unit preview:
All units of this track have been delivered; waiting for the user to review or confirm a new track.
Source: Notice on pediatric clinical medication management: [link](https://www.nhc.gov.cn/example)
Note: This content is for doctors' continuing learning and does not provide individual diagnosis or treatment, prescription dosages, or emergency management advice.
"""
    result = validator.validate(
        text,
        module="daily_guideline_learning",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is False
    assert "the final unit must not keep using a next unit preview" in result["errors"]


def test_source_validator_rejects_review_as_final_evidence() -> None:
    validator = _load_module(_ROOT / "scripts" / "validate_output.py", "review_source_test")
    text = """[Guideline Learning Diagnosis | Assessment Only]
Basis: Pediatric rational medication learning plan
Learning objective: continue learning
Learning signals: recommend consolidation
Priority gaps to close: core concepts
Suggested starting point: start from the normative document
Next step: confirm the learning direction
Source: Pediatric rational medication systematic review: [link](https://www.medjournals.cn/review)
Boundary: This result only reflects the learning signals of this session; it is not a patient diagnosis, a clinical competence certification, or diagnosis-and-treatment advice.
"""
    result = validator.validate(
        text,
        module="guideline_learning_diagnosis",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is False
    assert (
        "final evidence must not use a non-normative document type: systematic_review"
        in result["errors"]
    )


def test_daily_learning_final_unit_can_ask_for_direction_without_review_fallback() -> None:
    validator = _load_module(
        _ROOT / "scripts" / "validate_output.py", "clinical_final_direction_validator_test"
    )
    text = """[Guideline Learning Unit | General Practice]
Track: Pediatric rational medication learning track
Basis: Notice on Further Strengthening the Management of Pediatric Clinical Medication (2023, National Health Commission)
Learning unit: 6 / 6
Section: Health education and follow-up
Topic: Parent guidance and medication follow-up
1. Study the core information in parent communication.
2. Focus on the follow-up system and continuity of medication.
3. Local execution rules are governed by formal policies.
next-stage planning (awaiting your choice):
not enough verifiable formal guidelines were obtained, so this does not use reviews or research papers to fill the gap. Please tell me the learning direction you would like to continue. No new track will be created or enabled before confirmation.
Source: Notice on pediatric clinical medication management: [link](https://www.nhc.gov.cn/example)
Note: This content is for doctors' continuing learning and does not provide individual diagnosis or treatment, prescription dosages, or emergency management advice.
"""
    result = validator.validate(
        text,
        module="daily_guideline_learning",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is True


def test_source_policy_filters_content_type_and_prefers_current_version() -> None:
    validator = _load_module(_ROOT / "scripts" / "validate_output.py", "source_policy_test")
    policy = validator._load_list_yaml(_ROOT / "references" / "source-policy.yaml")

    assert {
        "systematic_review",
        "meta_analysis",
        "narrative_review",
        "scoping_review",
        "umbrella_review",
        "science_popularization",
        "repost_or_excerpt",
        "interview_or_media_report",
        "public_health_check_education_or_interpretation",
    } <= set(policy["excluded_final_evidence_content_types"])
    assert "formal_journal_full_text" not in policy["allowed_final_evidence_content_types"]

    source_verify = (_ROOT / "skills" / "source-verify" / "SKILL.md").read_text(encoding="utf-8")
    assert "An authoritative website does not mean every page on it is an authoritative basis" in (
        source_verify
    )
    assert "Popular science, reprints/excerpts, interviews/media reports" in source_verify
    assert (
        'must not appear in the final "source", the next-stage guideline candidates, '
        "or the sources of a formal learning track"
    ) in source_verify
    assert "prefer the latest and currently effective formal version" in source_verify
    assert "do not treat a web page update time as the document version" in source_verify


def _carrier_learning_text(*, carrier_url: str, include_primary: bool = True) -> str:
    primary_source = (
        "Source: original metadata (Chinese Medical Association): "
        "[link](https://www.cma.org.cn/art/2025/example.shtml)\n"
        if include_primary
        else ""
    )
    return f"""[Guideline Section Expansion | Follow-up management]
Basis: China Primary-Care Follow-up Management Guideline (2025)
Section: Follow-up management section
Original-text locator: the follow-up management section in the formal full text
Key points of the original text: study the principles and quality requirements of follow-up management.
Learning tips: understand it together with the original text; do not apply it to a specific patient.
Boundary: This content does not replace the original text and does not provide individual diagnosis, prescription dosages, or emergency management advice.
{primary_source}Source: body-of-text host (original text access restricted): [link]({carrier_url})
"""


@pytest.mark.parametrize(
    ("domain", "primary", "secondary"),
    [
        ("guide.medlive.cn", False, True),
        ("www.dxy.cn", False, True),
        ("www.sinomed.ac.cn", False, False),
        ("www.medsci.cn", False, False),
        ("www.guidelines-registry.cn", False, False),
        ("kns.cnki.net", False, False),
        ("who.int", True, False),
        ("www.nice.org.uk", True, False),
        ("www.escardio.org", True, False),
        ("professional.diabetes.org", True, False),
        ("kdigo.org", True, False),
        ("ginasthma.org", True, False),
    ],
)
def test_source_policy_separates_primary_and_secondary_domains(
    domain: str, primary: bool, secondary: bool
) -> None:
    module_name = f"role_{domain.replace('.', '_')}"
    validator = _load_module(_ROOT / "scripts" / "validate_output.py", module_name)
    policy = validator._load_list_yaml(_ROOT / "references" / "source-policy.yaml")
    assert validator._is_primary_domain(domain, policy) is primary
    assert validator._is_secondary_domain(domain, policy) is secondary
    assert validator._is_allowed_domain(domain, policy) is (primary or secondary)


@pytest.mark.parametrize(
    "url",
    [
        "https://guide.medlive.cn/guideline/example",
        "https://www.dxy.cn/bbs/newweb/pc/post/example",
    ],
)
def test_secondary_fulltext_requires_primary_metadata_pair(url: str) -> None:
    domain = url.split("/", 3)[2].replace(".", "_")
    validator = _load_module(_ROOT / "scripts" / "validate_output.py", f"carrier_{domain}")

    paired = validator.validate(
        _carrier_learning_text(carrier_url=url),
        module="guideline_section_expansion",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert paired["ok"] is True

    unpaired = validator.validate(
        _carrier_learning_text(carrier_url=url, include_primary=False),
        module="guideline_section_expansion",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert unpaired["ok"] is False
    assert (
        "a B+ body-of-text host link must also provide an S/A original-metadata link"
        in unpaired["errors"]
    )
    assert "a B+ controlled downgrade must be labeled: original metadata" in unpaired["errors"]


def test_secondary_carrier_rejects_guideline_interpretation() -> None:
    validator = _load_module(
        _ROOT / "scripts" / "validate_output.py", "carrier_interpretation_test"
    )
    result = validator.validate(
        _carrier_learning_text(carrier_url="https://www.dxy.cn/bbs/newweb/pc/post/example").replace(
            "China Primary-Care Follow-up Management Guideline (2025)",
            "China Primary-Care Follow-up Management Guideline Interpretation",
        ),
        module="guideline_section_expansion",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is False
    assert (
        "final evidence must not use a non-normative document type: "
        "guideline_or_consensus_interpretation"
    ) in result["errors"]


@pytest.mark.parametrize(
    "url",
    [
        "https://www.sinomed.ac.cn/article/example",
        "https://www.medsci.cn/guideline/example",
        "https://kns.cnki.net/kcms2/article/abstract/example",
        "https://d.wanfangdata.com.cn/periodical/example",
        "https://www.cqvip.com/QK/example",
    ],
)
def test_discovery_and_legacy_academic_domains_cannot_be_final(url: str) -> None:
    domain = url.split("/", 3)[2].replace(".", "_")
    validator = _load_module(_ROOT / "scripts" / "validate_output.py", f"non_final_source_{domain}")
    result = validator.validate(
        _carrier_learning_text(carrier_url=url, include_primary=False),
        module="guideline_section_expansion",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is False
    assert f"source domain is not on the allowlist: {url.split('/', 3)[2]}" in result["errors"]


def test_fully_attributed_c_tier_relay_is_background_only() -> None:
    validator = _load_module(_ROOT / "scripts" / "validate_output.py", "attributed_relay_test")
    text = """[Guideline Section Expansion | Follow-up management]
Basis: China Primary-Care Follow-up Management Guideline (2025)
Section: Follow-up management section
Locator status: original text not obtained
Key points of the original text: only this page's background relay is described; no precise recommendation is extracted.
Learning tips: wait until the normative original text is obtained before verifying.
Boundary: This content does not replace the original text and does not provide individual diagnosis, prescription dosages, or emergency management advice.
Source: relay page (C-tier, background only): [link](https://example.org/clinical-report)
Original source: Chinese Medical Journal | China Primary-Care Follow-up Management Guideline | 2025 | DOI not provided
Verification status: no verifiable original text was obtained; the following is only a background relay and is not an authoritative basis.
"""
    result = validator.validate(
        text,
        module="guideline_section_expansion",
        policy_path=_ROOT / "references" / "source-policy.yaml",
        allow_no_source=False,
    )
    assert result["ok"] is True
    assert (
        "contains a C-tier web-wide relay page: background only, not final evidence"
        in result["warnings"]
    )


def test_clinical_fast_path_and_route_catalogs_are_registered() -> None:
    policy = _load_module(
        _ROOT / "scripts" / "validate_output.py", "fast_path_policy_test"
    )._load_list_yaml(_ROOT / "references" / "source-policy.yaml")
    assert "clinical_q_and_a" in policy["clinical_safety_modules"]
    assert policy["retrieval_budget_hard_limits"] == [
        "searchfree_search_max_3",
        "web_fetch_max_3",
        "international_sites_normally_1",
        "international_sites_absolute_max_2",
        "final_normative_documents_normally_1",
    ]

    professional_routes = (
        _ROOT / "references" / "professional-society-source-routes.yaml"
    ).read_text(encoding="utf-8")
    international_routes = (
        _ROOT / "references" / "international-guideline-source-routes.yaml"
    ).read_text(encoding="utf-8")
    assert "Respiratory Medicine Branch" in professional_routes
    assert "Chinese Pharmaceutical Association" in professional_routes
    assert "official_discovery_pending_fulltext_acceptance" in professional_routes
    assert (
        "request_budget: Normally visit only 1 international site; at most 2 when necessary"
        in international_routes
    )
    assert "id: gina" in international_routes


def test_internal_learning_team_members_have_no_tools() -> None:
    for name in ("guideline-learning-designer.md", "medical-learning-safety-reviewer.md"):
        text = (_ROOT / "agents" / name).read_text(encoding="utf-8")
        spec = parse_agent_markdown(text, path_fragment=f"agents/{name}", parent_tools=[])
        assert spec is not None
        assert spec["tools"] == []


def _create_active_track(profile: ModuleType, root: Path) -> tuple[str, list[str]]:
    _state, goal = profile.save_learning_goal(
        label="副高考试复习",
        kind="exam",
        daily_minutes=20,
        target_date="2026-10-31",
        priority=80,
        status="active",
        goal_id="exam-goal",
        confirm=True,
        root=root,
    )
    _state, track = profile.create_learning_track(
        label="高血压防治指南",
        publisher="国家卫生健康委",
        version="2024",
        source_url="https://www.nhc.gov.cn/example",
        source_revision="2024-01",
        goal_ids=[goal["id"]],
        track_id="hypertension-track",
        kind="guideline",
        confirm=True,
        root=root,
    )
    lesson_ids = ["hypertension-track-unit-1", "hypertension-track-unit-2"]
    lessons = [
        {
            "id": lesson_ids[0],
            "ordinal": 1,
            "title": "适用范围与核心定义",
            "source_anchor": {"section": "第一章", "locator": "1.1"},
            "objectives": ["理解适用人群"],
            "topic_tags": ["定义"],
            "estimated_minutes": 10,
        },
        {
            "id": lesson_ids[1],
            "ordinal": 2,
            "title": "风险分层框架",
            "source_anchor": {"section": "第二章", "locator": "2.1"},
            "objectives": ["识别学习中的分层概念"],
            "topic_tags": ["风险分层"],
            "estimated_minutes": 10,
        },
    ]
    profile.replace_track_lessons(
        track_id=track["id"],
        lesson_jsons=[json.dumps(item, ensure_ascii=False) for item in lessons],
        replace_pending=True,
        confirm=True,
        root=root,
    )
    profile.activate_learning_track(track_id=track["id"], confirm=True, root=root)
    return track["id"], lesson_ids


def test_learning_track_preview_is_read_only_and_delivery_lifecycle_is_not_exposed(
    tmp_path: Path,
) -> None:
    profile = _load_module(
        _ROOT / "scripts" / "clinical_profile.py", "clinical_profile_delivery_test"
    )
    track_id, lesson_ids = _create_active_track(profile, tmp_path)

    preview = profile.get_next_lesson(track_id=track_id, root=tmp_path)
    assert preview["lesson"]["id"] == lesson_ids[0]
    assert profile.load_state(tmp_path)["learning"]["delivery_ledger"] == []

    with pytest.raises(RuntimeError, match="authenticated outbox"):
        profile._claim_delivery_for_platform(
            track_id=track_id,
            lesson_id=lesson_ids[0],
            route_key="weixin:daily_guideline_learning",
            slot_key="weixin:daily_guideline_learning:2026-07-31",
            idempotency_key="cron:guideline:2026-07-31T07:30:00+08:00",
            lease_seconds=900,
            root=tmp_path,
        )
    assert profile.load_state(tmp_path)["learning"]["delivery_ledger"] == []

    parser = profile.build_parser()
    command_names = parser._subparsers._group_actions[0].choices
    # The platform-owned delivery lifecycle (claim/confirm with tokens) must stay
    # unexposed; only the weak cron dedup ledger commands are allowed.
    assert not any("claim" in name or "confirm-delivery" in name for name in command_names)
    assert "delivery-check" in command_names
    assert "delivery-record" in command_names


def test_weak_delivery_ledger_dedups_and_advances(tmp_path: Path) -> None:
    profile = _load_module(
        _ROOT / "scripts" / "clinical_profile.py", "clinical_profile_weak_delivery_test"
    )
    track_id, lesson_ids = _create_active_track(profile, tmp_path)

    first_check = profile.check_daily_delivery(
        track_id=track_id, logical_date="2026-08-03", root=tmp_path
    )
    assert first_check["already_sent"] is False

    recorded = profile.record_daily_delivery(
        track_id=track_id, lesson_id="", logical_date="2026-08-03", confirm=True, root=tmp_path
    )
    state, details = recorded
    assert details["recorded"] is True
    assert details["lesson_id"] == lesson_ids[0]

    second_check = profile.check_daily_delivery(
        track_id=track_id, logical_date="2026-08-03", root=tmp_path
    )
    assert second_check["already_sent"] is True

    _state2, dup = profile.record_daily_delivery(
        track_id=track_id, lesson_id="", logical_date="2026-08-03", confirm=True, root=tmp_path
    )
    assert dup["recorded"] is False
    assert dup["already_sent"] is True

    next_preview = profile.get_next_lesson(track_id=track_id, root=tmp_path)
    assert next_preview["lesson"]["id"] == lesson_ids[1]


def test_public_state_hides_delivery_ledger_and_route_metadata(tmp_path: Path) -> None:
    profile = _load_module(
        _ROOT / "scripts" / "clinical_profile.py", "clinical_profile_ledger_privacy_test"
    )
    track_id, lesson_ids = _create_active_track(profile, tmp_path)
    state = profile.load_state(tmp_path)
    state["learning"]["delivery_ledger"] = [
        {
            "id": "delivery-private",
            "track_id": track_id,
            "lesson_id": lesson_ids[0],
            "route_key_hash": "sha256:route",
            "slot_key_hash": "sha256:slot",
            "idempotency_key_hash": "sha256:key",
        }
    ]
    public = profile._public_state(state)
    assert "delivery_ledger" not in public["learning"]
    assert "route_key_hash" not in json.dumps(public, ensure_ascii=False)


def test_v1_day_progress_migrates_without_fabricating_delivery_receipt(tmp_path: Path) -> None:
    profile = _load_module(
        _ROOT / "scripts" / "clinical_profile.py", "clinical_profile_migration_test"
    )
    legacy = {
        "current_guideline": {
            "title": "高血压防治指南",
            "publisher": "国家卫生健康委",
            "source_url": "https://www.nhc.gov.cn/example",
            "total_days": 3,
            "current_day": 1,
            "status": "in_progress",
        }
    }
    (tmp_path / "clinical_learning_state.json").write_text(
        json.dumps(legacy, ensure_ascii=False),
        encoding="utf-8",
    )

    projected = profile.load_state(tmp_path)
    track = projected["learning"]["tracks"][0]
    assert track["plan_status"] == "needs_replan"
    assert track["lessons"][0]["delivery_status"] == "legacy_completed"
    assert track["lessons"][1]["delivery_status"] == "planned"
    assert projected["learning"]["delivery_ledger"] == []

    persisted, details = profile.state_migrate(confirm=True, dry_run=False, root=tmp_path)
    assert details["changes"] == ["legacy_current_guideline_imported"]
    assert persisted["revision"] == 1
    reloaded = json.loads((tmp_path / "clinical_learning_state.json").read_text(encoding="utf-8"))
    assert reloaded["learning"]["delivery_ledger"] == []
    assert reloaded["learning"]["tracks"][0]["lessons"][0]["delivery_status"] == "legacy_completed"


def test_version_migration_requires_confirmation_and_keeps_old_track(tmp_path: Path) -> None:
    profile = _load_module(
        _ROOT / "scripts" / "clinical_profile.py", "clinical_profile_version_migration_test"
    )
    track_id, _lesson_ids = _create_active_track(profile, tmp_path)
    preview = profile.preview_track_migration(
        track_id=track_id,
        publisher="国家卫生健康委",
        version="2026",
        source_url="https://www.nhc.gov.cn/new-example",
        source_revision="2026-01",
        root=tmp_path,
    )
    assert preview["preview_only"] is True
    assert preview["impact"]["requires_new_lessons"] is True

    with pytest.raises(ValueError, match="explicit confirmation"):
        profile.migrate_track(
            track_id=track_id,
            publisher="国家卫生健康委",
            version="2026",
            source_url="https://www.nhc.gov.cn/new-example",
            source_revision="2026-01",
            new_track_id="hypertension-track-2026",
            confirm=False,
            root=tmp_path,
        )

    state, details = profile.migrate_track(
        track_id=track_id,
        publisher="国家卫生健康委",
        version="2026",
        source_url="https://www.nhc.gov.cn/new-example",
        source_revision="2026-01",
        new_track_id="hypertension-track-2026",
        confirm=True,
        root=tmp_path,
    )
    assert details["new_track"]["id"] == "hypertension-track-2026"
    assert state["learning"]["tracks"][0]["status"] == "superseded"
    assert state["learning"]["tracks"][1]["status"] == "draft"
    assert state["learning"]["tracks"][1]["lessons"] == []


def test_user_summary_and_cli_state_hide_weixin_session_identifier(tmp_path: Path) -> None:
    profile = _load_module(
        _ROOT / "scripts" / "clinical_profile.py", "clinical_profile_privacy_test"
    )
    state = profile._deep_default_state()
    state["subscriptions"]["weixin_session_key"] = "user:weixin:private-session-value"
    profile.save_state(state, root=tmp_path)

    summary = (tmp_path / "USER.md").read_text(encoding="utf-8")
    assert "private-session-value" not in summary
    assert "session_key" not in summary
    assert profile._public_state(state)["subscriptions"]["weixin_session_key"] == "[hidden]"
