# Scenario Index - Maintenance Document

> **This document is for human maintainers**, describing the design rationale, maintenance process and statistics of the scenario index.
> AI does not need to read this file. The AI routing table is in `references/00-scenario-index.md`.

---

## Design Architecture

### Overall Positioning

`00-scenario-index.md` is the **Tier 2 routing table** of SKILL.md:

```
SKILL.md (Tier 1: 10 core scenarios, 80% coverage)
  ↓ no match
00-scenario-index.md (Tier 2: 60+ extended scenarios, 20% long tail)
  ↓ match found
commands/*.md or references/*.md (concrete execution)
```

### AI Usage Flow

```
User describes a problem
  ↓
1. Match a scenario in the index (keyword search, ~10 seconds)
  ↓
2. Run Quick Mode according to the recommended Reference (10 seconds)
   → Use the command variant matching the current OS
  ↓
3. If Quick Mode finds anomalies → run Deep Mode (20-60 seconds)
   → The Commands files contain complete platform command tables for reference
  ↓
4. Report results + remediation recommendations
```

### Matching Rules

- **Keyword trigger**: the keyword the user says → look up the corresponding scenario
- **Chinese and English**: the Chinese words meaning "slow" and "lag" map to "slow" and "lag"
- **Fuzzy matching**: "not enough memory" → "memory problem"
- **Default fallback**: no match → scenario 3.1 (comprehensive health check)

---

## AI Decision Algorithm (Pseudocode)

The following is a conceptual description of the AI scenario matching and execution flow, used to understand the design intent:

```python
def match_scenario(user_query):
    """Match a scenario based on the user query"""
    keywords = extract_keywords(user_query)
    
    # 1. Exact match
    for keyword in keywords:
        if scenario := exact_match(keyword):
            return scenario
    
    # 2. Fuzzy match
    for keyword in keywords:
        if scenario := fuzzy_match(keyword):
            return scenario
    
    # 3. Default scenario (comprehensive health check)
    return scenario_3_1

def execute_scenario(scenario, user_query):
    """Execute the scenario's recommended path"""
    path = scenario.recommended_path
    
    # Step 1: Quick Mode
    if "reference" in path.step1:
        quick_result = run_quick_mode(path.step1)
    
    # Step 2: Decide whether to run Deep
    if should_run_deep(quick_result, user_query):
        deep_result = run_deep_mode(path.step2, quick_result.focus)
        return generate_report(quick_result, deep_result)
    else:
        return generate_report(quick_result)

def should_run_deep(quick_result, user_query):
    """Decide whether to run Deep Mode"""
    if quick_result.has_critical():
        return True  # auto-trigger
    elif quick_result.has_warning():
        if "troubleshoot" in user_query or "slow" in user_query:
            return True  # auto-trigger
        else:
            return ask_user("anomaly found, run an in-depth analysis?")
    return False  # Deep not needed
```

---

## Usage Examples

### Example 1: The user says "the server is very slow"

```
AI decision flow:
1. Search the index for "slow" → matches scenario 1.1
2. Review the recommended path:
   - Step 1: resource-saturation-quick.md
3. Run Quick Mode (10 seconds)
4. Quick result: Memory WARNING
5. Trigger Deep Mode: resource-saturation-deep-memory.md (20 seconds)
6. Deep result: Java memory leak
7. Generate report + remediation recommendations
```

### Example 2: The user says "the disk is broken"

```
AI decision flow:
1. Search the index for "disk broken" → matches scenario 5.2
2. Review the recommended path:
   - Step 1: disk-smart-quick.md
3. Quick result: SMART CRITICAL
4. Trigger Deep Mode: disk-smart-deep.md
5. Deep result: Reallocated sectors 100+
6. Report: the disk is about to fail, back up immediately
```

### Example 3: The user says "check system health"

```
AI decision flow:
1. Search the index for "health check" → matches scenario 3.1
2. Review the recommended path:
   - Step 1: run 3 Quick checks
   - resource-saturation-quick.md
   - system-logs-quick.md
   - disk-smart-quick.md
3. All OK → report normal
4. If there are anomalies → trigger the corresponding Deep Mode
```

---

## Statistics

### Coverage
- **Total scenarios**: 20 major categories + 60+ detailed scenarios
- **Commands coverage**: 126 files
- **References coverage**: 5 core diagnostic modules
- **Estimated coverage**: 95%+ of common user problems

### Scenario Distribution
- **High-frequency scenarios** (⭐⭐⭐⭐⭐): 6 categories, 20 scenarios → 80% of user problems
- **Medium-frequency scenarios** (⭐⭐⭐⭐): 4 categories, 15 scenarios → 15% of user problems
- **Low-frequency scenarios** (⭐⭐⭐): 10 categories, 25+ scenarios → 5% of user problems

### Expected Results
- **Matching accuracy**: 90%+
- **First response time**: 10 seconds (Quick Mode)
- **Full diagnostic time**: 30-70 seconds (Quick + Deep)
- **Token savings**: 70-80%

---

## Maintenance Guide

### Update Frequency
- **High-frequency scenarios**: check once a month
- **Medium- and low-frequency scenarios**: check once a quarter
- **New Command/Reference**: update the index immediately

### Update Process
1. Identify the new scenario or Command
2. Analyze user keywords
3. Determine the priority (⭐⭐⭐⭐⭐ / ⭐⭐⭐⭐ / ⭐⭐⭐)
4. Add it to the corresponding category
5. Update the quick lookup table
6. Test the AI matching accuracy

### File Structure Notes

```
references/
  00-scenario-index.md          ← AI routing table (condensed, scenario matching info only)
  resource-saturation-*.md      ← resource saturation diagnostic module
  system-logs-*.md              ← system log diagnostic module
  disk-smart-*.md               ← disk SMART diagnostic module
  hardware-other.md             ← hardware health diagnostic module
  time-sync.md                  ← time synchronization diagnostic module

docs/
  architecture.md               ← system architecture design document
  scenario-decision-guide.md    ← extended scenario decision guide
  scenario-index-maintenance.md ← this file (maintenance document)
```

---

## Version History

| Version | Date | Change |
|------|------|------|
| 1.0 | 2026-03-24 | Initial version, complete scenario index |
| 2.0 | 2026-03-24 | Condensed into the AI routing table (~420 lines), human maintenance doc split out to docs/ |

---

**Maintainer**: AI Assistant
**Status**: production ready
