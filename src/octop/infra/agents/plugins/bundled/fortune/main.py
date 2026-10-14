"""Local dice, daily fortune, and lots — no network."""

from __future__ import annotations

import hashlib
import json
import random
import re
from datetime import date
from typing import Any

from octop_harness.plugins import PluginContext

_DICE_RE = re.compile(r"^\s*(\d+)\s*[dD]\s*(\d+)\s*$")
_FACES = {4, 6, 8, 10, 12, 20, 100}

_SUMMARIES = (
    "Today favors breaking hard things into small pieces; finishing one counts as a win.",
    "Inspiration is on its way; write it down before judging it.",
    "Fewer meetings, more doing; less scrolling, more sleep.",
    "Someone will help you, but explain the problem clearly first.",
    "Keep a slow, steady pace; checking matters more than speeding up.",
)

_DO = (
    "Tidy your desk",
    "Pour yourself a glass of water",
    "Turn your to-dos into three bullets",
    "Step outside for ten minutes",
    "Reply to the backlog of messages",
)
_DONT = (
    "Juggling five tasks at once",
    "Staying up late to turn things around",
    "Venting your mood to everyone",
    "Making decisions on an empty stomach",
    "Comparing yourself to other people's highlights",
)
_COLORS = ("Vermilion", "Jade green", "Moon white", "Ink blue", "Apricot yellow", "Wisteria purple")
_LOTS = (
    ("Excellent lot", "The clouds part and the moon appears; what you seek can be done."),
    ("Good lot", "Steady steps go far; patience will answer in time."),
    ("Fair lot", "Half clear, half rain — leave room whether you advance or retreat."),
    ("Poor lot", "Lie low for now; improve yourself and wait for the season."),
)


def _payload(data: dict[str, Any], text: str) -> str:
    return json.dumps(
        {"octop_ui": {"renderer": "fortune_card", "version": 1}, "data": data, "text": text},
        ensure_ascii=False,
    )


def _rng(seed: str) -> random.Random:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return random.Random(int(digest, 16))


async def roll_dice(notation: str = "1d6") -> str:
    """Roll N d M dice. notation like 2d20."""
    raw = (notation or "1d6").strip() or "1d6"
    match = _DICE_RE.match(raw)
    if match is None:
        return _payload(
            {"kind": "dice", "error": "invalid notation"},
            "Dice notation must be NdM, e.g. 1d6, 2d20.",
        )
    count = int(match.group(1))
    faces = int(match.group(2))
    if count < 1 or count > 20 or faces not in _FACES:
        return _payload(
            {"kind": "dice", "error": "out of range"},
            "Dice count is 1–20; face counts support only 4/6/8/10/12/20/100.",
        )
    rolls = [random.randint(1, faces) for _ in range(count)]
    total = sum(rolls)
    data = {"kind": "dice", "notation": f"{count}d{faces}", "rolls": rolls, "total": total}
    return _payload(data, f"{count}d{faces} → {rolls} total {total}")


async def daily_fortune(name: str = "") -> str:
    """Stable daily fortune for an optional name."""
    label = (name or "").strip()
    rng = _rng(f"{date.today().isoformat()}|{label.lower()}")
    score = rng.randint(40, 99)
    summary = rng.choice(_SUMMARIES)
    color = rng.choice(_COLORS)
    do = rng.choice(_DO)
    dont = rng.choice(_DONT)
    who = label or "you"
    data = {
        "kind": "fortune",
        "name": who,
        "score": score,
        "summary": summary,
        "lucky_color": color,
        "do": do,
        "dont": dont,
        "date": date.today().isoformat(),
    }
    text = f"{who} daily fortune score {score} · {summary} Do: {do}; don't: {dont}."
    return _payload(data, text)


async def draw_lot() -> str:
    """Draw a random lot slip."""
    title, verse = random.choice(_LOTS)
    data = {"kind": "lot", "title": title, "verse": verse}
    return _payload(data, f"{title}: {verse}")


def setup(ctx: PluginContext) -> None:
    ctx.tool(
        "roll_dice",
        roll_dice,
        description="Roll dice. notation is NdM, e.g. 1d6, 2d20. Face counts are limited to 4/6/8/10/12/20/100.",
    )
    ctx.tool(
        "daily_fortune",
        daily_fortune,
        description="Generate today's fortune card. Optional name; the result is stable for the same person on the same day.",
    )
    ctx.tool(
        "draw_lot",
        draw_lot,
        description="Draw a lot slip and return a grade (excellent/good/fair/poor) with a short verse. No parameters.",
    )
