# Technical Design: [Project Name]

## Document Control
- **Version:** 1.0
- **Date:** YYYY-MM-DD
- **Author:** 
- **PRD Reference:** [link to canonical `04-prd/<product>-prd.md`]
- **PRD Review:** Check the relevant gate and lane in `review/<product>.json`; approval binds the exact PRD bytes, not the document's filename.

---

## 1. Architecture Overview
High-level system architecture diagram description.

### Components
- **API Layer:** FastAPI
- **Database:** PostgreSQL / MongoDB / etc.
- **Cache:** Redis
- **Queue:** Celery / RabbitMQ / etc.
- **External APIs:** [list]

## 2. API Design
See `api-specs/` for OpenAPI specifications.

### Endpoints Summary
| Resource | Endpoint | Methods | Auth |
|----------|----------|---------|------|
|          |          |         |      |

## 3. Data Models
See `data-models/` for detailed schemas.

### Entity Relationship Summary
- 

## 4. External Integrations
See `integrations/` for integration specs.

| Service | Protocol | Auth Method | Failover Strategy |
|---------|----------|-------------|-------------------|
|         |          |             |                   |

## 5. Security Design
- Authentication: JWT / OAuth2 / API Keys
- Authorization: RBAC / ABAC
- Encryption: At rest / In transit
- Secrets management: 

## 6. Infrastructure
- Cloud provider: 
- Container orchestration: 
- CI/CD pipeline: 
- Monitoring: 
- Logging: 

## 7. Performance Considerations
- Expected load:
- Bottlenecks:
- Caching strategy:
- Database indexing:

## 8. Technical Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
|      |        |            |
