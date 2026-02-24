HAZOP_EXTRACTION_PROMPT = """You are a HAZOP (Hazard and Operability Study) expert analyzing a P&ID (Piping & Instrumentation Diagram).

Your goal is to extract ONLY the items relevant to performing a HAZOP study on the PRIMARY equipment (node) shown on this P&ID. Do NOT extract every instrument — only those that could CAUSE a process deviation or PROTECT against one.

=== WHAT TO EXTRACT ===

## 1. Major Equipment (the node being studied)
- The PRIMARY process equipment on this P&ID (vessel, separator, column, heat exchanger, etc.)
- Include its operating and design parameters (pressure, temperature, size)

## 2. Instruments/Valves that can CAUSE deviations
ONLY extract valves/instruments that meet ALL of these criteria:
- They are on a PROCESS INLET or PROCESS OUTLET line of the primary equipment
- They control FLOW, LEVEL, or PRESSURE into or out of the equipment
- Their failure (fail open, fail closed, spurious operation) could cause a HAZOP deviation (High/Low Pressure, High/Low Level, High/Low Flow, High/Low Temperature)

INCLUDE these types (if on process inlet/outlet lines):
- Flow control valves (FCV, FSV) — failure affects flow and pressure
- Level control valves (LCV) — failure affects level and can affect pressure
- Pressure control valves (PCV) — failure directly affects pressure
- Temperature control valves (TCV) — failure affects temperature
- Emergency shutdown valves (XCV, SDV, ESDV, BSDV) — on process lines
- On/Off valves on process lines that could block or release flow

EXCLUDE these (they do NOT cause process deviations):
- Chemical injection valves (small-bore injection quills, defoamer, demulsifier, corrosion inhibitor injection)
- Sample valves and sample connections
- Drain valves (to closed drain, open drain)
- Vent valves (small utility vents)
- Instrument isolation valves (root valves for pressure/level transmitters)
- Analyzers and analyzer sample systems (BS&W, H2S, pH analyzers)
- Mixers, static mixers on sample/analyzer lines
- Any valve on a non-process utility line (instrument air, nitrogen, hydraulic, chemical injection tubing)

## 3. Safety Devices that PROTECT against deviations
ONLY extract safety devices that provide AUTOMATIC protection:
- PSV (Pressure Safety Valve) — protects against high pressure
- PSHH (Pressure Switch High-High) — initiates shutdown on high pressure
- LSHH (Level Switch High-High) — initiates shutdown on high level
- LSLL (Level Switch Low-Low) — initiates shutdown on low level
- TSHH (Temperature Switch High-High) — initiates shutdown on high temperature
- Gas Detection systems — initiates BSDV closure on gas leak
- Deluge/TSE (Thermal Safety Element) — fire protection
- BSDV (Boarding Shutdown Valve) — isolates flow on ESD

EXCLUDE these (they are NOT automatic protective devices):
- Alarms only (PAH, PAL, LAH, LAL, TAH, TAL) — alarms notify operators but do NOT automatically protect
- Indicators (PI, TI, LI, FI) — display only
- Transmitters (PT, TT, LT, FT) — sensing only (unless paired with a switch like PSHH)
- Controllers (PIC, TIC, LIC, FIC) — control loop, not safety device
- Manual valves, manual bypasses
- Check valves on non-critical lines (injection, sample, drain)

=== HOW TO DETERMINE LINE SERVICE ===

For each valve/instrument, identify the line service:
- **Gas**: Lines going to gas headers, flare, compressor suction, gas dehydration (look for "PG" in line designation)
- **Liquid**: Lines going to liquid/oil headers, downstream separators, liquid outlets (look for "PL" in line designation)
- **Two-phase**: Inlet lines from upstream equipment carrying mixed gas+liquid
- Look at the line designation format: typically "SIZE-SERVICE-NUMBER-CLASS" (e.g., 10"-PG-304-A = 10 inch, Process Gas, line 304, class A)

Line designation codes:
- PG = Process Gas
- PL = Process Liquid
- PF = Process Flow (could be two-phase)
- FH = Flare Header
- DC = Drain Closed
- SP = Sample/Chemical injection (EXCLUDE these)

=== OUTPUT FORMAT ===

Return ONLY valid JSON with no additional text or markdown fences:

{
  "major_equipment": [
    {
      "tag": "Equipment tag number (e.g., MBD-1010)",
      "name": "Equipment name/description from title block or callout",
      "type": "Equipment type (e.g., Separator, Vessel, Column)",
      "upstream_equipment": "Tag of upstream equipment feeding into this, or 'N/A'",
      "downstream_equipment": "Tag of downstream equipment receiving from this, or 'N/A'",
      "operating_parameters": "Operating conditions as shown (e.g., 'OPER.: 1850-185 PSIG')",
      "design_parameters": "Design conditions as shown (e.g., 'DESIGN: 2120 PSIG AT 150°F')",
      "size": "Physical size if shown (e.g., '78\" O.D. x 27'-0\" S/S')"
    }
  ],
  "instruments_causes": [
    {
      "tag": "Valve tag (e.g., FSV-1010)",
      "type": "Type (e.g., Flow Shutdown Valve, Level Control Valve)",
      "description": "What it does (e.g., 'Controls gas outlet flow from separator to compressor suction')",
      "associated_equipment": "Tag of the primary equipment it serves",
      "position": "inlet or outlet of associated equipment",
      "line_tag": "Full line designation if visible (e.g., '10\"-PG-304-A')",
      "line_service": "gas, liquid, or two-phase (determined from line designation and destination)",
      "destination_or_source": "Where the line goes to or comes from (e.g., 'To Flash Gas Compressor 2nd Stage Suction')",
      "fail_position": "Fail open, fail closed, or fail last position (if shown, otherwise 'Not shown')"
    }
  ],
  "safety_devices": [
    {
      "tag": "Safety device tag (e.g., PSV-1010)",
      "type": "Type (e.g., Pressure Safety Valve, Pressure Switch High-High)",
      "description": "What it protects against and how (e.g., 'Relieves excess pressure to HP flare')",
      "associated_equipment": "Tag of equipment it protects",
      "setpoint": "Set pressure if shown (e.g., '2120 PSIG'), or 'Not shown'",
      "destination": "Where it relieves/vents to (e.g., 'HP Flare via 20\"-FH-513-A')",
      "line_service": "gas, liquid, or two-phase"
    }
  ]
}

=== IMPORTANT REMINDERS ===

- Focus on the PRIMARY equipment node only
- Only include items that can CAUSE deviations or PROTECT against them
- Do NOT include every instrument on the P&ID — be selective and HAZOP-relevant
- Use exact tag numbers as shown on the drawing
- If information is not visible or unclear, use "Not shown" or "N/A"
- Return ONLY the JSON object, no explanation or markdown formatting
- Quality over quantity: 5-10 well-identified cause instruments is typical for a single node"""

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

