# DailyHotApi API Documentation

npm package `dailyhot-api`, with 56 router modules in total. This document is the parameter reference manual; for the categorized navigation of data sources and scenario selection see `sources.md`.

## Installation

**Before the first DailyHotApi call in each session, you must make sure it is installed:**

```bash
npm list dailyhot-api 2>/dev/null || npm install dailyhot-api
```

Only run the script once the installation is confirmed. Do not skip the install and fall back to browser_use.

## How to Call It

**You must call it through the `fetch_dailyhot.mjs` script; do not write your own code or hand-build HTTP requests.**

**Call format:**
```bash
node <skill dir>/scripts/fetch_dailyhot.mjs <source> [key=value ...]
```

**Call examples:**
```bash
# Hupu Pedestrian Street — main board
node <skill dir>/scripts/fetch_dailyhot.mjs hupu

# Hupu — dating board
node <skill dir>/scripts/fetch_dailyhot.mjs hupu type=6

# Baidu trending searches
node <skill dir>/scripts/fetch_dailyhot.mjs baidu type=realtime

# GitHub Trending weekly list
node <skill dir>/scripts/fetch_dailyhot.mjs github type=weekly

# Weibo (no parameters)
node <skill dir>/scripts/fetch_dailyhot.mjs weibo
```

Here `<skill dir>` is the directory containing SKILL.md, and the script lives in its `scripts/` subdirectory.

**Return type RouterData:**
```json
{
  "name": "hupu",
  "title": "Hupu",
  "type": "Pedestrian Street hot posts",
  "total": 10,
  "updateTime": "2025-03-13T14:00:00.000Z",
  "fromCache": false,
  "data": [
    {
      "id": "12345",
      "title": "Post title",
      "desc": "Description (optional)",
      "hot": 1234,
      "timestamp": 1710000000,
      "url": "https://...",
      "mobileUrl": "https://..."
    }
  ]
}
```

## All Router Modules

### News

| source | Name | Parameters |
|--------|------|------|
| `toutiao` | Toutiao — Hot List | none |
| `qq-news` | Tencent News — Hot List | none |
| `netease-news` | NetEase News — Hot List | none |
| `thepaper` | The Paper — Hot List | none |
| `sina-news` | Sina News — Overall Ranking | `type`: 1=overall ranking, 2=video, 3=image, 4=domestic, 5=international, 6=society, 7=sports, 8=finance, 9=entertainment, 10=tech, 11=military |
| `sina` | Sina — Hot List | `type`: all=hot list, hotcmnt=hot discussion, minivideo=video, ent=entertainment, ai=AI, auto=cars, mother=parenting, fashion=fashion, travel=travel, esg=ESG |
| `nytimes` | The New York Times — Chinese site | `area`: china=Chinese site, global=global edition |

### Social Media

| source | Name | Parameters |
|--------|------|------|
| `weibo` | Weibo — Trending List | none |
| `zhihu` | Zhihu — Hot List | none |
| `zhihu-daily` | Zhihu Daily — Recommendation List | none |
| `douyin` | Douyin — Hot List | none |
| `kuaishou` | Kuaishou — Hot List | none |
| `tieba` | Baidu Tieba — Hot Discussion List | none |
| `douban-group` | Douban Groups — Selected Discussions | none |

### Search Engines

| source | Name | Parameters |
|--------|------|------|
| `baidu` | Baidu — Trending Searches | `type`: realtime=trending searches, novel=novels, movie=movies, teleplay=TV series, car=cars, game=games |

### Video Platforms

| source | Name | Parameters |
|--------|------|------|
| `bilibili` | Bilibili — Hot List | `type`: 0=all, 1=animation, 3=music, 4=gaming, 5=entertainment, 188=tech, 119=remixes, 129=dance, 155=fashion, 160=lifestyle, 168=Chinese animation, 181=film and TV |
| `acfun` | AcFun — Rankings | `type`: -1=general, 155=anime series, 1=animation, 60=entertainment, 201=lifestyle, 58=music, 123=dance, 59=gaming, 70=tech, 68=film and TV, 69=sports, 125=fish pond; `range`: DAY=today, THREE_DAYS=three days, WEEK=this week |

