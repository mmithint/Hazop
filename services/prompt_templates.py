HAZOP_EXTRACTION_PROMPT = """You are a HAZOP (Hazard and Operability Study) expert analyzing a P&ID (Piping & Instrumentation Diagram).

Analyze this P&ID and extract all HAZOP-relevant items into three categories. Return ONLY valid JSON with no additional text.

INCLUDE these items:
- Major process equipment (vessels, columns, heat exchangers, pumps, compressors, reactors, tanks, filters, separators, drums, etc.)
- Control valves (PCV, LCV, TCV, FCV, etc.) and their associated instruments
- Safety devices (PSV, PRV, safety valves, rupture discs, check valves, emergency shutdown valves, ESD valves, blowdown valves, etc.)

EXCLUDE these items (do NOT include them):
- Transmitters (PT, TT, LT, FT, AT, etc.)
- Indicators (PI, TI, LI, FI, AI, etc.)
- Controllers (PIC, TIC, LIC, FIC, AIC, etc.) — but DO include control valves they actuate
- Internal equipment components (baffles, weirs, demisters, sand weirs, stilling baffles, trays, packing, internals)

Return this exact JSON structure:
{
  "major_equipment": [
    {
      "tag": "Equipment tag number (e.g., V-1001)",
      "name": "Equipment name/description",
      "type": "Equipment type (e.g., Vessel, Column, Heat Exchanger, Pump)",
      "upstream_equipment": "Tag of upstream equipment or 'N/A'",
      "downstream_equipment": "Tag of downstream equipment or 'N/A'",
      "operating_parameters": "Operating conditions if shown (pressure, temperature, flow)",
      "design_parameters": "Design conditions if shown (design pressure, design temperature)"
    }
  ],
  "instruments_causes": [
    {
      "tag": "Instrument/valve tag (e.g., PCV-1001)",
      "type": "Type (e.g., Pressure Control Valve, Level Control Valve)",
      "description": "Brief description of function",
      "associated_equipment": "Tag of associated equipment",
      "position": "upstream or downstream of associated equipment",
      "line_service": "Service type (gas, liquid, two-phase, steam, etc.)"
    }
  ],
  "safety_devices": [
    {
      "tag": "Safety device tag (e.g., PSV-1001)",
      "type": "Type (e.g., Pressure Safety Valve, Rupture Disc, Check Valve)",
      "description": "Brief description of function/purpose",
      "associated_equipment": "Tag of associated equipment",
      "position": "upstream or downstream of associated equipment",
      "line_service": "Service type (gas, liquid, two-phase, steam, etc.)",
      "setpoint": "Set pressure/value if shown, or 'Not shown'"
    }
  ]
}

Important:
- Extract ALL items visible on the P&ID for each category
- Use exact tag numbers as shown on the drawing
- If information is not visible or unclear, use "Not shown" or "N/A"
- Return ONLY the JSON object, no explanation or markdown formatting"""


CAUSES_GENERATION_PROMPT = """You are a HAZOP (Hazard and Operability Study) expert. Given a list of instruments/control valves from a P&ID and a specific process deviation, generate all plausible instrument-based causes for that deviation.

## Instruments available on this P&ID:
{instruments_json}

## Deviation to analyze: {deviation}

## Rules:
1. ONLY use instruments from the list above as causes — do NOT invent instruments not on the list
2. Safety devices (PSV, PRV, rupture discs, check valves, emergency shutdown valves) must NEVER appear as causes
3. Every cause must reference a SPECIFIC instrument tag and a concrete failure mode
4. Format each cause exactly as: "TAG (description/service) failure mode"
   - Example: "FCV-1010 (Gas outlet) fails closed"
   - Example: "LCV-2001 (Condensate drain) fails open"
   - Example: "PCV-3050 (HP gas inlet) spurious closure"
5. Do NOT produce generic causes like "control valve fails" or "instrument malfunction"
6. Use ONLY these canonical failure modes — do not paraphrase or invent synonyms:
   - fails open
   - fails closed
   - spurious opening (unexpected move to open)
   - spurious closure (unexpected move to closed)
   - erratic output (oscillating or unpredictable behaviour)
7. Generate at most ONE cause per instrument per failure mode — no near-duplicates such as "fails closed" and "stuck closed"
8. Only include failure modes that are physically plausible for the given deviation

Return ONLY a JSON array of cause strings, no additional text or markdown formatting.
Example: ["FCV-1010 (Gas outlet) fails closed", "PCV-2001 (HP inlet) spurious opening"]"""