## ECR (Environmental Impairment Cleanup/Remediation Cost) Consequence Calculation

ECR consequence is determined by **spill volume** from liquid releases, mapped to environmental cleanup cost.

### ECR applies ONLY when:
- There is a LOPC (pressure ratio > 1.1x DP)
- The release involves **liquid** (oil/condensate), NOT gas-only releases
- For gas-only releases with no liquid inventory, ECR C = 1 (minimal environmental impact)

### Step-by-step Calculation:

1. **Determine if liquid release is possible**:
   - Check if the equipment has liquid inventory (from max_liquid_inventory parameter)
   - For full-bore rupture (>2x DP): assume worst-case liquid release up to max_liquid_inventory
   - For flange leak (1.1x–1.5x DP): assume small leak, ~1–10 bbl release
   - For large flange leak (1.5x–2x DP): assume moderate leak, ~10–100 bbl release

2. **Estimate spill volume (bbl)** based on release hole size and duration before isolation:
   - 1/4" hole (flange leak): ~1–10 bbl before isolation
   - 3/4" hole (large flange leak): ~10–100 bbl before isolation
   - Full-bore rupture: up to max_liquid_inventory (could be 100–600+ bbl)

   **IMPORTANT**: Use MIDPOINT of applicable range as default estimate.

3. **Map spill volume to ECR Consequence Level** (from Figure 2 - ECR Estimation Tool):

   | ECR Consequence (C) | Spill Volume (bbl)      | Approximate Cost ($MM) |
   |----------------------|-------------------------|------------------------|
   | C = 1                | < 1 bbl                 | Up to $1MM             |
   | C = 2                | >= 1 bbl to < 10 bbl    | $1MM to $5MM           |
   | C = 3                | >= 10 bbl to < 100 bbl  | $5MM to $10MM          |
   | C = 4                | >= 100 bbl to < 600 bbl | $10MM to $50MM         |
   | C = 5                | >= 600 bbl              | $50MM or more          |

   Note: For spill volumes < 500 bbl, the GOM Oil Spill Model is not directly applicable.
   Use the proposed volume-based thresholds (conservative with respect to cost trend line).

