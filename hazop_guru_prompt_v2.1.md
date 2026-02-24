# HAZOP GURU Prompt v2.1 — Consolidated Worksheet Generation

**Purpose**: Standalone prompt for generating complete HAZOP worksheet rows from P&ID extraction data and confirmed causes. Designed for copy-paste use with ChatGPT, Claude, or any LLM.

---

## PROMPT

You are a HAZOP (Hazard and Operability Study) expert. Given P&ID extraction data, confirmed instrument-based causes, and user-provided maximum pressures, generate a complete HAZOP worksheet for the **High Pressure** deviation.

---

### KNOWLEDGE BASE

#### Table 2: Release Hole Size (Pressure Ratio to Design Pressure)

| Pressure Ratio (vs DP) | LOPC Expected? | Release Hole Size |
|-------------------------|----------------|--------------------|
| <= 1.1x DP              | No             | N/A                |
| > 1.1x to 1.5x DP      | Yes            | 1/4" (6 mm) — Flange leak |
| > 1.5x to 2x DP        | Yes            | 3/4" (20 mm) — Large flange leak |
| > 2x DP                 | Yes            | Full-bore rupture. Gas: full-bore / Liquid: up to 6" |

#### Table 4 PAF: Consequence Severity (Pressure x Hole Size)

```
Pressure(psi) | 1/8"  | 1/4"  | 3/8"  | 1/2"  | 3/4"  | 1"    | 1.5"  | 2"    | 3"    | 4"    | 6"
------------- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | -----
20            |   2   |   2   |   2   |   2   |   2   |   2   |   2   |   3   |   3   |   3   |   3
50            |   2   |   2   |   2   |   2   |   3   |   3   |   3   |   3   |   4   |   4   |   4
100           |   2   |   2   |   3   |   3   |   3   |   3   |   4   |   4   |   4   |   5   |   5
150           |   2   |   3   |   3   |   3   |   3   |   4   |   4   |   4   |   5   |   5   |  PEC
200           |   2   |   3   |   3   |   3   |   4   |   4   |   4   |   5   |   5   |  PEC  |  PEC
300           |   3   |   3   |   3   |   4   |   4   |   4   |   5   |   5   |  PEC  |  PEC  |  PEC
500           |   3   |   3   |   4   |   4   |   5   |   5   |   5   |  PEC  |  PEC  |  PEC  |  PEC
720           |   3   |   4   |   4   |   5   |   5   |   5   |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
1000          |   3   |   4   |   5   |   5   |   5   |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
1200          |   4   |   4   |   5   |   5   |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
1480          |   4   |   5   |   5   |   5   |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
1500          |   4   |   5   |   5   |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
1800          |   4   |   5   |   5   |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
2000          |   4   |   5   |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
2500          |   5   |   5   |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
3000          |   5   |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
4000          |   5   |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
5000          |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC  |  PEC
```

When PAF value is "PEC", set pec = "YES" and consequence C = 5.

#### PD/LOR (Process Deviation / Loss of Revenue) Consequence Mapping

| Pressure Ratio (vs DP) | PD/LOR Consequence (C) |
|-------------------------|------------------------|
| < 1.1x DP               | C = 1                  |
| 1.1x to 1.5x DP         | C = 2                  |
| 1.5x to 2x DP           | C = 3                  |
| > 2x DP                 | C = 4                  |
| > 2x DP + VCE potential | C = 5                  |

#### Risk Matrix (5x5)

```
       C=1    C=2    C=3    C=4    C=5
P=1  |  A   |  A   |  B   |  B   |  C   |
P=2  |  A   |  B   |  B   |  C   |  D   |
P=3  |  A   |  B   |  C   |  D   |  D   |
P=4  |  B   |  C   |  D   |  D   |  E   |
P=5  |  B   |  C   |  D   |  E   |  E   |
```

Risk levels: A = Negligible, B = Low, C = Medium, D = High, E = Critical

#### Gas Event Tree (for gas line causes with LOPC)

When pressure ratio > 1.1x on a gas line:
1. Release occurs → potential jet fire
2. If pressure >= 100 psi AND confined/congested area → potential VCE (Vapor Cloud Explosion)
3. If full-bore rupture (> 2x DP) → potential BLEVE if liquid present

#### Liquid Event Tree (for liquid line causes with LOPC)

When pressure ratio > 1.1x on a liquid line:
1. Release occurs → potential pool fire
2. If flammable liquid → potential flash fire
3. Environmental contamination

---

### RULES

#### Exclusion Logic

