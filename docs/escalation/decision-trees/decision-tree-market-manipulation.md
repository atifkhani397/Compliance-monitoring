---
title: MACMS Market Manipulation Escalation Decision Tree
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# Market Manipulation Escalation Decision Tree

```mermaid
flowchart TD
    A([CS-02 or CS-06 alert]) --> B[Collect TM transaction evidence and CS corroboration]
    B --> C{Consensus confidence < 0.7?}
    C -- Yes --> D[Route to Tier 2; SLA 2 hours]
    C -- No --> E{Severity critical?}
    E -- Yes --> F[Route to Tier 3 Manager; SLA 1 hour]
    E -- No --> G[Route to Tier 1 Analyst; SLA 4 hours]
    D --> H{50% SLA elapsed without action?}
    F --> H
    G --> H
    H -- Yes --> I[Auto-escalate one tier]
    H -- No --> J[Human reviews evidence and dissent]
    I --> K{Tier 4?}
    K -- Yes --> L[CCO review; SLA 30 minutes]
    K -- No --> J
    J --> M([Record disposition and feedback])
```

The package must include the transaction pattern, impacted instruments and accounts, cross-agent evidence, confidence, and recommended action. If a regulatory conflict is found during review, the case follows the regulatory-conflict tree and is escalated to legal counsel.
