## Mercandes-api-inventory

Deterministic inventory API (F3) for MercadAndes.

## What this project does

This API has two primary responsibilities:

1. **Stock calculation**: Calculates available units for a (SKU, store) pair using a SHA-256 hash. The result is deterministic: the same `(seed, sku, store_id)` always returns the same stock. This endpoint does **not** need a database.
2. **Seller inventory API (F3)**: Simulated REST JSON service providing seller catalog and paginated inventory with:
   - **>= 3,000 sellers** persisted in PostgreSQL.
   - **50,000 SKUs** catalog pool (`SKU-00001` through `SKU-50000`).
   - **10-minute snapshot updates**: Quantities and timestamps refresh deterministically every 10 minutes.
   - **Authentication**: Secured via Bearer tokens.
   - **Fault injection & rate limiting**: Intermittent HTTP 429 (Rate limit) and HTTP 503 (Service unavailable) errors on >= 3% of requests.
   - **SKU filtering and direct retrieval**: Query by seller and SKU directly or filter the paginated catalog.

---

## How to run (step by step)

Follow these steps in order. Do not skip any step.

### Step 1: Copy environment variables

```powershell
Copy-Item .env.example .env
```

Edit `.env` if you need to change database credentials or tokens. The defaults should work for local testing.

### Step 2: Install dependencies and activate environment

Install dependencies with `uv`:

```powershell
uv sync --locked
```

*(Opcional)* Si prefieres activar el entorno virtual manualmente en PowerShell (en lugar de usar `uv run`):

```powershell
.\.venv\Scripts\Activate.ps1
```

```

### Step 3: Load example sellers into PostgreSQL (REQUIRED for sellers endpoint)

Before you can test the seller inventory endpoint, you must load sellers into your PostgreSQL database. Run this command:

```powershell
uv run python -m inventory.infrastructure.persistence.seed_sellers
```

This script:

- Reads your database credentials securely from `.env` (no passwords are hardcoded)
- Creates the `public.sellers` table if it does not exist
- Inserts 3,000 sellers (satisfying the >= 3,000 sellers requirement)

You should see output like:

```
Successfully loaded 3000 sellers into PostgreSQL.
Example seller_ids available for Swagger:
  - SEL-001: MercaAndes Retail Colombia
  - SEL-ABC: Test Seller
  - SEL-3P-101: AndesMarket Global
  - SEL-002: MercaAndes Retail Peru
  - SEL-0001: MercaAndes Express PE 1
```

### Step 4: Start the API

**Option A — Run as a Python module (Recomendado):**

```powershell
uv run python -m inventory.presentation.main
```

*(Si activaste el `.venv`: `python -m inventory.presentation.main`)*

**Option B — Run directly with uvicorn (con recarga automática para desarrollo):**

```powershell
uv run uvicorn inventory.presentation.fastapi.main:app --host 0.0.0.0 --port 8000 --reload
```

*(Si activaste el `.venv`: `uvicorn inventory.presentation.fastapi.main:app --host 0.0.0.0 --port 8000 --reload`)*

```

The API will be available at `http://localhost:8000`.

---

## How to test in Swagger UI

Open your browser at: `http://localhost:8000/docs`

---

### Endpoint 1: Deterministic Stock (NO database needed, NO authentication needed)

Use this endpoint to test stock calculation. You can type **any text** in `sku` and `store_id` — it does not need to exist in a database.

**URL:** `GET /api/v1/inventory/stock`

| Field         | What to type                   | Example value |
| ------------- | ------------------------------ | ------------- |
| `sku`       | Any product code (text)        | `SKU-001`   |
| `store_id`  | Any store code (text)          | `STO-001`   |
| `seed`      | Any positive integer           | `42`        |
| `max_stock` | Any number between 1 and 10000 | `450`       |

**Steps in Swagger:**

1. Click on `GET /api/v1/inventory/stock`
2. Click **Try it out**
3. Enter the example values from the table above
4. Click **Execute**

**Example response:**

```json
{
  "sku": "SKU-001",
  "store_id": "STO-001",
  "seed": 42,
  "quantity": 123,
  "max_stock": 450,
  "is_available": true
}
```

> The `quantity` is deterministic: same inputs always give the same result, but the exact number depends on the SHA-256 hash, so your number may be different from 123.

---

### Endpoint 2: List all sellers (NO authentication needed, database needed)

Use this endpoint to see which `seller_id` values exist in your database. You must have run Step 3 (seed_sellers) first.

**URL:** `GET /api/v1/sellers`

**Steps in Swagger:**

1. Click on `GET /api/v1/sellers`
2. Click **Try it out**
3. Click **Execute**

