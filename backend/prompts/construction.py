"""
Construction safety detection prompt.

This module MUST export two names that the analyzer imports:
    from backend.prompts.construction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

Design contract (must stay in sync with VisionAnalyzer):
1) The model must return a JSON OBJECT of the form:
       {"violations": [ {...}, {...} ]}
   because the analyzer calls the API with response_format={"type": "json_object"}
   and then reads data.get("violations", []).
2) Each violation's "violation_type" MUST be chosen from the allowed IDs that the
   analyzer injects at runtime via {allowed_ids_json}. The analyzer drops any
   violation whose type is not in that allow-list, so the model must use those
   exact codes (e.g. PPE_HELMET_MISSING, HEIGHT_NO_HARNESS) and never invent
   short codes like HELMET_MISSING.
3) "confidence_score" MUST be a number between 0 and 1 (the analyzer thresholds on it).
"""

SYSTEM_PROMPT = (
    "You are an expert construction safety inspector with deep knowledge of the "
    "Bangladesh National Building Code (BNBC) and the Bangladesh Labour Act. "
    "You analyze construction site images and report visible safety violations. "
    "You output ONLY valid JSON — no markdown, no backticks, no commentary."
)

# NOTE: literal JSON braces are doubled ({{ }}) so str.format() leaves them intact.
# Only {allowed_ids_json}, {max_items}, and {quality_hint} are substituted.
USER_PROMPT_TEMPLATE = r"""Analyze this construction site image and identify safety violations under Bangladesh construction safety law.

## Allowed violation codes
You MUST use ONLY codes from this exact list. Do not invent new codes, do not abbreviate, and do not modify them. If a hazard you see does not map to any code below, omit it.

{allowed_ids_json}

## What to look for (map what you see to the closest code above)
- Workers without hard hats / helmets  -> a PPE_HELMET_* code
- Workers without high-visibility vests -> a PPE_HIVIS / PPE_HV code
- Workers at height (>2m), on scaffolding or open edges, without a harness -> HEIGHT_NO_HARNESS or a FALL_HARNESS_* code
- Scaffolding missing guardrails, toeboards, bracing, or planks -> a SCAFFOLDING_UNSAFE_* or SCAFFOLD_UNSECURED code
- Open edges / floor openings without guardrails -> FALL_GUARDRAIL_MISSING or NO_GUARDRAIL_OPEN_EDGE
- Excavations without barricades, shoring, or signage -> an EXCAVATION_* code
- Site not fenced/barricaded from the public -> SITE_BARRICADE_MISSING or SITE_FENCING_MISSING
- Materials/debris blocking a road or footpath -> a ROAD_OBSTRUCTION_* code
- Exposed wiring or dangling cables -> ELECTRICAL_HAZARD_EXPOSED_WIRING or ELECTRICAL_DANGLING_CABLES
- Missing warning/caution signage -> NO_WARNING_SIGNS
- Apparent minors performing site work -> a CHILD_LABOUR_* code (report cautiously, confidence reflects certainty)

## Output format (STRICT)
Return a single JSON object with exactly one key, "violations", whose value is an array (possibly empty):

{{
  "violations": [
    {{
      "violation_type": "ONE_OF_THE_ALLOWED_CODES_ABOVE",
      "description": "Specific observation grounded in what is visible in THIS image",
      "severity": "critical|high|medium|low",
      "confidence_score": 0.0,
      "location": "where in the image (e.g. 'left worker on scaffold', 'center', 'foreground')",
      "affected_parties": ["workers"]
    }}
  ]
}}

## Rules
- "violation_type" MUST be copied exactly from the allowed list above.
- "confidence_score" is a number from 0 to 1 expressing how certain you are the violation is really present (0.9 = very clearly visible, 0.5 = plausible but partly obscured, 0.3 = weak/uncertain).
- "affected_parties" is an array containing "workers", "public", or both.
- Report a violation whenever you can reasonably see the hazard; use confidence_score to express uncertainty rather than staying silent.
- Return at most {max_items} violations, most severe first.
- If you truly see no violations, return {{"violations": []}}.
- Image quality context: {quality_hint}. If quality is poor, lower confidence_score accordingly but still report clearly visible hazards.

Return ONLY the JSON object.
"""

# Backwards-compat: keep the old name available in case anything else imports it.
CONSTRUCTION_VIOLATIONS_PROMPT = USER_PROMPT_TEMPLATE