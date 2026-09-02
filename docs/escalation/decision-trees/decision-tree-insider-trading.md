---
title: MACMS Insider Trading Escalation Decision Tree
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# Insider Trading Escalation Decision Tree

```mermaid
flowchart TD
    A([CS-01 or CS-10 alert]) --> B{Insider-trading or Rule 10b-5 indicator?}
    B -- No --> C[Use general escalation tree]
    B -- Yes --> D[Compile communications, transaction evidence, and entity history]
    D --> E{Senior management or repeated violation?}
    E -- Yes --> F[Route to Tier 4 Director/CCO; SLA 30 minutes]
    E -- No --> G[Route to Tier 3 Compliance Manager; SLA 1 hour]
    F --> H{Human action by 15 minutes?}
    G --> I{Human action by 30 minutes?}
    H -- No --> J[Page CCO and record SLA breach]
    I -- No --> K[Auto-escalate to Tier 4]
    H -- Yes --> L[Record approve/reject/override]
    I -- Yes --> L
    L --> M{Override of CRITICAL decision?}
    M -- Yes --> N[Require 50+ character justification and secondary approver]
    M -- No --> O([Close with audit])
    N --> O
```

The decision-support package must preserve trading timestamps, communication evidence, applicable regulations, historical violations, and all agent disagreement details. No external notification is implemented in Phase 4.
