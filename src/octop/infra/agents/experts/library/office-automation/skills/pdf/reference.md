# Advanced PDF Processing Reference

This document covers advanced PDF processing features, detailed examples and additional libraries that are not covered in the main skill description.

## pypdfium2 Library (Apache/BSD License)

### Overview
pypdfium2 is a Python binding to PDFium (Chromium's PDF library). It is well suited to fast PDF rendering and image generation, and can serve as a replacement for PyMuPDF.

### Rendering PDFs as Images
```python
import pypdfium2 as pdfium
from PIL import Image

# Load the PDF
pdf = pdfium.PdfDocument("document.pdf")

# Render the pages as images
page = pdf[0]  # the first page
bitmap = page.render(
    scale=2.0,  # higher resolution
    rotation=0  # no rotation
)

# Convert to a PIL Image
img = bitmap.to_pil()
img.save("page_1.png", "PNG")

# Process multiple pages
for i, page in enumerate(pdf):
    bitmap = page.render(scale=1.5)
    img = bitmap.to_pil()
    img.save(f"page_{i+1}.jpg", "JPEG", quality=90)
```

### Extracting Text with pypdfium2
```python
import pypdfium2 as pdfium

pdf = pdfium.PdfDocument("document.pdf")
for i, page in enumerate(pdf):
    text = page.get_text()
    print(f"Page {i+1} text length: {len(text)} chars")
```

## JavaScript Libraries

### pdf-lib (MIT License)

pdf-lib is a powerful JavaScript library that can create and modify PDF documents in any JavaScript environment.

#### Loading and Manipulating an Existing PDF
```javascript
import { PDFDocument } from 'pdf-lib';
import fs from 'fs';

async function manipulatePDF() {
    // Load the existing PDF
    const existingPdfBytes = fs.readFileSync('input.pdf');
    const pdfDoc = await PDFDocument.load(existingPdfBytes);

    // Get the page count
    const pageCount = pdfDoc.getPageCount();
    console.log(`Document has ${pageCount} pages`);

    // Add a new page
    const newPage = pdfDoc.addPage([600, 400]);
    newPage.drawText('Added by pdf-lib', {
        x: 100,
        y: 300,
        size: 16
    });

    // Save the modified PDF
    const pdfBytes = await pdfDoc.save();
    fs.writeFileSync('modified.pdf', pdfBytes);
}
```

#### Creating a Complex PDF from Scratch
```javascript
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import fs from 'fs';

async function createPDF() {
    const pdfDoc = await PDFDocument.create();

    // Add fonts
    const helveticaFont = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const helveticaBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);

    // Add a page
    const page = pdfDoc.addPage([595, 842]); // A4 size
    const { width, height } = page.getSize();

    // Add styled text
    page.drawText('Invoice #12345', {
        x: 50,
        y: height - 50,
        size: 18,
        font: helveticaBold,
        color: rgb(0.2, 0.2, 0.8)
    });

    // Add a rectangle (title background)
    page.drawRectangle({
        x: 40,
        y: height - 100,
        width: width - 80,
        height: 30,
        color: rgb(0.9, 0.9, 0.9)
    });

    // Add table-like content
    const items = [
        ['Item', 'Qty', 'Price', 'Total'],
        ['Widget', '2', '$50', '$100'],
        ['Gadget', '1', '$75', '$75']
    ];

    let yPos = height - 150;
    items.forEach(row => {
        let xPos = 50;
        row.forEach(cell => {
            page.drawText(cell, {
                x: xPos,
                y: yPos,
                size: 12,
                font: helveticaFont
            });
            xPos += 120;
        });
        yPos -= 25;
    });

    const pdfBytes = await pdfDoc.save();
    fs.writeFileSync('created.pdf', pdfBytes);
}
```

#### Advanced Merge and Split Operations
```javascript
import { PDFDocument } from 'pdf-lib';
import fs from 'fs';

async function mergePDFs() {
    // Create a new document
    const mergedPdf = await PDFDocument.create();

    // Load the source PDFs
    const pdf1Bytes = fs.readFileSync('doc1.pdf');
    const pdf2Bytes = fs.readFileSync('doc2.pdf');

    const pdf1 = await PDFDocument.load(pdf1Bytes);
    const pdf2 = await PDFDocument.load(pdf2Bytes);

    // Copy pages from the first PDF
    const pdf1Pages = await mergedPdf.copyPages(pdf1, pdf1.getPageIndices());
    pdf1Pages.forEach(page => mergedPdf.addPage(page));

    // Copy specific pages from the second PDF (pages 0, 2, 4)
    const pdf2Pages = await mergedPdf.copyPages(pdf2, [0, 2, 4]);
    pdf2Pages.forEach(page => mergedPdf.addPage(page));

    const mergedPdfBytes = await mergedPdf.save();
    fs.writeFileSync('merged.pdf', mergedPdfBytes);
}
```

### pdfjs-dist (Apache License)

PDF.js is Mozilla's JavaScript library for rendering PDFs in the browser.

#### Basic PDF Loading and Rendering
```javascript
import * as pdfjsLib from 'pdfjs-dist';

// Configure the worker (important for performance)
pdfjsLib.GlobalWorkerOptions.workerSrc = './pdf.worker.js';

async function renderPDF() {
    // Load the PDF
    const loadingTask = pdfjsLib.getDocument('document.pdf');
    const pdf = await loadingTask.promise;

    console.log(`Loaded PDF with ${pdf.numPages} pages`);

    // Get the first page
    const page = await pdf.getPage(1);
    const viewport = page.getViewport({ scale: 1.5 });

    // Render to the canvas
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
        canvasContext: context,
        viewport: viewport
    };

    await page.render(renderContext).promise;
    document.body.appendChild(canvas);
}
```

#### Extracting Text with Coordinates
```javascript
import * as pdfjsLib from 'pdfjs-dist';

async function extractText() {
    const loadingTask = pdfjsLib.getDocument('document.pdf');
    const pdf = await loadingTask.promise;

    let fullText = '';

    // Extract text from all pages
    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();

        const pageText = textContent.items
            .map(item => item.str)
            .join(' ');

        fullText += `\n--- Page ${i} ---\n${pageText}`;

        // Get text with coordinates for advanced processing
        const textWithCoords = textContent.items.map(item => ({
            text: item.str,
            x: item.transform[4],
            y: item.transform[5],
            width: item.width,
            height: item.height
        }));
    }

    console.log(fullText);
    return fullText;
}
```

#### Extracting Annotations and Forms
```javascript
import * as pdfjsLib from 'pdfjs-dist';

async function extractAnnotations() {
    const loadingTask = pdfjsLib.getDocument('annotated.pdf');
    const pdf = await loadingTask.promise;

    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const annotations = await page.getAnnotations();

        annotations.forEach(annotation => {
            console.log(`Annotation type: ${annotation.subtype}`);
            console.log(`Content: ${annotation.contents}`);
            console.log(`Coordinates: ${JSON.stringify(annotation.rect)}`);
        });
    }
}
```

## Advanced Command-line Operations

### poppler-utils Advanced Features

#### Extracting Text with Bounding-box Coordinates
```bash
# Extract text with bounding-box coordinates (critical for structured data)
pdftotext -bbox-layout document.pdf output.xml

# The XML output contains the exact coordinates of every text element
```

#### Advanced Image Conversion
```bash
# Convert to PNG images at a specified resolution
pdftoppm -png -r 300 document.pdf output_prefix

# Convert a specified page range at high resolution
pdftoppm -png -r 600 -f 1 -l 3 document.pdf high_res_pages

# Convert to JPEG at a specified quality
pdftoppm -jpeg -jpegopt quality=85 -r 200 document.pdf jpeg_output
```

#### Extracting Embedded Images
```bash
# Extract all embedded images with their metadata
pdfimages -j -p document.pdf page_images

# List image information without extracting
pdfimages -list document.pdf

# Extract images in their original format
pdfimages -all document.pdf images/img
```

### qpdf Advanced Features

#### Complex Page Operations
```bash
# Split a PDF into page groups
qpdf --split-pages=3 input.pdf output_group_%02d.pdf

# Extract specific pages by complex ranges
qpdf input.pdf --pages input.pdf 1,3-5,8,10-end -- extracted.pdf

# Merge specific pages from multiple PDFs
qpdf --empty --pages doc1.pdf 1-3 doc2.pdf 5-7 doc3.pdf 2,4 -- combined.pdf
```

#### PDF Optimization and Repair
```bash
# Optimize a PDF for the web (linearize it for streaming)
qpdf --linearize input.pdf optimized.pdf

# Remove unused objects and compress
qpdf --optimize-level=all input.pdf compressed.pdf

# Try to repair a damaged PDF structure
qpdf --check input.pdf
qpdf --fix-qdf damaged.pdf repaired.pdf

# Display the detailed PDF structure for debugging
qpdf --show-all-pages input.pdf > structure.txt
```

#### Advanced Encryption
```bash
# Add password protection with specific permissions
qpdf --encrypt user_pass owner_pass 256 --print=none --modify=none -- input.pdf encrypted.pdf

# Check the encryption status
qpdf --show-encryption encrypted.pdf

# Remove password protection (the password is required)
qpdf --password=secret123 --decrypt encrypted.pdf decrypted.pdf
```

## Advanced Python Techniques

### pdfplumber Advanced Features

#### Extracting Text with Exact Coordinates
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    page = pdf.pages[0]

    # Extract all text with coordinates
    chars = page.chars
    for char in chars[:10]:  # the first 10 characters
        print(f"Char: '{char['text']}' at x:{char['x0']:.1f} y:{char['y0']:.1f}")

    # Extract text by bounding box (left, top, right, bottom)
    bbox_text = page.within_bbox((100, 100, 400, 200)).extract_text()
```

#### Advanced Table Extraction with Custom Settings
```python
import pdfplumber
import pandas as pd

with pdfplumber.open("complex_table.pdf") as pdf:
    page = pdf.pages[0]

    # Extract tables from a complex layout with custom settings
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "intersection_tolerance": 15
    }
    tables = page.extract_tables(table_settings)

    # Visual debugging for table extraction
    img = page.to_image(resolution=150)
    img.save("debug_layout.png")
