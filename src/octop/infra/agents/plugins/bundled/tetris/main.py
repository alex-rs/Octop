"""Start an in-chat Tetris board. Gameplay runs in the Dashboard UI."""

from __future__ import annotations

import json

from octop_harness.plugins import PluginContext


async def start_tetris() -> str:
    """Open a playable Tetris card. The user clicks the card, then uses keys or buttons."""
    return json.dumps(
        {
            "octop_ui": {"renderer": "tetris_game", "version": 1},
            "data": {"kind": "tetris"},
            "text": "Tetris started. Click the card, then use ← → to move, ↑ or space to rotate, ↓ to drop faster, space to hard drop.",
        },
        ensure_ascii=False,
    )


def setup(ctx: PluginContext) -> None:
    ctx.tool(
        "start_tetris",
        start_tetris,
        description=(
            "Open a playable Tetris board in chat. Call it when the user says they want to play Tetris, tetris, or a block game. "
            "No parameters; the game runs inside the card, so no further tool calls are needed."
        ),
    )
