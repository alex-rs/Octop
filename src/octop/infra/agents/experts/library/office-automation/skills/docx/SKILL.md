---
name: docx
description: "Use this skill when the user needs to create, read, edit or process a Word document (.docx). Trigger scenarios include mentioning “Word document” or “.docx”, or asking for professional documents formatted with a table of contents, headings, page numbers, letterhead and so on; they also include extracting or restructuring .docx content, inserting or replacing images, find-and-replace inside Word files, handling revisions or comments, and organizing content into a formal Word document. If the user asks for Word / .docx deliverables such as “reports”, “memos”, “letters” or “templates”, this skill should also be used. Do not use it for PDF, spreadsheets, Google Docs, or general programming tasks unrelated to document generation."
license: Proprietary. LICENSE.txt has complete terms
metadata:
  builtin_skill_version: "1.1"
  octop:
    emoji: "📝"
    label:
      zh: "Word Documents"
      en: "Word Documents"
    summary:
      zh: "Create, read, edit or organize professional .docx documents."
      en: "Create, read, edit, or format professional .docx documents."
---

> **Important:** All `scripts/` paths are relative to this skill directory.
> How to run: `cd {this_skill_dir} && python scripts/...`
> Or use the `cwd` parameter of `execute_shell_command`.

# DOCX Creation, Editing and Analysis

## Prerequisites

- **docx** (`npm install -g docx`): creating new documents
- **LibreOffice** (`soffice`): `.doc` -> `.docx` conversion, accepting revisions, and PDF export
- **pandoc**: text extraction
- **pdftoppm** (poppler-utils): document-to-image workflows
- If `pdftoppm` is unavailable, the Python fallback path may use `pdf2image`.
- On Windows the dependencies must already be installed and available on `PATH`; if they are missing, report the dependency problem and stop (do not retry repeatedly).

## Overview

.docx files are ZIP archives containing XML files.

## Quick Reference

| Task | Method |
|------|------|
| Read/analyze content | `pandoc` or unzip to get the raw XML |
| Create a new document | Use `docx-js` - see "Creating a New Document" below |
| Edit an existing document | Unzip → edit the XML → repack - see "Editing an Existing Document" below |

### Converting .doc to .docx

Legacy `.doc` files must be converted before they can be edited:

```bash
python scripts/office/soffice.py --headless --convert-to docx document.doc
```

### Reading Content

```bash
# Extract text including revisions
pandoc --track-changes=all document.docx -o output.md

# Access the raw XML
python scripts/office/unpack.py document.docx unpacked/
```

### Converting to Images

```bash
python scripts/office/soffice.py --headless --convert-to pdf document.docx
pdftoppm -jpeg -r 150 document.pdf page
```

### Accepting Revisions

Produce a clean document with all revisions accepted (requires LibreOffice):

```bash
python scripts/accept_changes.py input.docx output.docx
```

---

## Creating a New Document

Generate .docx files with JavaScript, then validate them. Install with: `npm install -g docx`

### Initial Setup
```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
        Header, Footer, AlignmentType, PageOrientation, LevelFormat, ExternalHyperlink,
        TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
        VerticalAlign, PageNumber, PageBreak } = require('docx');

const doc = new Document({ sections: [{ children: [/* content */] }] });
Packer.toBuffer(doc).then(buffer => fs.writeFileSync("doc.docx", buffer));
```

### Validation
Validate after creating the file. If validation fails, unzip, fix the XML and repack.
```bash
python scripts/office/validate.py doc.docx
```

### Page Size

```javascript
// Key: docx-js defaults to A4, not US Letter
// Always set the page size explicitly for consistent results
sections: [{
  properties: {
    page: {
      size: {
        width: 12240,   // 8.5 inches (DXA units)
        height: 15840   // 11 inches (DXA units)
      },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } // 1-inch margins
    }
  },
  children: [/* content */]
}]
```

**Common page sizes (DXA units, 1440 DXA = 1 inch):**

| Paper | Width | Height | Content width (1-inch margins) |
|------|------|------|----------------------|
| US Letter | 12,240 | 15,840 | 9,360 |
| A4 (default) | 11,906 | 16,838 | 9,026 |