### Film, TV and Entertainment

| source | Name | Parameters |
|--------|------|------|
| `douban-movie` | Douban Movies — New Releases | none |
| `weread` | WeRead — Rising List | `type`: rising=rising list, hot_search=trending list, newbook=new books, general_novel_rising=novels, all=overall list |

### Tech and Business

| source | Name | Parameters |
|--------|------|------|
| `36kr` | 36Kr — Popularity List | `type`: hot=popularity list, video=video list, comment=most discussed, collect=most bookmarked |
| `huxiu` | Huxiu — 24 Hours | none |
| `ifanr` | iFanr — News Flash | none |
| `geekpark` | GeekPark — Popular Articles | none |
| `smzdm` | SMZDM — Popular | `type`: 1=popular today, 7=popular this week, 30=popular this month |

### Developers

| source | Name | Parameters |
|--------|------|------|
| `github` | GitHub Trending | `type`: daily=daily list, weekly=weekly list, monthly=monthly list |
| `hellogithub` | HelloGitHub — Popular Repositories | `sort`: featured=featured, all=all |
| `hackernews` | Hacker News — Popular | none |
| `producthunt` | Product Hunt — Today | none |
| `juejin` | Juejin — Article List | `type`: by category ID |
| `csdn` | CSDN — Rankings | none |
| `51cto` | 51CTO — Recommended List | none |
| `sspai` | SSPAI — Hot List | none |
| `v2ex` | V2EX — Topic List | `type`: hot=hottest topics, latest=latest topics |
| `nodeseek` | NodeSeek — Latest | none |
| `linuxdo` | Linux.do — Popular Articles | none |

### IT News

| source | Name | Parameters |
|--------|------|------|
| `ithome` | ITHome — Hot List | none |
| `ithome-xijiayi` | ITHome — Free Game Giveaways | none |
| `dgtle` | Dgtle — Popular Articles | none |

### Sports

| source | Name | Parameters |
|--------|------|------|
| `hupu` | Hupu — Pedestrian Street hot posts | `type`: 1=main board, 6=dating board, 11=campus board, 12=history board, 612=photography board |

### Gaming

| source | Name | Parameters |
|--------|------|------|
| `genshin` | Genshin Impact — Latest Updates | `type`: 1=announcements, 2=events, 3=news |
| `starrail` | Honkai: Star Rail — Latest Updates | `type`: 1=announcements, 2=events, 3=news |
| `honkai` | Honkai Impact 3rd — Latest Updates | `type`: 1=announcements, 2=events, 3=news |
| `miyoushe` | HoYoLAB (Miyoushe) — Announcements | `game`: 1=Honkai Impact 3rd, 2=Genshin Impact, 3=Houkai Gakuen 2, 4=Tears of Themis, 5=Dabieye, 6=Honkai: Star Rail, 8=Zenless Zone Zero; `type`: 1=announcements, 2=events, 3=news |
| `lol` | League of Legends — Patch Notes | none |
| `gameres` | GameRes — News | none |
| `yystv` | Yystv — All Articles | none |

### Community Forums

| source | Name | Parameters |
|--------|------|------|
| `coolapk` | Coolapk — Hot List | none |
| `newsmth` | NewSMTH — Hot Topics | none |
| `hostloc` | Hostloc — Popular | `type`: hot=latest popular, digest=latest picks, new=latest replies, newthread=latest posts |
| `52pojie` | 52PoJie — Picks | `type`: digest=latest picks, hot=latest popular, new=latest replies, newthread=latest posts |
| `ngabbs` | NGA — Hot Forum Posts | none |
| `jianshu` | Jianshu — Popular Picks | none |
| `guokr` | Guokr — Popular Articles | none |

### Everyday Tools

| source | Name | Parameters |
|--------|------|------|
| `history` | Today in History | `month`: month, `day`: day |
| `earthquake` | China Earthquake Networks Center — Earthquake Bulletins | none |
| `weatheralarm` | National Meteorological Center — Weather Alerts | `province`: province name |
