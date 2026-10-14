> **Important:** All `scripts/` paths are relative to the skill directory (where SKILL.md lives).
> How to run: `cd {this_skill_dir} && python scripts/...`
> Or use the `cwd` parameter of `execute_shell_command`.

# Editing Presentations

## Template-based Workflow

When using an existing presentation as a template:

1. **Analyze the existing slides**:
   ```bash
   python scripts/thumbnail.py template.pptx
   python -m markitdown template.pptx
   ```
   Look at `thumbnails.jpg` to understand the layouts, and at the markitdown output to understand the placeholder text.

2. **Plan the slide mapping**: pick a template slide for each content section.

   ⚠️ **Use varied layouts** - a monotonous deck is a common failure mode. Do not default to basic title-and-bullets slides. Actively look for:
   - Multi-column layouts (two columns, three columns)
   - Image + text combinations
   - Full-bleed images with text overlays
   - Quote or callout slides
   - Section divider slides
   - Data/number callouts
   - Icon grids or icon + text rows

   **Avoid:** repeating the same text-heavy layout on every slide.

   Match the content type to the layout style (for example: bullets → bullet slide, team information → multi-column layout, testimonials → quote slide).

3. **Unpack**: `python scripts/office/unpack.py template.pptx unpacked/`

4. **Build the deck** (do this yourself, do not use a subagent):
   - Delete the slides you do not need (remove them from `<p:sldIdLst>`)
   - Duplicate the slides you need to reuse (`add_slide.py`)
   - Reorder the slides in `<p:sldIdLst>`
   - **Complete all structural changes before step 5**

5. **Edit the content**: update the text in each `slide{N}.xml`.
   **Use subagents here if they are available** - slides are independent XML files, so subagents can edit them in parallel.

6. **Clean up**: `python scripts/clean.py unpacked/`

7. **Pack**: `python scripts/office/pack.py unpacked/ output.pptx --original template.pptx`

---

## Scripts

| Script | Purpose |
|------|------|
| `unpack.py` | Extract the PPTX and format it |
| `add_slide.py` | Duplicate a slide or create one from a layout |
| `clean.py` | Remove orphan files |
| `pack.py` | Repack and validate |
| `thumbnail.py` | Create a visual grid of the slides |

### unpack.py

```bash
python scripts/office/unpack.py input.pptx unpacked/
```

Extract the PPTX, format the XML, escape smart quotes.

### add_slide.py

```bash
python scripts/add_slide.py unpacked/ slide2.xml      # duplicate a slide
python scripts/add_slide.py unpacked/ slideLayout2.xml # create from a layout
```

Outputs the `<p:sldId>` to add at the specified position in `<p:sldIdLst>`.

### clean.py

```bash
python scripts/clean.py unpacked/
```

Removes slides that are not in `<p:sldIdLst>`, unreferenced media files and orphan relationship files.

### pack.py

```bash
python scripts/office/pack.py unpacked/ output.pptx --original input.pptx
```

Validate, fix, compress the XML and re-encode smart quotes.

### thumbnail.py

```bash
python scripts/thumbnail.py input.pptx [output_prefix] [--cols N]
```

Creates `thumbnails.jpg` labelled with the slide filenames. Defaults to 3 columns, up to 12 slides per grid.

**For template analysis only** (choosing layouts). For visual quality checks, use `soffice` + `pdftoppm` to create full-resolution single-slide images - see SKILL.md.

---

## Slide Operations

Slide order lives in `ppt/presentation.xml` → `<p:sldIdLst>`.

**Reordering**: rearrange the `<p:sldId>` elements.

**Deleting**: remove the `<p:sldId>`, then run `clean.py`.

**Adding**: use `add_slide.py`. Never copy slide files by hand - the script handles note references, Content_Types.xml and relationship IDs, which manual copying misses.

---

## Editing Content

**Subagents:** use them here if available (after step 4 is complete). Each slide is an independent XML file, so subagents can edit in parallel. Include the following in the prompt you give a subagent:
- The path of the slide file to edit
- **"Use the Edit tool for all changes"**
- The formatting rules and common issues below

For each slide:
1. Read the slide XML
2. Identify every item of placeholder content - text, images, charts, icons, captions
3. Replace each placeholder with the final content

**Use the Edit tool, not sed or Python scripts.** The Edit tool requires you to state exactly what is being replaced and where, which makes it more reliable.

### Formatting Rules

- **Bold all titles, subtitles and inline labels**: use `b="1"` on `<a:rPr>`. This includes:
  - Slide titles
  - Section headings within a slide
  - Inline labels (for example "Status:" or "Description:" at the start of a line)
- **Never use Unicode bullet characters (•)**: use `<a:buChar>` or `<a:buAutoNum>` for proper list formatting
- **Bullet consistency**: let bullets inherit from the layout. Only specify `<a:buChar>` or `<a:buNone>`.

---

## Common Issues

### Template Fit

When the source content has fewer items than the template:
- **Remove the extra elements entirely** (images, shapes, text boxes); do not just clear the text
- After clearing the text content, check for orphaned visual elements
- Run the visual quality check to catch count mismatches

When replacement text differs in length:
- **Shorter replacements**: usually safe
- **Longer replacements**: may overflow or wrap unexpectedly
- Run the visual quality check after changing text
- Consider truncating or splitting content to fit the design constraints of the template

**Template slots ≠ number of source items**: if the template has 4 team members but the source data only has 3 people, delete the entire group for the 4th member (image + text box), not just the text.

### Multi-item Content

If the source data has multiple items (a numbered list, several sections), create a separate `<a:p>` element for each item - **never concatenate everything into a single string**.

**❌ Wrong** - all items in one paragraph:
```xml
<a:p>
  <a:r><a:rPr .../><a:t>Step 1: Do the first thing. Step 2: Do the second thing.</a:t></a:r>
</a:p>
```

**✅ Right** - separate paragraphs with bold headings:
```xml
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" b="1" .../><a:t>Step 1</a:t></a:r>
</a:p>
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" .../><a:t>Do the first thing.</a:t></a:r>
</a:p>
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" b="1" .../><a:t>Step 2</a:t></a:r>
</a:p>
<!-- Continue this pattern -->
```

Copy `<a:pPr>` from the original paragraph to preserve line spacing. Use `b="1"` for headings.

### Smart Quotes

Handled automatically by unpack/pack. However, the Edit tool converts smart quotes to ASCII.

**When adding new text that contains quotes, use XML entities:**

```xml
<a:t>the &#x201C;Agreement&#x201D;</a:t>
```

| Character | Name | Unicode | XML entity |
|------|------|---------|----------|
| `\u201c` | Left double quote | U+201C | `&#x201C;` |
| `\u201d` | Right double quote | U+201D | `&#x201D;` |
| `\u2018` | Left single quote | U+2018 | `&#x2018;` |
| `\u2019` | Right single quote | U+2019 | `&#x2019;` |

### Other

- **Whitespace**: use `xml:space="preserve"` on `<a:t>` elements with leading/trailing spaces
- **XML parsing**: use `defusedxml.minidom` rather than `xml.etree.ElementTree` (which breaks namespaces)
