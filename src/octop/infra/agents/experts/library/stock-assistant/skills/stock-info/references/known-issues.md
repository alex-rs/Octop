# Known-Issue Endpoints and Alternatives

Check this list before calling; if an entry matches, use the alternative directly and do not waste time trying.

## Completely broken (do not use)

| Broken endpoint | Alternative |
|---------|---------|
| `stock_us_spot_em` | `stock_us_daily` (Sina source) |
| `stock_zh_index_spot_sina` | `index_global_spot_em` |
| `fund_etf_spot_em` | `fund_etf_hist_em` taking the latest day |
| `stock_financial_analysis_indicator_em` | `stock_financial_analysis_indicator` (Sina source) |
| `stock_profit_sheet_by_report_em` | `stock_financial_benefit_new_ths` (Tonghuashun) |
| `stock_balance_sheet_by_report_em` | `stock_financial_debt_new_ths` (Tonghuashun) |
| `stock_cash_flow_sheet_by_report_em` | `stock_financial_cash_new_ths` (Tonghuashun) |
| `stock_intraday_sina` | `stock_intraday_em` |

## Extremely slow (avoid unless necessary)

| Endpoint | Duration | Lightweight alternative |
|------|------|---------|
| `stock_zh_a_spot_em` | 59s | `stock_individual_info_em` (0.1s) |
| `stock_hk_spot_em` | 59s | `stock_hk_hist` (0.6s) |
| `stock_main_fund_flow("all stocks")` | 62s | `stock_individual_fund_flow_rank("today")` (7s) |

## Lightweight endpoint substitution table

| Scenario | Forbidden (slow/broken) | Use instead (fast) |
|------|----------------|-------------|
| Look up a single A-share | `stock_zh_a_spot_em` (30-60s) | `stock_individual_info_em` (0.1s) + `stock_zh_a_hist` (0.2s) |
| Look up a single Hong Kong stock | `stock_hk_spot_em` (59s) | `stock_hk_hist` (0.6s) |
| Look up a single US stock | `stock_us_spot_em` broken | `stock_us_daily` |
| Name to code | `stock_zh_a_spot_em` iteration | `stock_info_sh_name_code` (1s) + `stock_info_sz_name_code` (0.6s) |
| Market index | `stock_zh_index_spot_sina` broken | `index_global_spot_em` (0.3s) |
| ETF real-time | `fund_etf_spot_em` timeout | `fund_etf_hist_em` (0.2s) taking the latest day |
