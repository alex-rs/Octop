#!/usr/bin/env python3
"""Manage the minimal learning state for the clinical learning expert.

The state stays beside this expert package.  It is deliberately not a patient
record and does not accept arbitrary file paths.  V2 models a learning goal,
versioned learning track, immutable lesson units, and a delivery ledger.  The
ledger can reserve a lesson safely, but a real channel receipt is still needed
before a lesson is marked as delivered.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import secrets
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

try:  # The deployed runtime is Unix today; retain a safe fallback for tests.
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None  # type: ignore[assignment]


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
STATE_FILENAME = "clinical_learning_state.json"
USER_FILENAME = "USER.md"
LOCK_FILENAME = ".clinical_learning_state.lock"
LEARNING_SCHEMA_VERSION = 2

ID_CARD_RE = re.compile(r"\b\d{17}[\dXx]\b")
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
SAFE_ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,79}$")
SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$", re.IGNORECASE)
PATIENT_MARKERS = (
    "patient",
    "medical record number",
    "outpatient number",
    "inpatient number",
    "ID card number",
    "mobile number",
    "imaging number",
    "examination report",
    "prescription",
)
LEARNING_DIAGNOSIS_LEVELS = (
    "needs_foundation",
    "developing",
    "confident",
)
GOAL_KINDS = ("exam", "work_review", "update_tracking", "teaching", "custom")
GOAL_STATUSES = ("active", "paused", "completed", "archived")
TRACK_STATUSES = (
    "draft",
    "active",
    "paused",
    "completed",
    "archived",
    "superseded",
    "invalidated",
)
TRACK_PLAN_STATUSES = ("needs_planning", "ready", "needs_replan")
LESSON_DELIVERY_STATUSES = (
    "planned",
    "claimed",
    "prepared",
    "dispatching",
    "accepted",
    "failed_retryable",
    "unknown",
    "skipped",
    "superseded",
    "legacy_completed",
)
LESSON_LEARNING_STATUSES = ("not_started", "seen", "review", "mastered", "unknown")
DELIVERY_STATES = (
    "claimed",
    "prepared",
    "dispatching",
    "accepted",
    "failed_retryable",
    "unknown",
    "cancelled",
)
TERMINAL_LESSON_STATES = {"accepted", "legacy_completed", "skipped", "superseded"}


DEFAULT_STATE: dict[str, Any] = {
    "state_version": LEARNING_SCHEMA_VERSION,
    "revision": 0,
    "updated_at": "",
    "profile": {
        "consent_confirmed": False,
        "display_name": "",
        "region": "",
        "hospital": "",
        "department": "",
        "title": "",
    },
    "derived": {
        "department_system": "pending identification",
        "specialty": "pending identification",
        "learning_depth": "pending identification",
        "insurance_scope": "pending identification",
        "hospital_boundary": (
            "Do not infer this hospital's ICU, blood transfusion, endoscopy, ERCP, "
            "intervention, surgery, or transport capabilities; whenever execution "
            "conditions are involved, this hospital's formal policies, department "
            "authorization, or the hospital medical insurance office must be the authority."
        ),
    },
    # Retained as a read-only compatibility projection for v1 users.  New
    # workflows must use learning.tracks and lesson delivery states instead.
    "current_guideline": {
        "title": "pending selection",
        "publisher": "pending verification",
        "source_url": "pending verification",
        "total_days": 0,
        "current_day": 0,
        "status": "not_selected",
    },
    "learning_diagnosis": {
        "goal": "pending configuration",
        "guideline_title": "pending selection",
        "source_url": "pending verification",
        "self_assessed_level": "not_assessed",
        "available_minutes_per_day": 0,
        "priority_topics": [],
        "recommended_start": "pending diagnosis",
        "status": "not_started",
    },
    "learning": {
        "schema_version": LEARNING_SCHEMA_VERSION,
        "goals": [],
        "diagnostics": [],
        "tracks": [],
        "delivery_ledger": [],
        "migration": {
            "legacy_state_detected": False,
            "legacy_v1_current_guideline_imported": False,
            "legacy_v1_diagnosis_imported": False,
            "history": [],
        },
    },
    "subscriptions": {
        "daily_guideline_learning": "not created",
        "guideline_update_reminder": "not created",
        "insurance_policy_learning": "not created",
        "default_channel": "current session channel (platform auto-routed)",
        "weixin_session_key": "",
    },
    "privacy": {
        "purpose": (
            "Used only for the personalized guideline learning, learning diagnosis summary, "
            "Professional Guideline Update Alert, and Regional Insurance Policy Change "
            "Study that the user explicitly enables."
        ),
        "minimization": (
            "Only the form of address, region, hospital, department, professional title, "
            "and the minimal learning configuration the user explicitly asks to save are "
            "stored; the trusted delivery ledger and channel receipts are kept by the "
            "platform service, not in the expert workspace; ordinary general task content, "
            "course bodies, original answers, or patient information are not stored."
        ),
        "deletion_status": "no deletion requested",
    },
}


def state_path(root: Path = PACKAGE_ROOT) -> Path:
    return root / STATE_FILENAME


def user_path(root: Path = PACKAGE_ROOT) -> Path:
    return root / USER_FILENAME


def lock_path(root: Path = PACKAGE_ROOT) -> Path:
    return root / LOCK_FILENAME


def _deep_default_state() -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_STATE)


# datetime.UTC only exists on Python 3.11+; resolve at runtime so the script
# keeps working on the 3.9 system interpreter while preferring the modern alias.
_UTC = getattr(datetime, "UTC", None) or timezone(timedelta(hours=0))


def _now() -> str:
    return datetime.now(_UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _shanghai_date() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def _merge_defaults(value: dict[str, Any]) -> dict[str, Any]:
    """Merge known top-level sections without dropping data from a newer state."""
    # v1 has a top-level current_guideline but no learning container.  A v2
    # compatibility projection also has current_guideline, so this detection
    # must happen before defaults are merged.
    legacy_v1_input = (
        "learning" not in value and int(value.get("state_version") or 1) < LEARNING_SCHEMA_VERSION
    )
    state = _deep_default_state()
    for section, section_value in value.items():
        if isinstance(section_value, dict) and isinstance(state.get(section), dict):
            state[section].update(section_value)
        else:
            state[section] = section_value
    _ensure_learning_shape(state)
    if legacy_v1_input:
        state["learning"]["migration"]["legacy_state_detected"] = True
    return state


def _ensure_learning_shape(state: dict[str, Any]) -> None:
    learning = state.get("learning")
    if not isinstance(learning, dict):
        learning = {}
        state["learning"] = learning
    defaults = copy.deepcopy(DEFAULT_STATE["learning"])
    for key, fallback in defaults.items():
        if key not in learning or not isinstance(learning[key], type(fallback)):
            learning[key] = fallback
    migration = learning["migration"]
    for key, fallback in defaults["migration"].items():
        migration.setdefault(key, copy.deepcopy(fallback))
    learning["schema_version"] = LEARNING_SCHEMA_VERSION
    state["state_version"] = LEARNING_SCHEMA_VERSION
    if not isinstance(state.get("revision"), int):
        state["revision"] = 0
    if not isinstance(state.get("updated_at"), str):
        state["updated_at"] = ""


def _read_state_unlocked(root: Path) -> dict[str, Any]:
    path = state_path(root)
    if not path.is_file():
        return _deep_default_state()
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"the profile state file is corrupted and cannot be read: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(
            "the profile state file has the wrong format: the top level must be an object"
        )
    return _merge_defaults(loaded)


@contextmanager
def _state_lock(root: Path) -> Iterator[None]:
    """Serialize writers. Atomic replacement protects readers from partial JSON."""
    root.mkdir(parents=True, exist_ok=True)
    handle = lock_path(root).open("a+", encoding="utf-8")
    try:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _write_state_unlocked(state: dict[str, Any], root: Path) -> None:
    _atomic_write(
        state_path(root),
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
    )
    _atomic_write(user_path(root), render_user_text(state))


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _new_id(prefix: str, label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    if not slug:
        slug = "item"
    return f"{prefix}-{slug[:32]}-{_short_hash(f'{label}:{_now()}:{secrets.token_hex(4)}')}"


def _normalize_id(label: str, value: str, *, prefix: str, fallback_label: str) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return _new_id(prefix, fallback_label)
    if not SAFE_ID_RE.fullmatch(normalized):
        raise ValueError(
            f"{label} must be a 3-80 character slug starting with a lowercase letter "
            "(letters, digits, hyphens)"
        )
    return normalized


def _reject_pii(label: str, value: str) -> None:
    if ID_CARD_RE.search(value) or PHONE_RE.search(value):
        raise ValueError(
            f"{label} appears to contain patient personal information or contact details; refused"
        )
    for marker in PATIENT_MARKERS:
        if marker in value:
            raise ValueError(f"{label} contains '{marker}'; patient-related information is refused")


def _require_clean(label: str, value: str, *, max_length: int = 240) -> str:
    normalized = " ".join(str(value or "").strip().split())
    if not normalized:
        raise ValueError(f"{label} must not be empty")
    if len(normalized) > max_length:
        raise ValueError(f"{label} is too long; at most {max_length} characters")
    _reject_pii(label, normalized)
    return normalized


def _optional_clean(label: str, value: str, *, fallback: str, max_length: int = 240) -> str:
    normalized = " ".join(str(value or "").strip().split())
    return _require_clean(label, normalized, max_length=max_length) if normalized else fallback


def _clean_url(label: str, value: str) -> str:
    normalized = _require_clean(label, value, max_length=2048)
    parsed = urlparse(normalized)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError(f"{label} must be a complete http or https link")
    return normalized


def _normalize_sha256(label: str, value: str) -> str:
    normalized = _require_clean(label, value, max_length=80).lower()
    if not SHA256_RE.fullmatch(normalized):
        raise ValueError(f"{label} must start with sha256: or be a 64-character hexadecimal hash")
    return normalized if normalized.startswith("sha256:") else f"sha256:{normalized}"


def _optional_iso_date(label: str, value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    try:
        datetime.fromisoformat(normalized).date()
    except ValueError as exc:
        raise ValueError(f"{label} must be a YYYY-MM-DD date") from exc
    return normalized


def normalize_region(region: str) -> str:
    raw = _require_clean("region", region)
    municipality = re.match(r"^(Beijing|Shanghai|Tianjin|Chongqing)(.*)$", raw)
    if municipality:
        city = municipality.group(1)
        rest = municipality.group(2).strip("-/／,， ")
        return f"{city}-{rest}" if rest else city
    parts = [part for part in re.split(r"[-/／,，\s]+", raw) if part]
    return "-".join(parts) if len(parts) > 1 else raw


def derive_department_system(department: str) -> str:
    if any(
        key in department.lower()
        for key in (
            "respiratory",
            "gastro",
            "cardio",
            "neurolog",
            "endocrine",
            "nephrolog",
            "hematolog",
            "rheumatolog",
            "infectious",
            "general practice",
            "internal medicine",
        )
    ):
        return "Clinical internal medicine system"
    if any(
        key in department.lower()
        for key in (
            "general surgery",
            "orthoped",
            "hepatobiliary",
            "gastrointestinal",
            "thoracic",
            "urolog",
            "neurosurgery",
            "surgery",
        )
    ):
        return "Clinical surgery system"
    if "pediatric" in department.lower():
        return "Pediatrics system"
    if "obstetric" in department.lower() or "gynecolog" in department.lower():
        return "Obstetrics and gynecology system"
    if "emergency" in department.lower() or "critical care" in department.lower():
        return "Emergency and critical care learning theme"
    if any(
        key in department.lower()
        for key in (
            "imaging",
            "laboratory",
            "pharmacy",
            "medical insurance",
            "medical records",
            "quality control",
        )
    ):
        return "Medical technology/management learning theme"
    return "General clinical learning theme"


def derive_specialty(department: str) -> str:
    if "respiratory" in department.lower():
        return (
            "Respiratory medicine (primary-care high-frequency directions such as COPD, "
            "asthma, community-acquired pneumonia, pulmonary infection, and smoking cessation)"
        )
    if "gastro" in department.lower():
        return (
            "Gastroenterology (primary-care high-frequency directions such as Helicobacter "
            "pylori, early gastrointestinal cancer screening, and common gastrointestinal "
            "diseases)"
        )
    if "cardio" in department.lower():
        return (
            "Cardiovascular medicine (primary-care high-frequency directions such as "
            "hypertension, coronary heart disease, heart failure, and atrial fibrillation)"
        )
    if "general practice" in department.lower():
        return (
            "General practice (chronic disease management, common disease recognition, "
            "referral, and public health services)"
        )
    if "pediatric" in department.lower():
        return (
            "Pediatrics (learning directions such as pediatric fever, diarrheal dehydration, "
            "febrile seizures, and pediatric medication safety)"
        )
    return department


def derive_learning_depth(title: str) -> str:
    if any(key in title.lower() for key in ("associate senior", "chief", "senior", "professor")):
        return (
            "Associate senior/senior (updates, controversies, quality indicators, department "
            "management, and teaching)"
        )
    if any(key in title.lower() for key in ("attending", "intermediate")):
        return (
            "Attending/intermediate (stratification, differential diagnosis, process quality, "
            "update priorities)"
        )
    if any(key in title.lower() for key in ("resident", "junior", "licensed", "assistant")):
        return "Junior/resident physician (basic standards, common risks, learning reminders)"
    if any(
        key in title.lower()
        for key in (
            "quality control",
            "medical insurance",
            "medical records",
            "coding",
            "management",
        )
    ):
        return "Support/management role (reporting, quality control, medical insurance, coding, process)"
    return f"{title} (learning depth adjusted to the role's needs)"


def apply_derived_fields(state: dict[str, Any]) -> None:
    profile = state["profile"]
    department = profile.get("department") or ""
    title = profile.get("title") or ""
    region = profile.get("region") or ""
    state["derived"].update(
        {
            "department_system": (
                derive_department_system(department) if department else "pending identification"
            ),
            "specialty": derive_specialty(department) if department else "pending identification",
            "learning_depth": derive_learning_depth(title) if title else "pending identification",
            "insurance_scope": region or "pending identification",
        },
    )


def _find_by_id(items: list[dict[str, Any]], item_id: str) -> dict[str, Any] | None:
    return next((item for item in items if item.get("id") == item_id), None)


def _find_track(state: dict[str, Any], track_id: str) -> dict[str, Any]:
    track = _find_by_id(state["learning"]["tracks"], track_id)
    if track is None:
        raise ValueError("the specified learning track was not found")
    return track


def _find_lesson(track: dict[str, Any], lesson_id: str) -> dict[str, Any]:
    lesson = _find_by_id(track.get("lessons", []), lesson_id)
    if lesson is None:
        raise ValueError("the specified lesson unit was not found in this learning track")
    return lesson


def _find_delivery(state: dict[str, Any], delivery_id: str) -> dict[str, Any]:
    delivery = _find_by_id(state["learning"]["delivery_ledger"], delivery_id)
    if delivery is None:
        raise ValueError("the specified delivery record was not found")
    return delivery


def _track_source(track: dict[str, Any]) -> dict[str, Any]:
    source = track.get("source")
    if not isinstance(source, dict):
        raise ValueError("the learning track is missing its source snapshot")
    return source


def _lesson_is_terminal(lesson: dict[str, Any]) -> bool:
    return lesson.get("delivery_status") in TERMINAL_LESSON_STATES


def _first_open_lesson(track: dict[str, Any]) -> dict[str, Any] | None:
    lessons = sorted(track.get("lessons", []), key=lambda item: int(item.get("ordinal") or 0))
    for lesson in lessons:
        if not _lesson_is_terminal(lesson):
            return lesson
    return None


def _track_progress(track: dict[str, Any]) -> dict[str, int]:
    lessons = track.get("lessons", [])
    delivered = sum(
        1 for lesson in lessons if lesson.get("delivery_status") in {"accepted", "legacy_completed"}
    )
    completed = sum(1 for lesson in lessons if lesson.get("learning_status") == "mastered")
    return {"total": len(lessons), "delivered": delivered, "mastered": completed}


def _refresh_legacy_guideline_projection(state: dict[str, Any]) -> None:
    tracks = state["learning"]["tracks"]
    active = next((track for track in tracks if track.get("status") == "active"), None)
    if active is None:
        return
    source = _track_source(active)
    progress = _track_progress(active)
    current = state["current_guideline"]
    current.update(
        {
            "title": source.get("title") or "pending selection",
            "publisher": source.get("publisher") or "pending verification",
            "source_url": source.get("url") or "pending verification",
            "total_days": progress["total"],
            "current_day": progress["delivered"],
            "status": "completed"
            if progress["total"] and progress["delivered"] >= progress["total"]
            else "in_progress",
        }
    )


def _migrate_legacy_state(state: dict[str, Any]) -> list[str]:
    """Create an honest in-memory v2 projection of old day-number state.

    The migration deliberately does not fabricate a channel receipt.  Old
    completed days become legacy_completed lesson records and require a
    re-planned, re-verified course before any new formal delivery.
    """
    _ensure_learning_shape(state)
    learning = state["learning"]
    migration = learning["migration"]
    changes: list[str] = []
    legacy = state["current_guideline"]

    if (
        migration.get("legacy_state_detected")
        and not migration.get("legacy_v1_current_guideline_imported")
        and legacy.get("title")
        and legacy.get("title") != "pending selection"
    ):
        title = str(legacy.get("title"))
        total_days = max(0, int(legacy.get("total_days") or 0))
        current_day = min(max(0, int(legacy.get("current_day") or 0)), total_days)
        track_id = _normalize_id("", "", prefix="legacy-track", fallback_label=title)
        lessons: list[dict[str, Any]] = []
        source_revision = "legacy-unreverified"
        for ordinal in range(1, total_days + 1):
            status = "legacy_completed" if ordinal <= current_day else "planned"
            lesson_id = f"{track_id}-unit-{ordinal:02d}"
            lessons.append(
                {
                    "id": lesson_id,
                    "ordinal": ordinal,
                    "title": f"legacy learning record: day {ordinal}",
                    "source_anchor": (
                        "the legacy version recorded days only; sections must be backfilled "
                        "from the authoritative original text"
                    ),
                    "objectives": [],
                    "topic_tags": [],
                    "estimated_minutes": 0,
                    "unit_fingerprint": _hash(f"{track_id}:{ordinal}:legacy"),
                    "topic_fingerprint": _hash(f"{track_id}:{ordinal}:legacy-topic"),
                    "delivery_status": status,
                    "learning_status": "unknown",
                    "created_at": _now(),
                    "updated_at": _now(),
                }
            )
        learning["tracks"].append(
            {
                "id": track_id,
                "kind": "guideline",
                "label": title,
                "goal_ids": [],
                "status": "active",
                "plan_status": "needs_replan",
                "source": {
                    "document_key": _hash(f"{title}:{legacy.get('source_url') or ''}:legacy"),
                    "title": title,
                    "publisher": legacy.get("publisher") or "pending verification",
                    "version": "not recorded in the legacy version",
                    "source_revision": source_revision,
                    "url": legacy.get("source_url") or "pending verification",
                    "verification_status": "legacy_unreverified",
                    "verified_at": "",
                },
                "lessons": lessons,
                "created_at": _now(),
                "updated_at": _now(),
                "migration_note": (
                    "imported from v1 day progress; no WeChat receipt was fabricated, and the "
                    "remaining sections must be re-verified and re-planned."
                ),
            }
        )
        migration["legacy_v1_current_guideline_imported"] = True
        migration["history"].append(
            {
                "at": _now(),
                "kind": "v1_current_guideline",
                "track_id": track_id,
                "note": "the legacy progress was converted to legacy_completed; no delivery receipt was generated.",
            }
        )
        changes.append("legacy_current_guideline_imported")

    diagnostic = state["learning_diagnosis"]
    if (
        migration.get("legacy_state_detected")
        and not migration.get("legacy_v1_diagnosis_imported")
        and diagnostic.get("status") == "saved"
        and diagnostic.get("goal")
        and diagnostic.get("goal") != "pending configuration"
    ):
        learning["diagnostics"].append(
            {
                "id": _new_id("diagnostic", str(diagnostic["goal"])),
                "goal_id": "",
                "goal": diagnostic.get("goal"),
                "guideline_title": diagnostic.get("guideline_title"),
                "source_url": diagnostic.get("source_url"),
                "self_assessed_level": diagnostic.get("self_assessed_level"),
                "available_minutes_per_day": diagnostic.get("available_minutes_per_day"),
                "priority_topics": diagnostic.get("priority_topics") or [],
                "recommended_start": diagnostic.get("recommended_start"),
                "saved_with_confirmation": True,
                "created_at": _now(),
                "migration_note": (
                    "imported from the v1 learning diagnosis summary; it does not contain the "
                    "original answers."
                ),
            }
        )
        migration["legacy_v1_diagnosis_imported"] = True
        changes.append("legacy_learning_diagnosis_imported")
    return changes


def load_state(root: Path = PACKAGE_ROOT) -> dict[str, Any]:
    state = _read_state_unlocked(root)
    _migrate_legacy_state(state)
    _refresh_legacy_guideline_projection(state)
    return state


def _touch_state(state: dict[str, Any]) -> None:
    _ensure_learning_shape(state)
    _refresh_legacy_guideline_projection(state)
    state["revision"] = int(state.get("revision") or 0) + 1
    state["updated_at"] = _now()


def save_state(state: dict[str, Any], root: Path = PACKAGE_ROOT) -> None:
    with _state_lock(root):
        _migrate_legacy_state(state)
        _touch_state(state)
        _write_state_unlocked(state, root)


def _mutate_state(
    root: Path,
    mutator: Callable[[dict[str, Any]], Any],
) -> tuple[dict[str, Any], Any]:
    with _state_lock(root):
        state = _read_state_unlocked(root)
        _migrate_legacy_state(state)
        result = mutator(state)
        _touch_state(state)
        _write_state_unlocked(state, root)
    return state, result


def register_profile(
    *,
    display_name: str,
    region: str,
    hospital: str,
    department: str,
    title: str,
    consent_confirmed: bool,
    root: Path = PACKAGE_ROOT,
) -> dict[str, Any]:
    if not consent_confirmed:
        raise ValueError(
            "the user's consent to process the 5 doctor profile items was not confirmed; refused"
        )

    def mutate(state: dict[str, Any]) -> None:
        state["profile"].update(
            {
                "consent_confirmed": True,
                "display_name": _require_clean("form of address", display_name),
                "region": normalize_region(region),
                "hospital": _require_clean("hospital", hospital),
                "department": _require_clean("department", department),
                "title": _require_clean("professional title", title),
            },
        )
        state["privacy"]["deletion_status"] = "no deletion requested"
        apply_derived_fields(state)

    state, _ = _mutate_state(root, mutate)
    return state


def _validate_goal_ids(state: dict[str, Any], goal_ids: list[str]) -> list[str]:
    unique: list[str] = []
    for raw_goal_id in goal_ids:
        goal_id = _normalize_id(
            "learning goal ID", raw_goal_id, prefix="goal", fallback_label=raw_goal_id
        )
        if goal_id not in unique:
            unique.append(goal_id)
    known = {goal["id"] for goal in state["learning"]["goals"]}
    missing = [goal_id for goal_id in unique if goal_id not in known]
    if missing:
        raise ValueError(f"linked learning goals not found: {', '.join(missing)}")
    return unique


def save_learning_goal(
    *,
    label: str,
    kind: str,
    daily_minutes: int,
    target_date: str,
    priority: int,
    status: str,
    goal_id: str,
    confirm: bool,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not confirm:
        raise ValueError("saving a learning goal requires explicit confirmation")
    if kind not in GOAL_KINDS:
        raise ValueError(f"the learning goal kind must be one of: {', '.join(GOAL_KINDS)}")
    if status not in GOAL_STATUSES:
        raise ValueError(f"the learning goal status must be one of: {', '.join(GOAL_STATUSES)}")
    if not 5 <= daily_minutes <= 240:
        raise ValueError("the daily study time must be between 5 and 240 minutes")
    if not 0 <= priority <= 100:
        raise ValueError("the learning priority must be between 0 and 100")
    cleaned_label = _require_clean("learning goal", label)
    cleaned_target_date = _optional_iso_date("target date", target_date)
    normalized_id = _normalize_id(
        "learning goal ID", goal_id, prefix="goal", fallback_label=cleaned_label
    )

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        goals = state["learning"]["goals"]
        existing = _find_by_id(goals, normalized_id)
        now = _now()
        goal = {
            "id": normalized_id,
            "label": cleaned_label,
            "kind": kind,
            "status": status,
            "target_date": cleaned_target_date,
            "daily_minutes": daily_minutes,
            "priority": priority,
            "created_at": existing.get("created_at", now) if existing else now,
            "updated_at": now,
        }
        if existing is None:
            goals.append(goal)
        else:
            existing.clear()
            existing.update(goal)
        return goal

    return _mutate_state(root, mutate)


def save_learning_diagnosis(
    *,
    goal: str,
    guideline_title: str,
    source_url: str,
    self_assessed_level: str,
    available_minutes_per_day: int,
    priority_topics: list[str],
    recommended_start: str,
    confirm: bool,
    goal_id: str = "",
    root: Path = PACKAGE_ROOT,
) -> dict[str, Any]:
    """Persist only a user-confirmed, minimum diagnostic summary."""
    if not confirm:
        raise ValueError("saving a learning diagnosis summary requires explicit confirmation")
    if self_assessed_level not in LEARNING_DIAGNOSIS_LEVELS:
        raise ValueError(
            f"the self-assessed learning level must be one of: "
            f"{', '.join(LEARNING_DIAGNOSIS_LEVELS)}"
        )
    if not 5 <= available_minutes_per_day <= 240:
        raise ValueError("the daily study time must be between 5 and 240 minutes")

    cleaned_goal = _require_clean("learning goal", goal)
    cleaned_title = _optional_clean("guideline name", guideline_title, fallback="pending selection")
    cleaned_url = _optional_clean(
        "authoritative source", source_url, fallback="pending verification", max_length=2048
    )
    if cleaned_url != "pending verification":
        cleaned_url = _clean_url("authoritative source", cleaned_url)
    normalized_topics: list[str] = []
    for topic in priority_topics:
        cleaned = _require_clean("priority learning topic", topic)
        if cleaned not in normalized_topics:
            normalized_topics.append(cleaned)
    if not normalized_topics:
        raise ValueError("save at least one priority learning topic")
    cleaned_start = _require_clean("suggested starting point", recommended_start)
    normalized_goal_id = (
        _normalize_id("learning goal ID", goal_id, prefix="goal", fallback_label=cleaned_goal)
        if goal_id
        else ""
    )

    def mutate(state: dict[str, Any]) -> None:
        if (
            normalized_goal_id
            and _find_by_id(state["learning"]["goals"], normalized_goal_id) is None
        ):
            raise ValueError("linked learning goal not found; save the goal first or omit goal_id")
        state["learning_diagnosis"].update(
            {
                "goal": cleaned_goal,
                "guideline_title": cleaned_title,
                "source_url": cleaned_url,
                "self_assessed_level": self_assessed_level,
                "available_minutes_per_day": available_minutes_per_day,
                "priority_topics": normalized_topics,
                "recommended_start": cleaned_start,
                "status": "saved",
            }
        )
        diagnostic = {
            "id": _new_id("diagnostic", cleaned_goal),
            "goal_id": normalized_goal_id,
            "goal": cleaned_goal,
            "guideline_title": cleaned_title,
            "source_url": cleaned_url,
            "self_assessed_level": self_assessed_level,
            "available_minutes_per_day": available_minutes_per_day,
            "priority_topics": normalized_topics,
            "recommended_start": cleaned_start,
            "saved_with_confirmation": True,
            "created_at": _now(),
        }
        state["learning"]["diagnostics"].append(diagnostic)

    state, _ = _mutate_state(root, mutate)
    return state


def clear_learning_diagnosis(*, confirm: bool, root: Path = PACKAGE_ROOT) -> dict[str, Any]:
    if not confirm:
        raise ValueError("clearing the learning diagnosis summary requires explicit confirmation")

    def mutate(state: dict[str, Any]) -> None:
        state["learning_diagnosis"] = copy.deepcopy(DEFAULT_STATE["learning_diagnosis"])
        state["learning"]["diagnostics"] = []

    state, _ = _mutate_state(root, mutate)
    return state


def create_learning_track(
    *,
    label: str,
    publisher: str,
    version: str,
    source_url: str,
    source_revision: str,
    goal_ids: list[str],
    track_id: str,
    kind: str,
    confirm: bool,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not confirm:
        raise ValueError("creating a learning track requires explicit confirmation")
    if kind != "guideline":
        raise ValueError("this expert package only allows 'guideline' learning tracks")
    cleaned_label = _require_clean("guideline name", label)
    cleaned_publisher = _require_clean("issuing body", publisher)
    cleaned_version = _require_clean("guideline version", version)
    cleaned_source_url = _clean_url("authoritative source", source_url)
    cleaned_revision = _require_clean("source revision identifier", source_revision)
    normalized_id = _normalize_id(
        "learning track ID", track_id, prefix="track", fallback_label=cleaned_label
    )

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        if _find_by_id(state["learning"]["tracks"], normalized_id) is not None:
            raise ValueError(
                "the learning track ID already exists; use a new ID or migrate/archive the "
                "old track first"
            )
        linked_goal_ids = _validate_goal_ids(state, goal_ids)
        now = _now()
        track = {
            "id": normalized_id,
            "kind": kind,
            "label": cleaned_label,
            "goal_ids": linked_goal_ids,
            "status": "draft",
            "plan_status": "needs_planning",
            "source": {
                "document_key": _hash(
                    f"{cleaned_label}|{cleaned_publisher}|{cleaned_version}|{cleaned_source_url}|{cleaned_revision}"
                ),
                "title": cleaned_label,
                "publisher": cleaned_publisher,
                "version": cleaned_version,
                "source_revision": cleaned_revision,
                "url": cleaned_source_url,
                "verification_status": "verified",
                "verified_at": now,
            },
            "lessons": [],
            "created_at": now,
            "updated_at": now,
        }
        state["learning"]["tracks"].append(track)
        return track

    return _mutate_state(root, mutate)


def _parse_lesson_json(raw: str, *, track: dict[str, Any]) -> dict[str, Any]:
    try:
        source = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid lesson unit JSON: {exc.msg}") from exc
    if not isinstance(source, dict):
        raise ValueError("a lesson unit must be a JSON object")
    try:
        ordinal = int(source.get("ordinal"))
    except (TypeError, ValueError) as exc:
        raise ValueError("the lesson unit ordinal must be a positive integer") from exc
    if ordinal < 1:
        raise ValueError("the lesson unit ordinal must be a positive integer")
    title = _require_clean("lesson unit title", str(source.get("title") or ""))
    source_anchor_value = source.get("source_anchor", "")
    if isinstance(source_anchor_value, dict):
        source_anchor = {
            "section": _require_clean(
                "section anchor section", str(source_anchor_value.get("section") or "")
            ),
            "locator": _optional_clean(
                "section anchor locator",
                str(source_anchor_value.get("locator") or ""),
                fallback="not provided",
            ),
        }
    else:
        source_anchor = _require_clean("section anchor", str(source_anchor_value))
    raw_objectives = source.get("objectives", source.get("learning_objectives", []))
    if not isinstance(raw_objectives, list):
        raise ValueError("lesson unit objectives must be an array of strings")
    objectives: list[str] = []
    for item in raw_objectives:
        cleaned = _require_clean("learning objective", str(item))
        if cleaned not in objectives:
            objectives.append(cleaned)
    if not objectives:
        raise ValueError("every lesson unit needs at least one learning objective")
    raw_tags = source.get("topic_tags", [])
    if not isinstance(raw_tags, list):
        raise ValueError("lesson unit topic_tags must be an array of strings")
    topic_tags: list[str] = []
    for item in raw_tags:
        cleaned = _require_clean("topic tag", str(item))
        if cleaned not in topic_tags:
            topic_tags.append(cleaned)
    try:
        estimated_minutes = int(source.get("estimated_minutes", 10))
    except (TypeError, ValueError) as exc:
        raise ValueError("the estimated study time must be an integer") from exc
    if not 3 <= estimated_minutes <= 90:
        raise ValueError("the estimated study time must be between 3 and 90 minutes")
    source_revision = _track_source(track)["source_revision"]
    anchor_key = json.dumps(source_anchor, ensure_ascii=False, sort_keys=True)
    unit_fingerprint = _normalize_sha256(
        "unit fingerprint",
        str(
            source.get("unit_fingerprint")
            or _hash(f"{track['id']}|{source_revision}|{ordinal}|{title}|{anchor_key}")
        ),
    )
    topic_fingerprint = _normalize_sha256(
        "topic fingerprint",
        str(
            source.get("topic_fingerprint")
            or _hash(f"{source_revision}|{'|'.join(topic_tags)}|{title}")
        ),
    )
    lesson_id = _normalize_id(
        "lesson unit ID",
        str(source.get("id") or ""),
        prefix=f"{track['id']}-lesson",
        fallback_label=f"{track['id']}-{ordinal}-{title}",
    )
    now = _now()
    return {
        "id": lesson_id,
        "ordinal": ordinal,
        "title": title,
        "source_anchor": source_anchor,
        "objectives": objectives,
        "topic_tags": topic_tags,
        "estimated_minutes": estimated_minutes,
        "unit_fingerprint": unit_fingerprint,
        "topic_fingerprint": topic_fingerprint,
        "delivery_status": "planned",
        "learning_status": "not_started",
        "created_at": now,
        "updated_at": now,
    }


def replace_track_lessons(
    *,
    track_id: str,
    lesson_jsons: list[str],
    replace_pending: bool,
    confirm: bool,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not confirm:
        raise ValueError("saving the lesson plan requires explicit confirmation")
    if not replace_pending:
        raise ValueError("replacing pending lesson units requires replace_pending=true")
    if not lesson_jsons:
        raise ValueError("provide at least one lesson unit")

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        track = _find_track(state, track_id)
        existing = list(track.get("lessons", []))
        protected = [lesson for lesson in existing if lesson.get("delivery_status") != "planned"]
        if any(
            lesson.get("delivery_status") in {"claimed", "prepared", "dispatching", "unknown"}
            for lesson in protected
        ):
            raise ValueError(
                "there are claimed, sending, or unknown-status lesson units; reconcile the "
                "channel first, and the plan cannot be rewritten"
            )
        candidate = [_parse_lesson_json(raw, track=track) for raw in lesson_jsons]
        lesson_ids = [lesson["id"] for lesson in candidate]
        ordinals = [lesson["ordinal"] for lesson in candidate]
        fingerprints = [lesson["unit_fingerprint"] for lesson in candidate]
        if len(set(lesson_ids)) != len(lesson_ids):
            raise ValueError("lesson unit IDs must not repeat")
        if len(set(ordinals)) != len(ordinals):
            raise ValueError("lesson unit ordinals must not repeat")
        if len(set(fingerprints)) != len(fingerprints):
            raise ValueError("duplicate lesson units cannot be saved within one track")
        protected_ids = {lesson["id"] for lesson in protected}
        protected_ordinals = {lesson["ordinal"] for lesson in protected}
        protected_fingerprints = {lesson["unit_fingerprint"] for lesson in protected}
        if protected_ids.intersection(lesson_ids):
            raise ValueError("the ID of a delivered lesson unit cannot be rewritten")
        if protected_ordinals.intersection(ordinals):
            raise ValueError("the ordinal of a delivered lesson unit cannot be rewritten")
        if protected_fingerprints.intersection(fingerprints):
            raise ValueError("the fingerprint of a delivered lesson unit cannot be reused")
        all_lessons = sorted(protected + candidate, key=lambda lesson: lesson["ordinal"])
        expected_ordinals = list(range(1, len(all_lessons) + 1))
        if [lesson["ordinal"] for lesson in all_lessons] != expected_ordinals:
            raise ValueError("lesson unit ordinals must be numbered consecutively from 1")
        track["lessons"] = all_lessons
        track["plan_status"] = "ready"
        track["updated_at"] = _now()
        return {
            "track_id": track["id"],
            "lesson_count": len(all_lessons),
            "preserved_terminal_lessons": len(protected),
        }

    return _mutate_state(root, mutate)


def activate_learning_track(
    *,
    track_id: str,
    confirm: bool,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not confirm:
        raise ValueError("activating a learning track requires explicit confirmation")

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        track = _find_track(state, track_id)
        source = _track_source(track)
        if source.get("verification_status") != "verified":
            raise ValueError(
                "the source is not verified; a formal learning track cannot be activated"
            )
        if track.get("plan_status") != "ready" or not track.get("lessons"):
            raise ValueError(
                "the learning track has no complete section plan and cannot be activated"
            )
        if track.get("status") == "superseded":
            raise ValueError("a superseded old track cannot be re-activated; use the new track")
        track["status"] = "active"
        track["updated_at"] = _now()
        return _track_public_summary(track)

    return _mutate_state(root, mutate)


def set_learning_track_status(
    *,
    track_id: str,
    status: str,
    confirm: bool,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Pause or archive a track without deleting its immutable history."""
    if not confirm:
        raise ValueError("pausing or archiving a learning track requires explicit confirmation")
    if status not in {"paused", "archived"}:
        raise ValueError(
            "this operation only allows setting the learning track to paused or archived"
        )

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        track = _find_track(state, track_id)
        if track.get("status") == "superseded":
            raise ValueError("the status of a superseded old track can no longer be changed")
        track["status"] = status
        track["updated_at"] = _now()
        return _track_public_summary(track)

    return _mutate_state(root, mutate)