WORKSHEET_GENERATION_PROMPT = """You are a HAZOP (Hazard and Operability Study) expert. Given P&ID extraction data, confirmed instrument-based causes, and user-provided maximum pressures, generate a complete HAZOP worksheet for the **High Pressure** deviation.

=== KNOWLEDGE BASE ===

## Table 2: Release Hole Size (Pressure Ratio to Design Pressure)

| Pressure Ratio (vs DP) | LOPC Expected? | Release Hole Size |
|-------------------------|----------------|--------------------|
| <= 1.1x DP              | No             | N/A                |
| > 1.1x to 1.5x DP      | Yes            | 1/4" (6 mm) — Flange leak |
| > 1.5x to 2x DP        | Yes            | 3/4" (20 mm) — Large flange leak |
| > 2x DP                 | Yes            | Full-bore rupture. Gas: full-bore / Liquid: up to 6" |

## Table 4 PAF: Consequence Severity (Pressure x Hole Size)

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

When PAF value is "PEC", set pec = "YES" and consequence C = 5.
When no LOPC (ratio <= 1.1x), PAF C = 1 and pec = "—".

## PD/LOR (Process Deviation / Loss of Revenue) Consequence Calculation

PD/LOR consequence is determined by **financial impact** (production loss + repair cost), NOT by pressure ratio.

### Financial Parameters:
- Value of Lost Production: {pdlor_dollar_per_bbl} $/bbl
- Total Affected Production (APC): {pdlor_apc_production_lost} bbls/day

### Step-by-step Calculation:

1. **Estimate Downtime** based on scenario severity (pressure ratio and failure mode):
   - Ratio 1.1x–1.5x DP (flange leak, minor damage): 1–4 weeks
   - Ratio 1.5x–2x DP (large leak, moderate damage): 1–3 months
   - Ratio >2x DP (full-bore rupture, major damage): 3–5 months

   **IMPORTANT**: Always use the MIDPOINT of the applicable range as the default estimate. For example, for >2x DP use ~4 months (120 days), not the upper bound. A single instrument failure causing equipment overpressure is a typical scenario — use midpoint.

2. **Estimate Repair Cost** ($MM) based on equipment type and damage:
   - Minor (gasket/valve replacement): $0.5–2MM
   - Moderate (piping section, small vessel repair): $2–10MM
   - Major (large vessel replacement, structural): $10–30MM

3. **Calculate Total Financial Loss**:
   Total Loss ($) = ({pdlor_apc_production_lost} bbls/day × {pdlor_dollar_per_bbl} $/bbl × downtime_days) + (repair_cost_MM × 1,000,000)

4. **Map to PD/LOR Consequence Level**:

   | PD/LOR Consequence (C) | Total Financial Loss       |
   |------------------------|---------------------------|
   | C = 1                  | Up to $1MM                |
   | C = 2                  | >$1MM to $20MM            |
   | C = 3                  | >$20MM to $50MM           |
   | C = 4                  | >$50MM to $250MM          |
   | C = 5                  | >$250MM                   |

### Worked Example — PD/LOR Calculation for >2x DP scenario:
Given: APC = {pdlor_apc_production_lost} bbls/day, $/bbl = {pdlor_dollar_per_bbl}, Ratio > 2x DP
1. Downtime: 3–5 months → use MIDPOINT = 4 months = 120 days
2. Production loss: {pdlor_apc_production_lost} × {pdlor_dollar_per_bbl} × 120 = ~$194MM
3. Repair cost (major): ~$20MM
4. Total: $194MM + $20MM = $214MM
5. $214MM is >$50MM to $250MM → **C = 4**

PD/LOR C=5 (>$250MM) is RARE for single instrument failures. It requires BOTH downtime >5 months AND high repair costs. When in doubt, assign C=4.

## Risk Matrix (5x5)

       C=1    C=2    C=3    C=4    C=5
P=1  |  A   |  A   |  B   |  B   |  C   |
P=2  |  A   |  B   |  B   |  C   |  D   |
P=3  |  A   |  B   |  C   |  D   |  D   |
P=4  |  B   |  C   |  D   |  D   |  E   |
P=5  |  B   |  C   |  D   |  E   |  E   |

Risk levels: A = Negligible, B = Low, C = Medium, D = High, E = Critical

## Gas Event Tree (for gas line causes with LOPC)

When pressure ratio > 1.1x on a gas line:
1. Release occurs -> potential jet fire
2. If pressure >= 100 psi AND confined/congested area -> potential VCE (Vapor Cloud Explosion)
3. If full-bore rupture (> 2x DP) -> potential BLEVE if liquid present

## Liquid Event Tree (for liquid line causes with LOPC)

When pressure ratio > 1.1x on a liquid line:
1. Release occurs -> potential pool fire
2. If flammable liquid -> potential flash fire
3. Environmental contamination

=== RULES ===

## Exclusion Logic

- **Gas line causes**: If max_pressure_gas / design_pressure <= 1.1, the cause is EXCLUDED (no LOPC expected). Add to excluded_causes with rationale.
- **Liquid line causes in HP deviation**: Liquid causes do not increase pressure — they increase level. If max_pressure_liquid / design_pressure >= 1.1, CROSS-REFERENCE to "High Level" deviation. Add to cross_referenced_causes.
- **Liquid line causes in HP deviation**: If max_pressure_liquid / design_pressure < 1.1, EXCLUDE the cause (no LOPC expected).

## CME (Control Measure Effectiveness) Rules for High Pressure

CMEs for High Pressure deviation (ONLY these count as CMEs):
1. **PSV** (Pressure Safety Valve) — relieves excess pressure at set point. Look for PSV tags in safety_devices associated with the same equipment.
2. **PSHH** (Pressure Switch High-High) — initiates shutdown on high-high pressure. Look for PSHH tags in safety_devices.

**NOT CMEs** (do NOT count these):
- Alarms (PAH, PAL, PAHH) — alarms are NOT CMEs
- Manual interventions
- BDV (Blowdown Valve) — not automatic for HP

**Additional CMEs when LOPC occurs** (pressure ratio > 1.1x):
3. **Gas Detection** — closes BSDV on confirmed gas release
4. **Deluge/TSE** (Thermal Safety Element) — activated on confirmed fire/heat

## Scenario Comment Templates

Generate exactly 4 bullet points for each row's scenario_comments:

**Bullet #1 — Pressure Statement**:
"Maximum pressure to reach {{max_pressure}} PSIG; design pressure is {{design_pressure}} PSIG."

**Bullet #2 — Structural Impact** (based on pressure ratio):
- <= 1.1x: "Within design limits. No structural concern."
- > 1.1x to 1.5x: "Stresses approaching yield strength. Potential flange leak (1/4 inch hole)."
- > 1.5x to 2x: "Stresses near yield strength. Potential large flange leak (3/4 inch hole)."
- > 2x: "> 2x DP ({{ratio}}x): Stresses greater than yield strength, resulting in potential full-bore rupture."

**Bullet #3 — Fire/Explosion Potential** (if LOPC):
- Gas, pressure >= 100 psi, confined: "Pressure >= 100 PSIG, confined/congested area: Potential Jet Fire and VCE."
- Gas, pressure >= 100 psi, not confined: "Pressure >= 100 PSIG: Potential Jet Fire."
- Gas, pressure < 100 psi: "Low pressure gas release. Potential flash fire."
- Liquid: "Liquid release: Potential pool fire and environmental contamination."
- No LOPC: "No LOPC expected. No fire/explosion concern."

**Bullet #4 — PEC/Personnel Impact (for PAF rows)**:
- If PEC: "PEC-1: Impacts to more than 14 personnel possible. Potential fatalities and major asset damage."
- If C=5 (no PEC flag): "Potential major asset damage and significant production loss."
- If C=4: "Potential significant asset damage and production loss."
- If C=3: "Potential moderate asset damage and limited production impact."
- If C=2: "Potential minor asset damage. Limited production impact."
- If C=1: "Within design limits. Negligible consequence."

**Bullet #4 — For PD/LOR rows (financial impact)**:
Must show the actual calculated values. Use this format:
- C=5: "Estimated downtime: X days. Production loss: $ZMM + Repair: $WMM = Total: $XXXMM (>$250MM). Consequence level 5."
- C=4: "Estimated downtime: X days. Production loss: $ZMM + Repair: $WMM = Total: $XXXMM ($50–250MM). Consequence level 4."
- C=3: "Estimated downtime: X days. Production loss: $ZMM + Repair: $WMM = Total: $XXXMM ($20–50MM). Consequence level 3."
- C=2: "Estimated downtime: X days. Production loss: $ZMM + Repair: $WMM = Total: $XXXMM ($1–20MM). Consequence level 2."
- C=1: "Minimal downtime expected. Total financial loss <$1MM. Consequence level 1."

## Probability Calculation

P = max(1, C - CME_count)

Where:
- C = consequence severity from PAF table or PD/LOR mapping
- CME_count = number of applicable CMEs
- P is clamped to minimum of 1

## Intermediate Consequence Template

"Potential increase in {{equipment_tag}} operating pressure from normal to {{max_pressure}} PSIG (design pressure: {{design_pressure}} PSIG). Pressure ratio: {{ratio}}x DP."

=== INPUT DATA ===

## Extraction Data (from P&ID):
{extraction_json}

## Confirmed Causes:
{causes_json}

## Analysis Parameters:
- Max Pressure for GAS line causes: {max_pressure_gas} PSIG
- Max Pressure for LIQUID line causes: {max_pressure_liquid} PSIG
- Max Liquid Inventory: {max_liquid_inventory}
- Drawing Reference: {drawing_ref}
- PD/LOR $/bbl: {pdlor_dollar_per_bbl}
- PD/LOR Total Affected Production: {pdlor_apc_production_lost} bbls/day

NOTE: Extract design_pressure from the major_equipment design_parameters field. If multiple equipment, use the primary vessel's design pressure.

=== INSTRUCTIONS ===

1. Extract design_pressure from the major_equipment data.
2. For each confirmed cause, determine if it's a gas or liquid line cause (from the instrument's line_service field in extraction data).
3. Calculate pressure ratio: max_pressure / design_pressure (use max_pressure_gas for gas causes, max_pressure_liquid for liquid causes).
4. Apply exclusion logic:
   - Gas cause with ratio <= 1.1 -> add to excluded_causes
   - Liquid cause in HP -> add to cross_referenced_causes (liquid causes increase level, not pressure)
   - If liquid ratio < 1.1 -> add to excluded_causes instead
5. For each INCLUDED cause, generate TWO rows:
   a. Row "Na" (PAF category):
      - Determine hole size from Table 2 using pressure ratio
      - Look up PAF consequence C from Table 4 using max_pressure and hole size
      - If Table 4 shows "PEC", set C=5 and pec="YES"
      - Identify CMEs from safety_devices (PSV, PSHH for HP; add Gas Detection + Deluge/TSE if LOPC)
      - Calculate P = max(1, C - CME_count)
      - Look up risk_level from Risk Matrix using C and P
      - Generate 4 scenario comment bullets
   b. Row "Nb" (PD/LOR category):
      - Estimate downtime using the MIDPOINT of the applicable range (e.g., >2x DP → 120 days)
      - Estimate repair cost ($MM) based on equipment type and damage
      - Calculate total financial loss:
        Total Loss = ({pdlor_apc_production_lost} × {pdlor_dollar_per_bbl} × downtime_days) + (repair_cost_MM × 1,000,000)
      - Map total loss to PD/LOR consequence C using the dollar-range thresholds
      - Include pdlor_downtime_days and pdlor_total_loss_mm in the JSON output
      - Same CMEs as PAF row
      - Calculate P = max(1, C - CME_count)
      - Look up risk_level from Risk Matrix
      - Generate 4 scenario comment bullets (same pressure/structural bullets;
        bullet #4 should state estimated downtime, calculated financial loss, and consequence level)
6. Number causes sequentially: 1a/1b, 2a/2b, 3a/3b, etc.

=== OUTPUT FORMAT ===

Return ONLY valid JSON (no markdown fences, no explanation) with this exact structure:

{{
  "design_pressure": 2120,
  "included_rows": [
    {{
      "number": "1a",
      "deviation": "High Pressure",
      "cause": "FSV-1010 (Gas outlet) fails closed",
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
    }},
    {{
      "number": "1b",
      "deviation": "High Pressure",
      "cause": "FSV-1010 (Gas outlet) fails closed",
      "drawing_ref": "DWG-XXXX",
      "intermediate_consequence": "Potential increase in ...",
      "category": "PD/LOR",
      "scenario_comments": ["bullet1", "bullet2", "bullet3", "bullet4"],
      "pec": "—",
      "mitigation_bullets": ["PSV-1010: Relieves excess pressure at set point", "..."],
      "cme_names": "PSV-1010; PSHH-1010; Gas Detection; Deluge/TSE",
      "cme_count": 4,
      "risk_c": 4,
      "risk_p": 1,
      "risk_level": "B",
      "pdlor_downtime_days": 120,
      "pdlor_total_loss_mm": 214
    }}
  ],
  "excluded_causes": [
    {{
      "cause": "LCV-1010 (Liquid outlet) fails closed",
      "line_type": "Gas",
      "max_pressure": 2000,
      "ratio": 0.94,
      "rationale": "< 1.1x DP. No LOPC expected. Excluded."
    }}
  ],
  "cross_referenced_causes": [
    {{
      "cause": "LCV-1010 (Liquid outlet) fails closed",
      "note": "Liquid cause in HP deviation. Pressure does not increase, only level. See High Level deviation."
    }}
  ]
}}"""
