# IncomePilot

**Decision intelligence for covered-call income investors.**

IncomePilot is a full-stack local application that helps long-term NASDAQ investors manage covered calls systematically — scoring candidates, deciding when to roll, and journaling every decision with analytics.

> This is NOT an auto-trading bot. It is a decision-support tool.

---

## Monorepo Structure

```
IncomePilot/
├── backend/                  # Python 3.11 · FastAPI · SQLAlchemy 2.0
│   ├── app/
│   │   ├── engines/          # Core financial logic
│   │   │   ├── recommendation_engine.py
│   │   │   └── roll_engine.py
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── providers/        # Market-data abstraction
│   │   │   ├── base.py       # Abstract interface
│   │   │   └── mock_provider.py
│   │   ├── routers/          # FastAPI route handlers
│   │   ├── schemas/          # Pydantic v2 request/response models
│   │   ├── config.py         # Settings from .env
│   │   ├── database.py       # Engine & session factory
│   │   └── main.py           # App entry-point
│   ├── tests/                # Pytest suite (10+ tests)
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/                 # React 18 · TypeScript · Vite · Tailwind
│   ├── src/
│   │   ├── api/client.ts     # Typed HTTP client
│   │   ├── pages/            # Dashboard, Portfolio, Recommendations,
│   │   │                     # RollAssistant, Settings
│   │   └── types/index.ts    # Shared TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── sample_portfolio.csv      # Sample CSV for bulk import
├── Makefile                  # Dev commands
└── README.md
```

---

## Prerequisites

| Tool       | Version  |
|------------|----------|
| Python     | 3.11+    |
| Node.js    | 18+      |
| MySQL      | 8.0+     |
| npm        | 9+       |

---

## Setup (step by step)

### 1. Clone & enter the repo

```bash
cd IncomePilot
```

### 2. Create the MySQL database

```bash
mysql -u root -proot -e "CREATE DATABASE IF NOT EXISTS incomepilot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

Or use `make db-create`.

### 3. Configure the backend

```bash
cp backend/.env.example backend/.env
# Edit backend/.env if your MySQL credentials differ from root:root
```

### 4. Install dependencies

```bash
make install
# — or manually —
cd backend && pip install -r requirements-dev.txt
cd ../frontend && npm install
```

### 5. Start the backend

```bash
make backend
# Runs: uvicorn app.main:app --reload --port 8000
# Tables are created automatically on first startup.
```

### 6. Start the frontend (in a second terminal)

```bash
make frontend
# Runs: npm run dev → http://localhost:5173
```

### 7. Load demo data

Click **"Load Demo"** on the Portfolio page, or:

```bash
curl -X POST http://localhost:8000/api/holdings/demo
```

---

## Running Tests

```bash
make test            # runs both backend + frontend tests
make test-backend    # pytest only
make test-frontend   # vitest only
```

Backend tests use an **in-memory SQLite** database — no MySQL required for CI.

---

## API Endpoints

| Method | Path                            | Description                      |
|--------|---------------------------------|----------------------------------|
| GET    | /api/health                     | Health check                     |
| GET    | /api/holdings                   | List all holdings                |
| POST   | /api/holdings                   | Create a holding                 |
| PUT    | /api/holdings/:id               | Update a holding                 |
| DELETE | /api/holdings/:id               | Delete a holding                 |
| POST   | /api/holdings/import-csv        | Bulk import from CSV             |
| POST   | /api/holdings/demo              | Load demo portfolio              |
| GET    | /api/recommendations/:symbol    | Top-3 covered call recs          |
| POST   | /api/roll                       | Roll decision engine             |
| GET    | /api/journal                    | List journal entries             |
| POST   | /api/journal                    | Create journal entry             |
| PUT    | /api/journal/:id                | Update journal entry (outcome)   |
| DELETE | /api/journal/:id                | Delete journal entry             |
| GET    | /api/journal/analytics/dashboard| Dashboard analytics              |
| GET    | /api/settings                   | Get strategy config              |
| PUT    | /api/settings                   | Update strategy config           |
| GET    | /api/market/quote/:symbol       | Live quote (from provider)       |
| GET    | /api/market/chain/:symbol       | Option chain (from provider)     |
| GET    | /api/market/earnings/:symbol    | Next earnings date               |

---

## Scoring Formulas

### Covered Call Score (0–100)

```
score = w_yield     × yield_score
      + w_delta_fit × delta_fit_score
      + w_liquidity × liquidity_score
      + w_distance  × distance_score
      + w_earnings  × earnings_safety_score
