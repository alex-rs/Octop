> **Important:** All `scripts/` paths are relative to the skill directory (the directory containing SKILL.md).
> How to run: `cd {this_skill_dir} && python scripts/...`
> Or use the `cwd` parameter of `execute_shell_command`.

**Critical: you must complete the following steps in order; do not skip them and start writing code directly.**

If you need to fill in a PDF form, first check whether the PDF has fillable form fields. Run the following script from the directory containing this file:
 `python scripts/check_fillable_fields <file.pdf>`, then go to the "Fillable fields" or "Non-fillable fields" section depending on the result, and follow the matching instructions.

# Fillable Fields
If the PDF has fillable form fields:
- Run the following script from the directory containing this file: `python scripts/extract_form_field_info.py <input.pdf> <field_info.json>`. It creates a JSON file containing a list of fields in the following format:
```
[
  {
    "field_id": (unique identifier of the field),
    "page": (page number, starting from 1),
    "rect": ([left, bottom, right, top] bounding box in PDF coordinates, y=0 at the bottom of the page),
    "type": ("text", "checkbox", "radio_group" or "choice"),
  },
  // Checkboxes have "checked_value" and "unchecked_value" properties:
  {
    "field_id": (unique identifier of the field),
    "page": (page number, starting from 1),
    "type": "checkbox",
    "checked_value": (set the field to this value to check the checkbox),
    "unchecked_value": (set the field to this value to uncheck the checkbox),
  },
  // Radio button groups have a "radio_options" list with the available choices.
  {
    "field_id": (unique identifier of the field),
    "page": (page number, starting from 1),
    "type": "radio_group",
    "radio_options": [
      {
        "value": (set the field to this value to select this radio option),
        "rect": (bounding box of the radio button for this option)
      },
      // other radio options
    ]
  },
  // Multiple-choice fields have a "choice_options" list with the available choices:
  {
    "field_id": (unique identifier of the field),
    "page": (page number, starting from 1),
    "type": "choice",
    "choice_options": [
      {
        "value": (set the field to this value to select this choice),
        "text": (display text of the choice)
      },
      // other choices
    ],
  }
]
```
- Use the following script to convert the PDF into PNG images (one per page; run it from the directory containing this file):
`python scripts/convert_pdf_to_images.py <file.pdf> <output_directory>`
Then analyze the images to determine the purpose of each form field (make sure to convert the PDF coordinates of the bounding boxes into image coordinates).
- Create a `field_values.json` file in the following format, containing the value to fill in for each field:
```
[
  {
    "field_id": "last_name", // must match the field_id output by `extract_form_field_info.py`
    "description": "The user's last name",
    "page": 1, // must match the "page" value in field_info.json
    "value": "Simpson"
  },
  {
    "field_id": "Checkbox12",
    "description": "Checkbox to be checked if the user is 18 or over",
    "page": 1,
    "value": "/On" // for a checkbox, use its "checked_value" value to check it. For a radio group, use one of the "value" values in "radio_options".
  },
  // more fields
]
```
- Run the `fill_fillable_fields.py` script from the directory containing this file to create the filled PDF:
`python scripts/fill_fillable_fields.py <input pdf> <field_values.json> <output pdf>`
This script validates the field IDs and values you provide; if it prints an error message, correct the relevant field and try again.

# Non-fillable Fields
If the PDF has no fillable form fields, you need to add text annotations. First try to extract coordinates from the PDF structure (more precise); if that does not work, fall back to visual estimation.

## Step 1: Try structural extraction first

Run this script to extract the text labels, lines and checkboxes together with their exact PDF coordinates:
`python scripts/extract_form_structure.py <input.pdf> form_structure.json`

This creates a JSON file containing:
- **labels**: every text element with its exact coordinates (x0, top, x1, bottom, in PDF points)
- **lines**: horizontal lines that define row boundaries
- **checkboxes**: small square rectangles that act as checkboxes (including center coordinates)
- **row_boundaries**: row top/bottom positions computed from the horizontal lines

**Check the result**: if `form_structure.json` contains meaningful labels (text elements that correspond to form fields), use **Method A: structure-based coordinates**. If the PDF is scanned/image-based with few or no labels, use **Method B: visual estimation**.

---

## Method A: Structure-based coordinates (preferred)

Use this method when `extract_form_structure.py` finds text labels in the PDF.

### A.1: Analyze the structure

Read form_structure.json and identify:

1. **Label groups**: adjacent text elements that make up a single label (for example "Last" + "Name")
2. **Row structure**: labels with similar `top` values are on the same row
3. **Field columns**: the input area starts where the label ends (x0 = label.x1 + spacing)
4. **Checkboxes**: use the checkbox coordinates from the structure directly

**Coordinate system**: PDF coordinates, y=0 at the top of the page, with y increasing downwards.

### A.2: Check for missing elements

Structural extraction may fail to detect all form elements. Common cases:
- **Circular checkboxes**: only square rectangles are detected as checkboxes
- **Complex graphics**: decorative elements or non-standard form controls
- **Faint or light-colored elements**: may not be extracted

If you see form fields in the PDF image that are not in form_structure.json, you need to use **visual analysis** for those specific fields (see the "Hybrid method" below).

### A.3: Create fields.json using PDF coordinates

For each field, compute the entry coordinates from the extracted structure:

**Text fields:**
- entry x0 = label x1 + 5 (a small gap after the label)
- entry x1 = the x0 of the next label, or the row boundary
- entry top = the same as the label top
- entry bottom = the row boundary line below, or label bottom + row height

**Checkboxes:**
- Use the checkbox rectangle coordinates from form_structure.json directly
- entry_bounding_box = [checkbox.x0, checkbox.top, checkbox.x1, checkbox.bottom]

