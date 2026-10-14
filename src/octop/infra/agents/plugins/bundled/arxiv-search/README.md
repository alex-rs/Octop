# arXiv Paper Search

No API key required — query paper metadata through the official arXiv API.

After installing and enabling it from the Dashboard "Plugin Market", an ordinary Agent gets the `search_arxiv`
tool by default; it can be turned off individually in the Agent's tool settings.

Example calls:

```text
search_arxiv(query="retrieval augmented generation", limit=5)
search_arxiv(query="ti:transformer AND cat:cs.CL", sort_by="submittedDate")
search_arxiv(query="au:Vaswani", start=5, limit=5)
search_arxiv(query="1706.03762")
search_arxiv(query="https://arxiv.org/abs/1706.03762")
```

Supports keyword and title/author/category query syntax, as well as new and old paper
IDs, version numbers, and abstract/PDF links. Chinese questions are converted into English search terms
by the Agent. `limit` defaults to 5 with a range of 1–20; `start` is a pagination offset starting from 0.
`sort_by` supports `relevance`, `submittedDate`, and `lastUpdatedDate`, and `sort_order` supports `ascending` and `descending`.

Returns the title, authors, the full abstract, categories, publication/update time, DOI, journal
citation, and abstract/PDF links. The chat card supports Chinese and English plus light and dark themes;
IM channels use a plain-text fallback containing the abstract and links. Network requests are asynchronous, and requests in the same process are serialized with at least a 3-second gap.

API documentation: [arXiv API User's Manual](https://info.arxiv.org/help/api/user-manual.html).
The icon uses the [official arXiv Small Logomark SVG](https://cornell.box.com/v/arxiv-logomark-small-svg),
keeping the official shape and red/grey colors, as an acknowledgement of the paper data source.
Usage guidelines: [arXiv Name and Logo Use](https://info.arxiv.org/brand/brand-guidelines.html).

Thank you to arXiv for use of its open access interoperability. This service was
not reviewed or approved by, nor does it necessarily express or reflect the
policies or opinions of, arXiv.
