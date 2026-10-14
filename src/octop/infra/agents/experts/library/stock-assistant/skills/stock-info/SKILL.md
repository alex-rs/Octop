---
name: akshare-data
description: Fetch Chinese and global financial-market data with akshare-cli (1090+ functions). Covers the full range of stocks, funds, futures, bonds, forex, macroeconomics, indexes, options, and news. Trigger this skill whenever the user needs any of the following data — stock quotes, historical candlesticks, real-time quotes, limit-up/limit-down pools, dragon-tiger list, sector capital flows, fund/ETF NAV, futures quotes, bonds/convertible bonds, forex rates, macroeconomic indicators (GDP/CPI/PMI), index data, options data, financial news. Keyword triggers — akshare, stock, quotes, candlestick, fund, futures, forex, macro, treasury bonds, convertible bonds, limit-up, dragon-tiger list, sector, capital flows, stock data, market data, financial data, A-shares, Hong Kong stocks, US stocks. Even if the user merely mentions "take a look at some stock" or "how has the market been lately" in passing, it should trigger.
metadata:
  octop:
    emoji: "📈"
    label:
      zh: "Market Data"
      en: "Market Data"
    summary:
      zh: "Fetch stocks, funds, futures, macro, and financial news via akshare-cli."
      en: "Fetch stocks, funds, futures, macro, and financial news via akshare-cli."
---

# AKShare Financial Data Retrieval

`akshare-cli` wraps AKShare (1090+ functions), covering almost all of China's financial data plus some global data.

## Core Principles

1. **Prefer the lightweight path** — query a single stock with `stock_individual_info_em`(0.1s), not `stock_zh_a_spot_em`(59s). See `references/known-issues.md`.
2. **Inspect before you call** — for an unfamiliar function, run `--full-help` to see the parameters first, then call it.
3. **Always fall back on failure** — do not tell the user "cannot find it" after the first failure; go through all three fallback levels.
4. **Control the output size** — add `--limit N --sort desc` to full-range interfaces so you get the newest data rather than the oldest.

---

## Workflow: discover → inspect → call → fall back

Follow these steps strictly in order; do not skip any.

### Step 1: discover functions

Three ways; pick one for the situation:

**A. Shortcut commands** (use directly for common cases, no search needed):
```bash
akshare-cli stock hist <code> [--period daily|weekly|monthly] [--adjust qfq|hfq]
akshare-cli stock spot [--market all|sh|sz|bj|hk|us]
akshare-cli fund etf [code]
akshare-cli futures hist <contract>
akshare-cli bond convertible
akshare-cli macro gdp | macro cpi
akshare-cli forex spot | forex hist [currency pair]
akshare-cli index spot [--market global|cn]
```

**B. Keyword search** (use when you know the rough direction):
```bash
akshare-cli search <keyword>    # supports Chinese and English
```
English matches function names (fuller results); Chinese matches descriptions and category paths.

| User intent | English keyword (recommended) | Chinese keyword (pinyin) |
|---------|-------------------|-----------|
| News | `news` | `xinwen` |
| Stocks | `stock` | `gupiao` |
| Limit-up/limit-down | `stock_zt` | `zhangting` |
| Dragon-tiger list | `stock_lhb` | `longhubang` |
| Sector/concept | `stock_board` | `bankuai` |
| Capital flows | `fund_flow` | `zijin liuxiang` |
| Funds/ETFs | `fund` | `jijin` |
| Futures | `futures` | `qihuo` |
| Bonds | `bond` | `zhaiquan` |
| Forex | `forex` | `waihui` |
| Macro | `macro` | `hongguan` |
| Indexes | `index` | `zhishu` |

**C. Browse by category** (use when the keyword is uncertain; walk the category tree level by level):
```bash
akshare-cli browse                                # 30 top-level categories
akshare-cli browse Stock Data/A-shares/Historical Quotes          # drill down level by level
akshare-cli browse --func stock_zh_a_hist         # reverse-lookup a function's category
```

### Step 2: inspect the parameters (skippable when using shortcut commands)

```bash
akshare-cli call --full-help <function name>
akshare-cli call --full-help fn1,fn2,fn3       # batch lookup
```

The output includes: description, data source, target address, parameters (with enum options), and usage examples.

Watch the parameters closely: parameter names differ between functions (`symbol`/`code`/`indicator`), some have enum constraints, and dates are generally `YYYYMMDD`.

### Step 3: call

```bash
akshare-cli call <function name> [--param value ...] [--json] [--limit N] [--sort desc]
```

When querying the latest data, add `--sort desc --limit N`; otherwise `--limit` cuts off the oldest data.

### Step 4: three-level fallback on failure

AKShare scrapes third-party websites under the hood, and the upstream can go down at any time. After a failure, try these in order:

**Level 1: switch the data-source suffix**
`_em` (Eastmoney) fails → search for the same kind of function under `_ths` (Tonghuashun) or `_sina` (Sina):
```bash
akshare-cli search <similar keyword>
```

**Level 2: open the target address with browser_use and scrape the page data**
The `--full-help` output has a "target address" field, which is the web page URL the data comes from. Open this URL with the browser_use tool and extract the data straight from the page:
```bash
# first get the target address
akshare-cli call --full-help stock_zh_a_hist
# the output shows: target address: https://quote.eastmoney.com/concept/sh603777.html
# then open that URL with browser_use and extract the needed data from the page
```

**Level 3: WebSearch as the last resort**
Look the data up with a search engine:
```bash
# WebSearch "Kweichow Moutai financial data site:eastmoney.com"
```

Trigger conditions: non-zero exit code, empty data (0 rows), network error.

---

## Stock Code Recognition

| Format | Meaning | Handling |
|------|------|------|
| 6 digits | A-shares | Use directly |
| 5 digits | Hong Kong stocks | Use directly |
| Starts with a letter | US stocks | Use directly |
| sh/sz prefix | Strip the prefix | `sh600519` → `600519` |
| Stock name | Look up the code | `stock_info_sh_name_code` / `stock_info_sz_name_code` |

---

## Output Options

| Option | Effect |
|------|------|
| `--json` | JSON format (recommended) |
| `--csv` | CSV format |
| `--output FILE` | Save to a file (.csv/.json/.xlsx/.md) |
| `--limit N` | Limit the number of rows |
| `--sort desc\|asc` | Sort: `desc` newest first (default), `asc` oldest first |
| `--no-cache` | Skip the cache |

**The key to getting the latest data:** many historical-data interfaces return rows starting from the earliest by default. If you take only `--limit 10` without `--sort desc`, you get the oldest 10 rows instead of the newest. Always add `--sort desc` when querying the latest data:
```bash
akshare-cli call stock_zh_a_hist --symbol 000001 --json --limit 10 --sort desc   # the last 10 days
```

The cache is 30 minutes by default (24 hours for macro data); real-time quotes are not cached.

---

## Cautions

- **Known broken interfaces**: check `references/known-issues.md` before calling; if it is listed there, go straight to the alternative
- **Intraday vs after close**: outside trading hours prefer the historical interface (`stock_zh_a_hist`) — faster and more stable
- **Automatic date fill**: when no `date` parameter is given, the CLI fills in today's date automatically
- **Name-to-code lookup**: use `stock_info_sh_name_code` / `stock_info_sz_name_code`; never iterate the full spot list

> More workflow examples in `references/examples.md`
