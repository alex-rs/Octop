# 60s API Response Format Reference

Base URL: `https://60s.viki.moe/v2`

## Common Parameters

- `encoding`: response format, one of `json` (default) / `text` / `markdown`
- Some endpoints support extra parameters (such as `date`, `query`, `currency`); see the corresponding entry in `sources.md`

## Common Response Structure

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

## Hot-List Responses (Weibo/Zhihu/Baidu/Douyin, etc.)

```json
{
  "code": 200,
  "data": [
    { "title": "Topic title", "url": "https://...", "hot": "1234567", "rank": 1 }
  ]
}
```

## 60s Daily News

```json
{
  "code": 200,
  "data": {
    "date": "2025-03-13",
    "news": [
      { "title": "News headline", "link": "https://..." }
    ],
    "tip": "daily quote content"
  }
}
```

## Gold Price

```json
{
  "code": 200,
  "data": {
    "date": "2025-03-13",
    "metals": [
      { "name": "Gold_9999", "sell_price": "680.50", "today_price": "679.00", "high_price": "682.00", "low_price": "677.00", "unit": "CNY/gram" }
    ],
    "stores": [
      { "brand": "Chow Tai Fook", "product": "pure gold", "price": "750", "unit": "CNY/gram" }
    ],
    "banks": [
      { "bank": "ICBC", "product": "Ruyi gold bar", "price": "695.00", "unit": "CNY/gram" }
    ],
    "recycle": [
      { "type": "Gold recycling", "price": "670.00", "unit": "CNY/gram", "purity": "Au9999" }
    ]
  }
}
```

## Exchange Rate

```json
{
  "code": 200,
  "data": {
    "base_code": "CNY",
    "updated": "2025-03-13 12:00:00",
    "rates": [
      { "currency": "USD", "rate": 0.1372 },
      { "currency": "EUR", "rate": 0.1265 }
    ]
  }
}
```

## Request Examples

```
# Weibo trending searches
GET https://60s.viki.moe/v2/weibo

# Daily news (specific date, markdown format)
GET https://60s.viki.moe/v2/60s?date=2025-03-13&encoding=markdown

# Gold price
GET https://60s.viki.moe/v2/gold-price

# CNY exchange rate
GET https://60s.viki.moe/v2/exchange-rate?currency=CNY

# Beijing weather
GET https://60s.viki.moe/v2/weather/realtime?query=Beijing

# Hacker News popular posts
GET https://60s.viki.moe/v2/hacker-news/top
```
