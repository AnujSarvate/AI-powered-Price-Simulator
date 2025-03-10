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
| `Product` | `product_id: UUID` | name, sku, unit_cost, list_price, category_id, elasticity ε | `unit_cost ≥ 0`, `list_price > 0`, `ε > 0` |
| `Category` | `category_id: UUID` | name, default_ε | `default_ε > 0` |
| `Scenario` | `scenario_id: UUID` | name, horizon_weeks, products[], market_config | `horizon_weeks ∈ [1, 104]` |
| `MarketConfig` | embedded in scenario | seasonality_curve, promos[], competitor_rule | promo windows non-overlapping per product |
| `SimulationRun` | `run_id: UUID` | scenario snapshot, seed, results[] | immutable after `status=completed` |
| `DemandModel` | `model_id: UUID` | artifact path, metrics, feature_schema_version | trained only on server |

### 2.2 Value objects

```python
# Canonical types (Python); mirror in TypeScript via OpenAPI codegen

@dataclass(frozen=True)
class Money:
    amount: Decimal  # quantized to 4 dp internally, 2 dp in API JSON

@dataclass(frozen=True)
class WeeklyPoint:
    week_index: int  # 0-based
    price: Money
    quantity: float
    revenue: Money
    gross_profit: Money
    margin_ratio: float  # (price - cost) / price
```

---

## 3. Demand and simulation kernel

### 3.1 Constant-elasticity demand (baseline)

For product \(i\) at week \(t\):

\[
Q_i(p, t) = Q_{0,i} \cdot \left(\frac{p}{p_{0,i}}\right)^{-\varepsilon_i} \cdot S_i(t) \cdot M_i(t)
\]

- \(S_i(t)\): seasonality multiplier, piecewise constant or Fourier terms (configurable).
- \(M_i(t)\): promo multiplier (e.g. `0.8` price → effective demand boost via equivalent price reduction).

**Implementation:** pure function `demand_qty(price, params) -> float`; no I/O.

### 3.2 Cross-elasticity (optional module)

CES-lite pairwise adjustment for catalog size ≤ 20:

\[
Q_i \leftarrow Q_i \cdot \prod_{j \neq i} \left(\frac{p_j}{p_{j,0}}\right)^{\gamma_{ij}}
\]

Store \(\gamma_{ij}\) in sparse matrix (CSR) for O(n) updates per week.

### 3.3 Weekly simulation loop

```
INPUT: scenario_snapshot, rng_seed
FOR t IN 0 .. horizon_weeks-1:
  FOR each product i:
    p_i <- pricing_policy(i, t, state)   # user price path or competitor rule
    q_i <- demand_qty(p_i, t, params_i, cross_state)
    q_i <- min(q_i, inventory_i)         # if inventory enabled
    record WeeklyPoint(i, t, p_i, q_i, ...)
    update inventory_i, cumulative profit
OUTPUT: SimulationResult { series: Dict[product_id, List[WeeklyPoint]], aggregates }
```

**Complexity:** \(O(W \cdot P)\) per run; target \(W=52, P=50\) ≪ 1 ms in Python with NumPy vectorization over products per week.

### 3.4 Stochastic mode

Monte Carlo with `N` draws (`N` default 500, cap 5000):

- Sample \(\varepsilon \sim \mathcal{N}(\hat\varepsilon, \sigma_\varepsilon)\), truncate at `ε_min`.
- Sample multiplicative shock \(\eta \sim \text{LogNormal}(0, \sigma_\eta)\) on \(Q_0\).

Report per-week **p10 / p50 / p90** profit across draws. Seed-controlled for reproducibility.

---

## 4. Optimization subsystem

### 4.1 Single-product static optimum (unconstrained)

Maximize \(\pi(p) = (p - c) \cdot Q_0 (p/p_0)^{-\varepsilon}\).

Closed form for \(\varepsilon > 1\):

\[
p^* = c \cdot \frac{\varepsilon}{\varepsilon - 1}
\]

(Validate against numeric optimizer in tests.)

### 4.2 Constrained optimization (production path)

Problem per product:

\[
\max_{p \in [p_{\min}, p_{\max}]} \ (p - c) \cdot Q(p)
\]

Subject to:

- `margin_ratio(p) ≥ m_min`
- `|p - p_{t-1}| ≤ Δ_max` (dynamic pricing path)

**Algorithm:**

1. If no dynamic constraint and closed form valid → use \(p^*\), clip to `[p_min, p_max]`.
2. Else **golden-section search** on log-price axis (unimodal assumption documented) or **uniform grid** 200 steps if promo kinks break unimodality.
3. Multi-product: sequential per product (document as greedy) or small joint grid for P ≤ 3.

