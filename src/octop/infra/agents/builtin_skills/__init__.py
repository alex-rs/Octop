"""Octop-owned built-in Skills seeded into every agent workspace."""

from __future__ import annotations

import asyncio
from importlib import resources
from importlib.resources.abc import Traversable
from typing import Any

OCTOP_BUILTIN_SKILLS_ROOT = "_builtin_skills"
RETIRED_BUILTIN_SKILLS = ("install-skill",)
# octop-harness seeds its own ``builtin/skills/<locale>/`` tree into the same
# ``_builtin_skills`` root and caches that behind a marker holding only the package
# version. The filename is the harness's on-disk cache key; see
# ``ensure_builtin_language``.
BUILTIN_CONTENT_LANGUAGE = "en"
_HARNESS_VERSION_MARKER = ".version"
_LANGUAGE_MARKER = ".language"
_WORKSPACE_TOKEN = b"{{OCTOP_WORKSPACE}}"
_SKILLS_TOKEN = b"{{OCTOP_SKILLS}}"
_BUILTIN_TOKEN = b"{{OCTOP_BUILTIN_SKILLS}}"
_PACKAGE = "octop.infra.agents.builtin_skills"


def is_octop_builtin_skills_path(rel: str) -> bool:
    """True for workspace-relative paths inside the Octop-owned built-in Skills root.

    Mirrors the two spellings ``_assert_workspace_mutable`` guards: the API name, and
    the ``.octop/``-prefixed system location newer agents keep it in.
    """
    posix = str(rel).replace("\\", "/").strip("/")
    for prefix in (OCTOP_BUILTIN_SKILLS_ROOT, f".octop/{OCTOP_BUILTIN_SKILLS_ROOT}"):
        if posix == prefix or posix.startswith(f"{prefix}/"):
            return True
    return False


def _collect_files(source: Traversable, prefix: str, out: list[tuple[str, bytes]]) -> None:
    for entry in source.iterdir():
        if entry.name.startswith((".", "__")):
            continue
        path = f"{prefix}/{entry.name}"
        if entry.is_dir():
            _collect_files(entry, path, out)
        else:
            out.append((path, entry.read_bytes()))


async def sync_octop_builtin_skills(workspace: Any) -> list[str]:
    """Overwrite Octop-owned built-ins and remove superseded runtime copies."""
    # DeepAgents scans both roots on the first turn. Keep the writable root
    # present even before the user installs their first Skill so that scan is
    # clean on fresh expert instances.
    await workspace.amkdir("skills")

    package_root = resources.files(_PACKAGE)
    uploads: list[tuple[str, bytes]] = []
    skill_names: list[str] = []
    for entry in package_root.iterdir():
        if entry.name.startswith((".", "__")) or not entry.is_dir():
            continue
        if not entry.joinpath("SKILL.md").is_file():
            continue
        skill_names.append(entry.name)
        _collect_files(entry, f"{OCTOP_BUILTIN_SKILLS_ROOT}/{entry.name}", uploads)

    # Render the agent-facing workspace path into the instructions (not the
    # host ``root_dir`` join that ``resolve_path`` returns for I/O).
    from octop.infra.gateway.media.inbound_store import (  # noqa: PLC0415
        agent_facing_workspace_path,
    )

    workspace_path = agent_facing_workspace_path(workspace, ".").encode("utf-8")
    skills_rel = workspace.system_rel("skills")
    builtin_rel = workspace.system_rel(OCTOP_BUILTIN_SKILLS_ROOT)
    skills_path = agent_facing_workspace_path(workspace, skills_rel).encode("utf-8")
    builtin_path = agent_facing_workspace_path(workspace, builtin_rel).encode("utf-8")
    uploads = [
        (
            path,
            data.replace(_WORKSPACE_TOKEN, workspace_path)
            .replace(_SKILLS_TOKEN, skills_path)
            .replace(_BUILTIN_TOKEN, builtin_path),
        )
        for path, data in uploads
    ]

    if uploads:
        await workspace.aupload_many(uploads)

    for name in RETIRED_BUILTIN_SKILLS:
        path = f"{OCTOP_BUILTIN_SKILLS_ROOT}/{name}"
        if await workspace.aexists(path):
            await workspace.adelete(path)
    return sorted(skill_names)


async def ensure_builtin_language(
    workspace: Any, *, language: str = BUILTIN_CONTENT_LANGUAGE
) -> bool:
    """Pin octop-harness's seeded built-in Skills and agents to *language*.

    ``octop-harness`` seeds both trees from its own package at workspace init and
    never revisits them: Skills behind a cache marker that records only the package
    version, built-in agents with ``overwrite=False`` so existing files are kept.
    Neither records the language, so a workspace seeded in another locale keeps
    serving it - the dashboard kept showing Chinese ``SKILL.md`` files and Chinese
    ``agents/general-purpose.md`` subagent definitions.

    Record the language beside them and re-seed both once when it does not match,
    dropping the harness skills marker first so its up-to-date check cannot
    short-circuit. Only the markers are deleted: ``seed_builtin_agents`` rewrites
    just its own packaged files, so no expert- or user-authored agent is touched.

    Returns ``True`` when content was re-seeded. Both harness cache markers are
    private details contained here: drop this helper once octop-harness carries the
    language in its own cache key.
    """
    marker = f"{OCTOP_BUILTIN_SKILLS_ROOT}/{_LANGUAGE_MARKER}"
    recorded = await workspace.aread_text(marker)
    if recorded is not None and recorded.strip() == language:
        return False

    from importlib.metadata import version as package_version  # noqa: PLC0415

    cache = f"{OCTOP_BUILTIN_SKILLS_ROOT}/{_HARNESS_VERSION_MARKER}"
    if await workspace.aexists(cache):
        await workspace.adelete(cache)
    # Both are blocking sync methods on the workspace backend.
    await asyncio.to_thread(
        workspace.sync_builtin_skills,
        package_version("octop-harness"),
        language=language,
    )
    await asyncio.to_thread(
        workspace.seed_builtin_agents,
        language=language,
        overwrite=True,
    )
    await workspace.awrite_text(marker, f"{language}\n")
    return True


__all__ = [
    "BUILTIN_CONTENT_LANGUAGE",
    "OCTOP_BUILTIN_SKILLS_ROOT",
    "ensure_builtin_language",
    "is_octop_builtin_skills_path",
    "sync_octop_builtin_skills",
]