```

**Default weights:**
| Component        | Weight |
|------------------|--------|
| yield            | 0.35   |
| delta_fit        | 0.25   |
| liquidity        | 0.20   |
| distance         | 0.10   |
| earnings_safety  | 0.10   |

**Sub-score formulas:**

- **Yield score**: `clamp((annualized_yield - min_target) / (2 × min_target), 0, 1)`
- **Delta fit**: 1.0 inside `[target_min, target_max]`, linear decay outside (0 at ±0.20)
- **Liquidity**: `0.6 × clamp(OI / 1000) + 0.4 × clamp(vol / 500)`
- **Distance**: `clamp(1 - |moneyness - 0.05| / 0.10)` — peaks at 5% OTM
- **Earnings safety**: 1.0 if outside blackout window, 0.0 if inside

### Key Metrics

- `premium_yield_pct = mid / spot × 100`
- `annualized_yield_pct = premium_yield_pct × (365 / DTE)`
- `moneyness_pct = (strike - spot) / spot`
- `prob_itm_proxy = |delta|`

### Roll Decision Rules

1. **DTE ≤ 2 + deep ITM + no credit roll** → Accept Assignment
2. **DTE ≤ 2 + deep ITM + credit roll available** → Roll Out / Roll Up & Out
3. **DTE < 5 + ITM (gamma risk)** → Roll Out or Close
4. **OTM + extrinsic > 50% of mid + DTE > 5** → Hold
5. **Credit roll available** → Roll Up & Out (if higher strike) or Roll Out
6. **Default** → Hold

---

## How to Add a Real MarketDataProvider

1. **Create a new file** `backend/app/providers/polygon_provider.py` (or `tradier_provider.py`, etc.).

2. **Import and subclass** `MarketDataProvider` from `app.providers.base`.

3. **Implement all three abstract methods**: `get_quote()`, `get_option_chain()`, `get_earnings_calendar()`. Each must return the corresponding Pydantic schema (`Quote`, `OptionChain`, `EarningsDate`).

4. **Add your API key** to `backend/app/config.py` as a new field (e.g., `polygon_api_key: str = ""`), and set it in `.env`.

5. **Register the provider** in `backend/app/providers/__init__.py` inside the `get_provider()` function — add an `elif name == "polygon":` branch that imports and instantiates your class.

6. **Set the provider** in `.env`: `MARKET_DATA_PROVIDER=polygon`.

7. **Map the API response** to IncomePilot's `OptionContract` schema. The mock provider shows exactly which fields are required (delta, gamma, theta, IV, OI, volume, bid, ask, etc.).

8. **For option chains**, ensure you return contracts for call options across multiple expiry dates within a reasonable DTE window (7–45 days). The recommendation engine filters by DTE, delta, OI, and volume.

9. **Handle rate limits** in your provider. Consider adding `functools.lru_cache` or a TTL cache (e.g., `cachetools`) around `get_option_chain()` to avoid redundant API calls.

10. **Test your provider** by creating `tests/test_polygon_provider.py` with integration tests (can be skipped in CI via `@pytest.mark.skipif(not os.getenv("POLYGON_API_KEY"))`).

11. **No changes needed** to the recommendation engine, roll engine, routers, or frontend — the provider interface is fully decoupled.

12. **Restart the backend** after changing `.env`. The provider is loaded once at startup via `@lru_cache`.

---

## License

Private — for personal use.
