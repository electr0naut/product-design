# Spec: Risk Decision Brief

## Purpose
A short risk decision brief summarising how and whether we can model the product's risks. This is a BRD input, not a standalone gate.

## Scope
- Risk categories (market, credit, operational, liquidity)
- Risk models and assumptions
- Risk limits and controls
- Risk measurement and reporting
- Main uncertainty
- Decision needed

## Sections
1. **Risk Categories**: Which risk categories apply (market, credit, operational, liquidity)
2. **Risk Models**: What models are used to measure each risk
3. **Risk Limits**: What limits are set for each risk
4. **Risk Controls**: What controls are in place to manage each risk
5. **Risk Measurement**: How risks are measured and reported
6. **Main Uncertainty**: Biggest unknown in the risk assessment
7. **Decision Needed**: What the risk team needs to decide

## Validation Rules
- Decision layer lines must cite evidence cards `[C1]` for non-Unknown claims
- Evidence cards must have Claim, Source, and Quote fields
- Quote must be an exact line from the BRD
- Cannot claim approval in a draft
- Cannot mix Unknown/none yet with assertions on the same line

## Output
- Path: `03-brd/risk-decision-brief.md`
- Format: Markdown with decision layer and evidence cards
- Status: Draft for human review

## Tests
- Valid brief with provenance passes validation
- Brief with all Unknown/none yet fields accepted
- Brief claiming approval rejected
- Brief with unstructured evidence cards rejected
