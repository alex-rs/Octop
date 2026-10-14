---
name: xlsx
description: "Use this skill when a spreadsheet file is the main input or output. This means the user wants to: open, read, edit or repair an existing .xlsx, .xlsm, .csv or .tsv file (for example adding columns, computing formulas, formatting, charting, cleaning up messy data); create a new spreadsheet from scratch or from another data source; or convert between spreadsheet file formats. It is triggered in particular when the user refers to a spreadsheet file by name or path - even in passing (such as \"the xlsx in my Downloads folder\") - and wants to work on it or generate content from it. It also applies to cleaning up or restructuring messy tabular data files (malformed rows, misaligned headers, junk data) into well-formed spreadsheets. The deliverable must be a spreadsheet file. Do not trigger it when the main deliverable is a Word document, an HTML report, a standalone Python script, a database pipeline or a Google Sheets API integration, even if tabular data is involved."
license: Proprietary. LICENSE.txt has complete terms
metadata:
  builtin_skill_version: "1.1"
  octop:
    emoji: "📊"
    label:
      zh: "Spreadsheets"
      en: "Spreadsheets"
    summary:
      zh: "Create, read, edit or clean .xlsx, .csv and related spreadsheets."
      en: "Create, read, edit, or clean .xlsx, .csv, and related spreadsheets."
---

> **Important:** All `scripts/` paths are relative to this skill directory.
> How to run: `cd {this_skill_dir} && python scripts/...`
> Or use the `cwd` parameter of `execute_shell_command`.

# Output Requirements

## All Excel Files

### Professional Fonts
- Unless the user instructs otherwise, all deliverables should use a consistent professional font (such as Arial or Times New Roman)

### Zero Formula Errors
- Every Excel model must be delivered with zero formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?)

### Preserve Existing Templates (When Updating a Template)
- When modifying a file, study the existing formatting, styles and conventions closely and match them exactly
- Never impose standardized formatting on files that already have an established pattern
- Existing template conventions always take precedence over this guide

## Financial Models

### Color Coding Standards
Unless the user or an existing template specifies otherwise

#### Industry-standard Color Conventions
- **Blue text (RGB: 0,0,255)**: hard-coded inputs, and numbers the user will change for different scenarios
- **Black text (RGB: 0,0,0)**: all formulas and calculations
- **Green text (RGB: 0,128,0)**: links pulled from other sheets in the same workbook
- **Red text (RGB: 255,0,0)**: external links to other files
- **Yellow background (RGB: 255,255,0)**: key assumptions that need attention, or cells that need updating

### Number Format Standards

#### Required Formatting Rules
- **Years**: format them as text strings (for example "2024" rather than "2,024")
- **Currency**: use the $#,##0 format; always state the unit in the header ("Revenue ($mm)")
- **Zero values**: use a number format that displays all zero values as "-", including percentages (for example "$#,##0;($#,##0);-")
- **Percentages**: use the 0.0% format by default (one decimal place)
- **Multiples**: use the 0.0x format for valuation multiples (EV/EBITDA, P/E)
- **Negative numbers**: use parentheses (123) rather than a minus sign -123

### Formula Construction Rules

#### Placing Assumptions
- Put all assumptions (growth rates, margins, multiples and so on) in separate assumption cells
- Use cell references in formulas rather than hard-coded values
- Example: use =B5*(1+$B$6) rather than =B5*1.05

#### Preventing Formula Errors
- Verify that all cell references are correct
- Check for offset errors in ranges
- Make sure formulas are consistent across all forecast periods
- Test edge cases (zero values, negative numbers)
- Verify there are no unintended circular references

#### Documentation Requirements for Hard-coded Values
- Add a note in a comment or in the adjacent cell (if at the end of the table). Format: "Source: [system/document], [date], [specific reference], [URL (if applicable)]"
- Example:
  - "Source: Company 10-K, FY2024, Page 45, Revenue Note, [SEC EDGAR URL]"
  - "Source: Company 10-Q, Q2 2025, Exhibit 99.1, [SEC EDGAR URL]"
  - "Source: Bloomberg Terminal, 8/15/2025, AAPL US Equity"
  - "Source: FactSet, 8/20/2025, Consensus Estimates Screen"

