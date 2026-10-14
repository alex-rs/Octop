"""What to eat — local meal suggestions."""

from __future__ import annotations

import hashlib
import json
import random
from datetime import date
from typing import Any

from octop_harness.plugins import PluginContext

_MEALS: dict[str, tuple[str, ...]] = {
    "breakfast": (
        "Soy milk and fried dough sticks",
        "Soup dumplings",
        "Congee with pickles",
        "Sandwich",
        "Oatmeal with yogurt",
    ),
    "lunch": (
        "Braised chicken rice",
        "Lanzhou beef noodles",
        "Spicy dry pot",
        "Light salad bowl",
        "Curry rice",
        "Rice with toppings",
    ),
    "dinner": ("Hot pot", "Barbecue", "Sushi", "Home-style three-veg one-meat", "Pizza", "Pho"),
    "snack": ("Milk tea", "Fried chicken cutlet", "Fruit platter", "Oden", "Ice cream"),
}

_SPICY = (
    "Chongqing noodles",
    "Sichuan boiled fish",
    "Xinjiang fried rice noodles",
    "Hunan-style stir-fry",
    "Malatang",
)
_MILD = (
    "Cantonese roast meats",
    "Japanese set meal",
    "Suzhou-style noodle soup",
    "Thai tom yum (mild)",
    "Spaghetti",
)


def _payload(data: dict[str, Any], text: str) -> str:
    return json.dumps(
        {"octop_ui": {"renderer": "what_to_eat_card", "version": 1}, "data": data, "text": text},
        ensure_ascii=False,
    )


async def what_to_eat(meal: str = "lunch", spicy: bool | None = None) -> str:
    """Suggest a dish. meal: breakfast/lunch/dinner/snack; spicy True/False optional."""
    key = (meal or "lunch").strip().lower()
    pool = list(_MEALS.get(key, _MEALS["lunch"]))
    if spicy is True:
        pool = list(_SPICY) + pool
    elif spicy is False:
        pool = list(_MILD) + pool
    seed = f"{date.today().isoformat()}|{key}|{spicy}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    rng = random.Random(int(digest[:16], 16))
    dish = rng.choice(pool)
    data = {"meal": key, "dish": dish, "spicy": spicy}
    return _payload(data, f"{key} recommendation: {dish}")


def setup(ctx: PluginContext) -> None:
    ctx.tool(
        "what_to_eat",
        what_to_eat,
        description="Randomly recommend something to eat. meal is breakfast/lunch/dinner/snack; spicy optionally favors spicy or mild.",
    )
