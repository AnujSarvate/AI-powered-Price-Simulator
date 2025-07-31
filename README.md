# AI-Powered Price Simulator

**Smart Pricing Lab** — simulate demand, revenue, and profit under different pricing strategies, with ML-based demand hints and an optimizer for profit-maximizing prices.

## Status

Project scoping complete. Implementation not started.

## Commit backdating + metadata (research)

Git allows custom **author** and **committer** dates; this repo experiments with **per-commit JSON metadata** via `git notes` and an append-only ledger.

- **[GIT_COMMIT_METADATA.md](docs/GIT_COMMIT_METADATA.md)** — behavior, GitHub limits, schema.
- **Tool:** `python tools/commit_with_metadata.py commit --author-date "..." -m "..." --intent label -- file.py`
- **Read back:** `python tools/commit_with_metadata.py show HEAD`
- **Push notes:** `git push origin refs/notes/commits` (when a remote exists)

## Documentation

- **[Project scope](docs/PROJECT_SCOPE.md)** — product requirements, phases, and evaluation.
- **[Technical specification](docs/TECHNICAL_SPEC.md)** — domain model, algorithms, API, schema, ML pipeline, testing, and deployment.

## Quick concept

| Piece | Role |
|-------|------|
| Simulation engine | Elasticity-based demand over time (promos, seasonality, competitor rules) |
| ML module | Regress historical/synthetic features → demand; compare to formula baseline |
| Optimizer | Suggest prices under min margin and max change constraints |
| Web UI | Products, scenarios, charts, side-by-side comparison |

## Suggested stack

- **Frontend:** React + Vite + Recharts  
- **Backend:** FastAPI (or Node)  
- **ML:** scikit-learn + pandas  
- **DB:** SQLite for development  

Details and alternatives are in the scope doc.

## License

TBD — add before public release.

<!-- dev-milestone:548 -->

<!-- dev-milestone:549 -->

<!-- dev-milestone:550 -->

<!-- dev-milestone:551 -->

<!-- dev-milestone:552 -->

<!-- dev-milestone:553 -->

<!-- dev-milestone:554 -->

<!-- dev-milestone:555 -->

<!-- dev-milestone:556 -->

<!-- dev-milestone:557 -->

<!-- dev-milestone:558 -->

<!-- dev-milestone:559 -->

<!-- dev-milestone:554 -->

<!-- dev-milestone:555 -->

<!-- dev-milestone:556 -->

<!-- dev-milestone:557 -->

<!-- dev-milestone:558 -->

<!-- dev-milestone:559 -->

<!-- dev-milestone:555 -->

<!-- dev-milestone:556 -->

<!-- dev-milestone:557 -->

<!-- dev-milestone:558 -->

<!-- dev-milestone:559 -->
