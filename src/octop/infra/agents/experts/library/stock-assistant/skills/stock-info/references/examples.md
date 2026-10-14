# Workflow Examples

## Example 1: "Look up how Kweichow Moutai has been moving lately"

```bash
# lightweight interface, do not use the full spot list:
akshare-cli call stock_individual_info_em --symbol 600519 --json       # basic info (0.1s)
akshare-cli stock hist 600519 --period daily --start 20260101 --json   # recent candlesticks (0.2s)
```

## Example 2: "Which concept sectors did well today?"

```bash
akshare-cli search stock_board_concept
akshare-cli call --full-help stock_board_concept_name_em
akshare-cli call stock_board_concept_name_em --json --limit 20
```

## Example 3: "Look up China's latest CPI data"

```bash
akshare-cli macro cpi --json
```

## Example 4: "Which stocks hit the limit-up yesterday?"

```bash
akshare-cli search stock_zt
akshare-cli call --full-help stock_zt_pool_em
akshare-cli call stock_zt_pool_em --date 20260314 --json
```

## Example 5: three-level fallback when an interface fails

```bash
# the Eastmoney financial interface is broken:
$ akshare-cli call stock_profit_sheet_by_report_em --symbol 600519 --json
Error: NoneType error

# Level 1: switch to the Tonghuashun source
akshare-cli call stock_financial_benefit_new_ths --symbol 600519 --json

# if Tonghuashun also fails:
# Level 2: open the target address from --full-help with browser_use
# Level 3: WebSearch "Kweichow Moutai income statement site:eastmoney.com"
```

## Example 6: browse by category to find a function

```bash
akshare-cli browse                                    # 30 top-level categories
akshare-cli browse Stock Data                             # 52 subcategories
akshare-cli browse Stock Data/A-shares/Historical Quotes              # 8 subcategories
akshare-cli browse Stock Data/A-shares/Historical Quotes/Historical Quotes - Eastmoney  # a specific function

# reverse-lookup a function's category
akshare-cli browse --func stock_zh_a_hist
# output: category: Stock Data > A-shares > Historical Quotes > Historical Quotes - Eastmoney
```

## Example 7: inspect several functions in one batch

```bash
akshare-cli call --full-help stock_zh_a_hist,news_cctv,macro_cnbs
```