**API:** `POST /v1/optimize` returns `{ recommended_price, expected_profit, binding_constraints[] }`.

---

## 5. Machine learning pipeline

### 5.1 Problem formulation

**Supervised regression:** predict `units_sold` from feature vector \(\mathbf{x}\).

| Feature | Type | Notes |
|---------|------|-------|
| `log_price` | float | \(\log(p + \epsilon)\) |
| `promo_active` | bool | |
| `week_of_year` | int | cyclical sin/cos encoding |
| `category_*` | one-hot | |
| `lag_1_sales` | float | optional |
| `competitor_price_ratio` | float | \(p / p_{comp}\) |

**Targets:** `units_sold` (float); optional quantile heads later.

### 5.2 Training flow

```
CSV upload or synthetic generator
  -> schema validation (pandera)
  -> train/test split (time-based, last 20% weeks)
  -> Pipeline: ColumnTransformer + StandardScaler + Ridge | RandomForestRegressor
  -> cross_val on train (TimeSeriesSplit, n_splits=5)
  -> persist with joblib + metadata JSON (features, metrics, git hash)
```

**Serving:** `POST /v1/models/{id}/predict` with batch rows; latency target p95 < 50 ms for 100 rows.

### 5.3 Evaluation protocol

| Metric | Baseline A (mean) | Baseline B (elasticity only) | Model |
|--------|-------------------|------------------------------|-------|
| MAE | ✓ | ✓ | ✓ |
| RMSE | ✓ | ✓ | ✓ |
| MAPE | ✓ | ✓ | ✓ |
| R² | ✓ | ✓ | ✓ |

Store results in `DemandModel.metrics` for UI display.

### 5.4 Integration with simulator

Hybrid mode (default):

\[
Q_{\text{final}} = \alpha \cdot Q_{\text{ML}} + (1 - \alpha) \cdot Q_{\text{elasticity}}
\]

with \(\alpha \in [0,1]\) scenario-configurable; default `0.3` when model MAPE < threshold else `0`.

---

## 6. API specification (REST, OpenAPI 3.1)

Base URL: `/v1`  
Auth: `Bearer` JWT (optional MVP: API key header for single tenant).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | `{ status, version, db_ok }` |
| CRUD | `/products` | Standard pagination `?limit=&cursor=` |
| CRUD | `/scenarios` | Embeds `market_config` JSON schema v1 |
| POST | `/scenarios/{id}/simulate` | Body: `{ seed?, mode: deterministic|monte_carlo, n_draws? }` |
| GET | `/runs/{run_id}` | Full time series + aggregates |
| POST | `/optimize` | Body: `{ product_id, scenario_id?, constraints }` |
| POST | `/models/train` | multipart CSV or `{ use_synthetic: true, n_rows }` |
| GET | `/models/{id}` | Metadata + metrics |
| POST | `/models/{id}/predict` | Batch inference |
| POST | `/explain` | Optional LLM; body: `{ run_id }` → cached narrative |

**Error envelope:**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "human readable",
    "details": [{ "field": "elasticity", "issue": "must be > 0" }]
  }
}
```

**Idempotency:** `POST /simulate` accepts `Idempotency-Key` header; duplicate returns same `run_id` if payload hash matches within 24h.

---

## 7. Persistence

### 7.1 Schema (PostgreSQL-compatible)

```sql
CREATE TABLE products (
  product_id UUID PRIMARY KEY,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  unit_cost NUMERIC(12,4) NOT NULL,
  list_price NUMERIC(12,4) NOT NULL,
  category_id UUID REFERENCES categories(category_id),
  elasticity NUMERIC(8,4) NOT NULL CHECK (elasticity > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE scenarios (
  scenario_id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  horizon_weeks INT NOT NULL CHECK (horizon_weeks BETWEEN 1 AND 104),
  market_config JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE simulation_runs (
  run_id UUID PRIMARY KEY,
  scenario_id UUID NOT NULL REFERENCES scenarios(scenario_id),
  scenario_snapshot JSONB NOT NULL,
  mode TEXT NOT NULL,
  seed BIGINT,
  status TEXT NOT NULL,
  result JSONB,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

CREATE INDEX idx_runs_scenario ON simulation_runs(scenario_id, completed_at DESC);
```

Migrations: **Alembic**; SQLite for local dev with same DDL (adjusted types).

---

## 8. Frontend architecture

- **State:** TanStack Query for server cache; URL query params for active `scenario_id` / `run_id`.
- **Charts:** Recharts; downsample series > 500 points for render (LTTB algorithm).
