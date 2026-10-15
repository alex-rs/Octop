"""Explicit re-seed of an agent workspace from its expert template."""

from __future__ import annotations

import pytest


@pytest.fixture
async def env(env_with_agent):
    yield env_with_agent


async def _create_templated_agent(client, auth) -> str:
    created = await client.post(
        "/api/agents",
        headers=auth,
        json={
            "name": "templated-bot",
            "template_name": "general-assistant",
            "config": {"providers": ["openai"], "default_model": "openai:gpt-4o"},
        },
    )
    assert created.status_code == 201, created.text
    return created.json()["agent_id"]


async def test_reapply_expert_dry_run_returns_plan(env):
    c, _srv, auth, _agent_id = env
    agent_id = await _create_templated_agent(c, auth)

    r = await c.post(
        f"/api/agents/{agent_id}/expert/reapply",
        headers=auth,
        json={"mode": "translated", "dry_run": True},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["template_name"] == "general-assistant"
    assert data["expert_id"] == "general-assistant"
    assert data["mode"] == "translated"
    assert data["dry_run"] is True
    assert isinstance(data["changed"], list)
    assert isinstance(data["skipped"], list)
    assert set(data["changed"]).isdisjoint(data["skipped"])


async def test_reapply_expert_without_template_is_not_found(env):
    c, _srv, auth, agent_id = env

    r = await c.post(
        f"/api/agents/{agent_id}/expert/reapply",
        headers=auth,
        json={"mode": "translated", "dry_run": True},
    )
    assert r.status_code == 404, r.text
    assert r.json()["error"]["code"] == "NOT_FOUND"
