---
title: MACMS General Escalation Decision Tree
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# General Escalation Decision Tree

```mermaid
flowchart TD
    A([Alert or consensus result]) --> B{Confidence < 0.7?}
    B -- Yes --> C[Create decision-support package]
    B -- No --> D{Severity or trigger requires review?}
    D -- No --> E([Close without human escalation])
    D -- Yes --> C
    C --> F{Required tier?}
    F -- Low/Medium --> G[Assign Tier 1 Analyst; SLA 4 hours]
    F -- High --> H[Assign Tier 2 Senior Analyst; SLA 2 hours]
    F -- Critical/Regulatory --> I[Assign Tier 3 Manager; SLA 1 hour]
    F -- MRIA/Board/C-suite --> J[Assign Tier 4 Director/CCO; SLA 30 minutes]
    G --> K{First human action by 50% SLA?}
    H --> K
    I --> K
    J --> K
    K -- No --> L[Auto-escalate to next tier]
    K -- Yes --> M{Approve, reject, request info, or override?}
    L --> N{Tier 4 reached?}
    N -- No --> K
    N -- Yes --> O[Page CCO; record SLA violation]
    M --> P[Record decision and justification]
    P --> Q{Override authorized?}
    Q -- No --> R[Reject override; retain original state]
    Q -- Yes --> S[Record before/after state and approver]
    R --> T([Close with audit])
    S --> T
```

The escalation service records every transition in memory and in the append-only audit chain. A missed SLA is actionable after 50 percent of the tier SLA has elapsed. Tier 3 and Tier 4 use the on-call route after hours; Tier 4 goes directly to the CCO.