Create fields.json using `pdf_width` and `pdf_height` (which denote PDF coordinates):
```json
{
  "pages": [
    {"page_number": 1, "pdf_width": 612, "pdf_height": 792}
  ],
  "form_fields": [
    {
      "page_number": 1,
      "description": "Last name entry field",
      "field_label": "Last Name",
      "label_bounding_box": [43, 63, 87, 73],
      "entry_bounding_box": [92, 63, 260, 79],
      "entry_text": {"text": "Smith", "font_size": 10}
    },
    {
      "page_number": 1,
      "description": "US Citizen Yes checkbox",
      "field_label": "Yes",
      "label_bounding_box": [260, 200, 280, 210],
      "entry_bounding_box": [285, 197, 292, 205],
      "entry_text": {"text": "X"}
    }
  ]
}
```

**Important**: use `pdf_width`/`pdf_height` together with coordinates taken directly from form_structure.json.

### A.4: Validate the bounding boxes

Before filling, check the bounding boxes for errors:
`python scripts/check_bounding_boxes.py fields.json`

This checks for intersecting bounding boxes and for entry boxes too small to fit the font size. Fix every reported error before filling.

---

## Method B: Visual estimation (fallback)

Use this method when the PDF is scanned/image-based and structural extraction found no usable text labels (for example when all text shows up as "(cid:X)" patterns).

### B.1: Convert the PDF into images

`python scripts/convert_pdf_to_images.py <input.pdf> <images_dir/>`

### B.2: Initial field identification

Inspect each page image to identify the form areas and get a **rough estimate** of the field positions:
- Form field labels and their approximate positions
- Entry areas (lines, boxes, or blank areas used for text input)
- Checkboxes and their approximate positions

For each field, note down the approximate pixel coordinates (high precision is not needed at this point).

### B.3: Zoom refinement (critical for accuracy)

For each field, crop the area around the estimated position to pin down the coordinates precisely.

**Create zoomed crops with ImageMagick:**
```bash
magick <page_image> -crop <width>x<height>+<x>+<y> +repage <crop_output.png>
```

Where:
- `<x>, <y>` = the top-left corner of the crop area (use the rough estimate minus the padding)
- `<width>, <height>` = the size of the crop area (the field area plus about 50 pixels of padding on each side)

**Example:** to refine a "Last Name" field estimated to be near (100, 150):
```bash
magick images_dir/page_1.png -crop 300x80+50+120 +repage crops/name_field.png
```

(Note: if the `magick` command is unavailable, try the `convert` command with the same arguments).

**Inspect the cropped image** to determine the exact coordinates:
1. Determine the exact pixel position where the entry area starts (after the label)
2. Determine where the entry area ends (before the next field or at the edge)
3. Determine the top and bottom of the entry row/box

**Convert the crop coordinates back to full-image coordinates:**
- full_x = crop_x + crop_offset_x
- full_y = crop_y + crop_offset_y

Example: if the crop starts at (50, 120) and the entry box starts at (52, 18) inside the crop:
- entry_x0 = 52 + 50 = 102
- entry_top = 18 + 120 = 138

**Repeat this process for each field**, grouping adjacent fields into a single crop wherever possible.

### B.4: Create fields.json using the exact coordinates

Create fields.json using `image_width` and `image_height` (which denote image coordinates):
```json
{
  "pages": [
    {"page_number": 1, "image_width": 1700, "image_height": 2200}
  ],
  "form_fields": [
    {
      "page_number": 1,
      "description": "Last name entry field",
      "field_label": "Last Name",
      "label_bounding_box": [120, 175, 242, 198],
      "entry_bounding_box": [255, 175, 720, 218],
      "entry_text": {"text": "Smith", "font_size": 10}
    }
  ]
}
```

**Important**: use `image_width`/`image_height` together with the exact pixel coordinates obtained from the zoom analysis.

### B.5: Validate the bounding boxes

Before filling, check the bounding boxes for errors:
`python scripts/check_bounding_boxes.py fields.json`

This checks for intersecting bounding boxes and for entry boxes too small to fit the font size. Fix every reported error before filling.

---

## Hybrid method: structure + visual

Use this method when structural extraction works for most fields but misses some elements (for example circular checkboxes or uncommon form controls).

1. **Use Method A** for the fields detected in form_structure.json
2. **Convert the PDF into images** to visually analyze the missing fields
3. **Use zoom refinement** (from Method B) for the missing fields
4. **Merge the coordinates**: for fields taken from structural extraction, use `pdf_width`/`pdf_height`. For visually estimated fields, you must convert image coordinates into PDF coordinates:
   - pdf_x = image_x * (pdf_width / image_width)
   - pdf_y = image_y * (pdf_height / image_height)
5. **Use a single coordinate system in fields.json** - convert all coordinates to PDF coordinates using `pdf_width`/`pdf_height`

---

## Step 2: Validate before filling

**Always validate the bounding boxes before filling:**
`python scripts/check_bounding_boxes.py fields.json`

This checks for:
- Intersecting bounding boxes (which cause text to overlap)
- Entry boxes that are too small for the specified font size

Fix every reported error in fields.json before continuing.

## Step 3: Fill in the form

The fill script detects the coordinate system automatically and handles the conversion:
`python scripts/fill_pdf_form_with_annotations.py <input.pdf> fields.json <output.pdf>`

## Step 4: Verify the output

Convert the filled PDF into images and verify the text positions:
`python scripts/convert_pdf_to_images.py <output.pdf> <verify_images/>`

If the text positions are incorrect:
- **Method A**: check that PDF coordinates from form_structure.json and `pdf_width`/`pdf_height` were used
- **Method B**: check that the image dimensions match and that the coordinates are exact pixel values
- **Hybrid method**: make sure the coordinate conversion is correct for the visually estimated fields