```

### reportlab Advanced Features

#### Creating Professional Reports with Tables
```python
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Sample data
data = [
    ['Product', 'Q1', 'Q2', 'Q3', 'Q4'],
    ['Widgets', '120', '135', '142', '158'],
    ['Gadgets', '85', '92', '98', '105']
]

# Create a PDF with a table
doc = SimpleDocTemplate("report.pdf")
elements = []

# Add a title
styles = getSampleStyleSheet()
title = Paragraph("Quarterly Sales Report", styles['Title'])
elements.append(title)

# Add a table with advanced styling
table = Table(data)
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 14),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))
elements.append(table)

doc.build(elements)
```

## Complex Workflows

### Extracting Graphics/Images from a PDF

#### Method 1: Use pdfimages (fastest)
```bash
# Extract all images at their original quality
pdfimages -all document.pdf images/img
```

#### Method 2: Use pypdfium2 + image processing
```python
import pypdfium2 as pdfium
from PIL import Image
import numpy as np

def extract_figures(pdf_path, output_dir):
    pdf = pdfium.PdfDocument(pdf_path)

    for page_num, page in enumerate(pdf):
        # Render the pages at high resolution
        bitmap = page.render(scale=3.0)
        img = bitmap.to_pil()

        # Convert to numpy for processing
        img_array = np.array(img)

        # Simple shape detection (non-white areas)
        mask = np.any(img_array != [255, 255, 255], axis=2)

        # Find contours and extract bounding boxes
        # (this is a simplified version - a real implementation needs more complex detection)

        # Save the detected shapes
        # ... the implementation depends on the specific requirement
