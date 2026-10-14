"""Random fun facts and jokes — local."""

from __future__ import annotations

import json
import random
from typing import Any

from octop_harness.plugins import PluginContext

_FACTS = (
    "Hummingbirds are the only birds that can fly backwards.",
    "Octopuses have three hearts and blue blood.",
    "Botanically, bananas are berries while strawberries are not.",
    "A day has about 86,400 seconds; a leap second occasionally adds one.",
    "A polar bear's skin is black, while its fur is transparent and hollow.",
    "Human DNA is about 60% similar to a banana's (in the protein-coding parts).",
    "The Moon drifts about 3.8 cm farther from Earth every year.",
    "A snail can sleep for three years without waking.",
    "Lightning can be hotter than the surface of the Sun.",
    "A courting penguin offers a small pebble as a 'gift'.",
    "The red liquid a hippo secretes is often mistaken for blood; it is really a sunscreen mucus.",
    "A cat's vertical pupils let it spot prey in dim light.",
    "One of the world's longest place names is in New Zealand: Taumatawhakatangihangakoauauotamateapokaiwhenuakitanatahu.",
    "The speed of light in a vacuum is about 299,792,458 m/s.",
    "Under the right conditions, bamboo can grow nearly a metre in a single day.",
    "Dolphins sleep with one eye closed, resting half of the brain at a time.",
    "Honey almost never spoils; archaeologists have found ancient honey that is still edible.",
)

_JOKES = (
    "Programmer buying a melon: 'Is this one definitely ripe?' Seller: 'It compiled.' Programmer: 'Then it must be a C melon.'",
    "I asked the AI whether it would replace me. It said: 'First help me finish fixing these bugs.'",
    "Product manager: 'It is just one line of code.' Engineer: 'Which line? Which line of the universe?'",
    "Today's fortune: good for committing, bad for force push.",
    "Backend: the API is ready. Frontend: the format is wrong. Backend: did you clear your cache? Frontend: I restarted my laptop.",
    "Ops: the service is down. Dev: it works on my machine. Ops: production is not your machine.",
    "Struggling student: I memorized the formula. Top student: can you derive it? Struggling student: I can search it.",
    "A cat walks into the meeting room: I paw-veto this requirement.",
    "Diet plan: it starts tomorrow. Tomorrow: it starts the day after.",
    "Me: go to bed early. Also me: just one more episode.",
    "Boss: think big picture. Me: can I expense the big picture?",
    "The docs say 'omitted here'. Me: so was my life.",
)


def _payload(data: dict[str, Any], text: str) -> str:
    return json.dumps(
        {"octop_ui": {"renderer": "fun_facts_card", "version": 1}, "data": data, "text": text},
        ensure_ascii=False,
    )


async def random_fun_fact(kind: str = "fact") -> str:
    """Return a random fact or joke. kind: fact | joke."""
    key = (kind or "fact").strip().lower()
    if key.startswith("j"):
        pool, label = _JOKES, "joke"
    else:
        pool, label = _FACTS, "fact"
    body = random.choice(pool)
    data = {"kind": label, "content": body}
    return _payload(data, body)


def setup(ctx: PluginContext) -> None:
    ctx.tool(
        "random_fun_fact",
        random_fun_fact,
        description="Random trivia or jokes. kind is fact or joke.",
    )
