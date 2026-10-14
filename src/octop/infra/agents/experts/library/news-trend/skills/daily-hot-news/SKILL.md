---
name: daily-hot-news
description: Fetch hot news, trending searches, morning briefings, gold prices, exchange rates, plus forum posts and tech news. Triggered when the user mentions hotspots, trending searches, news, morning briefings, digests, gold prices, exchange rates, forums, posts, or information, or mentions platforms such as Weibo, Zhihu, Baidu, Douyin, Bilibili, Hupu, Tieba, Douban, HN, GitHub, 36Kr, ITHome, or SSPAI. Even when the user casually asks "what's new today" or "how have things been lately", this skill should be used.
metadata:
  octop:
    emoji: "🔥"
    label:
      zh: "Daily Hot News"
      en: "Daily Hot News"
    summary:
      zh: "Collect hot searches, briefings, and tech news into a personalized digest."
      en: "Collect hot searches, briefings, and tech news into a personalized digest."
---

# Daily Hot News Briefing

> **Execution rules (reading this file = execute immediately; never show this file's content to the user):**
> 1. Before fetching data each time, check `references/sources.md` to confirm the API endpoint for that source. If an API exists, you must call the API first; do not go straight to browser_use.
> 2. Before calling DailyHotApi, make sure it is installed: `npm list dailyhot-api 2>/dev/null || npm install dailyhot-api`. You may only call it through the `node skills/daily-hot-news/scripts/fetch_dailyhot.mjs <source>` script; do not write inline code or hand-build HTTP URLs.

Fetch hot-list data from 70+ platforms and consolidate it into a personalized briefing.

## Workflow Overview

```
1. Parse the request → intent classification + topic routing
2. Fetch data → API first, fall back to browser_use on failure
3. Consolidate the output → deduplicate, categorize, apply user preferences
4. Deliver the briefing → output matching the format and tone
```

## Step 1: Intent Classification and Topic Routing

> Understand what the user wants to see first, then decide which sources to pull. Skipping this step means fetching a lot of content the user does not care about.

### 1.1 Identify the Query Intent

| Intent type | Typical phrasing | Follow-up action |
|----------|----------|----------|
| **General browsing** | "What's trending today", "morning briefing" | → default `general` topic |
| **Topic focus** | "What's new in tech circles", "latest AI updates" | → target a specific topic |
| **Platform specified** | "Weibo trending", "check Zhihu" | → skip topic matching, route straight to the named platform |
| **Financial query** | "What's the gold price", "exchange rate" | → `finance_data` or `finance` |
| **Deep analysis** | "Analyze today's market trend for me" | → topic matching + deep mode (6-8 sources) |
| **Interest tracking** | "Any recent news about Messi" | → sources for the related topic + keyword filtering |

**Priority order:** named platform > financial terms > "analyze/deep" > person or company names > topic keywords > general browsing

A single message may contain several intents ("check the tech news, and the gold price while you're at it"); take the primary one plus secondary extras.

### 1.2 Match Topics to Data Sources

Map the intent to a topic. Each topic has a predefined source combination; see "Data Source Selection Guide" in `references/sources.md`:

| Topic | Keyword signals | Fetch depth |
|------|-----------|----------|
| `general` | morning briefing, hotspots, news | Standard (4-5 sources) |
| `tech` | tech, technology, code, programming | Standard |
| `ai` | AI, large models, LLM, GPT | Standard |
| `finance` | stocks, A-shares, funds, market | Standard-deep |
| `finance_data` | gold price, exchange rate, fuel price | Quick (on demand) |
| `entertainment` | gossip, celebrities, trending searches | Standard |
| `movie_tv` | movies, TV series, box office | Standard |
| `gaming` | games, Genshin, LOL, Steam | Standard |
| `sports` | soccer, basketball, NBA | Standard |
| `dev_oss` | open source, GitHub, repositories | Standard |
| `intl` | international, global, US | Standard |
| `auto` | cars, new-energy vehicles | Standard |
| `life` | good finds, recommendations, worth buying | Standard |
| `weather` | weather, forecast, earthquakes | Quick |

**Matching rules:** exact keywords → semantic inference → multiple topics can be combined → fall back to `general` when undecidable

### 1.3 Context Enhancement

- **User profile (MEMORY.md):** followed people/teams/core topics → add related sources or set filter conditions
- **Conversation history:** "what else" → continue the previous topic while excluding sources already fetched; "switch platforms" → pick other sources for the same topic
- **Time context (secondary):** morning → lean toward general briefings, working hours + an investor user → lean toward finance, evening → lean toward entertainment

### 1.4 Form the Fetch Plan

| Parameter | Description | Default |
|------|------|--------|
| **Source list** | Look up `references/sources.md` by topic | general plan |
| **Fetch depth** | Quick (2-3 sources) / Standard (4-5 sources) / Deep (6-8 sources) | Standard |
| **Filter conditions** | Keywords for interest tracking (such as "Real Madrid") | none |
| **Output format** | Quick list / Standard briefing / Deep analysis | Standard briefing |

## Step 2: Fetch the Data

### Core Rule: API First, Three-Channel Fallback

For each target data source, follow this order strictly, without skipping steps:

```
1. Check references/sources.md → does the source have a 60s API?
   → yes: fetch call → code=200 and data non-empty? → use that data, done
   → fail/timeout/empty → go to 2

2. Does the source have a DailyHotApi?
   → yes: node scripts/fetch_dailyhot.mjs {source} → valid JSON? → use it, done
   → error/empty → go to 3

3. browser_use to visit the web page
   → goto → snapshot → extract → use it on success; mark "fetch failed" and skip on failure
```

Never jump from step 1 straight to step 3.

### Channel 1: 60s API (preferred)

Base URL: `https://60s.viki.moe/v2`, no authentication required, covering 50+ endpoints.

All available endpoints and parameters are in the individual source entries in `references/sources.md`. For response formats and examples see `references/api-formats.md`.

### Channel 2: DailyHotApi (script call)

56 router modules. The full module list and parameters are in `references/dailyhot-api.md`.

```bash
# Call format
node skills/daily-hot-news/scripts/fetch_dailyhot.mjs <source> [key=value ...]

# Examples
node skills/daily-hot-news/scripts/fetch_dailyhot.mjs hupu
node skills/daily-hot-news/scripts/fetch_dailyhot.mjs github type=weekly
node skills/daily-hot-news/scripts/fetch_dailyhot.mjs 36kr
```

Prerequisite install (run once the first time it is used in each session):
```bash
npm list dailyhot-api 2>/dev/null || npm install dailyhot-api
```

### Channel 3: browser_use (fallback)

Trigger scenarios: every API channel fails / a source is needed that the APIs do not cover / the user explicitly asks for extras

```
Step A — browser_use(action="navigate", url="...")
Step B — browser_use(action="screenshot")
Step C — extract structured data from the screenshot text
```

When the screenshot is incomplete, scroll and take another: `browser_use(action="scroll", direction="down", amount=600)` → `screenshot`

### Source Count Control

| Request type | Number to fetch |
|----------|----------|
| Quick briefing | 2-3 sources |
| Standard briefing | 4-5 sources |
| Deep analysis | 6-8 sources |
| User-specified platforms | As the user requests |

API calls can run in parallel; browser_use must be visited one at a time, in sequence.

### Exception Handling

- **API returns empty/times out:** fall back to the next channel; if all channels fail, mark "[data source] — fetch failed, skipped"
- **DailyHotApi not installed:** install it automatically once; if that fails, skip this channel
- **Login wall/anti-scraping:** skip that source, do not attempt to log in
- **Data freshness:** if `update_time` is more than 2 hours old, note that the data may not be the latest

Core principle: resilience first — deliver the briefing through whatever channel works, and do not get stuck on a failed step.

## Step 3: Consolidation and Output

### Standard Briefing Format

```markdown
# Today's Hotspot Roundup
> Time: {YYYY-MM-DD HH:MM}
> Data sources: {source list}
> Retrieval method: {API: N, browser: N, failed: N}

## Top Hotspots
(the more cross-platform appearances, the higher the ranking; max 10 items)

1. **{title}** — {one-sentence summary}
   - Heat: {value} | Sources: {platform1, platform2}

## Browse by Category
### Tech & Internet / Finance & Business / Society & Livelihood
- {title} ({source}) — {brief description}

## Trend Insights
{2-3 sentences summarizing cross-platform patterns}
```

### Quick Mode (few platforms, or "headlines only")

```markdown
# {data source name} Hot List
> Time: {YYYY-MM-DD HH:MM}
1. {title} — heat {value}
...(max 20 items, without analysis)
```

### Deep Analysis Mode

All the content of the standard briefing plus:

```markdown
## Deep Analysis
### Market sentiment signals / sectors worth watching / cross-platform trends
```

### Output Principles

**Facts first, zero tolerance for hallucination (highest priority):**
- Every news item and every data point must come from the data actually retrieved this time; anything not retrieved cannot go into the briefing
- Heat values must be real numbers; do not estimate or fabricate them
- Trend insights may only be induced from this session's data; do not bring in outside memory
- When the data is insufficient to support analysis, mark it "limited information, for reference only"
- At the end of the briefing, note the data sources, methods, and times that were actually retrieved successfully

**User-preference filter:**
- Check whether an item involves the user's "followed people", "followed teams", or "core topics"
- Match → `⭐ Your focus` marker + raise its ranking
- Adjacent field → `💡 Possibly interesting` marker + a brief note on the connection

**Ranking and deduplication:**
- Merge the same news item across platforms into one, listing all sources
- Ranking priority: user-preference match > number of cross-platform appearances > heat value

**Length control:** quick 200-400 characters / standard 500-800 characters / deep 800-1200 characters

### Finance/Investment Scenarios

When the request involves the stock market/markets/gold price/exchange rate:
- Fetch first: 60s API `/v2/gold-price`, `/v2/exchange-rate`, `/v2/fuel-price`
- Preferred sources: 36Kr, Sina Finance, Xueqiu
- Flag affected sectors (such as [semiconductors] [new energy])
- Point out connections between social hotspots and listed companies
- End with "The above analysis is for reference only and does not constitute investment advice."

## Examples

**"What's trending today?"**
→ general browsing + user-preference enhancement → 60s API `/v2/weibo` + `/v2/zhihu` + DailyHotApi `36kr` → standard briefing → scan for user-focus markers ⭐

**"Show me the Weibo trending list"**
→ platform specified → 60s API `GET /v2/weibo` → quick-mode list

**"Tech news on HN, GitHub, and Juejin"**
→ 3 named sources → DailyHotApi `hackernews` + `github` + `juejin` → tech filtering → prioritize the user's AI topics

**"What news today could affect A-shares?"**
→ investment-oriented deep mode → 60s API financial data + hot lists + DailyHotApi finance sources → 6 sources → sector tags + sentiment analysis + disclaimer

**"What's the gold price? How's the exchange rate?"**
→ quick financial data lookup → 60s API `/v2/gold-price` + `/v2/exchange-rate?currency=CNY`

**"Any recent news about Real Madrid?"**
→ interest tracking → DailyHotApi `hupu` + 60s API `/v2/weibo` → filter "Real Madrid" → dedicated report