**Landscape orientation:** docx-js swaps width/height internally, so pass portrait dimensions and let it handle the swap:
```javascript
size: {
  width: 12240,   // pass the short edge as width
  height: 15840,  // pass the long edge as height
  orientation: PageOrientation.LANDSCAPE  // docx-js swaps them in the XML
},
// Content width = 15840 - left margin - right margin (using the long edge)
```

### Styles (Overriding the Built-in Headings)

Use Arial as the default font (universally supported). Keep headings black for readability.

```javascript
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } }, // 12pt by default
    paragraphStyles: [
      // Important: use the exact IDs to override the built-in styles
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } }, // outlineLevel is required for the table of contents
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    children: [
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Title")] }),
    ]
  }]
});
```

### Lists (Never Use Unicode Symbols)

```javascript
// ❌ Wrong - never insert bullet characters manually
new Paragraph({ children: [new TextRun("• Item")] })  // wrong
new Paragraph({ children: [new TextRun("\u2022 Item")] })  // wrong

// ✅ Right - use numbering config with LevelFormat.BULLET
const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [{
    children: [
      new Paragraph({ numbering: { reference: "bullets", level: 0 },
        children: [new TextRun("Bullet item")] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 },
        children: [new TextRun("Numbered item")] }),
    ]
  }]
});

// ⚠️ Each reference creates a separate numbering sequence
// Same reference = numbering continues (1,2,3 then 4,5,6)
// Different reference = numbering restarts (1,2,3 then 1,2,3)
```

### Tables

**Key: tables need a double width setting** - you must set `columnWidths` on the table and `width` on every cell. Without either one, the table renders incorrectly on some platforms.

```javascript
// Key: always set the table width for consistent rendering
// Key: use ShadingType.CLEAR (rather than SOLID) to prevent a black background
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

new Table({
  width: { size: 9360, type: WidthType.DXA }, // always use DXA (percentages break in Google Docs)
  columnWidths: [4680, 4680], // must add up to the table width (DXA: 1440 = 1 inch)
  rows: [
    new TableRow({
      children: [
        new TableCell({
          borders,
          width: { size: 4680, type: WidthType.DXA }, // also needed on every cell
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR }, // CLEAR rather than SOLID
          margins: { top: 80, bottom: 80, left: 120, right: 120 }, // cell padding (internal, does not increase the width)
          children: [new Paragraph({ children: [new TextRun("Cell")] })]
        })
      ]
    })
  ]
})
```

**Table width calculation:**

Always use `WidthType.DXA` -- `WidthType.PERCENTAGE` breaks in Google Docs.

```javascript
// Table width = sum of columnWidths = content width
// US Letter with 1-inch margins: 12240 - 2880 = 9360 DXA
width: { size: 9360, type: WidthType.DXA },
columnWidths: [7000, 2360]  // must add up to the table width
```

**Width rules:**
- **Always use `WidthType.DXA`** -- never use `WidthType.PERCENTAGE` (incompatible with Google Docs)
- The table width must equal the sum of `columnWidths`
- Each cell `width` must match the corresponding `columnWidth`
- Cell `margins` are internal padding - they shrink the content area rather than increasing the cell width
- Full-width tables: use the content width (page width minus the left and right margins)

### Images

```javascript
// Key: the type parameter is required
new Paragraph({
  children: [new ImageRun({
    type: "png", // required: png, jpg, jpeg, gif, bmp, svg
    data: fs.readFileSync("image.png"),
    transformation: { width: 200, height: 150 },
    altText: { title: "Title", description: "Desc", name: "Name" } // all three are required
  })]
})
```

### Page Breaks

```javascript
// Key: PageBreak must be inside a Paragraph
new Paragraph({ children: [new PageBreak()] })

// Or use pageBreakBefore
new Paragraph({ pageBreakBefore: true, children: [new TextRun("New page")] })
```

### Table of Contents

```javascript
// Key: headings must use HeadingLevel only - no custom styles
new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" })
```

### Headers/Footers

```javascript
sections: [{
  properties: {
    page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } // 1440 = 1 inch
  },
  headers: {
    default: new Header({ children: [new Paragraph({ children: [new TextRun("Header")] })] })
  },
  footers: {
    default: new Footer({ children: [new Paragraph({
      children: [new TextRun("Page "), new TextRun({ children: [PageNumber.CURRENT] })]
    })] })
  },
  children: [/* content */]
}]
```

### Key docx-js Rules

