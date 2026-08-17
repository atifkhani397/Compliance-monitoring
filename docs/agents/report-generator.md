---
title: Report Generator Agent Specification
agent_id: agent-rg-001
version: 2.0.0
date: 2026-08-17
status: Phase 2 Complete
---

# Report Generator Agent (agent-rg-001)

## 1. Overview

The Report Generator Agent produces all compliance reports for Meridian Global Bank, including scheduled periodic reports, event-triggered emergency reports, multi-audience adaptations, evidence compilation packages, and regulatory filing drafts. All reports require human authorization before external distribution.

---

## 2. Capability Table

| Capability | Description | Scope | Input Data | Output Data | SLA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Scheduled Reports** | Automated production of daily, weekly, monthly, quarterly, and annual reports per defined templates | All regulatory reporting obligations | Report templates, aggregated compliance data | Formatted reports in multiple formats | Per schedule |
| **Event-Triggered Reporting** | Immediate report generation for critical compliance events including SAR/STR filings | Sub-15-minute generation for critical events | Alert data, evidence compilation | Emergency reports, draft filings | < 15 minutes |
| **Multi-Audience Adaptation** | Automatic adjustment of detail, terminology, and format based on target audience | Board, Management, Operations, Regulator profiles | Audience profile, raw report data | Audience-specific report variants | < 5 minutes |
| **Evidence Compilation** | Automated compilation of supporting evidence including data extracts, communication excerpts | Cross-agent evidence synthesis with source attribution | Evidence references from all agents | Evidence packages with chain of custody | < 10 minutes |
| **Regulatory Filing Preparation** | Generation of regulatory filing drafts in required formats (XBRL, XML, PDF) | SAR, STR, CTR, Form 13F, TRACE, CAT formats | Structured compliance data, filing templates | Draft filings in required formats | Per filing deadline |

---

## 3. Constraints

- **No Autonomous Filing**: Cannot file regulatory reports without human authorization; dual sign-off is required for all external filings.
- **Version-Controlled Templates**: Report templates must be version-controlled; template modifications require change approval workflow.
- **No Privileged Materials**: Cannot include privileged materials (attorney-client, work product) without explicit legal clearance.
- **Restricted Distribution**: Distribution lists are restricted and role-based; no ad-hoc report distribution without compliance officer approval.

---

## 4. Input Interfaces

| Protocol | Source | Data Format | Frequency |
| :--- | :--- | :--- | :--- |
| ALERT Messages | All agents via Orchestrator | MACMS Message (AlertPayload) | Event-driven |
| UPDATE Messages | All agents via Orchestrator | MACMS Message (UpdatePayload) | Event-driven |
| Report Templates | Template repository | Jinja2/XSLT templates | On-change |
| Filing Specifications | Regulatory filing format definitions | XML Schema, XBRL taxonomy | On-change |
| Evidence References | Cross-agent evidence store | JSON (reference IDs, data extracts) | On-demand |

---

## 5. Output Interfaces

| Output Type | Destination | Content | Routing |
| :--- | :--- | :--- | :--- |
| Report Distribution | Compliance officers, Board, Management | Formatted reports (PDF, HTML, Excel) | Internal distribution system |
| Regulatory Filing Drafts | Filing portals (via human approval) | XBRL, XML, PDF in regulatory formats | Human approval gate → filing portal |
| Dashboard API | Compliance dashboard | JSON (report status, metrics, KPIs) | REST API |
| HEARTBEAT | Orchestrator | Agent health, report generation queue, filing deadlines | Direct to heartbeat topic |

---

## 6. Resource Requirements

| Resource | Specification | Notes |
| :--- | :--- | :--- |
| vCPU | 16 | Document generation, template rendering, format conversion |
| Memory | 64 GB RAM | Large report datasets, evidence compilation |
| Storage | SSD | Template repository, report archive, evidence packages |
| Document Engine | Dedicated | PDF/XBRL/XML generation engine |
| Template System | Version-controlled | Jinja2/XSLT template management |

---

## 7. Dual Sign-Off Workflow

The Report Generator implements a mandatory dual sign-off process for all regulatory filings:

```
Report Generated → Primary Review (Compliance Officer) → Secondary Review (Senior Manager)
                                                                      ↓
                                                              Filing Approved
                                                                      ↓
                                                         Regulatory Portal Submission
```

### Sign-Off Rules

1. **Primary Reviewer**: Must be a designated Compliance Officer with domain expertise in the specific regulatory area.
2. **Secondary Reviewer**: Must be a Senior Manager or above, independent from the primary reviewer's reporting line.
3. **Time Constraints**: Filing deadlines trigger automated escalation if sign-offs are not completed within 75% of the filing window.
4. **Audit Trail**: All sign-off decisions, timestamps, reviewer identities, and any modifications are recorded in the cryptographic audit chain.
5. **Rejection Handling**: Rejected filings return to the Report Generator for revision with reviewer comments attached.

---

## 8. Health Check Endpoint

```json
{
  "agent_id": "agent-rg-001",
  "status": "HEALTHY | DEGRADED | UNHEALTHY",
  "uptime_seconds": 86400.0,
  "queue_depth": 8,
  "processed_count": 4521,
  "last_processed_timestamp": "2026-08-17T08:00:00+00:00",
  "capabilities_status": {
    "scheduled_reports": "ACTIVE",
    "event_triggered_reporting": "ACTIVE",
    "multi_audience_adaptation": "ACTIVE",
    "evidence_compilation": "ACTIVE",
    "regulatory_filing_preparation": "ACTIVE"
  },
  "pending_filings": {
    "SAR": 2,
    "Form_13F": 0,
    "TRACE": 1
  },
  "pending_signoffs": 1
}
```
