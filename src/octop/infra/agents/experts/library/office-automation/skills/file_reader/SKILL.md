---
name: file_reader
description: "Only for reading and summarizing text-type files. For text formats prefer read_file; use execute_shell_command when you need to probe the file type. PDFs, Office files, images and archives are handled by other skills."
metadata:
  builtin_skill_version: "1.2"
  qwenpaw:
    emoji: "📄"
    requires: {}
  octop:
    emoji: "📖"
    label:
      zh: "File Reader"
      en: "File Reader"
    summary:
      zh: "Read and summarize local text files; does not handle PDF or Office."
      en: "Read and summarize local text files, not PDF or Office."
---
# File Reader Toolkit

Use this skill when the user asks you to read or summarize local text files. PDFs, Office documents, images, audio and video are outside this skill's scope and should be handled by their dedicated skills/tools.

## Quick Type Check

Probe the type before reading:

```bash
file -b --mime-type "/path/to/file"
```

If the file is large, avoid printing the whole content; extract a small relevant portion and summarize it.

## Text Files (use read_file)

Applies to: `.txt`, `.md`, `.json`, `.yaml/.yml`, `.csv/.tsv`, `.log`, `.sql`, `ini`, `toml`, `py`, `js`, `html`, `xml` source code.

Steps:

1. Use `read_file` to get the content.
2. Summarize the key parts or show the relevant excerpt the user asked for.
3. For JSON/YAML, list the top-level keys and the important fields.
4. For CSV/TSV, show the header row and the first few rows, then summarize each column.

## Large Log Files

If the file is very large, use a tail window:

```bash
tail -n 200 "/path/to/file.log"
```

Summarize the most recent errors/warnings and any notable patterns.

## Out of Scope

The following are not handled by this skill (other skills cover them):

- PDF
- Office (docx/xlsx/pptx)
- Images
- Audio/video

## Safety and Behavior Rules

- Never execute untrusted files.
- Prefer reading only the smallest portion you need.
- If a required tool is missing, explain the limitation and ask the user for another format.