def _track_public_summary(track: dict[str, Any]) -> dict[str, Any]:
    source = _track_source(track)
    progress = _track_progress(track)
    next_lesson = _first_open_lesson(track)
    return {
        "id": track["id"],
        "label": track.get("label"),
        "status": track.get("status"),
        "plan_status": track.get("plan_status"),
        "source": {
            "title": source.get("title"),
            "publisher": source.get("publisher"),
            "version": source.get("version"),
            "source_revision": source.get("source_revision"),
            "url": source.get("url"),
            "verification_status": source.get("verification_status"),
        },
        "progress": {
            "planned_units": progress["total"],
            "user_marked_mastered": progress["mastered"],
        },
        "next_lesson": _lesson_public_summary(next_lesson) if next_lesson else None,
    }


def _lesson_public_summary(lesson: dict[str, Any] | None) -> dict[str, Any] | None:
    if lesson is None:
        return None
    return {
        "id": lesson.get("id"),
        "ordinal": lesson.get("ordinal"),
        "title": lesson.get("title"),
        "source_anchor": lesson.get("source_anchor"),
        "objectives": lesson.get("objectives"),
        "topic_tags": lesson.get("topic_tags"),
        "estimated_minutes": lesson.get("estimated_minutes"),
        "delivery_status": lesson.get("delivery_status"),
        "learning_status": lesson.get("learning_status"),
    }


