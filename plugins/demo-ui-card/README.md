# demo-ui-card

A combined frontend + backend example:

- **Backend** `main.py`: registers the `demo_ui_card` tool, which returns JSON with `octop_ui`
- **Frontend** `ui/dist/index.js`: renders a card in chat and demonstrates L2 refresh with `host.patchResult`

Install:

```bash
octop plugin install ./plugins/demo-ui-card --force
```

Then enable `demo_ui_card` for the agent under Dashboard "Tool management", and call the tool in chat to see the card.
