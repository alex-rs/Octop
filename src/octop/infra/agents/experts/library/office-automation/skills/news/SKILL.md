---
name: news
description: "Find the latest news for the user from the specified news sites. Provides authoritative URLs for the politics, finance, society, international, technology, sports and entertainment categories. Use browser_use to open each URL and get the content via snapshot, then summarize it for the user."
metadata:
  builtin_skill_version: "1.2"
  qwenpaw:
    emoji: "📰"
    requires: {}
  octop:
    emoji: "📰"
    label:
      zh: "News Digest"
      en: "News Digest"
    summary:
      zh: "Fetch and summarize the latest news by category such as politics, finance and technology."
      en: "Fetch and summarize latest news by category."
---

# News Reference

When the user asks about "the latest news", "what's in the news today" or "news in a certain category", use the **browser_use** tool with the categories and URLs below: open the page, take a snapshot, then extract the headlines and key points from the page content and reply to the user.

## Categories and Sources

| Category      | Source                    | URL |
|-----------|--------------------------|-----|
| **Politics**  | People's Daily / CPC News | https://cpc.people.com.cn/ |
| **Finance**  | China Economic Net        | http://www.ce.cn/ |
| **Society**  | China News Service / Society | https://www.chinanews.com/society/ |
| **International**  | CGTN                     | https://www.cgtn.com/ |
| **Technology**  | Science and Technology Daily | https://www.stdaily.com/ |
| **Sports**  | CCTV Sports               | https://sports.cctv.com/ |
| **Entertainment**  | Sina Entertainment        | https://ent.sina.com.cn/ |

## How to Use (browser_use)

1. **Clarify what the user needs**: determine which category or categories the user needs (politics / finance / society / international / technology / sports / entertainment), or pick 1-2 to fetch.
2. **Pick the URL**: use the URL for the corresponding category from the table; if several categories are needed, repeat the steps below for each URL.
3. **Open the page**: call **browser_use**:
   ```json
   {"action": "open", "url": "https://www.chinanews.com/society/"}
   ```
   Replace `url` with the corresponding URL from the table.
4. **Take a snapshot**: in the same session, call **browser_use** again:
   ```json
   {"action": "snapshot"}
   ```
   Extract the headlines, dates and summaries from the returned page content.
5. **Summarize and reply**: organize a short list by time or importance (headline + one or two sentences + source); if a site is unreachable or times out, say so and suggest another source.

## Notes

- Page structure may change when a site updates; if extraction fails, explain that and suggest the user open the link directly.
- When visiting multiple categories, run `open` and `snapshot` separately for each URL to avoid mixing up content from different pages.
- You may include the original links in the reply so the user can open them for details.