- **Set the page size explicitly** - docx-js defaults to A4; use US Letter for US documents (12240 x 15840 DXA)
- **Landscape: pass portrait dimensions** - docx-js swaps width/height internally; pass the short edge as `width` and the long edge as `height`, and set `orientation: PageOrientation.LANDSCAPE`
- **Never use `\n`** - use separate Paragraph elements
- **Never use Unicode symbols** - use `LevelFormat.BULLET` with a numbering config
- **PageBreak must be inside a Paragraph** - using it standalone creates invalid XML
- **ImageRun needs `type`** - always specify png/jpg etc.
- **Always set the table `width` with DXA** - never use `WidthType.PERCENTAGE` (breaks in Google Docs)
- **Tables need a double width** - the `columnWidths` array and the cell `width`, and both must match
- **Table width = sum of columnWidths** - for DXA, make sure they add up exactly
- **Always add cell margins** - use `margins: { top: 80, bottom: 80, left: 120, right: 120 }` for readable padding
- **Use `ShadingType.CLEAR`** - never use SOLID for table shading
- **The table of contents needs HeadingLevel only** - no custom styles for heading paragraphs
- **Override the built-in styles** - use the exact IDs: "Heading1", "Heading2", etc.
- **Include `outlineLevel`** - required for the table of contents (0 for H1, 1 for H2, and so on)

---

## Editing an Existing Document

**Carry out the following 3 steps in order.**

### Step 1: Unzip
```bash
python scripts/office/unpack.py document.docx unpacked/
```
Extract the XML, pretty-print it, merge adjacent runs, and convert smart quotes to XML entities (`&#x201C;` etc.) so that they are preserved during editing. Use `--merge-runs false` to skip run merging.

### Step 2: Edit the XML

Edit the files under `unpacked/word/`. See the XML reference below for the relevant patterns.

**Use "Claude" as the author** when adding revisions and comments, unless the user explicitly asks for another name.

**Use the Edit tool for string replacements directly. Do not write Python scripts.** Scripts introduce unnecessary complexity. The Edit tool shows exactly what is being replaced.

**Key: use smart quotes for new content.** When adding text that contains apostrophes or quotation marks, use XML entities to produce smart quotes:
```xml
<!-- Use these entities to produce professional typography -->
<w:t>Here&#x2019;s a quote: &#x201C;Hello&#x201D;</w:t>
```
| Entity | Character |
|------|------|
| `&#x2018;` | ' (left single quote) |
| `&#x2019;` | ' (right single quote / apostrophe) |
| `&#x201C;` | " (left double quote) |
| `&#x201D;` | " (right double quote) |

**Adding comments:** use `comment.py` for the boilerplate that spans multiple XML files (the text must be pre-escaped XML):
```bash
python scripts/comment.py unpacked/ 0 "Comment text with &amp; and &#x2019;"
python scripts/comment.py unpacked/ 1 "Reply text" --parent 0  # reply to comment 0
python scripts/comment.py unpacked/ 0 "Text" --author "Custom Author"  # custom author name
```
Then add the markup in document.xml (see the comments section of the XML reference).

### Step 3: Pack
```bash
python scripts/office/pack.py unpacked/ output.docx --original document.docx
```
Validate and auto-fix, compress the XML, then create the DOCX. Use `--validate false` to skip validation.

**Problems that auto-fix can repair:**
- `durableId` >= 0x7FFFFFFF (regenerate a valid ID)
- Missing `xml:space="preserve"` on `<w:t>` (when there is whitespace)

**Problems that auto-fix cannot repair:**
- Malformed XML, invalid element nesting, missing relationships, schema violations

### Common Pitfalls

- **Replacing an entire `<w:r>` element**: when adding a revision, replace the whole `<w:r>...</w:r>` block with `<w:del>...<w:ins>...` as sibling elements. Do not inject revision tags inside a run.
- **Preserve `<w:rPr>` formatting**: copy the original run `<w:rPr>` block into the revision run to keep bold, font size and other formatting.

---

## XML Reference

### Schema Compliance

- **Element order inside `<w:pPr>`**: `<w:pStyle>`, `<w:numPr>`, `<w:spacing>`, `<w:ind>`, `<w:jc>`, with `<w:rPr>` last
- **Whitespace**: add `xml:space="preserve"` on `<w:t>` elements that contain leading/trailing spaces
- **RSIDs**: must be 8-digit hexadecimal numbers (for example `00AB1234`)

