---
title: MACMS Communications Violation Escalation Decision Tree
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# Communications Violation Escalation Decision Tree

```mermaid
flowchart TD
    A([CS-05, CS-08, or CS-13 alert]) --> B[Compile message evidence, participants, and retention references]
    B --> C{Exculpatory evidence present?}
    C -- Yes --> D[Apply Type D suppression review]
    C -- No --> E{High/critical severity or confidence < 0.7?}
    E -- Yes --> F[Route Tier 2 Senior Analyst; SLA 2 hours]
    E -- No --> G[Route Tier 1 Analyst; SLA 4 hours]
    D --> H{Exculpatory evidence sufficient?}
    H -- Yes --> I[Suppress alert and record rationale]
    H -- No --> F
    F --> J{50% SLA elapsed?}
    G --> J
    J -- Yes --> K[Auto-escalate to next tier]
    J -- No --> L[Record human disposition]
    K --> M{Tier 4?}
    M -- Yes --> N[Director/CCO review; SLA 30 minutes]
    M -- No --> L
    I --> O([Close with audit])
    L --> O
    N --> O
```

The decision-support package must identify source communications, participants, evidence references, historical context, and any dissenting agent assessments. Human overrides remain subject to the authority matrix and cooling period.
