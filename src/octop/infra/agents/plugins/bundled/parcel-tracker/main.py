"""Domestic parcel lookup via kuaidi100 public pages, with a link fallback."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import httpx
from octop_harness.plugins import PluginContext

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.kuaidi100.com/",
}


def _payload(data: dict[str, Any], text: str) -> str:
    return json.dumps(
        {"octop_ui": {"renderer": "parcel_timeline", "version": 1}, "data": data, "text": text},
        ensure_ascii=False,
    )


def _client() -> httpx.Client:
    return httpx.Client(timeout=15.0, headers=_HEADERS, follow_redirects=True)


def _detect_company(number: str) -> str:
    with _client() as client:
        resp = client.get(
            "https://www.kuaidi100.com/autonumber/autoComNum",
            params={"text": number},
        )
        resp.raise_for_status()
        payload = resp.json()
    autos = payload.get("auto") or []
    if autos and isinstance(autos[0], dict):
        return str(autos[0].get("comCode") or "").strip()
    return ""


def _query(company: str, number: str) -> list[dict[str, Any]]:
    with _client() as client:
        resp = client.get(
            "https://www.kuaidi100.com/query",
            params={"type": company, "postid": number},
        )
        resp.raise_for_status()
        payload = resp.json()
    traces: list[dict[str, Any]] = []
    for row in payload.get("data") or []:
        if not isinstance(row, dict):
            continue
        traces.append(
            {
                "time": str(row.get("time") or ""),
                "context": str(row.get("context") or ""),
                "status": str(row.get("status") or payload.get("status") or ""),
            },
        )
    return traces


async def track_parcel(number: str, company: str = "") -> str:
    """Look up a tracking number. company is a kuaidi100 comCode when known."""
    nu = (number or "").strip()
    if not nu:
        return _payload({"error": "number required"}, "Please provide a tracking number.")
    url = f"https://www.kuaidi100.com/chaxun?nu={quote(nu)}"
    com = (company or "").strip()
    try:
        if not com:
            com = _detect_company(nu)
        traces = _query(com, nu) if com else []
    except Exception as exc:
        data = {
            "number": nu,
            "company": com,
            "traces": [],
            "url": url,
            "error": str(exc),
        }
        return _payload(data, f"Lookup failed; open {url}. Reason: {exc}")

    data = {"number": nu, "company": com, "traces": traces, "url": url}
    if not traces:
        data["error"] = "no traces"
        return _payload(
            data,
            f"No tracking updates yet; open {url} to check. Number {nu}, carrier {com or 'unknown'}.",
        )
    latest = traces[0].get("context") or ""
    return _payload(data, f"{nu} ({com}) latest: {latest}")


def setup(ctx: PluginContext) -> None:
    ctx.tool(
        "track_parcel",
        track_parcel,
        description=(
            "Track domestic parcels. number is the tracking number; company is optional (a Kuaidi100 comCode such as yuantong). "
            "When nothing is found it returns the Kuaidi100 web link."
        ),
    )