```

### Batch PDF Processing with Error Handling
```python
import os
import glob
from pypdf import PdfReader, PdfWriter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_process_pdfs(input_dir, operation='merge'):
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))

    if operation == 'merge':
        writer = PdfWriter()
        for pdf_file in pdf_files:
            try:
                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    writer.add_page(page)
                logger.info(f"Processed: {pdf_file}")
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                continue

        with open("batch_merged.pdf", "wb") as output:
            writer.write(output)

    elif operation == 'extract_text':
        for pdf_file in pdf_files:
            try:
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()

                output_file = pdf_file.replace('.pdf', '.txt')
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                logger.info(f"Extracted text from: {pdf_file}")

            except Exception as e:
                logger.error(f"Failed to extract text from {pdf_file}: {e}")
                continue
```

### Advanced PDF Cropping
```python
from pypdf import PdfWriter, PdfReader

reader = PdfReader("input.pdf")
writer = PdfWriter()

# Crop the page (left, bottom, right, top, in points)
page = reader.pages[0]
page.mediabox.left = 50
page.mediabox.bottom = 50
page.mediabox.right = 550
page.mediabox.top = 750

writer.add_page(page)
with open("cropped.pdf", "wb") as output:
    writer.write(output)
```

## Performance Optimization Tips

### 1. Handling Large PDFs
- Use a streaming approach instead of loading the whole PDF into memory
- Use `qpdf --split-pages` to split large files
- Process page by page with pypdfium2

### 2. Text Extraction
- `pdftotext -bbox-layout` is the fastest way to extract plain text
- Use pdfplumber for structured data and tables
- For very large documents, avoid `pypdf.extract_text()`

### 3. Image Extraction
- `pdfimages` is much faster than rendering pages
- Use a low resolution for previews and a high resolution for the final output

### 4. Form Filling
- pdf-lib preserves form structure better than most alternatives
- Validate the form fields beforehand

### 5. Memory Management
```python
# Process the PDF in chunks
def process_large_pdf(pdf_path, chunk_size=10):
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    for start_idx in range(0, total_pages, chunk_size):
        end_idx = min(start_idx + chunk_size, total_pages)
        writer = PdfWriter()

        for i in range(start_idx, end_idx):
            writer.add_page(reader.pages[i])

        # Process the chunk
        with open(f"chunk_{start_idx//chunk_size}.pdf", "wb") as output:
            writer.write(output)
```

## Troubleshooting Common Issues

### Encrypted PDFs
```python
# Handle password-protected PDFs
from pypdf import PdfReader

try:
    reader = PdfReader("encrypted.pdf")
    if reader.is_encrypted:
        reader.decrypt("password")
except Exception as e:
    print(f"Failed to decrypt: {e}")
```

### Damaged PDFs
```bash
# Repair with qpdf
qpdf --check corrupted.pdf
qpdf --replace-input corrupted.pdf
```

### Text Extraction Issues
```python
# Fall back to OCR for scanned PDFs
import pytesseract
from pdf2image import convert_from_path

def extract_text_with_ocr(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for i, image in enumerate(images):
        text += pytesseract.image_to_string(image)
    return text
```

## License Information

- **pypdf**: BSD License
- **pdfplumber**: MIT License
- **pypdfium2**: Apache/BSD License
- **reportlab**: BSD License
- **poppler-utils**: GPL-2 License
- **qpdf**: Apache License
- **pdf-lib**: MIT License
- **pdfjs-dist**: Apache License
