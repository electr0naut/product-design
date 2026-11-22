# Product Requirements Document: [Project Name]

## Document Control
- **Version:** 1.0
- **Date:** YYYY-MM-DD
- **Product Manager:** 
- **Engineering Lead:** 
- **Design Lead:** 
- **Review Status:** Derived from `review/<product>.json` for this artifact's declared path and current bytes; do not set this by hand.
- **BRD Reference:** [link to canonical `03-brd/<product>-brd.md`]
- **BRD Review:** Check the relevant gate and lane in `review/<product>.json`; approval binds both the declared artifact path and the exact BRD bytes.

---

## 1. Overview
### 1.1 Problem Statement
(From BRD — refined with product lens)

### 1.2 Goals & Non-Goals
**Goals:**
- 

**Non-Goals:**
- 

## 2. User Personas
### Persona 1: [Name]
- **Role:** 
- **Pain points:** 
- **Goals:** 
- **Tech savviness:** 

## 3. Epics & Story Map
One row per story. Number stories US-001, US-002, ... across the whole PRD and
never reuse an ID. Acceptance criteria, dependencies and tasks are written per
epic in phase 06 (`06-backlog/`), after the technical design.

### E01: [Epic Name]
**Goal:** [Outcome this epic delivers]
**Traces to:** BR-001, BR-002

| ID | Story | Persona | Traces to | Priority |
|----|-------|---------|-----------|----------|
| US-001 | As a [persona], I want [action], so that [benefit]. | [Persona] | BR-001 | Must |
| US-002 | | | | Should |

Priority is one of Must, Should, Could, Won't.

## 4. Functional Specifications

### 4.1 Feature: [Name]
- **Description:** 
- **User flow:** 
- **Business rules:** 
- **Error handling:** 
- **Edge cases:** 

### 4.2 API Requirements
| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|--------------|
|          |        |         |              |

### 4.3 External Integrations
| Service | Purpose | API Type | Rate Limits | Cost |
|---------|---------|----------|-------------|------|
|         |         |          |             |      |

## 5. Non-Functional Requirements
- **Performance:** Response time < Xms for Y% of requests
- **Availability:** X% uptime SLA
- **Scalability:** Support X concurrent users, X requests/sec
- **Security:** Authentication, authorization, encryption standards
- **Data retention:** X days/months/years

## 6. Data Requirements
### 6.1 Data Models (high-level)
- 

### 6.2 Data Privacy
- PII handling
- Data residency
- Retention/deletion policies

## 7. UX/UI Requirements
- Wireframes: [link]
- Design system: 
- Accessibility: WCAG 2.1 AA

## 8. Release Plan
| Phase | Features | Target Date | Success Metric |
|-------|----------|-------------|---------------|
| MVP   |          |             |               |
| v1.1  |          |             |               |
| v2.0  |          |             |               |

## 9. Analytics & Metrics
| Metric | Definition | Target | Tracking Method |
|--------|-----------|--------|----------------|
|        |           |        |                |

## 10. Open Questions
- [ ] 
