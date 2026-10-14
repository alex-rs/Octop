---
name: wechat-publisher-personal
description: Personal Multi-Platform Publisher — a multi-platform publishing tool that posts a Markdown article to content operation platforms and social content platforms at the same time. The WeChat side uses wenyan-cli + a self-hosted server proxy; the social content platform side uses browser automation.
metadata:
  {
    "openclaw":
      {
        "emoji": "✍️",
        "requires": { "bins": ["node", "npx", "python3"] },
        "primaryEnv": "WECHAT_APP_ID",
      },
    "octop":
      {
        "emoji": "✍️",
        "label": { "zh": "Multi-Platform Publisher", "en": "Multi-Platform Publisher" },
        "summary":
          {
            "zh": "Publish one Markdown article to content and social platforms.",
            "en": "Publish one Markdown article to content and social platforms.",
          },
      },
  }
---

# Personal Multi-Platform Publishing Tool — Content Operation Platforms + Social Content Platforms

Write one Markdown article and publish it to **content operation platforms** and **social content platforms** at the same time. The WeChat side renders beautiful typography through wenyan-cli, while the social content platform side automatically adapts the content into a short post + image format. No third-party SaaS platform is required, and your data stays fully under your control.

> Integrates the [ClawHub hi-yu/xhs](https://clawhub.ai/hi-yu/xhs) v1.2.5 social content platform Skill capability

## Supported Platforms

| Platform | Publishing method | Content format |
|------|----------|----------|
| 📱 **Content operation platforms** | wenyan-cli + WeChat API → draft box | Long article + beautiful typography |
| 📕 **Social content platforms (RedNote)** | Playwright browser automation → publish directly | Short note + images + topic hashtags |

## Agent Persona Identity

This Skill follows the [SoulHub](https://github.com/Yourdaylight/soulhub) Agent specification and includes a complete persona identity definition:

| File | Description |
|------|------|
| [`manifest.yaml`](./manifest.yaml) | Agent metadata (name, category, tags, version) |
| [`IDENTITY.md`](./IDENTITY.md) | Identity definition — who I am, my expertise, how I work |
| [`SOUL.md`](./SOUL.md) | Soul specification — core principles, behavioral boundaries, tone and style |

> **Core persona**: ✍️ Multi-Platform Publishing Assistant — an independent content publisher that covers WeChat and social content platforms with a single Markdown article. Minimal and efficient, data autonomy, done in one step.

## Differences from agent-publisher

| Feature | agent-publisher (SaaS edition) | wechat-publisher-personal (personal edition) |
|------|--------------------------|----------------------------------|
| Deployment | Uses a shared backend service | The user's own server |
| Data storage | Stored in the backend database | Local files + the WeChat platform |
| User management | Multi-user, email registration | Single user, used directly |
| AI generation | Built-in AI Agent generates content | The user writes the content, or AI assists in writing it |
| Dependencies | Python + backend API | Node.js (wenyan-cli) + Python helper scripts |
| IP whitelist | Uses the shared server IP | The public IP of the user's own server |

## Prerequisites

### Content operation platforms (required)

1. **Node.js** >= 18 (used to run wenyan-cli)
2. **Python** >= 3.10 (used for helper scripts)
3. **A server with a fixed public IP** (used as the WeChat API IP whitelist proxy)
4. The **content operation platform** AppID and AppSecret

### Social content platforms (optional, enables multi-platform publishing)

5. **Python playwright** — `pip install playwright && playwright install chromium`
6. **A social content platform account** — log in by scanning a QR code
7. **AI cover generation (optional)** — configure one of `GEMINI_API_KEY` / `IMG_API_KEY` / `HUNYUAN_API_KEY`

## Quick Start

### Step 1: Install wenyan-cli

```bash
npm install -g @wenyan-md/cli
```

Verify the installation:
```bash
wenyan --help
```

### Step 2: Configure content operation platform credentials

Set the environment variables (recommended: write them into `~/.bashrc` or `~/.zshrc`):

```bash
export WECHAT_APP_ID="your_wechat_app_id"
export WECHAT_APP_SECRET="your_wechat_app_secret"
```

### Step 3: Obtain the AppID and AppSecret

If the user does not have content operation platform credentials yet:

1. Log in to the [WeChat Developer Platform](https://developers.weixin.qq.com/console/product/mp)
2. Go to "My Business and Services" → "Official Accounts" → "Basic Information"
3. Copy the **AppID**
4. Click "Reset" next to the AppSecret to generate a new key (⚠️ it is shown only once — save it immediately!)

### Step 4: Configure the IP whitelist

There are two modes; choose based on the user's situation:

#### Mode A: Local mode (fixed public IP available)

If your local network has a fixed public IP:
1. Get your public IP: `curl ifconfig.me`
2. On the WeChat Developer Platform → "API IP whitelist" → click "Edit" → add your IP

#### Mode B: Server mode (recommended when there is no fixed IP)

Deploy a wenyan server on your cloud server as a proxy:

```bash
python3 {baseDir}/scripts/wechat_publish.py setup-server --host your_server_ip
```

This will guide you to:
1. Install wenyan-cli on the server and start `wenyan serve`
2. Add the server's public IP to the WeChat whitelist
3. Configure the local CLI to connect to the server

Then set the server environment variables:
```bash
export WENYAN_SERVER="http://your_server_ip:7788"
export WENYAN_API_KEY="your_api_key"
```

### Step 5: Publish your first article

Prepare a Markdown file with frontmatter at the top:

```markdown
---
title: My First Article
cover: ./cover.jpg
author: Your Name
---

# Article Body

This is the body text...
```

Then publish:

```bash
python3 {baseDir}/scripts/wechat_publish.py publish article.md
```

---

## All Commands

### 📦 Multi-platform publishing (recommended)

**Publish to WeChat + social content platforms with a single command:**

```bash
python3 {baseDir}/scripts/wechat_publish.py multi-publish article.md
```

**Use draft mode for social content platforms (recommended for first use):**

```bash
python3 {baseDir}/scripts/wechat_publish.py multi-publish article.md --xhs-draft
```

**Batch multi-platform publishing:**

```bash
python3 {baseDir}/scripts/wechat_publish.py multi-publish article1.md article2.md
```

---

### 📱 Content operation platforms

#### Publish an article

**Publish Markdown directly to the content operation platform draft box:**

```bash
python3 {baseDir}/scripts/wechat_publish.py publish article.md
```

**Publish with a specified theme:**

```bash
python3 {baseDir}/scripts/wechat_publish.py publish article.md --theme github
```

**Publish through Server mode (when there is no fixed local IP):**

```bash
python3 {baseDir}/scripts/wechat_publish.py publish article.md --server http://your_server:7788 --api-key your_key
```

**Publish multiple articles in a batch:**

```bash
python3 {baseDir}/scripts/wechat_publish.py publish article1.md article2.md article3.md
```

### Render preview

**Render Markdown to HTML (preview only, no publishing):**

```bash
python3 {baseDir}/scripts/wechat_publish.py render article.md
```

**Render and save to a file:**

```bash
python3 {baseDir}/scripts/wechat_publish.py render article.md --output article.html
```

### Theme management

**List all available themes:**

```bash
python3 {baseDir}/scripts/wechat_publish.py themes
```

**Preview the effect of a theme:**

```bash
python3 {baseDir}/scripts/wechat_publish.py render article.md --theme elegant --output preview.html
```

### Server management

**Check the server connection status:**

```bash
python3 {baseDir}/scripts/wechat_publish.py server-status
```

**Deploy/configure wenyan server (interactive guidance):**

```bash
python3 {baseDir}/scripts/wechat_publish.py setup-server --host your_server_ip
```

### Configuration check

**Check whether the current environment configuration is correct:**

```bash
python3 {baseDir}/scripts/wechat_publish.py check
```

Output: wenyan-cli installation status, environment variables, IP whitelist suggestions, server connection, etc.

---

## Social Content Platform Commands

### Log in to the social content platform

**First use requires QR-code login:**

```bash
python3 {baseDir}/scripts/xhs_publish.py login
```

The browser opens automatically; just scan the QR code with the social content platform app. The cookie is saved automatically, so there is no need to log in again later.

### Publish to the social content platform

**Publish a Markdown file as a social content platform note:**

```bash
python3 {baseDir}/scripts/xhs_publish.py publish article.md
```

**Draft mode (fills in the content but does not click publish automatically):**

```bash
python3 {baseDir}/scripts/xhs_publish.py publish article.md --draft
```

**Headless mode (runs in the background):**

```bash
python3 {baseDir}/scripts/xhs_publish.py publish article.md --headless
```

### Preview the social content platform adaptation result

**See how the Markdown looks after conversion to the social content platform format:**

```bash
python3 {baseDir}/scripts/xhs_publish.py adapt article.md
```

This displays: title truncation (≤20 characters), body conversion, image extraction, topic hashtags, etc.

### Check the social content platform environment

```bash
python3 {baseDir}/scripts/xhs_publish.py check
```

---

## Multi-Platform Publishing Commands

### Publish to WeChat + social content platforms at the same time

**One command publishes the Markdown to both platforms at once:**

```bash
# Publish to the content operation platform first
python3 {baseDir}/scripts/wechat_publish.py publish article.md

# Then publish to the social content platform
python3 {baseDir}/scripts/xhs_publish.py publish article.md
```

> 💡 **Automatic content adaptation**: the WeChat side keeps the complete long-form typography, while the social content platform side is automatically converted into a short note + images + topic hashtags format. One Markdown article, and each platform shows it in its best form.

---

## Environment Variables

### Content operation platforms

| Variable | Description | Default |
|----------|-------------|---------|
| `WECHAT_APP_ID` | Content operation platform AppID | — (required) |
| `WECHAT_APP_SECRET` | Content operation platform AppSecret | — (required) |
| `WENYAN_SERVER` | wenyan server URL (Server mode) | — (optional) |
| `WENYAN_API_KEY` | wenyan server API Key (Server mode) | — (optional) |
| `WENYAN_THEME` | Default rendering theme | `github` |

### Social content platforms

| Variable | Description | Default |
|----------|-------------|---------|
| `XHS_COOKIE_FILE` | Social content platform cookie file path | `~/.xhs-cookies.json` |
| `GEMINI_API_KEY` | Gemini API Key (AI cover generation) | — (optional) |
| `IMG_API_KEY` | Image generation API Key (AI cover generation) | — (optional) |
| `HUNYUAN_API_KEY` | Tencent Hunyuan API Key (AI cover generation) | — (optional) |

## Typical Workflow

### First use

1. **Install wenyan-cli** → `npm install -g @wenyan-md/cli`
2. **Install playwright** → `pip install playwright && playwright install chromium`
3. **Environment check** → `wechat_publish.py check` + `xhs_publish.py check`
4. **Configure the WeChat whitelist** → local mode or the `setup-server` Server mode
5. **Log in to the social content platform** → `xhs_publish.py login` (QR-code login)
6. **Write an article** → write it in Markdown and add frontmatter (title, cover, tags)
7. **Preview** → `wechat_publish.py render` + `xhs_publish.py adapt` (view each side's result separately)
8. **Multi-platform publishing** → `wechat_publish.py publish` + `xhs_publish.py publish`
9. **Log in to the Official Account backend** → check the draft box, then click publish
10. **Post-publish verification** → search for the article title on [Sogou WeChat Search](https://weixin.sogou.com/) to confirm the article has been indexed

### Daily use (multi-platform publishing)

1. **Write Markdown** → any editor
2. **Publish to WeChat** → `wechat_publish.py publish article.md`
3. **Publish to the social content platform** → `xhs_publish.py publish article.md`
4. **Go to the Official Account backend to publish** → check, then publish
5. **Post-publish verification** → go to [Sogou WeChat Search](https://weixin.sogou.com/) and search for the article title to confirm it can be found

### AI-assisted writing + multi-platform publishing

1. **Have the AI generate the Markdown content** → including frontmatter (title, cover, tags)
2. **Preview both sides** → `render` to see the WeChat typography + `adapt` to see the social content platform adaptation
3. **Revise and adjust** → the AI can keep refining it
4. **Publish to many platforms in one step** → first `wechat_publish.py publish`, then `xhs_publish.py publish`
5. **Post-publish verification** → after the user confirms publishing from the Official Account backend, verify by searching on [Sogou WeChat Search](https://weixin.sogou.com/)

---

## Markdown File Format

Every article's Markdown file must include frontmatter at the top:

```yaml
---
title: Article title (required)
cover: Cover image path or URL (optional, recommended)
author: Author name (optional)
source_url: Source article link (optional)
tags: tag1, tag2, tag3 (optional, used for social content platform topic hashtags)
---
```

### Social content platform adaptation rules

When Markdown is published to a social content platform it is adapted automatically:

| Item | Content operation platforms | Social content platforms |
|------|-----------|--------|
| Title | Full title | First 20 characters |
| Body | Beautiful HTML typography | Plain text, with emoji marking paragraphs |
| Images | Embedded in the article | Uploaded as note images |
| Code blocks | Syntax highlighting | Turned into text as `💻 Code snippet:` |
| Links | Hyperlinks preserved | Link text only |
| Tags | Not used | frontmatter `tags` → `#topic` |
| Length | Unlimited | ≤1800 characters; anything longer is truncated automatically |

### Image support

- Local images: `![alt](./images/photo.jpg)` — automatically uploaded to the WeChat image host
- Online images: `![alt](https://example.com/photo.jpg)` — automatically downloaded and uploaded
- Cover image: specified in the `cover` field of the frontmatter

---

## Post-Publish Verification

After the user reports that the draft has been officially published from the Official Account backend, one final verification step is required:

1. Open [Sogou WeChat Search](https://weixin.sogou.com/)
2. Search for the article title or the Official Account name
3. Confirm the article can be found

> **Note**: it usually takes some time (a few hours to a day) for an article to be indexed by Sogou after publishing. If you cannot find it right after publishing, try again later.

This step is the **final verification** of the entire publishing process, ensuring the article not only reaches the draft box and is published successfully from the Official Account backend, but can also be indexed and retrieved normally by external search engines.

## Notes

### Content operation platforms
- wenyan-cli automatically uploads the images in the article to the WeChat asset library
- After publishing, the article goes into the **draft box**, and you must log in to the Official Account backend to publish it manually
- Recommended cover image size: 900x383 or a 2.35:1 ratio
- If you use Server mode, you only need to configure the IP whitelist on the server, and the local IP can change freely
- Supports math formulas (LaTeX), code highlighting, automatic conversion of links to footnotes, and more

### Social content platforms
- A social content platform note **must contain at least one image**; it is recommended to set the `cover` field in the frontmatter
- Recommended cover image size: 1080x1440 (3:4 portrait) or 1080x1080 (square)
- The body text is automatically converted from Markdown into a plain-text format friendly to social content platforms
- Titles are limited to 20 characters; anything longer is truncated automatically
- The body text should stay within 1800 characters; anything longer is truncated automatically with an Official Account call-to-action appended
- Cookies are usually valid for 7-30 days; once they expire you need to `login` again by scanning the QR code
- The `tags` field in the frontmatter is automatically converted into social content platform `#topic hashtags`
- It is recommended to preview with `--draft` mode first, then publish for real once everything looks right