# XLSX Creation, Editing and Analysis

## Overview

The user may ask you to create, edit or analyze the content of a .xlsx file. You have different tools and workflows for different tasks.

## Prerequisites

- **openpyxl**: Excel file creation and editing
- **pandas**: data analysis and batch operations
- **LibreOffice** (`soffice`): formula recalculation via `scripts/recalc.py`
- `git` is optional, but it improves the redline diff output in the validation workflow.
- On Windows the dependencies must already be installed and available on `PATH`; if they are missing, report the dependency problem and stop (do not retry repeatedly).

## Important Requirements

**Formula recalculation requires LibreOffice**: use `scripts/recalc.py` to recalculate formula values. On its first run the script configures LibreOffice automatically and handles sandboxed environments with restricted Unix sockets (via `scripts/office/soffice.py`).

## Reading and Analyzing Data

### Data Analysis with pandas
For data analysis, visualization and basic operations, use the powerful data manipulation features provided by **pandas**:

```python
import pandas as pd

# Read Excel
df = pd.read_excel('file.xlsx')  # Default: first sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # All sheets as dict

# Analyze the data
df.head()      # Preview data
df.info()      # Column info
df.describe()  # Statistics

# Write Excel
df.to_excel('output.xlsx', index=False)
```

## Excel File Workflows

## Key requirement: use formulas, not hard-coded values

**Always use Excel formulas instead of computing values in Python and hard-coding them.** This keeps the spreadsheet dynamic and updatable.

### Wrong - hard-coded computed values
```python
# Wrong: computing in Python and hard-coding the result
total = df['Sales'].sum()
sheet['B10'] = total  # Hardcodes 5000

# Wrong: computing the growth rate in Python
growth = (df.iloc[-1]['Revenue'] - df.iloc[0]['Revenue']) / df.iloc[0]['Revenue']
sheet['C5'] = growth  # Hardcodes 0.15

# Wrong: computing the average in Python
avg = sum(values) / len(values)
sheet['D20'] = avg  # Hardcodes 42.5
```

### Right - use Excel formulas
```python
# Right: let Excel compute the sum itself
sheet['B10'] = '=SUM(B2:B9)'

# Right: write the growth rate as an Excel formula
sheet['C5'] = '=(C4-C2)/C2'

# Right: use an Excel function to compute the average
sheet['D20'] = '=AVERAGE(D2:D19)'
```

This applies to every calculation - totals, percentages, ratios, differences and so on. The spreadsheet should recalculate when the source data changes.

## General Workflow
1. **Choose the tool**: pandas for data processing, openpyxl for formulas/formatting
2. **Create/load**: create a new workbook or load an existing file
3. **Modify**: add/edit data, formulas and formatting
4. **Save**: write the file
5. **Recalculate formulas (required when formulas are used)**: use the scripts/recalc.py script
   ```bash
   python scripts/recalc.py output.xlsx
   ```
6. **Verify and fix any errors**:
   - The script returns JSON containing the error details
   - If `status` is `errors_found`, check `error_summary` for the specific error types and locations
   - Fix the identified errors and recalculate again
   - Common errors to fix:
     - `#REF!`: invalid cell reference
     - `#DIV/0!`: division by zero
     - `#VALUE!`: wrong data type in a formula
     - `#NAME?`: unrecognized formula name

### Creating a New Excel File

```python
# Use openpyxl for formulas and formatting
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# Add data
sheet['A1'] = 'Hello'
sheet['B1'] = 'World'
sheet.append(['Row', 'of', 'data'])

# Add formulas
sheet['B2'] = '=SUM(A1:A10)'

# Set the formatting
sheet['A1'].font = Font(bold=True, color='FF0000')
sheet['A1'].fill = PatternFill('solid', start_color='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')

# Column widths
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

### Editing an Existing Excel File

```python
# Use openpyxl to preserve formulas and formatting
from openpyxl import load_workbook

