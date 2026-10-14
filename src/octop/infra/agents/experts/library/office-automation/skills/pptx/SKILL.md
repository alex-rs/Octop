---
name: pptx
description: "Use this skill for any operation involving .pptx files - whether as input, output or both. This includes: creating slides, presentations or pitch decks; reading, parsing or extracting text from any .pptx file (even when the extracted content will be used elsewhere, such as in an email or a summary); editing, modifying or updating an existing presentation; merging or splitting slide files; and working with templates, layouts, speaker notes or comments. It triggers when the user mentions “presentation”, “slides” or “PPT”, or refers to a .pptx filename, regardless of how they intend to use the content afterwards. If you need to open, create or manipulate a .pptx file, use this skill."
license: Proprietary. LICENSE.txt has complete terms
metadata:
  builtin_skill_version: "1.1"
  octop:
    emoji: "📽️"
    label:
      zh: "PPT Presentations"
      en: "Presentations"
    summary:
      zh: "Create, read, edit or split .pptx presentations."
      en: "Create, read, edit, or split .pptx presentations."
---

> **Important:** All `scripts/` paths are relative to this skill directory.
> How to run: `cd {this_skill_dir} && python scripts/...`
> Or use the `cwd` parameter of `execute_shell_command`.

# PPTX Skill

## Prerequisites

- **markitdown[pptx]**: extract text from presentations
- **Pillow**: generate thumbnail grids
- **pptxgenjs** (`npm install -g pptxgenjs`): create presentations from scratch
- **LibreOffice** (`soffice`): presentation to PDF
- **pdftoppm** (poppler-utils): PDF to images, for thumbnail/visual workflows
- If `pdftoppm` is unavailable, the Python fallback `pdf2image` can be used.
- On Windows the dependencies must already be installed and available on `PATH`; if they are missing, report the dependency problem and stop (do not retry repeatedly).

## Quick Reference

| Task | Guide |
|------|------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit or build from a template | Read [editing.md](editing.md) |
| Create from scratch | Read [pptxgenjs.md](pptxgenjs.md) |

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview
python scripts/thumbnail.py presentation.pptx

# Raw XML
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [editing.md](editing.md) for the full details.**

1. Use `thumbnail.py` to analyze the template
2. Unpack → manipulate the slides → edit the content → clean up → pack

---

## Creating from Scratch

**Read [pptxgenjs.md](pptxgenjs.md) for the full details.**

Use this when no template or reference presentation is available.

---

## Design Ideas

**Do not create boring slides.** A white background with plain text bullets impresses no one. Consider the following design ideas for every slide.

### Before You Start

- **Choose a bold, content-relevant color scheme**: the colors should feel designed specifically for this topic. If your colors would still "work" in a completely different presentation, your choice is not targeted enough.
- **Establish clear hierarchy**: one color should dominate (60-70% of the visual weight), paired with 1-2 secondary tones and one sharp accent color. Never distribute all colors equally.
- **Light and dark contrast**: use dark backgrounds for the title and closing slides and light backgrounds for content slides (a "sandwich" structure). Or use dark backgrounds throughout to create a premium feel.
- **Commit to one visual theme**: choose one distinctive element and use it repeatedly - rounded image frames, icons in colored circles, thick single-sided borders. Carry it through every slide.

### Color Schemes

Choose colors that match the topic - do not default to generic blue. The following palettes are for reference:

| Theme | Primary | Secondary | Accent |
|------|------|--------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### Every Slide

**Every slide needs a visual element** - an image, a chart, an icon or a shape. Text-only slides make a weak impression.

**Layout options:**
- Two-column layout (text on the left, illustration on the right)
- Icon + text rows (icon in a colored circle, bold heading, description below)
- 2x2 or 2x3 grid (image on one side, a grid of content blocks on the other)
- Half-bleed image (filling the left or right side) plus a content overlay

**Presenting data:**
- Large numbers called out (a 60-72pt number with a small label below it)
- Comparison columns (before/after, pros and cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Place icons in small colored circles next to section headings
- Use italic accent text for key figures or taglines

### Typography

**Choose an interesting font pairing** - do not default to Arial. Pick a heading font with personality and pair it with a clean body font.

| Heading font | Body font |
|----------|----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|------|------|
| Slide title | 36-44pt bold |
| Section heading | 20-24pt bold |
| Body | 14-16pt |
| Captions | 10-12pt muted color |

### Spacing

- Minimum margin of 0.5"
- 0.3-0.5" between content blocks
- Leave breathing room - do not fill every inch

### Avoid (Common Mistakes)

- **Do not repeat the same layout** - vary the columns, cards and callout styles between slides
- **Do not center body text** - left-align paragraphs and lists; center only the titles
- **Do not neglect size contrast** - titles need 36pt+ to stand apart from 14-16pt body text
- **Do not default to blue** - choose colors that reflect the specific topic
- **Do not mix spacing arbitrarily** - pick 0.3" or 0.5" spacing and keep it consistent
- **Do not design one slide carefully and leave the rest blank** - either design everything carefully or keep it minimal throughout
- **Do not create text-only slides** - add images, icons, charts or visual elements; avoid a plain title with bullets
- **Do not forget text box padding** - when aligning lines or shapes with the text edge, set the text box `margin: 0` or offset the shape to compensate for the padding
- **Do not use low-contrast elements** - icons and text both need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **Never use an underline beneath a title** - it is the hallmark of AI-generated slides; use whitespace or a background color instead

---

## Quality Check (Mandatory)

**Assume that problems exist, and that your job is to find them.**

Your first render will almost never be fully correct. Treat the quality check as a bug hunt rather than a confirmation step. If the first check turns up zero issues, you did not look carefully enough.

### Content Check

```bash
python -m markitdown output.pptx
```

Check for missing content, typos and ordering mistakes.

**When using a template, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring the work done.

### Visual Check

**⚠️ Use a subagent** - even when there are only 2-3 slides. When you stare at the code you see what you expect to see rather than what is actually there. A subagent brings a fresh perspective.

Convert the slides to images (see [Converting to Images](#converting-to-images)), then use the following prompt:

```
Visually inspect these slides. Assume that problems exist - find them.

Check the following aspects:
- Elements overlapping (text crossing a shape, a line crossing text, elements stacked)
- Text overflowing or cut off at edges/box boundaries
- A decorative rule positioned for a single line of text while the heading wrapped to two lines
- A source citation or footer conflicting with the content above it
- Elements spaced too tightly (< 0.3" gap) or cards/areas almost touching
- Uneven spacing (a large empty area in one place, cramped elsewhere)
- Insufficient margin from the slide edge (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (such as light gray text on a cream background)
- Low-contrast icons (such as a dark icon on a dark background without a contrasting circle)
- Text boxes too narrow, causing excessive wrapping
- Leftover placeholder content

List the problems or concerns for every slide, even minor ones.

Read and analyze these images:
1. /path/to/slide-01.jpg (expected: [brief description])
2. /path/to/slide-02.jpg (expected: [brief description])

Report every problem found, including minor ones.
```

### Verification Loop

1. Generate the slides → convert to images → check
2. **List the problems found** (if you find none, check again against stricter criteria)
3. Fix the problems
4. **Re-verify the affected slides** - one fix often introduces another problem
5. Repeat until a full pass turns up no new problems

**Do not declare success before completing at least one fix-verify loop.**

---

## Converting to Images

Convert the presentation into individual slide images for visual inspection:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg` and other files.

Re-render specific slides after fixing them:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```
