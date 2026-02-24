# HAZOP Worksheet Column Reference Guide

A detailed reference for every column in the HAZOP worksheet. Covers what each column means, where the data comes from (user input, P&ID extraction, LLM prompt, or knowledge base lookup), and the possible values.

---

## Data Flow Overview

```
P&ID PDF
  | Claude extracts (HAZOP_EXTRACTION_PROMPT)
  v
Equipment + Instruments + Safety Devices
  | User inputs analysis parameters
  v
Max Pressure Gas/Liquid + Liquid Inventory
  | User selects from 14-item checklist
  v
Deviations
  | Claude generates (CAUSES_GENERATION_PROMPT)
  v
Causes (TAG + failure mode)
  | User confirms via checkboxes
  v
Confirmed Causes
  | Claude generates (WORKSHEET_GENERATION_PROMPT with all knowledge base tables)
  v
Complete Worksheet Rows (all columns populated)
```

---

## Column-by-Column Breakdown

### 1. Scenario ID (`#`)

| Attribute | Detail |
|-----------|--------|
| **What it is** | Sequential identifier for each worksheet row |
| **Source** | LLM generates sequentially |
| **JSON field** | `number` |

**Format**: `{N}a` and `{N}b`, where:

- `1a` = Cause 1, PAF category
- `1b` = Cause 1, PD/LOR category
- `2a` = Cause 2, PAF category
- `2b` = Cause 2, PD/LOR category

Every cause produces **two rows** — one assessed under the PAF framework and one under PD/LOR. The `a`/`b` suffix distinguishes them.

---

### 2. Deviation

| Attribute | Detail |
|-----------|--------|
| **What it is** | The process parameter that deviates from normal operating conditions |
| **Source** | User selects from a predefined checklist on the Deviations page (`templates/deviations.html`) |
| **JSON field** | `deviation` |

**The list** (14 standard + custom):

| # | Deviation |
|---|-----------|
| 1 | High Pressure |
| 2 | Low Pressure |
| 3 | High Level |
| 4 | Low Level |
| 5 | High Temperature |
| 6 | Low Temperature |
| 7 | No/Low Flow |
| 8 | More/High Flow |
| 9 | Reverse/Misdirected Flow |
| 10 | Tube Leak |
| 11 | Composition/Contamination |
| 12 | Leaks (Corrosion/Erosion) |
| 13 | Human Factors |
| 14 | Previous Incidents/Learnings |
| 15 | Other (user types custom) |

**Current scope**: Only **High Pressure** is fully implemented with the complete consequence analysis pipeline (Table 4 PAF, PD/LOR mapping, CME rules). Other deviations can be selected for cause generation, but the worksheet generation logic is built for HP only.

**In the app**: User checks boxes on `/deviations` → saved to `session["selected_deviations"]` → passed to cause generation.

---

### 3. Cause

| Attribute | Detail |
|-----------|--------|
| **What it is** | A specific instrument failure that could lead to the deviation, always referencing a real instrument tag from the P&ID |
| **Source** | Two-step LLM process (extraction then generation) |
| **JSON field** | `cause` |

**Step 1 — P&ID Extraction** (`services/claude_service.py` → `extract_hazop_items()`):

Claude reads the uploaded P&ID PDF and extracts `instruments_causes[]` — every control valve (PCV, LCV, TCV, FCV, etc.) with:

| Field | Description |
|-------|-------------|
| `tag` | Instrument tag number |
| `type` | Valve type (e.g., Flow Control Valve) |
| `description` | What the instrument controls |
| `associated_equipment` | Which vessel/separator it belongs to |
| `position` | upstream or downstream |
| `line_service` | gas, liquid, or two-phase |

Safety devices are extracted separately — they are **never** causes, only mitigations.

**Step 2 — Cause Generation** (`services/prompt_templates.py` → `CAUSES_GENERATION_PROMPT`):

The prompt sends the extracted instruments + selected deviation to Claude, which generates plausible failure modes.

**Rules**:

- Only instruments actually on the P&ID (no inventing)
- Safety devices (PSV, PRV, check valves, ESD) = **never** causes
- Only 5 canonical failure modes:
  - `fails open`
  - `fails closed`
  - `spurious opening`
  - `spurious closure`
  - `erratic output`
- Max one cause per instrument per failure mode
- Must be physically plausible for the deviation

**Format**: `"TAG (description/service) failure_mode"`
**Example**: `"FCV-1010 (Gas outlet) fails closed"`

**In the app**: Generated causes shown on `/causes` as checkboxes (all checked by default) → user unchecks any to exclude → confirmed causes sent to worksheet generation.

---