### Revisions

**Insertions:**
```xml
<w:ins w:id="1" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:t>inserted text</w:t></w:r>
</w:ins>
```

**Deletions:**
```xml
<w:del w:id="2" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:delText>deleted text</w:delText></w:r>
</w:del>
```

**Inside `<w:del>`**: use `<w:delText>` instead of `<w:t>`, and `<w:delInstrText>` instead of `<w:instrText>`.

**Minimal edits** - mark only the changed part:
```xml
<!-- Change "30 days" to "60 days" -->
<w:r><w:t>The term is </w:t></w:r>
<w:del w:id="1" w:author="Claude" w:date="...">
  <w:r><w:delText>30</w:delText></w:r>
</w:del>
<w:ins w:id="2" w:author="Claude" w:date="...">
  <w:r><w:t>60</w:t></w:r>
</w:ins>
<w:r><w:t> days.</w:t></w:r>
```

**Deleting an entire paragraph/list item** - when you delete all the content of a paragraph, you must also mark the paragraph mark as deleted so that it merges with the next paragraph. Add `<w:del/>` inside `<w:pPr><w:rPr>`:
```xml
<w:p>
  <w:pPr>
    <w:numPr>...</w:numPr>  <!-- list numbering (if present) -->
    <w:rPr>
      <w:del w:id="1" w:author="Claude" w:date="2025-01-01T00:00:00Z"/>
    </w:rPr>
  </w:pPr>
  <w:del w:id="2" w:author="Claude" w:date="2025-01-01T00:00:00Z">
    <w:r><w:delText>Entire paragraph content being deleted...</w:delText></w:r>
  </w:del>
</w:p>
```
Without `<w:del/>` inside `<w:pPr><w:rPr>`, accepting the revision leaves an empty paragraph/list item behind.

**Rejecting another author's insertion** - nest the deletion inside their insertion:
```xml
<w:ins w:author="Jane" w:id="5">
  <w:del w:author="Claude" w:id="10">
    <w:r><w:delText>their inserted text</w:delText></w:r>
  </w:del>
</w:ins>
```

**Restoring another author's deletion** - add an insertion after it (without modifying their deletion markup):
```xml
<w:del w:author="Jane" w:id="5">
  <w:r><w:delText>deleted text</w:delText></w:r>
</w:del>
<w:ins w:author="Claude" w:id="10">
  <w:r><w:t>deleted text</w:t></w:r>
</w:ins>
```

### Comments

After running `comment.py` (see Step 2), add the markup in document.xml. For replies, use the `--parent` flag and nest the markup inside the parent comment.

**Key: `<w:commentRangeStart>` and `<w:commentRangeEnd>` are siblings of `<w:r>`, never inside `<w:r>`.**

```xml
<!-- Comment markup is a direct child of w:p, never inside w:r -->
<w:commentRangeStart w:id="0"/>
<w:del w:id="1" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:delText>deleted</w:delText></w:r>
</w:del>
<w:r><w:t> more text</w:t></w:r>
<w:commentRangeEnd w:id="0"/>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>

<!-- Comment 0 and its nested reply 1 -->
<w:commentRangeStart w:id="0"/>
  <w:commentRangeStart w:id="1"/>
  <w:r><w:t>text</w:t></w:r>
  <w:commentRangeEnd w:id="1"/>
<w:commentRangeEnd w:id="0"/>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="1"/></w:r>
```

### Images

1. Add the image file to `word/media/`
2. Add the relationship in `word/_rels/document.xml.rels`:
```xml
<Relationship Id="rId5" Type=".../image" Target="media/image1.png"/>
```
3. Add the content type in `[Content_Types].xml`:
```xml
<Default Extension="png" ContentType="image/png"/>
```
4. Reference it in document.xml:
```xml
<w:drawing>
  <wp:inline>
    <wp:extent cx="914400" cy="914400"/>  <!-- EMU units: 914400 = 1 inch -->
    <a:graphic>
      <a:graphicData uri=".../picture">
        <pic:pic>
          <pic:blipFill><a:blip r:embed="rId5"/></pic:blipFill>
        </pic:pic>
      </a:graphicData>
    </a:graphic>
  </wp:inline>
</w:drawing>
```