# Load the existing file
wb = load_workbook('existing.xlsx')
sheet = wb.active  # or wb['SheetName'] for specific sheet

# Process multiple worksheets
for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]
    print(f"Sheet: {sheet_name}")

# Modify cells
sheet['A1'] = 'New Value'
sheet.insert_rows(2)  # Insert row at position 2
sheet.delete_cols(3)  # Delete column 3

# Add a new worksheet
new_sheet = wb.create_sheet('NewSheet')
new_sheet['A1'] = 'Data'

wb.save('modified.xlsx')
```

## Recalculating Formulas

Excel files created or modified through openpyxl contain formula strings but no calculated values. Use the provided `scripts/recalc.py` script to recalculate formula values:

```bash
python scripts/recalc.py <excel_file> [timeout_seconds]
```

Example:
```bash
python scripts/recalc.py output.xlsx 30
```

The script:
- Sets up the LibreOffice macro automatically on the first run
- Recalculates all formulas in all worksheets
- Scans every cell for Excel errors (#REF!, #DIV/0! and so on)
- Returns JSON containing detailed error locations and counts
- Works on Linux, macOS and Windows

## Formula Validation Checklist

Quick checks to make sure formulas work correctly:

### Basic Validation
- [ ] **Test 2-3 sample references**: verify that they fetch the correct values before building the full model
- [ ] **Column mapping**: confirm the Excel columns match (for example column 64 = BL, not BK)
- [ ] **Row offsets**: remember that Excel rows are indexed from 1 (DataFrame row 5 = Excel row 6)

### Common Pitfalls
- [ ] **NaN handling**: use `pd.notna()` to check for null values
- [ ] **Far-right columns**: fiscal-year data is often in column 50+
- [ ] **Multiple matches**: search all occurrences, not just the first one
- [ ] **Division by zero**: check the denominator before using `/` in a formula (#DIV/0!)
- [ ] **Wrong references**: verify that all cell references point to the intended cells (#REF!)
- [ ] **Cross-worksheet references**: use the correct format (Sheet1!A1) to link worksheets

### Formula Testing Strategy
- [ ] **Start small**: test the formula on 2-3 cells before applying it broadly
- [ ] **Verify dependencies**: check that all cells referenced in the formula exist
- [ ] **Test edge cases**: include zero values, negative values and extremely large values

### Interpreting scripts/recalc.py Output
The script returns JSON containing the error details:
```json
{
  "status": "success",           // or "errors_found"
  "total_errors": 0,              // Total error count
  "total_formulas": 42,           // Number of formulas in file
  "error_summary": {              // Only present if errors found
    "#REF!": {
      "count": 2,
      "locations": ["Sheet1!B5", "Sheet1!C10"]
    }
  }
}
```

## Best Practices

### Choosing a Library
- **pandas**: best for data analysis, batch operations and simple data exports
- **openpyxl**: best for complex formatting, formulas and Excel-specific features

### Using openpyxl
- Cell indices start at 1 (row=1, column=1 refers to cell A1)
- Read calculated values with `data_only=True`: `load_workbook('file.xlsx', data_only=True)`
- **Warning**: if you open and save with `data_only=True`, formulas are replaced by values and permanently lost
- For large files: use `read_only=True` when reading and `write_only=True` when writing
- Formulas are preserved but not calculated - use scripts/recalc.py to update the values

### Using pandas
- Specify data types to avoid inference problems: `pd.read_excel('file.xlsx', dtype={'id': str})`
- For large files, read specific columns: `pd.read_excel('file.xlsx', usecols=['A', 'C', 'E'])`
- Handle dates correctly: `pd.read_excel('file.xlsx', parse_dates=['date_column'])`

## Code Style Guide
**Important**: when generating Python code for Excel operations:
- Write concise Python code without adding unnecessary comments
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

**For the Excel file itself**:
- Add comments to cells that contain complex formulas or important assumptions
- Document the data source of hard-coded values
- Add explanations for key calculations and model sections