### 4. Drawing/Ref

| Attribute | Detail |
|-----------|--------|
| **What it is** | The P&ID drawing number or reference document for traceability |
| **Source** | Automatic — the PDF filename uploaded by the user |
| **JSON field** | `drawing_ref` |

Captured at upload time → `session["pdf_filename"]` → passed as `{drawing_ref}` to the worksheet prompt → Claude echoes it in every row.

**Example**: If user uploads `DWG-4020-Rev3.pdf`, the drawing_ref = `"DWG-4020-Rev3.pdf"`.

---

### 5. Intermediate Consequence

| Attribute | Detail |
|-----------|--------|
| **What it is** | The immediate physical consequence of the cause — what happens to the equipment before considering fire/explosion/personnel impacts |
| **Source** | LLM generates based on a template in the prompt |
| **JSON field** | `intermediate_consequence` |

**Template** (from `WORKSHEET_GENERATION_PROMPT`):

```
"Potential increase in {equipment_tag} operating pressure from normal to
{max_pressure} PSIG (design pressure: {design_pressure} PSIG).
Pressure ratio: {ratio}x DP."
```

**What feeds into it**:

| Variable | Source |
|----------|--------|
| `equipment_tag` | Extracted `major_equipment` — the vessel/separator the instrument is associated with |
| `max_pressure` | **User input** — `max_pressure_gas` or `max_pressure_liquid` depending on `line_service` |
| `design_pressure` | Extracted from `major_equipment[].design_parameters` |
| `ratio` | Calculated: `max_pressure / design_pressure` |

**Example**: "Potential increase in MBD-1010 operating pressure from normal to 5000 PSIG (design pressure: 2120 PSIG). Pressure ratio: 2.36x DP."

---

### 6. Consequence Category

| Attribute | Detail |
|-----------|--------|
| **What it is** | Which consequence framework is used to assess this row |
| **Source** | LLM assigns — always one of two values |
| **JSON field** | `category` |

**Possible values**:

| Value | Full Name | Meaning |
|-------|-----------|---------|
| **PAF** | People, Assets, Facilities | Physical consequences: injuries, fatalities, equipment damage, fires, explosions |
| **PD/LOR** | Process Deviation / Loss of Revenue | Business consequences: production loss, downtime, environmental cleanup |

**How they differ in calculation**:

| Aspect | PAF | PD/LOR |
|--------|-----|--------|
| Consequence (C) lookup | Table 4 PAF matrix (pressure x hole size) | Financial loss estimation using Table 10 (SME/user input) |
| Can trigger PEC? | Yes (if Table 4 shows "PEC") | No |
| Typical C values | Higher (3-5, often PEC at high pressure) | Varies (1-5, based on estimated financial loss) |

> **Note on PD/LOR C in the app**: The current LLM prompt (`prompt_templates.py`) uses pressure-ratio bands as a **proxy** to auto-generate a PD/LOR C value. This works as a reasonable approximation for automated worksheet generation. However, per the HSE Risk Assessment standard, the true PD/LOR C is determined by the SME through financial loss estimation (see Section 12 for the correct method). In a formal HAZOP review, the SME should validate or override the app-generated PD/LOR C based on actual financial loss analysis.

**Row styling in the app**:
- PAF rows: Light blue background (`#D6EAF8`)
- PD/LOR rows: Light orange background (`#FDEBD0`)

---

### 7. Scenario Comments / Final Impacts

| Attribute | Detail |
|-----------|--------|
| **What it is** | Four structured bullet points describing the full impact scenario |
| **Source** | LLM generates using 4 specific templates from the prompt |
| **JSON field** | `scenario_comments` (array of 4 strings) |

**The 4 bullets**:

#### Bullet 1 — Pressure Statement
Always the same for both PAF and PD/LOR rows of the same cause:
```
"Maximum pressure to reach {max_pressure} PSIG; design pressure is {design_pressure} PSIG."
```

#### Bullet 2 — Structural Impact
Based on the pressure ratio (from Table 2):

| Ratio | Text |
|-------|------|
| <= 1.1x | "Within design limits. No structural concern." |
| > 1.1x to 1.5x | "Stresses approaching yield strength. Potential flange leak (1/4 inch hole)." |
| > 1.5x to 2x | "Stresses near yield strength. Potential large flange leak (3/4 inch hole)." |
| > 2x | "> 2x DP ({ratio}x): Stresses greater than yield strength, resulting in potential full-bore rupture." |

#### Bullet 3 — Fire/Explosion Potential
Based on event trees:

| Condition | Text |
|-----------|------|
| Gas + pressure >= 100 psi + confined | "Pressure >= 100 PSIG, confined/congested area: Potential Jet Fire and VCE." |
| Gas + pressure >= 100 psi + not confined | "Pressure >= 100 PSIG: Potential Jet Fire." |
| Gas + pressure < 100 psi | "Low pressure gas release. Potential flash fire." |
| Liquid | "Liquid release: Potential pool fire and environmental contamination." |
| No LOPC (ratio <= 1.1x) | "No LOPC expected. No fire/explosion concern." |

#### Bullet 4 — PEC/Personnel Impact
Based on consequence severity:

| Condition | Text |
|-----------|------|
| PEC | "PEC-1: Impacts to more than 14 personnel possible. Potential fatalities and major asset damage." |
| C=5 (no PEC) | "Potential major asset damage and significant production loss." |
| C=4 | "Potential significant asset damage and production loss." |
| C=3 | "Potential moderate asset damage and limited production impact." |
| C=2 | "Potential minor asset damage. Limited production impact." |
| C=1 | "Within design limits. Negligible consequence." |

---

### 8. PEC (Potentially Exposed Crowd)

| Attribute | Detail |
|-----------|--------|
| **What it is** | Flag indicating whether the scenario could affect more than 14 personnel |
| **Source** | Knowledge base lookup — Table 4 PAF matrix |
| **JSON field** | `pec` |

**Possible values**:

| Value | Meaning |
|-------|---------|
| `"YES"` | Table 4 PAF returned "PEC" for this pressure x hole size combination. Automatically sets C = 5. |
| `"—"` (dash) | No PEC. Consequence determined by the numeric value from Table 4. |

**When PEC triggers** (examples from Table 4):