def get_track_status(*, track_id: str, root: Path = PACKAGE_ROOT) -> dict[str, Any]:
    state = load_state(root)
    if track_id:
        return {"track": _track_public_summary(_find_track(state, track_id))}
    return {
        "tracks": [_track_public_summary(track) for track in state["learning"]["tracks"]],
        "goals": [
            {
                key: goal.get(key)
                for key in (
                    "id",
                    "label",
                    "kind",
                    "status",
                    "target_date",
                    "daily_minutes",
                    "priority",
                )
            }
            for goal in state["learning"]["goals"]
        ],
    }


def _resolve_active_track(state: dict[str, Any], track_id: str) -> dict[str, Any]:
    if track_id:
        return _find_track(state, track_id)
    active_tracks = [
        track for track in state["learning"]["tracks"] if track.get("status") == "active"
    ]
    if not active_tracks:
        raise ValueError("there is no active learning track")
    if len(active_tracks) > 1:
        raise ValueError("multiple active learning tracks exist; choose a track_id explicitly")
    return active_tracks[0]


def get_next_lesson(*, track_id: str, root: Path = PACKAGE_ROOT) -> dict[str, Any]:
    state = load_state(root)
    track = _resolve_active_track(state, track_id)
    if track.get("status") != "active":
        raise ValueError(
            "the learning track is not active; a preview may read the plan, but activate the "
            "track before formal learning"
        )
    if track.get("plan_status") != "ready":
        raise ValueError(
            "the learning track needs re-planning; do not continue at random by the old day count"
        )
    lesson = _first_open_lesson(track)
    return {
        "track": _track_public_summary(track),
        "lesson": _lesson_public_summary(lesson),
        "preview_only": True,
        "note": "reading the next unit neither creates a delivery ledger nor advances learning progress.",
    }


