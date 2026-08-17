---
title: MACMS Cryptographic Audit Trail Specification
date: 2026-08-17
version: 1.0.0
status: Approved
---

# MACMS Cryptographic Audit Trail Specification

## 1. Overview
Details the SHA-256 hash-chaining mechanism that links all system decisions into a tamper-evident sequence.

## 2. Hash Chain Mechanics
$$\text{Hash}_n = \text{SHA256}(\text{Hash}_{n-1} \parallel \text{Serialize}(\text{Entry}_n))$$
- Initial seed entry: $\text{Hash}_0 = \text{SHA256}("MERIDIAN\_GENESIS\_BLOCK")$.
- Deterministic JSON formatting (`sort_keys=True`).
