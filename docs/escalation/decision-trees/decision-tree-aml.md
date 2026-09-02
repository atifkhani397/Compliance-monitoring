---
title: MACMS AML and Sanctions Escalation Decision Tree
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# AML and Sanctions Escalation Decision Tree

```mermaid
flowchart TD
    A([CS-04, CS-09, or CS-20 alert]) --> B{OFAC, EU, MAS, or sanctions indicator?}
    B -- Yes --> C[Create high-priority package and route Tier 3 Manager; SLA 1 hour]
    B -- No --> D{Confidence < 0.7 or repeated entity?}
    D -- Yes --> E[Route Tier 2 Senior Analyst; SLA 2 hours]
    D -- No --> F[Route Tier 1 Analyst; SLA 4 hours]
    C --> G{Cross-jurisdictional?}
    G -- Yes --> H[Classify Type E and escalate legal counsel]
    G -- No --> I[Review evidence and entity history]
    E --> I
    F --> I
    I --> J{Action by 50% SLA?}
    J -- No --> K[Auto-escalate to next tier]
    J -- Yes --> L[Record disposition and feedback]
    K --> M{Tier 4?}
    M -- Yes --> N[Director/CCO review; SLA 30 minutes]
    M -- No --> I
    L --> O([Close with audit])
    N --> O
    H --> O
```

The package must preserve sanction-list references, jurisdictions, affected entities, evidence custody, regulatory context, and the recommended action. External sanctions feeds and paging are explicitly outside Phase 4.