### Worked Example — ECR Calculation for >2x DP scenario:
Given: Full-bore rupture, max_liquid_inventory = {max_liquid_inventory} bbl
1. Release type: Full-bore rupture -> potential release of full liquid inventory
2. Spill volume estimate: ~{max_liquid_inventory} bbl (using max_liquid_inventory)
3. Map to ECR threshold table -> **determine C from volume**

### Worked Example — ECR for 1.1x–1.5x DP (flange leak):
Given: 1/4" flange leak, liquid present
1. Release type: Small flange leak -> limited release before isolation
2. Spill volume estimate: ~5 bbl (midpoint of 1–10 bbl)
3. 5 bbl is >= 1 bbl to < 10 bbl -> **C = 2**

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

## CME Rules for ECR (Environmental Cleanup/Remediation)

CMEs that mitigate environmental consequence (limit release duration/volume):
1. **PSHH** (Pressure Switch High-High) — closes BSDV on high-high pressure, limiting release duration
2. **Gas Detection** — closes BSDV on confirmed gas/leak, limiting release duration
3. **BSDV** (Boarding Shutdown Valve) — isolates flow to limit spill volume

**NOT CMEs for ECR** (do NOT count these for ECR rows):
- PSV (vents to atmosphere — does not prevent environmental release)
- Deluge/TSE (fire suppression — does not prevent spill)
- Alarms, manual interventions

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

**Bullet #4 — For ECR rows (environmental impact)**:
Must show the estimated spill volume and cost. Use this format:
- C=5: "Estimated spill volume: ~X bbl. Environmental cleanup cost: >$50MM. Consequence level 5."
- C=4: "Estimated spill volume: ~X bbl. Environmental cleanup cost: $10–50MM. Consequence level 4."
- C=3: "Estimated spill volume: ~X bbl. Environmental cleanup cost: $5–10MM. Consequence level 3."
- C=2: "Estimated spill volume: ~X bbl. Environmental cleanup cost: $1–5MM. Consequence level 2."
- C=1: "No significant liquid release expected. Environmental cleanup cost <$1MM. Consequence level 1."

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
5. For each INCLUDED cause, generate THREE rows:
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
   c. Row "Nc" (ECR category):
      - Determine if liquid release is possible (check max_liquid_inventory)
      - If no liquid inventory or no LOPC: set ECR C = 1
      - Estimate spill volume based on hole size and liquid inventory (use MIDPOINT)
      - Map spill volume to ECR consequence C using the volume-based thresholds
      - Include ecr_spill_volume_bbl and ecr_estimated_cost_mm in JSON output
      - Identify ECR-specific CMEs (PSHH, Gas Detection, BSDV — NOT PSV or Deluge)
      - Calculate P = max(1, C - CME_count)
      - Look up risk_level from Risk Matrix
      - Generate 4 scenario comment bullets (same pressure/structural bullets;
        bullet #4 should state estimated spill volume, cleanup cost, and consequence level)
6. Number causes sequentially: 1a/1b/1c, 2a/2b/2c, 3a/3b/3c, etc.

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
    }},
    {{
      "number": "1c",
      "deviation": "High Pressure",
      "cause": "FSV-1010 (Gas outlet) fails closed",
      "drawing_ref": "DWG-XXXX",
      "intermediate_consequence": "Potential increase in ...",
      "category": "ECR",
      "scenario_comments": ["bullet1", "bullet2", "bullet3", "bullet4"],
      "pec": "—",
      "mitigation_bullets": ["PSHH-1010: Closes BSDV on high-high pressure", "Gas Detection: Closes BSDV on confirmed release"],
      "cme_names": "PSHH-1010; Gas Detection",
      "cme_count": 2,
      "risk_c": 2,
      "risk_p": 1,
      "risk_level": "A",
      "ecr_spill_volume_bbl": 5,
      "ecr_estimated_cost_mm": 3
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
