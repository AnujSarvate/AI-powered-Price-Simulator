# Technical Specification — AI-Powered Price Simulator

Version: 0.1.0 (draft)  
Status: Pre-implementation  
Primary stack: **FastAPI + Python 3.11**, **React 18 + TypeScript**, **SQLite** (dev) / **PostgreSQL** (prod)

---

## 1. System context

```mermaid
C4Context
  title System context
  Person(analyst, "Pricing analyst", "Explores scenarios")
  System(app, "Price Simulator", "Simulation, ML, API, UI")
  System_Ext(llm, "LLM API", "Optional explanations")
  Rel(analyst, app, "HTTPS")
  Rel(app, llm, "Optional, server-side")
```

**Boundary:** All pricing logic and ML training run server-side. The client never holds model weights; it receives predictions and simulation time series only.

---

## 2. Domain model

### 2.1 Entities

| Entity | Identity | Mutable fields | Invariants |
|--------|----------|----------------|------------|