**Example response:**

```json
[
  {
    "seller_id": "SEL-001",
    "name": "MercaAndes Retail Colombia",
    "seller_type": "own",
    "country": "CO"
  },
  {
    "seller_id": "SEL-ABC",
    "name": "Test Seller",
    "seller_type": "own",
    "country": "CO"
  },
  {
    "seller_id": "SEL-3P-101",
    "name": "AndesMarket Global",
    "seller_type": "third_party",
    "country": "CL"
  },
  {
    "seller_id": "SEL-002",
    "name": "MercaAndes Retail Peru",
    "seller_type": "own",
    "country": "PE"
  }
]
```

**Copy any `seller_id` from this list** — for example: `SEL-001`

---

### Endpoint 3: Get a seller by ID (NO authentication needed)

Use this endpoint to retrieve the details of a single seller by their `seller_id`.

**URL:** `GET /api/v1/sellers/{seller_id}`


| Field       | What to type      | Example value |
| ------------- | ------------------- | --------------- |
| `seller_id` | Seller identifier | `SEL-001`     |

**Steps in Swagger:**

1. Click on `GET /api/v1/sellers/{seller_id}`
2. Click **Try it out**
3. Enter `SEL-001` in the `seller_id` field
4. Click **Execute**

**Example response:**

```json
{
  "seller_id": "SEL-001",
  "name": "MercaAndes Retail Colombia",
  "seller_type": "own",
  "country": "CO"
}
```

---

### Endpoint 4: Get seller inventory (REQUIRES authentication and seller_id)

**Prerequisites:**

1. You must have run Step 3 (seed_sellers) so sellers exist in PostgreSQL.
2. You must copy a `seller_id` from Endpoint 2 above.
3. You must have a valid Bearer token.

**URL:** `GET /api/v1/sellers/{seller_id}/inventory`

> Inventory refreshes deterministically every 10 minutes from a pool of 50,000 SKUs. At least 3% of requests return simulated rate-limit or service errors (HTTP 429 / 503). You can optionally filter by adding query parameter `sku=SKU-XXXXX`.


| Field           | What to type                              | Example value      |
| ----------------- | ------------------------------------------- | -------------------- |
| `seller_id`     | Copy from Endpoint 2 response             | `SEL-001`          |
| `page`          | Leave as default                          | `1`                |
| `limit`         | Leave as default                          | `10`               |
| `sku`           | (Optional) Product SKU filter             | `SKU-00042`        |
| `Authorization` | Click **Authorize** button, paste a token | `token-seller-123` |

---

### Endpoint 5: Get seller inventory for a single SKU (REQUIRES authentication)

Retrieve the stock for a single SKU belonging to a seller.

**URL:** `GET /api/v1/sellers/{seller_id}/inventory/{sku}`


| Field           | What to type                              | Example value      |
| ----------------- | ------------------------------------------- | -------------------- |
| `seller_id`     | Copy from Endpoint 2 response             | `SEL-001`          |
| `sku`           | Product SKU                               | (From Endpoint 4)  |
| `Authorization` | Click **Authorize** button, paste a token | `token-seller-123` |

**Valid tokens (from your `.env` file):**

- `token-seller-123`
- `bearer-token-mercaandes-2026`
- `test-token`

**Steps in Swagger:**

1. Click the **Authorize** button (top right of the page)
2. In the `bearerAuth` field, paste one of the valid tokens above (for example: `token-seller-123`)
3. Click **Authorize**, then close the dialog
4. Click on `GET /api/v1/sellers/{seller_id}/inventory`
5. Click **Try it out**
6. In the `seller_id` field, paste the ID you copied from Endpoint 2 (for example: `SEL-001`)
7. Click **Execute**

**Example response:**

```json
{
  "seller_id": "SEL-001",
  "page": 1,
  "limit": 10,
  "total_items": 20,
  "total_pages": 2,
  "data": [
    {
      "sku": "SKU-00001",
      "quantity": 45,
      "updated_at": "2026-10-05T12:00:00Z"
    },
    {
      "sku": "SKU-00007",
      "quantity": 120,
      "updated_at": "2026-10-05T12:00:00Z"
    }
  ]
}
```

---

## Summary: exact values to copy and paste

If you just want working values without thinking, use these:


