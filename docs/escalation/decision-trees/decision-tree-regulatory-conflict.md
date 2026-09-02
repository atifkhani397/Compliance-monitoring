---
title: MACMS Regulatory Conflict Escalation Decision Tree
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# Regulatory Conflict Escalation Decision Tree

```mermaid
flowchart TD
    A([CS-19 or Type E result]) --> B[Compile conflicting jurisdictional requirements]
    B --> C[Classify Type E; set severity CRITICAL]
    C --> D[Route Tier 3 Compliance Manager; SLA 1 hour]
    D --> E{Legal counsel assigned?}
    E -- No --> F[Auto-escalate to Tier 4 Director/CCO]
    E -- Yes --> G[Legal and compliance review]
    F --> H[CCO direct page; SLA 30 minutes]
    H --> G
    G --> I{Requirements reconciled?}
    I -- No --> J[Maintain open status and record unresolved conflict]
    I -- Yes --> K[Record approved regulatory action]
    J --> L([Close only with documented legal resolution])
    K --> L
```

Type E cannot be suppressed by numerical agreement between agents. The package must retain each jurisdiction, requirement, evidence source, applicable enforcement context, and the reason legal counsel was engaged.
