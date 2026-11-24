# Spec: Compliance Decision Brief

## Purpose
A short compliance decision brief summarising regulatory requirements, compliance obligations, and what's needed to meet them. This is a BRD input, not a standalone gate.

## Scope
- Regulatory requirements applicable to the product
- Compliance obligations (licensing, reporting, record-keeping)
- What's needed to meet each obligation
- Gaps or blockers
- Main uncertainty
- Decision needed

## Sections
1. **Regulatory Requirements**: Which regulations apply (e.g., MiFID II, AML, GDPR)
2. **Compliance Obligations**: Specific obligations under each regulation (licensing, reporting, record-keeping, etc.)
3. **Meeting Obligations**: What's needed to meet each obligation (processes, systems, controls)
4. **Gaps/Blockers**: What's missing or blocking compliance
5. **Main Uncertainty**: Biggest unknown in the compliance assessment
6. **Decision Needed**: What the compliance team needs to decide

## Validation Rules
- Decision layer lines must cite evidence cards `[C1]` for non-Unknown claims
- Evidence cards must have Claim, Source, and Quote fields
- Quote must be an exact line from the BRD
- Cannot claim approval in a draft
- Cannot mix Unknown/none yet with assertions on the same line

## Output
- Path: `03-brd/compliance-decision-brief.md`
- Format: Markdown with decision layer and evidence cards
- Status: Draft for human review

## Tests
- Valid brief with provenance passes validation
- Brief with all Unknown/none yet fields accepted
- Brief claiming approval rejected
- Brief with unstructured evidence cards rejected
