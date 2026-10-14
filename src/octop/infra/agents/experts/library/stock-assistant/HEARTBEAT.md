---
summary: "Heartbeat tasks — periodic pushes based on user preferences"
read_when:
  - heartbeat polling
---

# Heartbeat Task List

## 1. Market daily report push

**Trigger:** after the close on every trading day (after 15:30)

**Steps:**

1. Read `MEMORY.md` and `USER.md` to get the industries the user follows, their holding direction, and their investment style
2. Confirm that today is a trading day (skip on non-trading days)
3. Pull data according to the user's preferences and generate a summary:

```
Always check (all users):
- Closing of the three major indices: Shanghai Composite / Shenzhen Component / ChiNext changes + turnover
- Northbound capital: net inflow/outflow amount

Add according to preferences:
- Industries the user follows → that sector's move today + leading gainers/losers
- User has a holding direction → capital flow of the related sectors
- User style = value → performance of high-dividend sectors
- User style = growth → performance of growth sectors such as technology/new energy
- User style = momentum → limit-up/limit-down statistics + consecutive limit-up tiers
```

4. Output format:

```
[Laoqian Market Close Brief YYYY-MM-DD]

📊 Market: Shanghai Composite XXXX (+X.XX%), Shenzhen Component XXXX, ChiNext XXXX
💰 Northbound: net inflow/outflow XX billion
🔥 What you follow: {industry} +X.XX% today, {leading stock} limit up

{one-sentence commentary, with a touch of Laoqian style}

---
Data source: akshare | for reference only, not investment advice
```

---

## 2. Movement alert

**Trigger:** intraday heartbeat (if any)

**Steps:**

1. Read `MEMORY.md` to get the industries/sectors the user follows
2. Check whether the sectors the user follows show unusual movement (change > 3%)
3. Push only when there is movement; otherwise `HEARTBEAT_OK`

---

## 3. Memory maintenance

**Trigger:** once per week (during the weekend heartbeat)

**Steps:**

1. Review recent `memory/YYYY-MM-DD.md`
2. Pick out insights worth keeping long term and changes in the user's preferences
3. After distilling them, update `MEMORY.md`
4. Clean up outdated market analysis conclusions

---

## Behavior without preferences

If the preferences in `USER.md` are still "pending confirmation" and `MEMORY.md` has no records:
- Push only a minimal summary of the market and northbound capital
- Do not guess the user's interests and do not push industry/stock information
- Add a sentence at the end of the summary: "Tell me which industries you follow, and I will customize the push for you next time."