| Endpoint                                          | Field           | Copy this value                            |
| --------------------------------------------------- | ----------------- | -------------------------------------------- |
| `GET /api/v1/inventory/stock`                     | `sku`           | `SKU-001`                                  |
| `GET /api/v1/inventory/stock`                     | `store_id`      | `STO-001`                                  |
| `GET /api/v1/inventory/stock`                     | `seed`          | `42`                                       |
| `GET /api/v1/inventory/stock`                     | `max_stock`     | `450`                                      |
| `GET /api/v1/sellers`                             | (none)          | Just click Execute                         |
| `GET /api/v1/sellers/{seller_id}`                 | `seller_id`     | `SEL-001`                                  |
| `GET /api/v1/sellers/{seller_id}/inventory`       | `seller_id`     | `SEL-001`                                  |
| `GET /api/v1/sellers/{seller_id}/inventory`       | `Authorization` | `token-seller-123`                         |
| `GET /api/v1/sellers/{seller_id}/inventory/{sku}` | `seller_id`     | `SEL-001`                                  |
| `GET /api/v1/sellers/{seller_id}/inventory/{sku}` | `sku`           | (Any SKU from inventory, e.g. `SKU-23229`) |
| `GET /api/v1/sellers/{seller_id}/inventory/{sku}` | `Authorization` | `token-seller-123`                         |

---

## Health check (verify the API is running)

```bash
curl http://localhost:8000/
```

Expected response:

```json
{
  "status": "ok",
  "service": "api-inventory",
  "version": "1.0.0"
}
```

---

## Folder structure

```
api-inventory/
├── pyproject.toml
├── .env.example
├── .env
├── .gitignore
├── Dockerfile
├── README.md
├── src/
│   └── inventory/
│       ├── __init__.py
│       ├── config.py
│       ├── stock.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   ├── seller.py
│       │   │   └── stock.py
│       │   └── repositories/
│       │       ├── __init__.py
│       │       ├── seller_repository.py
│       │       └── stock_repository.py
│       ├── application/
│       │   ├── __init__.py
│       │   ├── use_cases/
│       │   │   ├── __init__.py
│       │   │   ├── calculate_stock.py
│       │   │   ├── dto.py
│       │   │   ├── get_seller_inventory.py
│       │   │   └── list_sellers.py
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── persistence/
│       │       ├── __init__.py
│       │       ├── seed_sellers.py
│       │       ├── sqlalchemy_stock_repository.py
│       │       └── sqlalchemy_seller_repository.py
│       └── presentation/
│           ├── __init__.py
│           ├── main.py
│           └── fastapi/
│               ├── __init__.py
│               ├── deps.py
│               ├── main.py
│               └── routes/
│                   ├── __init__.py
│                   ├── sellers.py
│                   └── stock.py
├── tests/
│   ├── __init__.py
│   └── unit/
│       ├── __init__.py
│       ├── test_inventory.py
│       └── test_sellers.py
└── .github/workflows/
    └── ci.yml
```

---

## Environment variables


| Variable                    | Description                           | Default value                                              |
| ----------------------------- | --------------------------------------- | ------------------------------------------------------------ |
| `APP_ENV`                   | Runtime environment                   | `development`                                              |
| `MASTER_SEED`               | Seed for deterministic catalog        | `42`                                                       |
| `MAX_STOCK`                 | Maximum stock per item                | `450`                                                      |
| `API_HOST`                  | API host                              | `0.0.0.0`                                                  |
| `API_PORT`                  | API port                              | `8000`                                                     |
| `ERROR_RATE`                | Fault injection rate (0 to 1)         | `0.03`                                                     |
| `ENABLE_NEGATIVE_INVENTORY` | Allow negative inventory              | `true`                                                     |
| `VALID_TOKENS`              | Valid Bearer tokens (comma-separated) | `token-seller-123,bearer-token-mercaandes-2026,test-token` |
| `POS_DB_HOST`               | PostgreSQL host                       | `localhost`                                                |
| `POS_DB_PORT`               | PostgreSQL port                       | `5432`                                                     |
| `POS_DB_NAME`               | Database name                         | Change_me                                                  |
| `POS_DB_USER`               | PostgreSQL user                       | Change_me                                                  |
| `POS_DB_PASSWORD`           | PostgreSQL password                   | Change_me                                                  |

---

## Running tests and linter locally

To run the automated unit tests (17 tests) and code checks locally:

```powershell
# Run unit tests
uv run pytest

# Run linter
uv run ruff check
```

---

## CI/CD

Every push to `main` or `develop` triggers `.github/workflows/ci.yml`:

1. `uv sync --locked --dev`
2. `uv run ruff check`
3. `uv run pytest`
4. Docker image build and push to GitHub Container Registry (GHCR)
   ===============================================================

# Inventory_Api

>>>>>>> 3cffdb9f1f34ca24db241f565b82d70bc6a3d462
>>>>>>>
>>>>>>
>>>>>
>>>>
>>>
>>