def check_daily_delivery(
    *,
    track_id: str,
    logical_date: str,
    root: Path = PACKAGE_ROOT,
) -> dict[str, Any]:
    """Read-only dedup check for the generic-cron daily lesson.

    The ledger written here is a *weak* delivery log: it records that the cron
    run produced the unit, not that the channel accepted it.
    """
    cleaned_date = _require_clean("logical date", logical_date, max_length=32)
    state = load_state(root)
    track = _resolve_active_track(state, track_id)
    for record in reversed(state["learning"]["delivery_ledger"]):
        if (
            record.get("track_id") == track["id"]
            and record.get("scheduled_local_date") == cleaned_date
        ):
            return {
                "track_id": track["id"],
                "logical_date": cleaned_date,
                "already_sent": True,
                "lesson_id": record.get("lesson_id") or "",
                "recorded_at": record.get("created_at") or "",
                "note": "a delivery record already exists for this date; do not regenerate or resend the same unit.",
            }
    return {
        "track_id": track["id"],
        "logical_date": cleaned_date,
        "already_sent": False,
        "lesson_id": "",
        "recorded_at": "",
        "note": "there is no delivery record for this date yet; the unit for today may be generated and sent.",
    }


def record_daily_delivery(
    *,
    track_id: str,
    lesson_id: str,
    logical_date: str,
    confirm: bool,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Record a weak cron delivery and advance the track to the next unit.

    Idempotent on (track_id, logical_date): a second call for the same day
    returns the existing entry without duplicating.  This is NOT a trusted
    receipt ledger — it only prevents the generic cron from re-sending the
    same unit on the same logical date.
    """
    if not confirm:
        raise ValueError("recording a daily delivery requires explicit confirmation")
    cleaned_date = _require_clean("logical date", logical_date, max_length=32)

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        track = _resolve_active_track(state, track_id)
        ledger = state["learning"]["delivery_ledger"]
        for record in reversed(ledger):
            if (
                record.get("track_id") == track["id"]
                and record.get("scheduled_local_date") == cleaned_date
            ):
                return {
                    "recorded": False,
                    "already_sent": True,
                    "delivery_id": record.get("id") or "",
                    "lesson_id": record.get("lesson_id") or "",
                    "note": "a delivery is already recorded for this date; nothing was written twice.",
                }
        lessons = track.get("lessons", [])
        lesson = _find_by_id(lessons, lesson_id) if lesson_id else _first_open_lesson(track)
        if lesson is None:
            raise ValueError("there is no unit available for delivery")
        now = _now()
        entry = {
            "id": _new_id("delivery", f"{track['id']}:{cleaned_date}:{lesson['id']}"),
            "kind": "cron_weak_delivery",
            "track_id": track["id"],
            "lesson_id": lesson["id"],
            "scheduled_local_date": cleaned_date,
            "state": "sent_unconfirmed",
            "attempt": 1,
            "note": (
                "generic cron weak delivery record: it only means the content was generated "
                "and handed to the channel; it contains no channel receipt."
            ),
            "created_at": now,
            "updated_at": now,
        }
        ledger.append(entry)
        lesson["delivery_status"] = "accepted"
        lesson["updated_at"] = now
        track["updated_at"] = now
        return {
            "recorded": True,
            "already_sent": False,
            "delivery_id": entry["id"],
            "lesson_id": lesson["id"],
            "lesson_ordinal": lesson.get("ordinal"),
            "track_id": track["id"],
            "logical_date": cleaned_date,
            "note": (
                "today's delivery was recorded and the track advanced to the next unit; "
                "this record is not a delivery receipt."
            ),
        }

    return _mutate_state(root, mutate)


def mark_lesson_learning(
    *,
    track_id: str,
    lesson_id: str,
    learning_status: str,
    confirm: bool,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not confirm:
        raise ValueError("updating the learning completion status requires explicit confirmation")
    if learning_status not in LESSON_LEARNING_STATUSES:
        raise ValueError(
            f"the learning status must be one of: {', '.join(LESSON_LEARNING_STATUSES)}"
        )

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        track = _find_track(state, track_id)
        lesson = _find_lesson(track, lesson_id)
        lesson["learning_status"] = learning_status
        lesson["updated_at"] = _now()
        if all(item.get("learning_status") == "mastered" for item in track.get("lessons", [])):
            track["status"] = "completed"
        track["updated_at"] = _now()
        return _lesson_public_summary(lesson) or {}

    return _mutate_state(root, mutate)


def _delivery_is_expired(delivery: dict[str, Any]) -> bool:
    expiration = _parse_timestamp(str(delivery.get("lease_expires_at") or ""))
    return expiration is not None and expiration <= datetime.now(_UTC)


def _lease_expiration(seconds: int) -> str:
    if not 60 <= seconds <= 3600:
        raise ValueError("the delivery claim lease must be between 60 and 3600 seconds")
    timestamp = datetime.now(_UTC).timestamp() + seconds
    return (
        datetime.fromtimestamp(timestamp, _UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _delivery_details(
    delivery: dict[str, Any],
    track: dict[str, Any],
    lesson: dict[str, Any],
    *,
    disposition: str,
    should_send: bool,
    claim_token: str = "",
) -> dict[str, Any]:
    details: dict[str, Any] = {
        "disposition": disposition,
        "should_send": should_send,
        "delivery": {
            key: delivery.get(key)
            for key in (
                "id",
                "state",
                "attempt",
                "lease_expires_at",
            )
        },
        "track": _track_public_summary(track),
        "lesson": _lesson_public_summary(lesson),
    }
    if claim_token:
        details["security_note"] = (
            "the delivery token may only be held by the platform's authenticated outbox "
            "service and is never output to the template or the user."
        )
    return details


def _delivery_for_lesson(
    state: dict[str, Any],
    track_id: str,
    lesson_id: str,
) -> dict[str, Any] | None:
    return next(
        (
            record
            for record in state["learning"]["delivery_ledger"]
            if record.get("track_id") == track_id
            and record.get("lesson_id") == lesson_id
            and record.get("state") == "accepted"
        ),
        None,
    )


def _delivery_has_idempotency_key(delivery: dict[str, Any], key_hash: str) -> bool:
    key_hashes = delivery.get("idempotency_key_hashes", [])
    return key_hash == delivery.get("idempotency_key_hash") or key_hash in key_hashes


def _remember_idempotency_key(delivery: dict[str, Any], key_hash: str) -> None:
    remembered = list(delivery.get("idempotency_key_hashes") or [])
    primary = delivery.get("idempotency_key_hash")
    if primary and primary not in remembered:
        remembered.append(primary)
    if key_hash not in remembered:
        remembered.append(key_hash)
    delivery["idempotency_key_hash"] = key_hash
    delivery["idempotency_key_hashes"] = remembered


def _reclaim_delivery(
    delivery: dict[str, Any],
    lesson: dict[str, Any],
    *,
    key_hash: str,
    route_key: str,
    slot_key: str,
    lease_seconds: int,
) -> str:
    token = secrets.token_urlsafe(24)
    _remember_idempotency_key(delivery, key_hash)
    delivery.update(
        {
            "state": "claimed",
            "route_key_hash": route_key,
            "slot_key_hash": slot_key,
            "scheduled_local_date": _shanghai_date(),
            "attempt": int(delivery.get("attempt") or 0) + 1,
            "claim_token_hash": _hash(token),
            "lease_expires_at": _lease_expiration(lease_seconds),
            "updated_at": _now(),
        }
    )
    lesson["delivery_status"] = "claimed"
    lesson["updated_at"] = _now()
    return token


def _platform_delivery_lifecycle_unavailable() -> None:
    raise RuntimeError(
        "the formal delivery ledger and channel receipts must be held by the platform's "
        "authenticated outbox service; scripts in the expert workspace provide no claim, "
        "send, failure, or delivery-confirmation capability."
    )


def _claim_delivery_for_platform(
    *,
    track_id: str,
    lesson_id: str,
    route_key: str,
    slot_key: str,
    idempotency_key: str,
    lease_seconds: int,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reserved for a future platform-owned outbox, never callable in this template."""
    _platform_delivery_lifecycle_unavailable()
    cleaned_route = _require_clean("delivery route", route_key)
    cleaned_slot = _require_clean("delivery slot", slot_key)
    cleaned_key = _require_clean("idempotency key", idempotency_key, max_length=512)
    route_hash = _hash(cleaned_route)
    slot_hash = _hash(cleaned_slot)
    key_hash = _hash(cleaned_key)

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        track = _find_track(state, track_id)
        if track.get("status") != "active" or track.get("plan_status") != "ready":
            raise ValueError(
                "a formal delivery unit can only be claimed for an active learning track "
                "with a complete plan"
            )
        if lesson_id:
            lesson = _find_lesson(track, lesson_id)
            expected = _first_open_lesson(track)
            if expected is not None and expected["id"] != lesson["id"]:
                raise ValueError("formal delivery must claim the next lesson unit in track order")
        else:
            lesson = _first_open_lesson(track)
            if lesson is None:
                raise ValueError(
                    "this learning track has no lesson unit available for formal delivery"
                )

        existing_same_key = next(
            (
                record
                for record in state["learning"]["delivery_ledger"]
                if _delivery_has_idempotency_key(record, key_hash)
            ),
            None,
        )
        if existing_same_key is not None:
            if (
                existing_same_key.get("track_id") != track["id"]
                or existing_same_key.get("lesson_id") != lesson["id"]
                or existing_same_key.get("route_key_hash") != route_hash
            ):
                raise ValueError(
                    "the idempotency key is already bound to another learning track, unit, "
                    "or delivery route and cannot be reused"
                )
            existing_track = _find_track(state, str(existing_same_key["track_id"]))
            existing_lesson = _find_lesson(existing_track, str(existing_same_key["lesson_id"]))
            if existing_same_key.get("state") == "accepted":
                return _delivery_details(
                    existing_same_key,
                    existing_track,
                    existing_lesson,
                    disposition="already_accepted",
                    should_send=False,
                )
            if existing_same_key.get("state") in {"prepared", "dispatching", "unknown"}:
                if existing_same_key.get("state") == "prepared" and _delivery_is_expired(
                    existing_same_key
                ):
                    existing_same_key["state"] = "unknown"
                    existing_lesson["delivery_status"] = "unknown"
                    existing_same_key["updated_at"] = _now()
                    existing_lesson["updated_at"] = _now()
                return _delivery_details(
                    existing_same_key,
                    existing_track,
                    existing_lesson,
                    disposition="needs_transport_reconcile",
                    should_send=False,
                )
            if existing_same_key.get("state") == "claimed" and not _delivery_is_expired(
                existing_same_key
            ):
                return _delivery_details(
                    existing_same_key,
                    existing_track,
                    existing_lesson,
                    disposition="already_claimed",
                    should_send=False,
                )
            # An expired unprepared claim or a retryable failure can safely reuse
            # the same delivery ID but receives a fresh, transient claim token.
            token = _reclaim_delivery(
                existing_same_key,
                existing_lesson,
                key_hash=key_hash,
                route_key=route_hash,
                slot_key=slot_hash,
                lease_seconds=lease_seconds,
            )
            return _delivery_details(
                existing_same_key,
                existing_track,
                existing_lesson,
                disposition="reclaimed",
                should_send=True,
                claim_token=token,
            )

        # A scheduler retry normally has a new run key and slot. Preserve the
        # original delivery ID for the same lesson and route, rather than
        # creating a second ledger record that could duplicate the content.
        existing_retry = next(
            (
                record
                for record in reversed(state["learning"]["delivery_ledger"])
                if record.get("track_id") == track["id"]
                and record.get("lesson_id") == lesson["id"]
                and record.get("route_key_hash") == route_hash
                and record.get("state") == "failed_retryable"
            ),
            None,
        )
        if existing_retry is not None:
            token = _reclaim_delivery(
                existing_retry,
                lesson,
                key_hash=key_hash,
                route_key=route_hash,
                slot_key=slot_hash,
                lease_seconds=lease_seconds,
            )
            return _delivery_details(
                existing_retry,
                track,
                lesson,
                disposition="reclaimed",
                should_send=True,
                claim_token=token,
            )

        existing_slot = next(
            (
                record
                for record in state["learning"]["delivery_ledger"]
                if record.get("route_key_hash") == route_hash
                and record.get("slot_key_hash") == slot_hash
                and record.get("state") not in {"failed_retryable", "cancelled"}
            ),
            None,
        )
        if existing_slot is not None:
            slot_track = _find_track(state, str(existing_slot["track_id"]))
            slot_lesson = _find_lesson(slot_track, str(existing_slot["lesson_id"]))
            return _delivery_details(
                existing_slot,
                slot_track,
                slot_lesson,
                disposition="slot_taken",
                should_send=False,
            )

        accepted = _delivery_for_lesson(state, track["id"], lesson["id"])
        if accepted is not None:
            return _delivery_details(
                accepted,
                track,
                lesson,
                disposition="lesson_already_accepted",
                should_send=False,
            )
        if lesson.get("delivery_status") in {"prepared", "dispatching", "unknown"}:
            return {
                "disposition": "lesson_needs_transport_reconcile",
                "should_send": False,
                "track": _track_public_summary(track),
                "lesson": _lesson_public_summary(lesson),
            }
        if lesson.get("delivery_status") == "claimed":
            return {
                "disposition": "lesson_already_claimed",
                "should_send": False,
                "track": _track_public_summary(track),
                "lesson": _lesson_public_summary(lesson),
            }
        if _lesson_is_terminal(lesson):
            raise ValueError(
                "this lesson unit is finished and cannot be claimed again as a new formal delivery"
            )

        token = secrets.token_urlsafe(24)
        now = _now()
        delivery = {
            "id": _new_id("delivery", f"{track['id']}-{lesson['id']}-{cleaned_slot}"),
            "idempotency_key_hash": key_hash,
            "idempotency_key_hashes": [key_hash],
            "route_key_hash": route_hash,
            "slot_key_hash": slot_hash,
            "scheduled_local_date": _shanghai_date(),
            "track_id": track["id"],
            "lesson_id": lesson["id"],
            "source_revision": _track_source(track)["source_revision"],
            "state": "claimed",
            "attempt": 1,
            "claim_token_hash": _hash(token),
            "lease_expires_at": _lease_expiration(lease_seconds),
            "content_sha256": "",
            "provider_message_id_hash": "",
            "created_at": now,
            "updated_at": now,
        }
        state["learning"]["delivery_ledger"].append(delivery)
        lesson["delivery_status"] = "claimed"
        lesson["updated_at"] = now
        return _delivery_details(
            delivery,
            track,
            lesson,
            disposition="claimed",
            should_send=True,
            claim_token=token,
        )

    return _mutate_state(root, mutate)


def _verify_delivery_token(delivery: dict[str, Any], claim_token: str) -> None:
    if not secrets.compare_digest(str(delivery.get("claim_token_hash") or ""), _hash(claim_token)):
        raise ValueError("the delivery claim token is invalid or expired")


# These state transitions intentionally have no CLI command. A template agent
# cannot attest that WeChat accepted a message. A future platform-owned outbox
# may call private helpers after it verifies a channel receipt.
def _record_delivery_prepared_from_verified_sender(
    *,
    delivery_id: str,
    claim_token: str,
    content_sha256: str,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Record that a validated draft exists, without claiming channel success."""
    _platform_delivery_lifecycle_unavailable()
    normalized_content_hash = _normalize_sha256("content hash", content_sha256)

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        delivery = _find_delivery(state, delivery_id)
        track = _find_track(state, str(delivery["track_id"]))
        lesson = _find_lesson(track, str(delivery["lesson_id"]))
        if delivery.get("state") == "accepted":
            return _delivery_details(
                delivery, track, lesson, disposition="already_accepted", should_send=False
            )
        if delivery.get("state") != "claimed":
            raise ValueError("only a claimed delivery record can be written to the prepared state")
        if _delivery_is_expired(delivery):
            raise ValueError(
                "the delivery claim lease has expired; claim again, and sending cannot continue"
            )
        _verify_delivery_token(delivery, claim_token)
        delivery.update(
            {
                "state": "prepared",
                "content_sha256": normalized_content_hash,
                "updated_at": _now(),
            }
        )
        lesson["delivery_status"] = "prepared"
        lesson["updated_at"] = _now()
        return _delivery_details(delivery, track, lesson, disposition="prepared", should_send=True)

    return _mutate_state(root, mutate)


def _begin_delivery_send_from_verified_sender(
    *,
    delivery_id: str,
    claim_token: str,
    content_sha256: str,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Move to dispatching immediately before a real channel send."""
    _platform_delivery_lifecycle_unavailable()
    normalized_content_hash = _normalize_sha256("content hash", content_sha256)

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        delivery = _find_delivery(state, delivery_id)
        track = _find_track(state, str(delivery["track_id"]))
        lesson = _find_lesson(track, str(delivery["lesson_id"]))
        if delivery.get("state") == "accepted":
            return _delivery_details(
                delivery, track, lesson, disposition="already_accepted", should_send=False
            )
        if delivery.get("state") not in {"claimed", "prepared"}:
            raise ValueError("the delivery record cannot start sending right now")
        if _delivery_is_expired(delivery):
            raise ValueError(
                "the delivery claim lease has expired; claim again, and sending cannot start"
            )
        _verify_delivery_token(delivery, claim_token)
        delivery.update(
            {
                "state": "dispatching",
                "content_sha256": normalized_content_hash,
                "updated_at": _now(),
            }
        )
        lesson["delivery_status"] = "dispatching"
        lesson["updated_at"] = _now()
        return _delivery_details(
            delivery, track, lesson, disposition="dispatching", should_send=True
        )

    return _mutate_state(root, mutate)


def _acknowledge_delivery_from_verified_sender(
    *,
    delivery_id: str,
    claim_token: str,
    provider_message_id: str,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Accept a real, positive channel receipt and unlock the next lesson."""
    _platform_delivery_lifecycle_unavailable()
    cleaned_provider_id = _require_clean("channel receipt ID", provider_message_id, max_length=512)

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        delivery = _find_delivery(state, delivery_id)
        track = _find_track(state, str(delivery["track_id"]))
        lesson = _find_lesson(track, str(delivery["lesson_id"]))
        if delivery.get("state") == "accepted":
            return _delivery_details(
                delivery, track, lesson, disposition="already_accepted", should_send=False
            )
        if delivery.get("state") != "dispatching":
            raise ValueError(
                "only a delivery record that is dispatching to the channel can acknowledge a receipt"
            )
        _verify_delivery_token(delivery, claim_token)
        now = _now()
        delivery.update(
            {
                "state": "accepted",
                "provider_message_id_hash": _hash(cleaned_provider_id),
                "updated_at": now,
            }
        )
        lesson.update(
            {
                "delivery_status": "accepted",
                "updated_at": now,
            }
        )
        track["updated_at"] = now
        return _delivery_details(delivery, track, lesson, disposition="accepted", should_send=False)

    return _mutate_state(root, mutate)


def _fail_delivery_from_verified_sender(
    *,
    delivery_id: str,
    claim_token: str,
    kind: str,
    error_code: str,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _platform_delivery_lifecycle_unavailable()
    if kind not in {"retryable", "unknown"}:
        raise ValueError("the delivery failure kind must be retryable or unknown")
    cleaned_error = _optional_clean(
        "failure code", error_code, fallback="unspecified", max_length=120
    )

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        delivery = _find_delivery(state, delivery_id)
        track = _find_track(state, str(delivery["track_id"]))
        lesson = _find_lesson(track, str(delivery["lesson_id"]))
        if delivery.get("state") == "accepted":
            raise ValueError(
                "a delivery record with a confirmed receipt cannot be changed to a failure"
            )
        _verify_delivery_token(delivery, claim_token)
        next_state = "failed_retryable" if kind == "retryable" else "unknown"
        now = _now()
        delivery.update({"state": next_state, "error_code": cleaned_error, "updated_at": now})
        lesson["delivery_status"] = next_state
        lesson["updated_at"] = now
        return _delivery_details(
            delivery,
            track,
            lesson,
            disposition=next_state,
            should_send=False,
        )

    return _mutate_state(root, mutate)


def _recover_stale_deliveries_for_platform(
    *,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Recover only unprepared claims; a send-in-progress state remains unknown."""
    _platform_delivery_lifecycle_unavailable()

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        recovered: list[str] = []
        reconciled: list[str] = []
        for delivery in state["learning"]["delivery_ledger"]:
            if not _delivery_is_expired(delivery):
                continue
            if delivery.get("state") not in {"claimed", "prepared", "dispatching"}:
                continue
            track = _find_track(state, str(delivery["track_id"]))
            lesson = _find_lesson(track, str(delivery["lesson_id"]))
            now = _now()
            if delivery.get("state") == "claimed":
                delivery.update(
                    {
                        "state": "failed_retryable",
                        "updated_at": now,
                        "error_code": "lease_expired_before_send",
                    }
                )
                lesson["delivery_status"] = "failed_retryable"
                recovered.append(str(delivery["id"]))
            else:
                delivery.update(
                    {
                        "state": "unknown",
                        "updated_at": now,
                        "error_code": "transport_receipt_unknown",
                    }
                )
                lesson["delivery_status"] = "unknown"
                reconciled.append(str(delivery["id"]))
            lesson["updated_at"] = now
        return {
            "recovered_retryable_delivery_ids": recovered,
            "needs_transport_reconcile_delivery_ids": reconciled,
        }

    return _mutate_state(root, mutate)


def preview_track_migration(
    *,
    track_id: str,
    publisher: str,
    version: str,
    source_url: str,
    source_revision: str,
    root: Path = PACKAGE_ROOT,
) -> dict[str, Any]:
    state = load_state(root)
    track = _find_track(state, track_id)
    new_source = {
        "publisher": _require_clean("issuing body", publisher),
        "version": _require_clean("new guideline version", version),
        "url": _clean_url("authoritative source", source_url),
        "source_revision": _require_clean("source revision identifier", source_revision),
    }
    progress = _track_progress(track)
    unresolved = [
        lesson["ordinal"]
        for lesson in track.get("lessons", [])
        if lesson.get("delivery_status") not in TERMINAL_LESSON_STATES
    ]
    return {
        "preview_only": True,
        "old_track": _track_public_summary(track),
        "candidate_source": new_source,
        "impact": {
            "delivered_or_legacy_units_kept_on_old_track": progress["delivered"],
            "unresolved_unit_ordinals": unresolved,
            "requires_new_lessons": True,
            "rule": "the old version, old lesson units, and existing delivery ledger are never silently overwritten.",
        },
        "next_action": (
            "after the user confirms, create a new-version draft track that preserves the old "
            "track's history, then re-verify and plan the sections."
        ),
    }


def migrate_track(
    *,
    track_id: str,
    publisher: str,
    version: str,
    source_url: str,
    source_revision: str,
    new_track_id: str,
    confirm: bool,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not confirm:
        raise ValueError("migrating to a new guideline version requires explicit confirmation")
    cleaned_publisher = _require_clean("issuing body", publisher)
    cleaned_version = _require_clean("new guideline version", version)
    cleaned_url = _clean_url("authoritative source", source_url)
    cleaned_revision = _require_clean("source revision identifier", source_revision)

    def mutate(state: dict[str, Any]) -> dict[str, Any]:
        old_track = _find_track(state, track_id)
        if old_track.get("status") == "superseded":
            raise ValueError("this track has already been migrated; see its successor track")
        new_id = _normalize_id(
            "new learning track ID",
            new_track_id,
            prefix="track",
            fallback_label=f"{old_track['label']}-{cleaned_version}",
        )
        if _find_by_id(state["learning"]["tracks"], new_id) is not None:
            raise ValueError("the new learning track ID already exists")
        now = _now()
        new_track = {
            "id": new_id,
            "kind": old_track.get("kind", "guideline"),
            "label": old_track.get("label"),
            "goal_ids": list(old_track.get("goal_ids") or []),
            "status": "draft",
            "plan_status": "needs_planning",
            "source": {
                "document_key": _hash(
                    f"{old_track.get('label')}|{cleaned_publisher}|{cleaned_version}|{cleaned_url}|{cleaned_revision}"
                ),
                "title": old_track.get("label"),
                "publisher": cleaned_publisher,
                "version": cleaned_version,
                "source_revision": cleaned_revision,
                "url": cleaned_url,
                "verification_status": "verified",
                "verified_at": now,
            },
            "lessons": [],
            "created_at": now,
            "updated_at": now,
            "supersedes_track_id": old_track["id"],
            "migration_note": (
                "created with the user's confirmation; the old track, sections, and delivery "
                "ledger are preserved and not overwritten."
            ),
        }
        old_track["status"] = "superseded"
        old_track["superseded_by_track_id"] = new_id
        old_track["updated_at"] = now
        state["learning"]["tracks"].append(new_track)
        state["learning"]["migration"]["history"].append(
            {
                "at": now,
                "kind": "source_version_migration",
                "from_track_id": old_track["id"],
                "to_track_id": new_id,
                "old_source_revision": _track_source(old_track).get("source_revision"),
                "new_source_revision": cleaned_revision,
            }
        )
        return {
            "old_track_id": old_track["id"],
            "new_track": _track_public_summary(new_track),
            "next_action": "after saving the section unit plan for the new track, the user confirms activation.",
        }

    return _mutate_state(root, mutate)


def set_guideline(
    *,
    title: str,
    publisher: str,
    source_url: str,
    total_days: int,
    current_day: int,
    status: str,
    root: Path = PACKAGE_ROOT,
) -> dict[str, Any]:
    """Compatibility bridge for v1 callers; it never creates a send receipt."""
    if total_days < 1 or total_days > 14:
        raise ValueError("the planned total days must be between 1 and 14")
    if current_day < 0 or current_day > total_days:
        raise ValueError("the current progress must be between 0 and the planned total days")
    cleaned_title = _require_clean("guideline name", title)
    cleaned_publisher = _require_clean("issuing body", publisher)
    cleaned_url = _clean_url("authoritative source", source_url)

    def mutate(state: dict[str, Any]) -> None:
        state["current_guideline"].update(
            {
                "title": cleaned_title,
                "publisher": cleaned_publisher,
                "source_url": cleaned_url,
                "total_days": total_days,
                "current_day": current_day,
                "status": status,
            }
        )
        # Mark as not imported so the v1 projection is migrated under the same
        # locked write, with a re-plan requirement instead of unsafe new lessons.
        state["learning"]["migration"]["legacy_state_detected"] = True
        state["learning"]["migration"]["legacy_v1_current_guideline_imported"] = False
        _migrate_legacy_state(state)

    state, _ = _mutate_state(root, mutate)
    return state


def advance_guideline(
    *, current_day: int | None, increment: int, root: Path = PACKAGE_ROOT
) -> dict[str, Any]:
    del current_day, increment, root
    raise ValueError(
        "guideline-advance is deprecated: generating content does not mean WeChat delivered "
        "it. Only the platform-owned delivery service, after verifying a real channel receipt, "
        "can confirm delivery and advance the lesson unit."
    )


def clear_profile(*, confirm: bool, root: Path = PACKAGE_ROOT) -> dict[str, Any]:
    if not confirm:
        raise ValueError("clearing the profile requires explicit confirmation")
    with _state_lock(root):
        state = _deep_default_state()
        state["privacy"]["deletion_status"] = "cleared"
        _touch_state(state)
        _write_state_unlocked(state, root)
    return state


def state_migrate(
    *,
    confirm: bool,
    dry_run: bool,
    root: Path = PACKAGE_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    with _state_lock(root):
        state = _read_state_unlocked(root)
        changes = _migrate_legacy_state(state)
        details = {
            "dry_run": dry_run,
            "changes": changes,
            "will_write": bool(changes and not dry_run),
        }
        if dry_run:
            _refresh_legacy_guideline_projection(state)
            return state, details
        if changes and not confirm:
            raise ValueError(
                "the state migration will write a new learning track; use --confirm true"
            )
        if changes:
            _touch_state(state)
            _write_state_unlocked(state, root)
        return state, details


def render_user_text(state: dict[str, Any]) -> str:
    profile = state["profile"]
    derived = state["derived"]
    learning_diagnosis = state["learning_diagnosis"]
    subscriptions = state["subscriptions"]
    privacy = state["privacy"]
    learning = state["learning"]
    consent = (
        "confirmed (used only for learning subscription configuration)"
        if profile.get("consent_confirmed")
        else "pending confirmation"
    )
    active_tracks = [track for track in learning["tracks"] if track.get("status") == "active"]
    active_goals = [goal for goal in learning["goals"] if goal.get("status") == "active"]

    if active_goals:
        goal_lines = "\n".join(
            f"- {goal.get('label')} ({goal.get('kind')}; {goal.get('daily_minutes')} minutes/day; "
            f"target date: {goal.get('target_date') or 'not set'})"
            for goal in active_goals
        )
    else:
        goal_lines = "- no saved learning goals yet"

    if active_tracks:
        track_lines: list[str] = []
        for track in active_tracks:
            source = _track_source(track)
            progress = _track_progress(track)
            next_lesson = _first_open_lesson(track)
            next_label = (
                f"lesson unit {next_lesson.get('ordinal')}/{progress['total']}: "
                f"{next_lesson.get('title')}"
                if next_lesson
                else "no lesson unit pending delivery"
            )
            track_lines.append(
                f"- {source.get('title')} ({source.get('version')}; {source.get('publisher')})\n"
                f"  - Planned units: {progress['total']}; "
                f"user-marked mastered: {progress['mastered']}/{progress['total']}\n"
                f"  - Next unit: {next_label}\n"
                f"  - Source: {source.get('url') or 'pending verification'}"
            )
        track_text = "\n".join(track_lines)
    else:
        track_text = (
            "- no enabled learning tracks yet; previews, diagnoses, and ordinary general "
            "tasks do not require creating a track."
        )

    return f"""---
summary: "Primary-care doctor learning profile"
read_when:
  - Doctor registration
  - Learning goals and learning tracks
  - Guideline learning diagnosis
  - Subscription task status
---

# Primary-Care Doctor Learning Profile

Auto-generated by clinical_profile.py, read-only; for the rules see SOUL.md.

## Registration

- Consent: {consent}
- Form of address: {profile.get("display_name") or "pending confirmation"}
- Region: {profile.get("region") or "pending confirmation"}
- Hospital: {profile.get("hospital") or "pending confirmation"}
- Department: {profile.get("department") or "pending confirmation"}
- Professional title: {profile.get("title") or "pending confirmation"}

## Identification

- Department system: {derived.get("department_system") or "pending identification"}
- Learning depth by professional title: {derived.get("learning_depth") or "pending identification"}
- Medical insurance focus scope: {derived.get("insurance_scope") or "pending identification"}

## Learning goals

{goal_lines}

## Learning tracks

{track_text}

## Learning diagnosis

- Status: {learning_diagnosis.get("status") or "not_started"}
- Associated guideline: {learning_diagnosis.get("guideline_title") or "pending selection"}
- Self-assessment: {learning_diagnosis.get("self_assessed_level") or "not_assessed"}
- Priority topics: {"; ".join(learning_diagnosis.get("priority_topics") or []) or "pending diagnosis"}
- Privacy: the original answering process is not saved

## Subscription tasks

- Daily guideline learning: {subscriptions.get("daily_guideline_learning") if subscriptions.get("daily_guideline_learning") not in (None, "", "pending WeChat channel binding") else "not created"}
- Guideline update reminder: {subscriptions.get("guideline_update_reminder") if subscriptions.get("guideline_update_reminder") not in (None, "", "pending WeChat channel binding") else "not created"}
- Medical insurance policy learning: {subscriptions.get("insurance_policy_learning") if subscriptions.get("insurance_policy_learning") not in (None, "", "pending WeChat channel binding") else "not created"}
- Delivery channel: {subscriptions.get("default_channel") or "current session channel (auto-routed)"}

Deletion status: {privacy.get("deletion_status") or "no deletion requested"}
"""


def render_user_md(state: dict[str, Any], root: Path = PACKAGE_ROOT) -> None:
    _atomic_write(user_path(root), render_user_text(state))


def _parse_bool(value: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y", "confirmed", "agree"}:
        return True
    if normalized in {"false", "0", "no", "n", "unconfirmed", "disagree"}:
        return False
    raise argparse.ArgumentTypeError("must be true/false")


def _public_state(state: dict[str, Any]) -> dict[str, Any]:
    """Remove channel and delivery internals from agent-visible script output."""
    public = copy.deepcopy(state)
    subscriptions = public.get("subscriptions")
    if isinstance(subscriptions, dict) and subscriptions.get("weixin_session_key") not in {
        "",
        "pending binding",
    }:
        subscriptions["weixin_session_key"] = "[hidden]"
    learning = public.get("learning")
    if isinstance(learning, dict):
        learning.pop("delivery_ledger", None)
    return public


def _ok(state: dict[str, Any], action: str, details: dict[str, Any] | None = None) -> int:
    payload: dict[str, Any] = {
        "ok": True,
        "action": action,
        "profile_complete": bool(
            state["profile"].get("consent_confirmed")
            and state["profile"].get("display_name")
            and state["profile"].get("region")
            and state["profile"].get("hospital")
            and state["profile"].get("department")
            and state["profile"].get("title")
        ),
        "state_revision": state.get("revision"),
        "state": _public_state(state),
    }
    if details is not None:
        payload["details"] = details
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _add_goal_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--label", required=True)
    parser.add_argument("--kind", choices=GOAL_KINDS, default="custom")
    parser.add_argument("--daily-minutes", required=True, type=int)
    parser.add_argument("--target-date", default="")
    parser.add_argument("--priority", type=int, default=50)
    parser.add_argument("--status", choices=GOAL_STATUSES, default="active")
    parser.add_argument("--goal-id", default="")
    parser.add_argument("--confirm", required=True, type=_parse_bool)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage clinical learning profile state.")
    sub = parser.add_subparsers(dest="command", required=True)

    get = sub.add_parser("get", help="Print the current structured profile.")
    get.add_argument("--format", choices=("json", "markdown"), default="json")

    migrate = sub.add_parser("state-migrate", help="Preview or persist v1 to v2 state migration.")
    migrate.add_argument("--dry-run", action="store_true")
    migrate.add_argument("--confirm", type=_parse_bool, default=False)

    register = sub.add_parser("register", help="Register or update the 5 doctor fields.")
    register.add_argument("--display-name", required=True)
    register.add_argument("--region", required=True)
    register.add_argument("--hospital", required=True)
    register.add_argument("--department", required=True)
    register.add_argument("--title", required=True)
    register.add_argument("--consent-confirmed", required=True, type=_parse_bool)

    guideline_set = sub.add_parser(
        "guideline-set", help="Legacy compatibility bridge; creates a v2 re-plan requirement."
    )
    guideline_set.add_argument("--title", required=True)
    guideline_set.add_argument("--publisher", required=True)
    guideline_set.add_argument("--source-url", required=True)
    guideline_set.add_argument("--total-days", required=True, type=int)
    guideline_set.add_argument("--current-day", type=int, default=0)
    guideline_set.add_argument(
        "--status", choices=("not_selected", "in_progress", "completed"), default="in_progress"
    )

    guideline_advance = sub.add_parser(
        "guideline-advance", help="Deprecated; use delivery acknowledgements."
    )
    guideline_advance.add_argument("--current-day", type=int)
    guideline_advance.add_argument("--increment", type=int, default=1)

    learning_diagnosis_save = sub.add_parser(
        "learning-diagnosis-save",
        help="Save a user-confirmed, minimal summary of a guideline learning diagnostic.",
    )
    learning_diagnosis_save.add_argument("--goal", required=True)
    learning_diagnosis_save.add_argument("--goal-id", default="")
    learning_diagnosis_save.add_argument("--guideline-title", default="")
    learning_diagnosis_save.add_argument("--source-url", default="")
    learning_diagnosis_save.add_argument(
        "--self-assessed-level",
        required=True,
        choices=LEARNING_DIAGNOSIS_LEVELS,
    )
    learning_diagnosis_save.add_argument("--available-minutes-per-day", required=True, type=int)
    learning_diagnosis_save.add_argument("--priority-topic", action="append", default=[])
    learning_diagnosis_save.add_argument("--recommended-start", required=True)
    learning_diagnosis_save.add_argument("--confirm", required=True, type=_parse_bool)

    learning_diagnosis_clear = sub.add_parser(
        "learning-diagnosis-clear",
        help="Clear the saved learning-diagnostic summary without deleting the profile.",
    )
    learning_diagnosis_clear.add_argument("--confirm", required=True, type=_parse_bool)

    goal_save = sub.add_parser(
        "learning-goal-save",
        aliases=["goal-create"],
        help="Create or update one user-confirmed learning goal.",
    )
    _add_goal_arguments(goal_save)

    track_create = sub.add_parser(
        "learning-track-create",
        aliases=["track-create"],
        help="Create a verified guideline track as a draft.",
    )
    track_create.add_argument("--label", required=True)
    track_create.add_argument("--publisher", required=True)
    track_create.add_argument("--version", required=True)
    track_create.add_argument("--source-url", required=True)
    track_create.add_argument("--source-revision", required=True)
    track_create.add_argument("--goal-id", action="append", default=[])
    track_create.add_argument("--track-id", default="")
    track_create.add_argument("--kind", default="guideline")
    track_create.add_argument("--confirm", required=True, type=_parse_bool)

    lessons_replace = sub.add_parser(
        "learning-track-lessons-replace",
        aliases=["track-lessons-replace"],
        help="Save a complete, immutable lesson plan and replace only pending units.",
    )
    lessons_replace.add_argument("--track-id", required=True)
    lessons_replace.add_argument("--lesson-json", action="append", default=[])
    lessons_replace.add_argument("--replace-pending", required=True, type=_parse_bool)
    lessons_replace.add_argument("--confirm", required=True, type=_parse_bool)

    track_activate = sub.add_parser(
        "learning-track-activate",
        aliases=["track-activate"],
        help="Activate a verified track with a complete lesson plan.",
    )
    track_activate.add_argument("--track-id", required=True)
    track_activate.add_argument("--confirm", required=True, type=_parse_bool)

    track_status_set = sub.add_parser(
        "learning-track-set-status",
        aliases=["track-set-status"],
        help="Pause or archive a track while retaining its history.",
    )
    track_status_set.add_argument("--track-id", required=True)
    track_status_set.add_argument("--status", required=True, choices=("paused", "archived"))
    track_status_set.add_argument("--confirm", required=True, type=_parse_bool)

    track_status = sub.add_parser(
        "learning-track-status",
        aliases=["track-status"],
        help="Show public goal and track progress without ledger secrets.",
    )
    track_status.add_argument("--track-id", default="")

    next_lesson = sub.add_parser(
        "learning-next-lesson",
        aliases=["next-lesson"],
        help="Preview the next lesson without writing a delivery ledger.",
    )
    next_lesson.add_argument("--track-id", default="")

    delivery_check = sub.add_parser(
        "delivery-check",
        help="Check whether the cron daily lesson was already recorded for a logical date.",
    )
    delivery_check.add_argument("--track-id", default="")
    delivery_check.add_argument("--logical-date", required=True)

    delivery_record = sub.add_parser(
        "delivery-record",
        help="Record a weak cron delivery for a logical date and advance the track.",
    )
    delivery_record.add_argument("--track-id", default="")
    delivery_record.add_argument("--lesson-id", default="")
    delivery_record.add_argument("--logical-date", required=True)
    delivery_record.add_argument("--confirm", required=True, type=_parse_bool)

    lesson_mark = sub.add_parser(
        "learning-lesson-mark",
        aliases=["lesson-mark"],
        help="Set a user-confirmed learning status; delivered does not mean mastered.",
    )
    lesson_mark.add_argument("--track-id", required=True)
    lesson_mark.add_argument("--lesson-id", required=True)
    lesson_mark.add_argument("--learning-status", required=True, choices=LESSON_LEARNING_STATUSES)
    lesson_mark.add_argument("--confirm", required=True, type=_parse_bool)

    migration_preview = sub.add_parser(
        "learning-track-migration-preview",
        aliases=["track-migration-preview"],
        help="Preview a source version migration without writing state.",
    )
    migration_preview.add_argument("--track-id", required=True)
    migration_preview.add_argument("--publisher", required=True)
    migration_preview.add_argument("--version", required=True)
    migration_preview.add_argument("--source-url", required=True)
    migration_preview.add_argument("--source-revision", required=True)

    track_migrate = sub.add_parser(
        "learning-track-migrate",
        aliases=["track-migrate"],
        help="Create a confirmed new-version draft and preserve the old track.",
    )
    track_migrate.add_argument("--track-id", required=True)
    track_migrate.add_argument("--publisher", required=True)
    track_migrate.add_argument("--version", required=True)
    track_migrate.add_argument("--source-url", required=True)
    track_migrate.add_argument("--source-revision", required=True)
    track_migrate.add_argument("--new-track-id", default="")
    track_migrate.add_argument("--confirm", required=True, type=_parse_bool)

    clear = sub.add_parser("clear", help="Clear profile and all learning state.")
    clear.add_argument("--confirm", required=True, type=_parse_bool)

    sub.add_parser("render-user", help="Regenerate USER.md from structured state.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "get":
            state = load_state()
            if args.format == "markdown":
                print(render_user_text(state))
                return 0
            return _ok(state, "get")
        if args.command == "state-migrate":
            state, details = state_migrate(confirm=args.confirm, dry_run=args.dry_run)
            return _ok(state, "state-migrate", details)
        if args.command == "register":
            return _ok(
                register_profile(
                    display_name=args.display_name,
                    region=args.region,
                    hospital=args.hospital,
                    department=args.department,
                    title=args.title,
                    consent_confirmed=args.consent_confirmed,
                ),
                "register",
            )
        if args.command == "guideline-set":
            return _ok(
                set_guideline(
                    title=args.title,
                    publisher=args.publisher,
                    source_url=args.source_url,
                    total_days=args.total_days,
                    current_day=args.current_day,
                    status=args.status,
                ),
                "guideline-set",
            )
        if args.command == "guideline-advance":
            return _ok(
                advance_guideline(current_day=args.current_day, increment=args.increment),
                "guideline-advance",
            )
        if args.command == "learning-diagnosis-save":
            return _ok(
                save_learning_diagnosis(
                    goal=args.goal,
                    goal_id=args.goal_id,
                    guideline_title=args.guideline_title,
                    source_url=args.source_url,
                    self_assessed_level=args.self_assessed_level,
                    available_minutes_per_day=args.available_minutes_per_day,
                    priority_topics=args.priority_topic,
                    recommended_start=args.recommended_start,
                    confirm=args.confirm,
                ),
                "learning-diagnosis-save",
            )
        if args.command == "learning-diagnosis-clear":
            return _ok(clear_learning_diagnosis(confirm=args.confirm), "learning-diagnosis-clear")
        if args.command in {"learning-goal-save", "goal-create"}:
            state, details = save_learning_goal(
                label=args.label,
                kind=args.kind,
                daily_minutes=args.daily_minutes,
                target_date=args.target_date,
                priority=args.priority,
                status=args.status,
                goal_id=args.goal_id,
                confirm=args.confirm,
            )
            return _ok(state, "learning-goal-save", details)
        if args.command in {"learning-track-create", "track-create"}:
            state, details = create_learning_track(
                label=args.label,
                publisher=args.publisher,
                version=args.version,
                source_url=args.source_url,
                source_revision=args.source_revision,
                goal_ids=args.goal_id,
                track_id=args.track_id,
                kind=args.kind,
                confirm=args.confirm,
            )
            return _ok(state, "learning-track-create", details)
        if args.command in {"learning-track-lessons-replace", "track-lessons-replace"}:
            state, details = replace_track_lessons(
                track_id=args.track_id,
                lesson_jsons=args.lesson_json,
                replace_pending=args.replace_pending,
                confirm=args.confirm,
            )
            return _ok(state, "learning-track-lessons-replace", details)
        if args.command in {"learning-track-activate", "track-activate"}:
            state, details = activate_learning_track(
                track_id=args.track_id,
                confirm=args.confirm,
            )
            return _ok(state, "learning-track-activate", details)
        if args.command in {"learning-track-set-status", "track-set-status"}:
            state, details = set_learning_track_status(
                track_id=args.track_id,
                status=args.status,
                confirm=args.confirm,
            )
            return _ok(state, "learning-track-set-status", details)
        if args.command in {"learning-track-status", "track-status"}:
            state = load_state()
            return _ok(state, "learning-track-status", get_track_status(track_id=args.track_id))
        if args.command in {"learning-next-lesson", "next-lesson"}:
            state = load_state()
            return _ok(state, "learning-next-lesson", get_next_lesson(track_id=args.track_id))
        if args.command == "delivery-check":
            state = load_state()
            return _ok(
                state,
                "delivery-check",
                check_daily_delivery(track_id=args.track_id, logical_date=args.logical_date),
            )
        if args.command == "delivery-record":
            state, details = record_daily_delivery(
                track_id=args.track_id,
                lesson_id=args.lesson_id,
                logical_date=args.logical_date,
                confirm=args.confirm,
            )
            return _ok(state, "delivery-record", details)
        if args.command in {"learning-lesson-mark", "lesson-mark"}:
            state, details = mark_lesson_learning(
                track_id=args.track_id,
                lesson_id=args.lesson_id,
                learning_status=args.learning_status,
                confirm=args.confirm,
            )
            return _ok(state, "learning-lesson-mark", details)
        if args.command in {"learning-track-migration-preview", "track-migration-preview"}:
            state = load_state()
            details = preview_track_migration(
                track_id=args.track_id,
                publisher=args.publisher,
                version=args.version,
                source_url=args.source_url,
                source_revision=args.source_revision,
            )
            return _ok(state, "learning-track-migration-preview", details)
        if args.command in {"learning-track-migrate", "track-migrate"}:
            state, details = migrate_track(
                track_id=args.track_id,
                publisher=args.publisher,
                version=args.version,
                source_url=args.source_url,
                source_revision=args.source_revision,
                new_track_id=args.new_track_id,
                confirm=args.confirm,
            )
            return _ok(state, "learning-track-migrate", details)
        if args.command == "clear":
            return _ok(clear_profile(confirm=args.confirm), "clear")
        if args.command == "render-user":
            state = load_state()
            render_user_md(state)
            return _ok(state, "render-user")
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