- **Gas line causes**: If max_pressure / design_pressure <= 1.1, the cause is EXCLUDED (no LOPC expected). Provide rationale.
- **Liquid line causes**: If max_pressure / design_pressure >= 1.1, the cause is CROSS-REFERENCED to "High Level" deviation (liquid causes in HP don't increase pressure, only level). Provide cross-reference note.

#### CME (Control Measure Effectiveness) Rules for High Pressure

CMEs for High Pressure deviation (only these count as CMEs):
1. **PSV** (Pressure Safety Valve) — relieves excess pressure at set point
2. **PSHH** (Pressure Switch High-High) — initiates shutdown on high-high pressure

**NOT CMEs** (do not count these):
- Alarms (PAH, PAL, PAHH) — alarms are NOT CMEs
- Manual interventions
- BDV (Blowdown Valve) — not automatic for HP

**Additional CMEs when LOPC occurs** (pressure ratio > 1.1x):
3. **Gas Detection** — closes BSDV on confirmed gas release
4. **Deluge/TSE** (Thermal Safety Element) — activated on confirmed fire/heat

#### Scenario Comment Templates

Generate exactly 4 bullet points for each row's scenario_comments:

**Bullet #1 — Pressure Statement**:
"Maximum pressure to reach {max_pressure} PSIG; design pressure is {design_pressure} PSIG."

**Bullet #2 — Structural Impact** (based on pressure ratio):
- <= 1.1x: "Within design limits. No structural concern."
- > 1.1x to 1.5x: "Stresses approaching yield strength. Potential flange leak (1/4\" hole)."
- > 1.5x to 2x: "Stresses near yield strength. Potential large flange leak (3/4\" hole)."
- > 2x: "> 2x DP ({ratio}x): Stresses greater than yield strength, resulting in potential full-bore rupture."

**Bullet #3 — Fire/Explosion Potential** (if LOPC):
- Gas, pressure >= 100 psi, confined: "Pressure >= 100 PSIG, confined/congested area: Potential Jet Fire and VCE."
- Gas, pressure >= 100 psi, not confined: "Pressure >= 100 PSIG: Potential Jet Fire."
- Gas, pressure < 100 psi: "Low pressure gas release. Potential flash fire."
- Liquid: "Liquid release: Potential pool fire and environmental contamination."
- No LOPC: "No LOPC expected. No fire/explosion concern."

**Bullet #4 — PEC/Personnel Impact**:
- If PEC: "PEC-1: Impacts to more than 14 personnel possible. Potential fatalities and major asset damage."
- If C=5 (no PEC): "Potential major asset damage and significant production loss."
- If C=4: "Potential significant asset damage and production loss."
- If C=3: "Potential moderate asset damage and limited production impact."
- If C=2: "Potential minor asset damage. Limited production impact."
- If C=1: "Within design limits. Negligible consequence."

#### Probability Calculation

```
P = max(1, C - CME_count)
```

Where:
- C = consequence severity from PAF table or PD/LOR mapping
- CME_count = number of applicable CMEs
- P is clamped to minimum of 1

#### Intermediate Consequence Template

"Potential increase in {equipment_tag} operating pressure from normal to {max_pressure} PSIG (design pressure: {design_pressure} PSIG). Pressure ratio: {ratio}x DP."

---

### OUTPUT FORMAT

Return ONLY valid JSON with this exact structure:

```json
{
  "included_rows": [
    {
      "number": "1a",
      "deviation": "High Pressure",
      "cause": "FSV-1010 (Gas outlet) fails closed",
      "drawing_ref": "DWG-XXXX",
      "intermediate_consequence": "Potential increase in ...",
      "category": "PAF",
      "scenario_comments": ["bullet1", "bullet2", "bullet3", "bullet4"],
      "pec": "YES or —",
      "mitigation_bullets": ["CME1 description", "CME2 description"],
      "cme_names": "PSV-1010; PSHH-1010; ...",
      "cme_count": 4,
      "risk_c": 5,
      "risk_p": 1,
      "risk_level": "C"
    }
  ],
  "excluded_causes": [
    {
      "cause": "description",
      "line_type": "Gas or Liquid",
      "max_pressure": 2000,
      "ratio": 0.94,
      "rationale": "< 1.1x DP. No LOPC expected. Excluded."
    }
  ],
  "cross_referenced_causes": [
    {
      "cause": "description",
      "note": "Liquid cause in HP deviation. Pressure does not increase, only level. See High Level deviation."
    }
  ]
}
```

**Row numbering**: Each included cause gets TWO rows:
- `{n}a` = PAF row (consequence from Table 4 PAF)
- `{n}b` = PD/LOR row (consequence from PD/LOR mapping)

Where n = 1, 2, 3... for each cause.

---

### INPUT DATA

**Extraction Data (from P&ID)**:
{extraction_json}

**Confirmed Causes**:
{causes_json}

**Analysis Parameters**:
- Max Pressure for GAS line causes: {max_pressure_gas} PSIG
- Max Pressure for LIQUID line causes: {max_pressure_liquid} PSIG
- Max Liquid Inventory: {max_liquid_inventory}
- Drawing Reference: {drawing_ref}

**Design Pressure**: Extract from the major_equipment design_parameters field.

---

### INSTRUCTIONS

1. For each confirmed cause, determine if it's a gas or liquid line cause (from line_service field).
2. Apply exclusion logic:
   - Gas cause with ratio <= 1.1x → add to excluded_causes
   - Liquid cause with ratio >= 1.1x → add to cross_referenced_causes
3. For included causes, generate TWO rows each (PAF + PD/LOR):
   a. Look up Table 4 PAF using max_pressure and hole size from Table 2
   b. Look up PD/LOR consequence using pressure ratio
   c. Identify applicable CMEs from safety_devices list
   d. Calculate P = max(1, C - CME_count)
   e. Look up risk_level from Risk Matrix
   f. Generate 4 scenario comment bullets using templates
   g. Format intermediate_consequence
4. Return the complete JSON structure.
