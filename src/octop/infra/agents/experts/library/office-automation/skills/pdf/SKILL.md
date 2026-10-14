---
name: pdf
description: Use this skill when the user needs any operation on a PDF file. This includes reading or extracting text/tables from a PDF, merging multiple PDFs, splitting a PDF, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and running OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to generate a PDF, use this skill.
license: Proprietary. LICENSE.txt has complete terms
metadata:
  builtin_skill_version: "1.1"
  octop:
    emoji: "📄"
    label:
      zh: "PDF Tools"
      en: "PDF Tools"
    summary:
      zh: "Read, merge, split, fill forms, or run OCR on PDFs."
      en: "Read, merge, split, fill forms, or OCR PDFs."
---

> **Important:** All `scripts/` paths are relative to this skill directory.
> How to run: `cd {this_skill_dir} && python scripts/...`
> Or use the `cwd` parameter of `execute_shell_command`.

# PDF Processing Guide

## Prerequisites

- **pypdf**: core PDF read/write functionality
- **pdfplumber**: text and table extraction
- **reportlab**: PDF creation
- **pdftotext** (poppler-utils): command-line text extraction
- **pdftoppm** (poppler-utils): PDF to image conversion
- **qpdf**: PDF manipulation (merge, split, rotate, decrypt)

## Overview

This guide covers the basic PDF operations performed with Python libraries and command-line tools. For advanced features, JavaScript libraries, and detailed examples, see REFERENCE.md. If you need to fill in a PDF form, read FORMS.md and follow the instructions there.

## Quick Start

```python
from pypdf import PdfReader, PdfWriter

# Read the PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# Extract text
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Python Libraries

### pypdf - Basic Operations

#### Merging PDFs
```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

#### Splitting a PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### Extracting Metadata
```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Subject: {meta.subject}")
print(f"Creator: {meta.creator}")
```

#### Rotating Pages
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # rotate 90 degrees clockwise
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### pdfplumber - Text and Table Extraction

#### Extracting Text with Layout
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### Extracting Tables
```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Table {j+1} on page {i+1}:")
            for row in table:
                print(row)
```

#### Advanced Table Extraction
```python
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # check whether the table is empty
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# Merge all the tables
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

### reportlab - Creating PDFs

#### Basic PDF Creation
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("hello.pdf", pagesize=letter)
width, height = letter

# Add text
c.drawString(100, height - 100, "Hello World!")
c.drawString(100, height - 120, "This is a PDF created with reportlab")

# Add lines
c.line(100, height - 140, 400, height - 140)

# Save
c.save()
```

#### Creating Multi-page PDFs
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

# Add content
title = Paragraph("Report Title", styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

body = Paragraph("This is the body of the report. " * 20, styles['Normal'])
story.append(body)
story.append(PageBreak())

# Page 2
story.append(Paragraph("Page 2", styles['Heading1']))
story.append(Paragraph("Content for page 2", styles['Normal']))

# Build the PDF
doc.build(story)
```

#### Subscripts and Superscripts

**Important**: never use Unicode subscript/superscript characters (₀₁₂₃₄₅₆₇₈₉, ⁰¹²³⁴⁵⁶⁷⁸⁹) in ReportLab PDFs. The built-in fonts do not contain these glyphs, so they render as black boxes.

Instead, use ReportLab's XML markup tags inside Paragraph objects:
```python
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

# Subscript: use the <sub> tag
chemical = Paragraph("H<sub>2</sub>O", styles['Normal'])

# Superscript: use the <super> tag
squared = Paragraph("x<super>2</super> + y<super>2</super>", styles['Normal'])
```

For text drawn with canvas (not Paragraph objects), adjust the font size and position manually instead of using Unicode subscripts/superscripts.

## Command-line Tools

### pdftotext (poppler-utils)
```bash
# Extract text
pdftotext input.pdf output.txt

# Extract text preserving layout
pdftotext -layout input.pdf output.txt

# Extract specific pages
pdftotext -f 1 -l 5 input.pdf output.txt  # pages 1-5
```

### qpdf
```bash
# Merge PDFs
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# Split pages
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# Rotate pages
qpdf input.pdf output.pdf --rotate=+90:1  # rotate page 1 by 90 degrees

# Remove the password
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf
```

### pdftk (if available)
```bash
# Merge
pdftk file1.pdf file2.pdf cat output merged.pdf

# Split
pdftk input.pdf burst

# Rotate
pdftk input.pdf rotate 1east output rotated.pdf
```

## Common Tasks

### Extracting Text from a Scanned PDF
```python
# Requires: pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# Convert the PDF to images
images = convert_from_path('scanned.pdf')

# OCR each page
text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

### Adding a Watermark
```python
from pypdf import PdfReader, PdfWriter

# Create the watermark (or load an existing one)
watermark = PdfReader("watermark.pdf").pages[0]

# Apply it to all pages
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

### Extracting Images
```bash
# Using pdfimages (poppler-utils)
pdfimages -j input.pdf output_prefix

# This extracts all images as output_prefix-000.jpg, output_prefix-001.jpg, etc.
```

### Password Protection
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Add a password
writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## Quick Reference

| Task | Best tool | Command/code |
|------|----------|-----------|
| Merge PDFs | pypdf | `writer.add_page(page)` |
| Split a PDF | pypdf | one file per page |
| Extract text | pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| Create PDFs | reportlab | Canvas or Platypus |
| Merge from the command line | qpdf | `qpdf --empty --pages ...` |
| OCR a scanned PDF | pytesseract | convert to images first |
| Fill a PDF form | pdf-lib or pypdf (see FORMS.md) | see FORMS.md |

## Next Steps

- For advanced usage of pypdfium2, see REFERENCE.md
- For the JavaScript library (pdf-lib), see REFERENCE.md
- If you need to fill in a PDF form, follow the instructions in FORMS.md
- For troubleshooting guidance, see REFERENCE.md