| Max Pressure | PEC for hole sizes... |
|-------------|----------------------|
| 5000 PSIG | ALL hole sizes (even 1/8") |
| 3000 PSIG | 1/4" and above |
| 1000 PSIG | 1" and above |
| 150 PSIG | 6" only |

**Only applies to PAF rows.** PD/LOR rows never have PEC — they use a different consequence table.

---

### 9. Mitigation (CME Details)

| Attribute | Detail |
|-----------|--------|
| **What it is** | Bulleted list of safety barriers / protective measures that reduce the probability of the scenario |
| **Source** | LLM identifies from extracted `safety_devices[]` + hard-coded rules in the prompt |
| **JSON field** | `mitigation_bullets` (array of strings) |

**For High Pressure deviation, valid CMEs**:

| CME | What it does | Where it comes from |
|-----|-------------|---------------------|
| **PSV-XXXX** (Pressure Safety Valve) | Relieves excess pressure at set point | Extracted from P&ID `safety_devices[]` — must have PSV tag associated with same equipment |
| **PSHH-XXXX** (Pressure Switch High-High) | Initiates automatic shutdown on high-high pressure | Extracted from P&ID `safety_devices[]` |
| **Gas Detection** | Closes BSDV on confirmed gas release | Added automatically IF LOPC occurs (ratio > 1.1x) |
| **Deluge/TSE** (Thermal Safety Element) | Activated on confirmed fire/heat | Added automatically IF LOPC occurs (ratio > 1.1x) |

**What is NOT a CME** (explicitly excluded in prompt):

- Alarms (PAH, PAL, PAHH) — alarms notify operators but don't automatically mitigate
- Manual interventions — not automatic
- BDV (Blowdown Valve) — not automatic for HP

**Format example**:
```
- PSV-1010: Relieves excess pressure at set point
- PSHH-1010: Initiates shutdown on high-high pressure
- Gas Detection: Closes BSDV on confirmed gas release
- Deluge/TSE: Activated on confirmed fire/heat
```

---

### 10. CME Name

| Attribute | Detail |
|-----------|--------|
| **What it is** | Semicolon-separated list of all applicable CME names/tags for this row |
| **Source** | LLM generates by matching safety_devices to the cause's equipment |
| **JSON field** | `cme_names` |

**Format**: `"PSV-1010; PSHH-1010; Gas Detection; Deluge/TSE"`

This directly feeds the CME Count which drives the Risk P calculation.

---

### 11. CME Count (`CME #`)

| Attribute | Detail |
|-----------|--------|
| **What it is** | The number of applicable CMEs for this row |
| **Source** | LLM counts from the CME list |
| **JSON field** | `cme_count` |

Used in the probability formula: `P = max(1, C - cme_count)`.

**Typical values**: 2-4 depending on how many safety devices are associated with the equipment and whether LOPC triggers Gas Detection and Deluge/TSE.

---

### 12. Risk C (Consequence Severity)

| Attribute | Detail |
|-----------|--------|
| **What it is** | How severe the consequence would be, on a scale of 1-5 |
| **Source** | Knowledge base lookup — different table depending on category |
| **JSON field** | `risk_c` |

#### For PAF rows — Table 4 PAF (18x11 matrix)

- **Input**: max_pressure (row) x hole_size (column)
- **Hole size**: Determined by Table 2 based on pressure ratio
- **Output**: C = 1-5, or "PEC" (which maps to C=5)

**Table 2 — Release Hole Size**:

| Pressure Ratio | LOPC? | Hole Size |
|---------------|-------|-----------|
| <= 1.1x DP | No LOPC expected | N/A |
| > 1.1x to 1.5x DP | Yes | 1/4" (6 mm) flange leak |
| > 1.5x to 2x DP | Yes | 3/4" (20 mm) large flange leak |
| > 2x DP | Yes | Full-bore rupture |

#### For PD/LOR rows — Financial Loss Estimation (Table 10)

Per the HSE Risk Assessment standard, PD/LOR consequence is determined by **financial loss estimation**, not by pressure ratio. The SME estimates the total financial impact of the scenario and maps it to the consequence scale:

| PD/LOR C | Financial Loss (Facility Property Damage + Loss of Revenue) |
|----------|-------------------------------------------------------------|
| 1        | Up to $1MM                                                  |
| 2        | >$1MM to $20MM                                              |
| 3        | >$20MM to $50MM                                             |
| 4        | >$50MM to $250MM                                            |
| 5        | >$250MM                                                     |

**How to estimate financial loss** (Table 10 — PD/LOR Consequence Category Estimation Tool):

The SME calculates:
```
Financial Loss = (Affected Production in BOPD × $/bbl × Downtime in days) + Repair Cost ($MM)
```

Inputs required:
- **Total affected production** (BOPD) — how much production is lost
- **Value of lost production** ($/bbl) — current commodity price
- **Estimated downtime** (days/weeks/months) — how long until production resumes
- **Repair cost** ($MM) — cost to repair or replace damaged equipment

The resulting dollar amount is then mapped to the PD/LOR C scale above.

**This is SME/user input** — the PD/LOR C value is determined by the subject matter expert based on their knowledge of the facility's production rates, commodity prices, and repair logistics. It is **not** auto-calculated from pressure ratio.

> **App implementation note**: The current LLM prompt in `prompt_templates.py` uses a pressure-ratio-based proxy to auto-generate PD/LOR C values (< 1.1x → C=1, 1.1x–1.5x → C=2, 1.5x–2x → C=3, > 2x → C=4, > 2x + VCE → C=5). This is a reasonable approximation for automated worksheet generation, but in a formal HAZOP review the SME should validate or override these values using the financial loss method described above.

---

### 13. Risk P (Probability)

| Attribute | Detail |
|-----------|--------|
| **What it is** | How likely the consequence is, considering safety barriers |
| **Source** | Calculated by formula |
| **JSON field** | `risk_p` |

**Formula**:
```
P = max(1, C - CME_count)
```

- Start with C (consequence severity)
- Subtract the number of CMEs (each CME reduces probability by 1)
- Minimum value is always 1 (can never be zero)

**Example**: C=5, CME_count=4 → P = max(1, 5-4) = **1**

---

### 14. Risk Level

| Attribute | Detail |
|-----------|--------|
| **What it is** | The final risk classification combining C and P |
| **Source** | Risk Matrix lookup (5x5 grid) |
| **JSON field** | `risk_level` |

**Risk Matrix**:

```
       C=1    C=2    C=3    C=4    C=5
P=1  |  A   |  A   |  B   |  B   |  C   |
P=2  |  A   |  B   |  B   |  C   |  D   |
P=3  |  A   |  B   |  C   |  D   |  D   |
P=4  |  B   |  C   |  D   |  D   |  E   |
P=5  |  B   |  C   |  D   |  E   |  E   |
```

**Risk levels and app colors**:

| Level | Name | Color |
|-------|------|-------|
| **A** | Negligible | Green (`#28a745`) |
| **B** | Low | Light Green (`#8bc34a`) |
| **C** | Medium | Yellow (`#ffc107`) |
| **D** | High | Orange (`#ff9800`) |
| **E** | Critical | Red (`#dc3545`) |

---

## Columns in the User's Excel Not Currently in the App

The following columns exist in the reference Excel spreadsheet but are **not yet generated** by the app's LLM prompt or displayed in the worksheet:

### Control Category

| Attribute | Detail |
|-----------|--------|
| **What it is** | Classification of the type of control measure |
| **Status** | Not currently generated — could be added to the prompt as an additional field per CME |

Would classify each CME as:

| Category | Meaning | Example |
|----------|---------|---------|
| **Prevention** | Stops the event from occurring | PSHH initiating shutdown |
| **Detection** | Detects the event | Gas Detection |
| **Mitigation** | Reduces consequences after the event | Deluge/TSE, PSV |

### Tags (Tag Number + P&ID Reference)

| Attribute | Detail |
|-----------|--------|
| **What it is** | Two sub-columns: specific safety device tag and the drawing where the CME is found |
| **Status** | Not currently a separate column — tag info is embedded in the CME Name and Mitigation columns |

| Sub-column | Source |
|-----------|--------|
| Tag Number | Extracted from `safety_devices[].tag` (e.g., PSV-1010, PSHH-1010) |
| P&ID (CME) | Same `pdf_filename` / drawing reference |

---

## Exclusion and Cross-Reference Logic

Not every confirmed cause makes it into the worksheet. The `WORKSHEET_GENERATION_PROMPT` applies exclusion rules:

### Excluded Causes

| Condition | Action |
|-----------|--------|
| Gas cause with ratio <= 1.1x | Excluded — no LOPC expected |
| Liquid cause in HP with ratio < 1.1x | Excluded |

Excluded causes are shown in a separate table below the main worksheet with columns: Cause, Line Type, Max Pressure, Ratio, Rationale.

### Cross-Referenced Causes

| Condition | Action |
|-----------|--------|
| Liquid cause in HP with ratio >= 1.1x | Cross-referenced to "High Level" deviation — liquid doesn't increase pressure, only level |

Cross-referenced causes appear in a warning-styled table below the excluded causes.

---

## JSON Output Structure

Each worksheet generation returns:

```json
{
  "design_pressure": 2120,
  "included_rows": [
    {
      "number": "1a",
      "deviation": "High Pressure",
      "cause": "FCV-1010 (Gas outlet) fails closed",
      "drawing_ref": "DWG-XXXX",
      "intermediate_consequence": "Potential increase in ...",
      "category": "PAF",
      "scenario_comments": ["bullet1", "bullet2", "bullet3", "bullet4"],
      "pec": "YES",
      "mitigation_bullets": ["PSV-1010: Relieves excess pressure at set point", "..."],
      "cme_names": "PSV-1010; PSHH-1010; Gas Detection; Deluge/TSE",
      "cme_count": 4,
      "risk_c": 5,
      "risk_p": 1,
      "risk_level": "C"
    }
  ],
  "excluded_causes": [
    {
      "cause": "LCV-1010 (Liquid outlet) fails closed",
      "line_type": "Gas",
      "max_pressure": 2000,
      "ratio": 0.94,
      "rationale": "< 1.1x DP. No LOPC expected. Excluded."
    }
  ],
  "cross_referenced_causes": [
    {
      "cause": "LCV-1010 (Liquid outlet) fails closed",
      "note": "Liquid cause in HP deviation. Pressure does not increase, only level. See High Level deviation."
    }
  ]
}
```

---

## Event Trees (Knowledge Base)

Used to determine Bullet 3 (Fire/Explosion Potential) in scenario comments:

### Gas Event Tree
```
Release → Jet Fire → VCE (if pressure >= 100 psi, confined) → BLEVE (if > 2x DP)
```

### Liquid Event Tree
```
Release → Pool Fire → Flash Fire (if flammable) → Environmental contamination
```

---

## Key Definitions

| Term | Definition |
|------|-----------|
| **LOPC** | Loss of Primary Containment — occurs when pressure ratio > 1.1x design pressure |
| **PEC** | Potentially Exposed Crowd — scenario could affect more than 14 personnel |
| **CME/KME** | Control Measure Effectiveness / Key Mitigating Element |
| **PAF** | People, Assets, Facilities |
| **PD/LOR** | Process Deviation / Loss of Revenue |
| **BSDV** | Blowdown Shutdown Valve |
| **TSE** | Thermal Safety Element |
| **VCE** | Vapor Cloud Explosion |
| **BLEVE** | Boiling Liquid Expanding Vapor Explosion |
| **DP** | Design Pressure |

---

## Source Files

| File | Relevance |
|------|-----------|
| `services/prompt_templates.py` | All 3 prompt templates with complete knowledge base tables |
| `services/claude_service.py` | Claude API integration and JSON response parsing |
| `templates/deviations.html` | Deviation selection UI (14 standard + custom) |
| `templates/causes.html` | Cause confirmation UI with checkboxes |
| `templates/worksheet.html` | Final worksheet display (14 columns) |
| `static/css/styles.css` | Column widths, row colors, risk level badge colors |
