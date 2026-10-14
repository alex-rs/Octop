# Data Source Reference Manual

A complete, categorized catalog of hot-list/hotspot content data sources.
Each entry notes the available retrieval channels (60s API / DailyHotApi / browser_use) and the priority.

> For DailyHotApi's call method, detailed parameters, and return format see `dailyhot-api.md`.
> In this file DailyHotApi is noted only by source name (such as `hupu`); the actual call command is `node <skill dir>/scripts/fetch_dailyhot.mjs <source> [parameters]`.

## Retrieval Channels

| Channel | Base URL | Characteristics |
|------|----------|------|
| **60s API** | `https://60s.viki.moe/v2` | Public and free, the fastest, no authentication, covering 50+ endpoints (including finance/weather/film and TV, etc.) |
| **DailyHotApi** | `node <skill dir>/scripts/fetch_dailyhot.mjs <source>` | Covers 56 sources with uniform JSON responses, filling in the sources the 60s API does not cover. See `dailyhot-api.md` |
| **browser_use** | Each site's URL | Direct browser access; the slowest but with the widest coverage |

**Priority: 60s API > DailyHotApi > browser_use**

## Contents
1. [Social Media and Trending Searches](#social-media-and-trending-searches)
2. [News Portals](#news-portals)
3. [Tech and Developers](#tech-and-developers)
4. [Finance and Business](#finance-and-business)
5. [Financial Tools and Data](#financial-tools-and-data)
6. [Video and Content](#video-and-content)
7. [Film, TV and Music](#film-tv-and-music)
8. [Community and Forums](#community-and-forums)
9. [Gaming](#gaming)
10. [Science and Digital](#science-and-digital)
11. [International](#international)
12. [Emergency and Weather](#emergency-and-weather)
13. [Practical Tools](#practical-tools)
14. [Data Source Selection Guide](#data-source-selection-guide)

---

## Social Media and Trending Searches

### 1. Weibo Trending Searches
- **60s API:** `GET /v2/weibo`
- **DailyHotApi:** `weibo`
- **browser_use:** `https://weibo.com/hot/search`
- **Reliability:** High
- **Extracted content:** A numbered list of trending terms, including rank, keyword, heat value, and trend tags (new/hot/boiling/explosive)

### 2. Zhihu Hot List
- **60s API:** `GET /v2/zhihu`
- **DailyHotApi:** `zhihu`
- **browser_use:** `https://www.zhihu.com/hot`
- **Reliability:** High
- **Extracted content:** The top 50 popular questions, including title, summary, and heat (for example, 1.2M heat)

### 3. Zhihu Daily
- **DailyHotApi:** `zhihu-daily`
- **browser_use:** `https://daily.zhihu.com`
- **Reliability:** Medium
- **Extracted content:** Editor-curated daily articles, including title and description

### 4. Baidu Trending Searches
- **60s API:** `GET /v2/baidu/hot`
- **DailyHotApi:** `baidu`
- **browser_use:** `https://top.baidu.com/board`
- **Reliability:** High
- **Extracted content:** Ranked search terms, including search index and a brief description

### 5. Douyin Hot Topics
- **60s API:** `GET /v2/douyin`
- **DailyHotApi:** `douyin`
- **browser_use:** `https://www.douyin.com/hot`
- **Reliability:** Medium (the browser may show login/download prompts; the API is more stable)
- **Extracted content:** Popular topics, including title, description, and heat value

### 6. Kuaishou Hot List
- **DailyHotApi:** `kuaishou`
- **browser_use:** `https://www.kuaishou.com`
- **Reliability:** Low (the browser relies on heavy JS rendering; use the API instead)
- **Extracted content:** Popular videos/topics

### 7. Baidu Tieba Hot Discussions
- **60s API:** `GET /v2/baidu/tieba`
- **DailyHotApi:** `tieba`
- **browser_use:** `https://tieba.baidu.com/hottopic/browse/topicList`
- **Reliability:** High
- **Extracted content:** Discussion topics, including reply counts and discussion heat

### 8. Xiaohongshu Hot Topics
- **60s API:** `GET /v2/rednote`
- **browser_use:** `https://www.xiaohongshu.com`
- **Reliability:** Medium
- **Extracted content:** Popular content on Xiaohongshu

### 9. Quark Hot Topics
- **60s API:** `GET /v2/quark`
- **browser_use:** `https://www.quark.cn`
- **Reliability:** Medium
- **Extracted content:** The Quark browser's hot list

### 10. Dongchedi Trending Searches
- **60s API:** `GET /v2/dongchedi`
- **browser_use:** `https://www.dongchedi.com`
- **Reliability:** Medium
- **Extracted content:** Trending search lists in the automotive field

---

## News Portals

### 11. Daily 60-Second News
- **60s API:** `GET /v2/60s` (supports the `date` and `encoding` parameters)
- **Reliability:** High
- **Extracted content:** 15 curated news items per day plus a daily quote. Updated every 30 minutes

### 12. AI News Briefing
- **60s API:** `GET /v2/ai-news`
- **Reliability:** High
- **Extracted content:** The latest news in the AI field (updated daily)

### 13. Toutiao
- **60s API:** `GET /v2/toutiao`
- **DailyHotApi:** `toutiao`
- **browser_use:** `https://www.toutiao.com/trending/`
- **Reliability:** High
- **Extracted content:** Popular articles ranked by heat, including title, heat value, and source

### 14. Tencent News
- **DailyHotApi:** `qq-news`
- **browser_use:** `https://news.qq.com`
- **Reliability:** High
- **Extracted content:** Front-page headline news, including title and category tags

### 15. The Paper
- **DailyHotApi:** `thepaper`
- **browser_use:** `https://www.thepaper.cn`
- **Reliability:** High
- **Extracted content:** Focus news and the "hot list", including view counts

### 16. Sina News
- **DailyHotApi:** `sina-news`
- **browser_use:** `https://news.sina.com.cn`
- **Reliability:** High
- **Extracted content:** Headline news organized by category (top news/international/society/finance)

### 17. Sina Trending Searches
- **DailyHotApi:** `sina`
- **browser_use:** `https://sinanews.sina.cn/news/hotnews`
- **Reliability:** Medium
- **Extracted content:** Ranking of hot news, including heat values

### 18. NetEase News
- **DailyHotApi:** `netease-news`
- **browser_use:** `https://news.163.com`
- **Reliability:** High
- **Extracted content:** Main headlines and popular sections

### 19. The New York Times Chinese
- **DailyHotApi:** `nytimes`
- **browser_use:** `https://cn.nytimes.com`
- **Reliability:** Medium (may have a paywall)
- **Extracted content:** International news headlines

### 20. Today in History
- **60s API:** `GET /v2/today-in-history`
- **DailyHotApi:** `history`
- **browser_use:** `https://baike.baidu.com/calendar`
- **Reliability:** High
- **Extracted content:** Historical events matching today's date

---

## Tech and Developers

### 21. Juejin
- **DailyHotApi:** `juejin`
- **browser_use:** `https://juejin.cn/hot/articles`
- **Reliability:** High
- **Extracted content:** Technical articles ranked by heat, including title, author, view count, and category tags

### 22. CSDN
- **DailyHotApi:** `csdn`
- **browser_use:** `https://blog.csdn.net/rank/list`
- **Reliability:** High
- **Extracted content:** Blog articles ranked by view count

### 23. 51CTO
- **DailyHotApi:** `51cto`
- **browser_use:** `https://www.51cto.com`
- **Reliability:** Medium
- **Extracted content:** Tech news and tutorial rankings

### 24. SSPAI
- **DailyHotApi:** `sspai`
- **browser_use:** `https://sspai.com`
- **Reliability:** High
- **Extracted content:** Selected articles on digital tools, productivity, and the Apple ecosystem

### 25. ITHome
- **DailyHotApi:** `ithome`
- **browser_use:** `https://www.ithome.com`
- **Reliability:** High
- **Extracted content:** Tech news headlines and the hot list

### 26. ITHome Free Game Giveaways
- **DailyHotApi:** `ithome-xijiayi`
- **browser_use:** `https://www.ithome.com/zt/xijiayi`
- **Reliability:** High
- **Extracted content:** Free game giveaways and discounts

### 27. GitHub Trending
- **DailyHotApi:** `github`
- **browser_use:** `https://github.com/trending`
- **Reliability:** High
- **Extracted content:** Popular repositories, including owner/repo name, description, star count, and stars gained today

### 28. HelloGitHub
- **DailyHotApi:** `hellogithub`
- **browser_use:** `https://hellogithub.com`
- **Reliability:** High
- **Extracted content:** Monthly selected open-source projects

### 29. NodeSeek
- **DailyHotApi:** `nodeseek`
- **browser_use:** `https://www.nodeseek.com`
- **Reliability:** High
- **Extracted content:** VPS/hosting community discussions

### 30. Jianshu
- **DailyHotApi:** `jianshu`
- **browser_use:** `https://www.jianshu.com`
- **Reliability:** Medium
- **Extracted content:** Popular articles and selected content

---

## Finance and Business

### 31. 36Kr
- **DailyHotApi:** `36kr`
- **browser_use:** `https://www.36kr.com/hot-list/catalog`
- **Reliability:** High
- **Extracted content:** Popular articles, focused on startups, VC funding, and industry analysis

### 32. iFanr
- **DailyHotApi:** `ifanr`
- **browser_use:** `https://www.ifanr.com`
- **Reliability:** High
- **Extracted content:** Tech product news, reviews, and industry analysis

### 33. SMZDM
- **DailyHotApi:** `smzdm`
- **browser_use:** `https://post.smzdm.com/fenlei/zhinan/`
- **Reliability:** High
- **Extracted content:** Consumer product recommendations and deals

### 34. Huxiu
- **DailyHotApi:** `huxiu`
- **browser_use:** `https://www.huxiu.com`
- **Reliability:** High
- **Extracted content:** Business analysis and industry insights

### 35. Sina Finance
- **DailyHotApi:** `sina`
- **browser_use:** `https://finance.sina.com.cn`
- **Reliability:** High
- **Extracted content:** Stock market headlines, major indices (SSE/SZSE/ChiNext), and finance news

### 36. Xueqiu
- **browser_use:** `https://xueqiu.com/today` (no API coverage)
- **Reliability:** Medium (login may be required)
- **Extracted content:** Investment discussions, individual stock analysis, and market commentary

---

## Financial Tools and Data

### 37. Gold Price
- **60s API:** `GET /v2/gold-price` (supports the `encoding` parameter: json/text/markdown)
- **Reliability:** High
- **Extracted content:** Real-time precious metal quotes (gold/silver/platinum/palladium), including international gold prices, prices at major jewelry stores, bank gold bar prices, and gold recycling prices

### 38. Currency Exchange Rates
- **60s API:** `GET /v2/exchange-rate` (parameter: `currency=CNY` sets the base currency)
- **Reliability:** High
- **Extracted content:** The day's global currency exchange rates, with CNY as the default base, including the update time and the next update time

### 39. Gasoline Prices
- **60s API:** `GET /v2/fuel-price`
- **Reliability:** High
- **Extracted content:** Fuel price lookups across domestic regions

---

## Video and Content

### 40. Bilibili Rankings
- **60s API:** `GET /v2/bili`
- **DailyHotApi:** `bilibili`
- **browser_use:** `https://www.bilibili.com/v/popular/rank/all`
- **Reliability:** High
- **Extracted content:** Popular video rankings, including title, uploader, and play count

### 41. AcFun
- **DailyHotApi:** `acfun`
- **browser_use:** `https://www.acfun.cn/rank/list`
- **Reliability:** High
- **Extracted content:** Video and article rankings

### 42. WeRead
- **DailyHotApi:** `weread`
- **browser_use:** `https://weread.qq.com`
- **Reliability:** Medium
- **Extracted content:** Popular books and reading lists

### 43. Yystv
- **DailyHotApi:** `yystv`
- **browser_use:** `https://www.yystv.cn`
- **Reliability:** High
- **Extracted content:** Gaming industry news, reviews, and analysis

---

## Film, TV and Music

### 44. Maoyan Global Box Office
- **60s API:** `GET /v2/maoyan/all/movie`
- **Reliability:** High
- **Extracted content:** Global movie box office overall ranking

### 45. Maoyan Real-Time Movie Box Office
- **60s API:** `GET /v2/maoyan/realtime/movie`
- **Reliability:** High
- **Extracted content:** Real-time movie box office data

### 46. Maoyan TV Ratings Ranking
- **60s API:** `GET /v2/maoyan/realtime/tv`
- **Reliability:** High
- **Extracted content:** TV drama ratings ranking

### 47. Maoyan Web Drama Popularity
- **60s API:** `GET /v2/maoyan/realtime/web`
- **Reliability:** High
- **Extracted content:** Real-time popularity ranking of web dramas

### 48. Douban Global Acclaimed Movies
- **60s API:** `GET /v2/douban/weekly/movie`
- **DailyHotApi:** `douban-movie`
- **browser_use:** `https://movie.douban.com/chart`
- **Reliability:** High
- **Extracted content:** Douban's globally acclaimed movies (updated weekly)

### 49. Douban Acclaimed Chinese-Language Series
- **60s API:** `GET /v2/douban/weekly/tv_chinese`
- **Reliability:** High
- **Extracted content:** Acclaimed Chinese-language series (updated weekly)

### 50. Douban Global Acclaimed Series
- **60s API:** `GET /v2/douban/weekly/tv_global`
- **Reliability:** High
- **Extracted content:** Globally acclaimed series (updated weekly)

### 51. Douban Acclaimed Chinese-Language Variety Shows
- **60s API:** `GET /v2/douban/weekly/show_chinese`
- **Reliability:** High
- **Extracted content:** Acclaimed Chinese-language variety shows (updated weekly)

### 52. Douban Global Acclaimed Variety Shows
- **60s API:** `GET /v2/douban/weekly/show_global`
- **Reliability:** High
- **Extracted content:** Globally acclaimed variety shows (updated weekly)

### 53. Baidu TV Drama List
- **60s API:** `GET /v2/baidu/teleplay`
- **Reliability:** High
- **Extracted content:** Baidu TV drama popularity ranking

### 54. NetEase Cloud Music Rankings
- **60s API:** `GET /v2/ncm-rank/list` (list of charts), `GET /v2/ncm-rank/:id` (chart details)
- **Reliability:** High
- **Extracted content:** Various music charts and song details

---

## Community and Forums

### 55. V2EX
- **DailyHotApi:** `v2ex`
- **browser_use:** `https://www.v2ex.com/?tab=hot`
- **Reliability:** High
- **Extracted content:** Popular discussion topics, a tech/developer community

### 56. Douban Discussions
- **DailyHotApi:** `douban-group`
- **browser_use:** `https://www.douban.com/group/explore`
- **Reliability:** Medium
- **Extracted content:** Popular group discussions on life, culture, and entertainment

### 57. Douban Movies
- **DailyHotApi:** `douban-movie`
- **browser_use:** `https://movie.douban.com/chart`
- **Reliability:** High
- **Extracted content:** Box office rankings, new releases, ratings
- **Note:** For acclaim lists prefer the 60s API (see the "Film, TV and Music" category, #48)

### 58. Hupu
- **DailyHotApi:** `hupu`
- **browser_use:** `https://bbs.hupu.com/all-gambia`
- **Reliability:** High
- **Extracted content:** Popular sports discussions and community topics

### 59. NGA
- **DailyHotApi:** `ngabbs`
- **browser_use:** `https://ngabbs.com`
- **Reliability:** High
- **Extracted content:** Popular discussions in the gaming community

### 60. NewSMTH
- **DailyHotApi:** `newsmth`
- **browser_use:** `https://www.newsmth.net`
- **Reliability:** Medium
- **Extracted content:** Popular topics in the academic and tech community

### 61. Hostloc
- **DailyHotApi:** `hostloc`
- **browser_use:** `https://hostloc.com/forum.php`
- **Reliability:** Medium
- **Extracted content:** VPS/hosting deals and technical discussions

### 62. 52PoJie
- **DailyHotApi:** `52pojie`
- **browser_use:** `https://www.52pojie.cn`
- **Reliability:** Medium
- **Extracted content:** Software and reverse engineering community discussions

### 63. Linux.do
- **DailyHotApi:** `linuxdo`
- **browser_use:** `https://linux.do`
- **Reliability:** High
- **Extracted content:** Linux/open-source community discussions

### 64. Coolapk
- **DailyHotApi:** `coolapk`
- **browser_use:** `https://www.coolapk.com`
- **Reliability:** Medium
- **Extracted content:** Android community discussions, app reviews, and digital product news

---

## Gaming

### 65. League of Legends
- **DailyHotApi:** `lol`
- **browser_use:** `https://lol.qq.com/news/`
- **Reliability:** High
- **Extracted content:** League of Legends news, version updates, and esports events

### 66. Genshin Impact (Miyoushe)
- **DailyHotApi:** `genshin`
- **browser_use:** `https://www.miyoushe.com/ys`
- **Reliability:** High
- **Extracted content:** Genshin Impact community news, announcements, and player creations

### 67. Honkai Impact 3rd (Miyoushe)
- **DailyHotApi:** `honkai`
- **browser_use:** `https://www.miyoushe.com/bh3`
- **Reliability:** High
- **Extracted content:** Honkai Impact 3rd community news and version updates

### 68. Honkai: Star Rail (Miyoushe)
- **DailyHotApi:** `starrail`
- **browser_use:** `https://www.miyoushe.com/sr`
- **Reliability:** High
- **Extracted content:** Honkai: Star Rail community news and version updates

### 69. GameRes
- **DailyHotApi:** `gameres`
- **browser_use:** `https://www.gameres.com`
- **Reliability:** Medium
- **Extracted content:** Gaming industry news, development resources, and analysis

---

## Science and Digital

### 70. Guokr
- **DailyHotApi:** `guokr`
- **browser_use:** `https://www.guokr.com`
- **Reliability:** High
- **Extracted content:** Science articles on biology, physics, health, and tech

### 71. GeekPark
- **DailyHotApi:** `geekpark`
- **browser_use:** `https://www.geekpark.net`
- **Reliability:** High
- **Extracted content:** In-depth tech industry reporting, founder interviews, and product analysis

### 72. Dgtle
- **DailyHotApi:** `dgtle`
- **browser_use:** `https://www.dgtle.com`
- **Reliability:** High
- **Extracted content:** Digital lifestyle, gadget reviews, and photography

---

## International

### 73. Hacker News
- **60s API:** `GET /v2/hacker-news/top` (also `/v2/hacker-news/new` and `/v2/hacker-news/best`)
- **DailyHotApi:** `hackernews`
- **browser_use:** `https://news.ycombinator.com`
- **Reliability:** High
- **Extracted content:** Headlines ranked by score, including title, link, score, and comment count

### 74. Product Hunt
- **DailyHotApi:** `producthunt`
- **browser_use:** `https://www.producthunt.com`
- **Reliability:** High
- **Extracted content:** Today's popular product launches, including product name, one-line pitch, and vote count

### 75. The New York Times
- **browser_use:** `https://www.nytimes.com` (no API coverage)
- **Reliability:** Medium (some articles are behind a paywall)
- **Extracted content:** Front-page international news headlines

---

## Emergency and Weather

### 76. National Meteorological Center (weather alerts)
- **DailyHotApi:** `weatheralarm`
- **browser_use:** `http://www.nmc.cn`
- **Reliability:** High
- **Extracted content:** Current weather warnings and alerts

### 77. China Earthquake Networks Center
- **DailyHotApi:** `earthquake`
- **browser_use:** `https://news.ceic.ac.cn`
- **Reliability:** High
- **Extracted content:** The latest earthquake reports, including magnitude, location, and time

### 78. Real-Time Weather
- **60s API:** `GET /v2/weather/realtime` (parameters: `query=city name`, defaults to Beijing)
- **Reliability:** High
- **Extracted content:** Current weather, temperature, humidity, wind, air quality (AQI/PM2.5), living indices, and weather alerts

### 79. Weather Forecast
- **60s API:** `GET /v2/weather/forecast` (parameters: `query=city name&days=7`)
- **Reliability:** High
- **Extracted content:** Hourly and daily weather forecasts, including high/low temperatures and weather conditions

---

## Practical Tools

### 80. Slack-Off Daily
- **60s API:** `GET /v2/moyu`
- **Reliability:** High
- **Extracted content:** Slack-off calendar

### 81. Epic Free Games
- **60s API:** `GET /v2/epic`
- **Reliability:** High
- **Extracted content:** Epic Games' currently free games (updated weekly)

### 82. Baidu Baike
- **60s API:** `GET /v2/baike` (parameters: `query=keyword`)
- **Reliability:** High
- **Extracted content:** Encyclopedia entry lookup

### 83. Translation
- **60s API:** `ALL /v2/fanyi` (parameters: `query=text&from=auto&to=zh`)
- **Reliability:** High
- **Extracted content:** Translation between 109 languages

### 84. Lyrics Search
- **60s API:** `ALL /v2/lyric` (parameters: `query=song name or lyrics`)
- **Reliability:** High
- **Extracted content:** Song lyrics

### 85. Bing Wallpaper
- **60s API:** `GET /v2/bing`
- **Reliability:** High
- **Extracted content:** Bing's daily wallpaper

---

## Data Source Selection Guide

When the user's request matches a category, use the following presets. Prefer the 60s API.

### Daily Morning Briefing (general)
`60s /v2/60s` → `60s /v2/weibo` → `60s /v2/zhihu` → `60s /v2/toutiao` → `fetch_dailyhot.mjs 36kr`

### Tech/Developers
`60s /v2/hacker-news/top` → `fetch_dailyhot.mjs github` → `fetch_dailyhot.mjs juejin` → `fetch_dailyhot.mjs v2ex` → `fetch_dailyhot.mjs ithome`

### Finance/Investment
`60s /v2/gold-price` → `60s /v2/exchange-rate` → `fetch_dailyhot.mjs 36kr` → `fetch_dailyhot.mjs sina` → `60s /v2/weibo` (filter for finance) → `browser_use Xueqiu`

### Entertainment/Social
`60s /v2/weibo` → `60s /v2/douyin` → `60s /v2/rednote` → `60s /v2/bili` → `fetch_dailyhot.mjs kuaishou`

### Film, TV and Variety
`60s /v2/maoyan/realtime/movie` → `60s /v2/douban/weekly/movie` → `60s /v2/douban/weekly/tv_chinese` → `60s /v2/baidu/teleplay` → `60s /v2/maoyan/realtime/web`

### Developers/Open Source
`60s /v2/hacker-news/top` → `fetch_dailyhot.mjs github` → `fetch_dailyhot.mjs v2ex` → `fetch_dailyhot.mjs juejin` → `fetch_dailyhot.mjs nodeseek` → `fetch_dailyhot.mjs linuxdo`

### International News
`60s /v2/hacker-news/top` → `fetch_dailyhot.mjs producthunt` → `fetch_dailyhot.mjs nytimes` → `browser_use The New York Times`

### AI
`60s /v2/ai-news` → `60s /v2/hacker-news/top` → `fetch_dailyhot.mjs 36kr` (filter for AI) → `fetch_dailyhot.mjs juejin` (filter for AI)

### Cars
`60s /v2/dongchedi` → `60s /v2/fuel-price` → `60s /v2/weibo` (filter for cars)

### Gaming
`60s /v2/epic` → `fetch_dailyhot.mjs ngabbs` → `fetch_dailyhot.mjs genshin` → `fetch_dailyhot.mjs yystv` → `fetch_dailyhot.mjs gameres`

### Sports
`fetch_dailyhot.mjs hupu` → `60s /v2/weibo` (filter for sports)

### Life/Consumption
`fetch_dailyhot.mjs smzdm` → `60s /v2/rednote` → `fetch_dailyhot.mjs coolapk`

### Weather/Emergency
`60s /v2/weather/realtime` → `60s /v2/weather/forecast` → `fetch_dailyhot.mjs earthquake` → `fetch_dailyhot.mjs weatheralarm`

### Financial Data (quick lookup)
`60s /v2/gold-price` → `60s /v2/exchange-rate` → `60s /v2/fuel-price` (select as needed)

---

## Channel Coverage Statistics

| Channel | Sources covered | Notes |
|------|----------|------|
| 60s API | 50+ | Hot lists (Weibo/Zhihu/Baidu/Douyin/Toutiao/Bilibili/Xiaohongshu/Quark/Dongchedi/HN) + film and TV (Maoyan/Douban/Baidu TV dramas) + finance (gold price/exchange rate/fuel price) + weather + music + AI news, etc. |
| DailyHotApi | 56 | Supplements the sources the 60s API does not cover (36Kr/Huxiu/Sina Finance/GitHub/Juejin, etc.) |
| browser_use | 85 | Every source can be visited in the browser (fallback) |
| browser_use only | 1 | Xueqiu (no API coverage) |
