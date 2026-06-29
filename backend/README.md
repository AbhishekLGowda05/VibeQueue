# VibeQueue Backend

FastAPI backend for the VibeQueue pilot — the interactive venue music queue system.

## Quick Start (Local Development)

```bash
# 1. Clone and set up environment
git clone https://github.com/your-org/vibequeue-backend.git
cd vibequeue-backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your actual keys

# 3. Start infrastructure (PostgreSQL + Redis)
docker compose up -d

# 4. Run database migrations
alembic upgrade head

# 5. Seed pilot data
python scripts/seed_db.py
python scripts/seed_catalogue.py   # Update venue IDs first

# 6. Start the API server
uvicorn app.main:app --reload --port 8000

# 7. Start Celery worker (separate terminal)
celery -A app.core.celery.celery_app worker --loglevel=info

# 8. Start Celery Beat scheduler (separate terminal)
celery -A app.core.celery.celery_app beat --loglevel=info
```

API docs available at: http://localhost:8000/docs (development only)

## Running Tests

```bash
pytest tests/unit/ -v                    # Unit tests only (no infra needed)
pytest tests/integration/ -v             # Integration tests (needs DB + Redis)
pytest --cov=app --cov-report=html       # With coverage report
locust -f tests/load/locustfile.py       # Load tests (open http://localhost:8089)
```

## Key Commands

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "add column X to songs"

# Create a new venue interactively
python scripts/create_venue.py

# Validate all YouTube video IDs
python scripts/validate_youtube_ids.py

# Generate weekly report for a venue
python scripts/generate_report.py --venue-id <uuid>

# Lint and format
ruff check app/ && ruff format app/
```

## Architecture Overview

```
Guest Phone (mobile data)
       ↓ HTTPS
   Cloudflare CDN
       ↓
     Nginx
       ↓
   FastAPI (Uvicorn / Gunicorn)
   ├── REST API  (/api/v1/*)
   └── WebSockets (/api/v1/ws/*)
       ↓           ↓
  PostgreSQL     Redis
  (source of   (live queue
    truth)       state +
                pub/sub)
       ↓
    Celery
  (background
    jobs)
```

## Project Structure

```
app/
├── main.py              # FastAPI app factory
├── core/                # Config, DB, Redis, security, logging
├── api/v1/              # Route handlers, dependencies, middleware
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic (queue engine, billing, playback)
├── repositories/        # Database access layer
├── workers/             # Celery tasks and beat schedule
├── utils/               # Shared utilities
└── exceptions/          # Domain exceptions
```

## Environment Variables

See `.env.example` for all required variables with descriptions.

## Deployment (Pilot — Railway)

```bash
railway login
railway link
railway up
railway run alembic upgrade head
```

## Support

WhatsApp group per venue for operational support.
Sentry dashboard for error monitoring.


# VibeQueue Backend — Complete Codebase Guide

> **Who this is for:** You, the founder, who needs to understand every file deeply enough to direct a developer, debug a problem at 11pm on a Friday, and make confident decisions about what to build next. Every file is explained with real-world scenarios from the Friday night bar context. No assumed knowledge. No glossed-over parts.

---

## How to Read This Document

This guide follows the journey of a **single Friday night request** through the entire codebase. The scenario:

> Arjun is at Table 7 at a Koramangala bar. He scans the QR code, enters the table code the waiter gave him, finds "Kesariya" by Arijit Singh, and pays ₹25 to boost it to position 3. The song plays. His bill shows ₹25. He pays and leaves.

Every file in this codebase either directly handles part of that journey, or supports the infrastructure that makes it work. You will see exactly where each file lives in that journey.

---

## Table of Contents

1. [The Mental Model — How the Layers Talk to Each Other](#1-the-mental-model)
2. [Root Configuration Files](#2-root-configuration-files)
3. [app/core/ — The Foundation Everything Sits On](#3-appcore)
4. [app/main.py — The Starting Point](#4-appmainpy)
5. [app/models/ — The Database Tables](#5-appmodels)
6. [app/schemas/ — The Data Contracts](#6-appschemas)
7. [app/repositories/ — The Database Access Layer](#7-apprepositories)
8. [app/services/ — The Business Logic](#8-appservices)
9. [app/api/v1/ — The HTTP Layer](#9-appapiv1)
10. [app/workers/ — The Background Jobs](#10-appworkers)
11. [app/utils/ — Shared Tools](#11-apputils)
12. [app/exceptions/ — The Error System](#12-appexceptions)
13. [alembic/ — Database Migrations](#13-alembic)
14. [tests/ — The Safety Net](#14-tests)
15. [scripts/ — Operations Toolkit](#15-scripts)
16. [nginx/ — The Front Door](#16-nginx)
17. [Docker Files — The Deployment Layer](#17-docker-files)
18. [.github/workflows/ — Automated Pipeline](#18-githubworkflows)
19. [The Complete Friday Night Request — Full Trace](#19-complete-request-trace)
20. [How to Add a New Feature](#20-how-to-add-a-new-feature)
21. [Common Tasks Reference](#21-common-tasks-reference)

---

## 1. The Mental Model

Before touching any file, understand this layering. Every feature request flows through these layers in order — top to bottom on the way in, bottom to top on the way out.

```
┌─────────────────────────────────────────────────────┐
│  GUEST PHONE / VENUE LAPTOP / AMBIENT TV             │
│  (these are NOT in this codebase — they're frontend) │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────┐
│  app/api/v1/routes/  ← "What URL did they hit?"     │
│  app/api/v1/dependencies/ ← "Who is this person?"   │
│  app/api/v1/middleware/ ← "Log this. Handle errors." │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  app/services/  ← "What should actually happen?"    │
│  (queue_engine.py lives here — the brain)           │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  app/repositories/ ← "Read/write the database"      │
│  (never write SQL anywhere else)                    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  PostgreSQL (permanent data)                        │
│  Redis (live queue state + pub/sub)                 │
└─────────────────────────────────────────────────────┘
```

**The rule:** Routes call Services. Services call Repositories. Repositories touch the database. If you ever find yourself writing a database query inside a route file, or business logic inside a repository — something has gone wrong.

**Why this layering?** Because when you need to change the database (say, from PostgreSQL to something else), you only touch repositories. When you add a new API endpoint, you only add a new route. The rest stays the same.

---

## 2. Root Configuration Files

These files live at the very top of the project. They configure the project as a whole — not individual features.

---

### `.gitignore`

**What it does:** Tells Git which files to never commit to version control.

**Why it matters for you:** The most important entries are `.env` (your real API keys — never committed) and `.venv/` (your Python environment — never committed, too large). The `.env.example` IS committed because it's a template with no real values.

**Real-world relevance:** If you accidentally commit your `RAZORPAY_KEY_SECRET` to GitHub, Razorpay's bots will detect it within minutes and disable the key. This file prevents that.

**What's in it (grouped by purpose):**
- Python runtime files (`__pycache__/`, `*.pyc`) — auto-generated, never commit
- Environment files (`.env`, `.env.local`, `.env.production`) — contain secrets
- IDE folders (`.vscode/`, `.idea/`) — editor preferences, personal to each developer
- Test artifacts (`htmlcov/`, `.pytest_cache/`) — generated by running tests
- Local Docker overrides (`docker-compose.override.yml`) — developer's personal tweaks

---

### `requirements.txt`

**What it does:** Lists every Python package the project depends on, with exact pinned versions.

**Why exact versions?** Imagine you're running the pilot successfully. Six months later you deploy to a new server and `fastapi` has released a major update that changes how authentication works. If versions aren't pinned, your new deployment breaks. Pinned versions guarantee identical behaviour everywhere.

**Key packages and why each exists:**

`fastapi==0.115.6` — The web framework. Handles HTTP requests, WebSockets, and automatic API documentation. The core of the entire backend.

`uvicorn[standard]==0.32.1` — The ASGI server. Think of FastAPI as the engine and Uvicorn as the chassis it sits in. Uvicorn is what actually listens on port 8000 and accepts incoming connections. The `[standard]` part adds WebSocket support.

`gunicorn==23.0.0` — In production, instead of running one Uvicorn process, you run Gunicorn managing multiple Uvicorn workers. More workers = more requests handled simultaneously. On a 2-CPU server, you'd run 4-5 workers.

`sqlalchemy==2.0.36` — The ORM (Object Relational Mapper). Instead of writing raw SQL like `SELECT * FROM boosts WHERE session_id = '...'`, you write Python like `await session.get(Boost, session_id)`. Keeps code readable and prevents SQL injection attacks.

`asyncpg==0.30.0` — The async driver that connects SQLAlchemy to PostgreSQL. The `async` part is critical — it means database queries don't block the server from handling other requests while waiting for the database to respond. Under high load, this is the difference between 50 concurrent users and 5000.

`alembic==1.14.0` — Database migration tool. When you add a new column to a model (e.g., adding `mood_tag` to the Song model), Alembic generates a migration script that safely adds that column to the live database without losing any existing data.

`pydantic==2.10.3` — Data validation library. When Arjun's phone sends a boost request with `amount_paise: "twenty-five"` (a string instead of a number), Pydantic catches that before it reaches the database and returns a clear error. Every schema file uses Pydantic.

`redis==5.2.1` — Python client for Redis. Used for live queue state, WebSocket pub/sub, rate limiting, and session cooldowns.

`celery==5.4.0` — Background job runner. When you need to send a WhatsApp message to a venue owner at 11pm on Sunday, you don't do it inside an HTTP request (it would make that request slow). You put it in a Celery task and it runs in the background.

`razorpay==1.4.2` — Official Razorpay Python SDK. Handles creating payment orders and verifying webhook signatures.

`google-api-python-client==2.155.0` — Google's official Python SDK. Used to query YouTube Data API to check if video IDs are still embeddable.

`structlog==24.4.0` — Structured logging. Instead of logging `"Error in payment processing"`, you log `{"event": "payment.failed", "venue_id": "...", "amount": 2500, "error": "timeout"}`. In production, structured logs can be queried and filtered. Plain text cannot.

`sentry-sdk[fastapi]==2.19.2` — Error monitoring. When an unhandled exception occurs in production, Sentry captures the full stack trace, the request that caused it, and emails or Slacks you. Without this, you only find out about errors when venue owners complain.

`httpx==0.28.1` — Async HTTP client. Used for WhatsApp API calls (Meta's WhatsApp Cloud API is just an HTTP API). Also used in tests as the test HTTP client.

`locust==2.32.4` — Load testing. Simulates 200 concurrent guests all boosting songs simultaneously to make sure the server doesn't buckle before the pilot.

---

### `.env.example`

**What it does:** Documents every environment variable the application needs, with safe placeholder values. This file IS committed to Git — it's a template, not real credentials.

**How to use it:** Copy it to `.env` (which is gitignored), then replace every `placeholder` value with a real one.

**Key variable groups explained:**

`SECRET_KEY` — Used by FastAPI for session security. Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

`DATABASE_URL` — The connection string for PostgreSQL. Format: `postgresql+asyncpg://username:password@host:port/database_name`. The `+asyncpg` part tells SQLAlchemy to use the async driver.

`REDIS_URL` — Redis connection. Has three DB indices: 0 (general), 1 (live queue), 2 (Celery). Separating them means a Celery task can't accidentally overwrite live queue data.

`DEFAULT_SPEND_CAP_PAISE=15000` — This is ₹150 expressed in paise (smallest unit). **Always store money in paise.** Never store ₹15.00 as a float — floating point arithmetic causes rounding errors. 1500 paise is always exactly 1500 paise.

`PLAYBACK_WATCHDOG_SECONDS=60` — If the venue laptop's YouTube Playback Tab hasn't acknowledged a "play this song" command within 60 seconds, something is wrong. The watchdog task fires an alert.

---

### `.env.development`

**What it does:** Provides safe, working defaults for local development so developers can get the server running without filling in every real API key immediately.

**What you put here vs `.env`:** Development defaults (local database URLs, fake API keys for testing) go here. Real Razorpay keys, real YouTube API keys, real WhatsApp tokens go in `.env` which is never committed.

**Practical use:** A new developer cloning the repo runs `cp .env.example .env`, fills in their personal API keys, and is running in minutes.

---

### `pyproject.toml`

**What it does:** Configures the development tools — the linter (ruff), the type checker (mypy), and the test runner (pytest).

**Why it matters:**

`ruff` — A fast Python linter. It catches issues like unused imports, incorrect indentation, and style inconsistencies. Running `ruff check app/` before committing keeps the codebase consistent no matter who writes the code.

`mypy` — A type checker. Python doesn't enforce types at runtime, but mypy can catch errors like passing a `str` where a `uuid.UUID` is expected before the code even runs. Set to non-strict during the pilot — you want to move fast without every function needing perfect type annotations.

`pytest.ini_options` — `asyncio_mode = "auto"` is critical. Without this, async test functions would need `@pytest.mark.asyncio` on every single test. This makes it automatic.

`coverage.fail_under = 70` — If test coverage drops below 70%, the CI pipeline fails. This prevents people from adding untested code without noticing.

---

## 3. app/core/

This folder is the foundation. Everything else depends on it. If something in `core/` breaks, the entire application stops working. Think of it as the utilities closet — electricity, plumbing, and security systems all live here.

---

### `app/core/config.py`

**What it does:** Reads every environment variable and makes it available as a typed Python object anywhere in the codebase.

**The key function — `get_settings()`:** This is decorated with `@lru_cache()`. That means the first time it's called, it reads all environment variables from the `.env` file. Every subsequent call returns the same cached object without re-reading the file. This is important because this function is called thousands of times per request (once per `Depends(get_settings)` injection).

**How to use it in a new file:**
```python
# Option 1: Dependency injection in routes (preferred)
@router.get("/")
async def my_route(settings = Depends(get_settings)):
    cap = settings.DEFAULT_SPEND_CAP_PAISE

# Option 2: Direct import in services/workers (acceptable)
from app.core.config import settings
cap = settings.DEFAULT_SPEND_CAP_PAISE
```

**The `@field_validator` for CORS_ORIGINS:** Environment variables are strings. `CORS_ORIGINS` needs to be a Python list. The validator converts `"http://localhost:5173,https://app.vibequeue.in"` into `["http://localhost:5173", "https://app.vibequeue.in"]` automatically at startup.

**Fail-fast principle:** If `SECRET_KEY` is missing from `.env`, the application refuses to start and tells you which variable is missing. This is intentional — it is far better to fail on startup than to silently use a default secret key in production.

**The `is_production` property:** Used in `app/main.py` to hide the Swagger docs in production (`docs_url=None if settings.is_production else "/docs"`). You don't want competitors browsing your API documentation.

**Real-world scenario:** When Arjun boosts Kesariya, the queue engine checks `settings.DEFAULT_SPEND_CAP_PAISE` to verify Table 7 hasn't exceeded their limit. This setting comes from config.py.

---

### `app/core/database.py`

**What it does:** Creates the database connection and provides a session to every route that needs to talk to PostgreSQL.

**The engine:** `create_async_engine(...)` creates a connection pool to PostgreSQL. A pool means instead of opening and closing a new database connection for every request (slow), it keeps a set of connections open and reuses them. `pool_size=10` means 10 connections are always open. `max_overflow=20` means up to 20 additional connections can be opened under load.

**`AsyncSessionLocal`:** This is a factory. Every time you call it (via `Depends(get_db)`), it creates a new session object — a workspace for one request's database operations. The session tracks what you've read and written, and commits or rolls back at the end.

**`get_db()` — The most important function:** This is an async generator injected into every route that needs the database.

```python
# This is how every route gets a database session
@router.post("/boosts/")
async def apply_boost(db: AsyncSession = Depends(get_db)):
    # db is a fresh session for this request
    # At the end of the function:
    #   - if everything worked: db.commit() runs automatically
    #   - if an exception was raised: db.rollback() runs automatically
    #   - db.close() always runs
```

**`expire_on_commit=False`:** After you commit a database transaction, SQLAlchemy by default "expires" all objects — meaning accessing their attributes would trigger another database query. With this set to `False`, you can still read `boost.amount_paise` after committing without an extra query.

**`Base`:** All database models (`Venue`, `Song`, `Boost`, etc.) inherit from this. It's the shared ancestor that tells SQLAlchemy "these Python classes represent database tables."

**Real-world scenario:** When Arjun's boost is saved to the database, `get_db()` provides the session. If the database is temporarily unavailable (network hiccup), the session rolls back and Arjun sees an error — his card is not charged.

---

### `app/core/redis.py`

**What it does:** Creates two Redis connection pools and defines a naming convention for all Redis keys.

**Why two pools?**
- `redis_client` (DB 0) — General purpose: rate limiting, session tokens, presence tracking
- `redis_queue_client` (DB 1) — Live queue state exclusively

Separating them means a bug that corrupts queue data cannot also corrupt rate limiting data. It also makes it easy to flush just the queue state (`redis_queue_client.flushdb()`) without affecting anything else.

**`RedisKeys` class — The naming convention:** Every Redis key in the entire application is generated by this class. Never write a Redis key string anywhere else.

```python
# Good — uses the factory
key = RedisKeys.live_queue("venue-123")
# Result: "vq:venue-123:queue"

# Bad — never do this
key = f"queue_{venue_id}"  # Could conflict with other keys
```

**Why naming conventions matter:** Redis is a single namespace. Without naming conventions, `queue` could mean the live queue, or a Celery queue, or something else. The `vq:` prefix (VibeQueue), combined with entity type, makes every key's purpose instantly obvious and prevents collisions.

**Key types and their purposes:**

`vq:{venue_id}:queue` — A Redis sorted set. Stores all song IDs in the live queue with their scores as the sort key. Sorted sets are perfect for priority queues because they maintain ordering automatically.

`vq:{venue_id}:session:{code}` — A Redis hash. Stores the table session data for fast lookup when a guest makes a request. Looking up a table code from Redis takes ~0.1ms. Looking it up from PostgreSQL takes ~5-10ms. For a high-frequency operation like validating every API request, this matters.

`vq:{venue_id}:ratelimit:{table_id}` — A Redis string with an expiry. When set, it means this table is in cooldown. When it expires (after `DEFAULT_REQUEST_COOLDOWN_SECONDS`), the cooldown is over — no explicit deletion needed, Redis handles it.

`vq:{venue_id}:spend:{table_id}` — A Redis integer tracking total spend for a table. Using `INCRBY` (atomic increment) means even if 10 boost requests arrive simultaneously, each one correctly adds to the total without race conditions.

`vq:{venue_id}:ws` — The pub/sub channel for WebSocket broadcasting. When the queue changes, the queue engine publishes `"queue_updated"` to this channel. All connected WebSocket clients (guest phones, ambient display) receive it instantly.

**Real-world scenario:** When Arjun boosts Kesariya, his table's spend total is incremented in Redis atomically. If Priya and Sneha both tap Boost at exactly the same millisecond, Redis ensures neither can exceed the cap — they're processed sequentially.

---

### `app/core/security.py`

**What it does:** Handles all security primitives — JWT tokens, password hashing, table code generation, and Razorpay signature verification.

**JWT tokens (JSON Web Tokens):** Think of a JWT as a digitally signed note that says "the server confirms this person is a venue staff member at venue X." The client presents this note on every request. The server verifies the signature to confirm it's genuine — no database lookup required.

`create_access_token(subject, role, extra)`:
- `subject` — The entity's ID (e.g., `session_id` for guests, `user_id` for staff)
- `role` — `"guest"`, `"venue_staff"`, or `"venue_owner"`. This controls what routes the token can access.
- `extra` — Additional claims (e.g., `venue_id`) embedded in the token so the API knows which venue this person belongs to without a database query

`create_refresh_token()` — A long-lived (30-day) token. Used to get a new short-lived (60-minute) access token without logging in again. Refresh tokens are stored nowhere on the server — they're self-contained.

**`generate_table_code()`:** Uses `secrets.choice()` rather than `random.choice()`. The difference: `random` is predictable if you know the seed. `secrets` uses the operating system's cryptographic random source, which is unpredictable even to someone who knows when the code was generated. An attacker cannot guess or enumerate table codes.

**`verify_razorpay_signature()`:** After a payment, Razorpay sends a webhook with a signature — an HMAC-SHA256 hash of the payment data using your secret as the key. This function recomputes the expected signature and compares it with `hmac.compare_digest()` (constant-time comparison that prevents timing attacks). If they match, the payment is genuine. If not, someone is trying to fake a payment confirmation.

**Real-world scenario:** When the waiter opens Table 7, `generate_table_code()` produces `"482176"`. The waiter tells Arjun. Arjun enters it. `create_access_token()` produces a JWT that Arjun's phone uses for every subsequent request. When Arjun's bill is paid, `verify_razorpay_signature()` confirms Razorpay actually processed the payment before VibeQueue marks it as paid.

---

### `app/core/logging.py`

**What it does:** Configures structured JSON logging for production and coloured console logging for development.

**Why structured logging matters:** In development, you want to read logs. In production, you want to search logs. A plain log line `"Error processing payment for user abc123"` cannot be searched by amount or venue. A structured log `{"event": "payment.failed", "venue_id": "...", "amount_paise": 2500, "error": "timeout"}` can be filtered by any field.

**`setup_logging()`:** Call this once at startup (done in `events.py`). After this, anywhere in the codebase you write:
```python
import structlog
logger = structlog.get_logger()
logger.info("boost.applied", venue_id=str(venue_id), amount_paise=2500)
```
...and it produces clean, searchable output.

**`add_app_context` processor:** Automatically adds `app=VibeQueue` and `env=production` to every log entry. When you're looking at production logs at 2am, you know exactly which app produced them.

**`merge_contextvars`:** The request logging middleware (in `app/api/v1/middleware/logging.py`) binds a `request_id` to the log context at the start of each request. Every log line produced during that request automatically includes that `request_id`. This means you can filter all logs for a single request — every database query, every service call, every event — just by the request ID.

---

### `app/core/celery.py`

**What it does:** Creates and configures the Celery application that runs background jobs.

**Why Celery instead of just running jobs inside FastAPI?** Imagine the weekly revenue report. It queries the database, calculates statistics for every venue, and sends a WhatsApp message to each owner. On 50 venues, this takes minutes. If you ran this inside an HTTP request, the request would time out. Celery runs it in a separate worker process, in the background, on a schedule.

**Task queues (routing):** Different types of jobs go to different queues:
- `catalogue` queue — YouTube validation jobs
- `payments` queue — Payment verification (high priority, fast)
- `notifications` queue — WhatsApp messages (medium priority)
- `cleanup` queue — Nightly database cleanup (low priority)

Separate queues mean payment verification is never blocked by a slow WhatsApp job.

**`beat_schedule` — The cron system:**
```python
"weekly-catalogue-validation": {
    "task": "...",
    "schedule": crontab(hour=3, minute=0, day_of_week=1),
}
```
This is equivalent to a Linux cron job `0 3 * * 1` — run at 3am every Monday. Celery Beat is the scheduler process that triggers these.

**`task_acks_late=True`:** By default, Celery marks a task as "done" before it finishes running. If the worker crashes mid-task, the task is lost. `acks_late=True` means "only mark done after the task actually completes." If the worker crashes, the task is re-queued.

**`task_reject_on_worker_lost=True`:** If the worker process dies unexpectedly during a task, that task goes back into the queue to be retried. Without this, a WhatsApp message that was sending when the server rebooted would be silently dropped.

---

### `app/core/events.py`

**What it does:** Defines what happens when the application starts and when it shuts down.

**The lifespan pattern:** In modern FastAPI, you use a context manager:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Everything here runs on startup
    setup_logging()
    await verify_redis()
    yield  # ← Application runs here
    # Everything here runs on shutdown
    await close_redis_connections()
```

**Fail-fast Redis check:** On startup, the app pings Redis. If Redis is unreachable, the app refuses to start with a `RuntimeError`. This is better than starting and then failing on the first request — it gives you a clear, immediate error on deployment rather than mysterious 500 errors later.

**Sentry initialization:** Sentry is only activated if `SENTRY_DSN` is set AND the environment is not development. This prevents Sentry from spamming error reports every time you make a mistake during local testing.

---

## 4. app/main.py

**What it does:** Creates the FastAPI application by plugging together all the components.

**Think of it as the restaurant floor plan.** The kitchen (services), the tables (routes), the entrance (middleware), and the staff (dependencies) are all built elsewhere. `main.py` is the blueprint that places them all in relation to each other.

**`create_application()`:** A factory function rather than a module-level `app = FastAPI()`. This makes testing easier — you can create a fresh application for each test without global state leaking between tests.

**`docs_url=None if settings.is_production else "/docs"`:** The automatic Swagger API documentation (interactive browser at `http://localhost:8000/docs`) is invaluable during development. In production, it exposes your entire API structure to anyone with a browser. Hidden in production, shown in development.

**`app.include_router(api_v1_router, prefix="/api/v1")`:** All routes are prefixed with `/api/v1`. This means when you build v2 routes, you add `/api/v2` without changing anything in v1. Your mobile clients on the old app version still work.

**Real-world scenario:** `main.py` is the first file Python executes when you run `uvicorn app.main:app`. It sets up logging, initializes Sentry, verifies Redis, registers all routes, and then signals "ready" — all before accepting a single request.

---

## 5. app/models/

Models are the definition of your database tables expressed as Python classes. Each class = one table. Each class attribute = one column.

**The inheritance pattern:**
```
Base (core/database.py)
  └── BaseModel (models/base.py)
        ├── UUIDMixin    ← adds id column
        ├── TimestampMixin ← adds created_at, updated_at
        └── (your model) ← adds specific columns
```

All models inherit from `BaseModel`, which means every table automatically gets `id`, `created_at`, and `updated_at`. You never write these manually.

---

### `app/models/base.py`

**What it does:** Defines `BaseModel` — the parent class every table inherits from.

**`UUIDMixin`:** Every primary key is a UUID (e.g., `550e8400-e29b-41d4-a716-446655440000`), not an auto-incrementing integer. Why?

With integers, `venue_id=1, venue_id=2, venue_id=3` — anyone who knows your API can guess valid IDs and probe your data. With UUIDs, the ID is unguessable. Also, UUIDs can be generated on the client (or in code) before being saved to the database, without a round-trip.

**`TimestampMixin`:** `server_default=func.now()` means the database itself sets the timestamp, not Python code. This ensures timestamp accuracy even if your application server's clock is slightly wrong.

**`to_dict()`:** A convenience method that converts a model instance to a plain Python dictionary. Used in scripts and tests, not in the main application flow.

---

### `app/models/venue.py`

**What it represents:** One row = one bar/restaurant using VibeQueue.

**Key columns:**

`slug` — A URL-safe identifier like `"koramangala-social"`. Used in the QR code URL: `https://app.vibequeue.in/koramangala-social`. Must be unique. The `index=True` makes slug lookups fast because an index is created in the database.

`mode` — `"A"` (YouTube auto-play) or `"B"` (manual). A single character column that controls which entire branch of the playback logic runs.

`queue_size_limit=8` — The maximum songs in the active queue. Stored per-venue so different venues can have different limits (though all pilots start at 8).

`spend_cap_paise=15000` — ₹150 in paise. Configurable per venue so upscale venues can set higher limits (₹300) if they want more revenue potential.

`is_active=False` — New venues start inactive. Flipped to `True` during the setup session. An inactive venue's QR codes show "VibeQueue not active tonight" to guests.

**Relationships:** `songs`, `sessions`, `users` are SQLAlchemy relationship definitions. They let you write `venue.sessions` to get all sessions for a venue, without writing a JOIN query yourself.

---

### `app/models/user.py`

**What it represents:** Venue owners and staff members who log into the venue dashboard.

**Important:** This is NOT for guests. Guests never create accounts. They authenticate via table codes, not usernames.

`role` — `"venue_owner"` (can change song pool, view revenue, adjust settings) or `"venue_staff"` (can open/close tables, mark songs as played) or `"superadmin"` (VibeQueue internal).

`hashed_password` — Never store plain passwords. The password is run through bcrypt (in `security.py`) which produces an irreversible hash. Even if the database is compromised, attackers can't recover passwords.

`venue_id` — Foreign key linking a user to their venue. A venue_staff user can only see data for their venue. A superadmin has `venue_id=NULL` because they can access any venue.

---

### `app/models/song.py`

**What it represents:** One row = one song in one venue's approved catalogue. The same song ("Kesariya") at two different venues is two rows — because one venue might have it enabled and the other might not.

`youtube_video_id` — The 11-character YouTube video identifier (e.g., `"BVBWugH_aFE"`). This is what the YouTube IFrame Player needs to play a specific video.

`is_embeddable` — Set to `False` by the weekly catalogue validation job if the video can no longer be embedded (taken down, made private, etc.). Songs with `is_embeddable=False` are hidden from guest search automatically.

`available_after_hour` / `available_before_hour` — Time-of-day restrictions. Jazz songs can be set to `available_before_hour=22` (only during the dinner hours before 10pm). EDM songs can be `available_after_hour=22` (only after 10pm). This is how venues control the vibe arc without touching a control panel.

---

### `app/models/session.py`

**What it represents:** One row = one table's evening session. When the waiter opens Table 7 at 9pm, a session row is created. When the table pays and leaves, it's closed.

`table_code` — The 6-digit verbal code (`"482176"`). The index on this column makes the lookup `SELECT * FROM table_sessions WHERE table_code = '482176'` fast even with thousands of sessions.

`expires_at` — 90 minutes after creation. After this, the code is invalid even if the session technically still exists. The table gets a new code (waiter generates it from the dashboard).

`is_billed` — Set to `True` when the billing is confirmed. Used to prevent double-billing if the billing endpoint is accidentally called twice.

`opened_by_user_id` — Which staff member opened this table. For audit purposes — if a dispute arises about what happened at a table, you can trace who opened it.

---

### `app/models/queue.py`

**What it represents:** One row = one song request in the queue. This is the central table that drives everything.

`status` — The lifecycle: `"active"` → `"playing"` → `"played"` | `"skipped"` | `"expired"` | `"cancelled"`

- `active` — In the queue, eligible to play
- `playing` — Currently playing (only one song at a time)
- `played` — Completed. Boosts confirmed. This is the billing trigger.
- `skipped` — Staff skipped it. Boosts cancelled.
- `expired` — 90 minutes passed, never played. Boosts cancelled.
- `cancelled` — Staff removed it manually. Boosts cancelled.

`position` — 1 through 8 = active queue (visible on ambient display). 9+ = waiting pool (visible only on guest's phone).

`boost_total_paise` — Running sum of all boosts applied to this song. Used in the scoring formula.

`score` — The calculated priority score at the last recalculation. Stored in the database so you can debug why a song is at a certain position.

**Real-world scenario:** When Arjun boosts Kesariya for ₹25, the `boost_total_paise` on this row goes from 0 to 2500. The `score` is recalculated and the `position` changes from 7 to 3. The Ambient Display updates within one second.

---

### `app/models/boost.py`

**What it represents:** One row = one individual boost transaction. If Arjun boosts twice (₹25 and then ₹35), that's two rows.

**The pending → confirmed lifecycle:** This is the core of the "pay only if it plays" promise.

1. Arjun taps Boost ₹25 → row created with `status="pending"`
2. Song plays (ENDED event fires) → row updated to `status="confirmed"`
3. If song never plays (expires, gets removed) → row updated to `status="cancelled"`

At billing time, only `status="confirmed"` rows are charged. This lifecycle is enforced at the database level — there is no way to charge for an unplayed song because the status simply won't be `"confirmed"`.

`confirmed_at` / `cancelled_at` — Timestamps for each status transition. Critical for the audit log and dispute resolution.

---

### `app/models/payment.py`

**What it represents:** One row = one completed billing event for one table session.

This row is created when the guest confirms their billing review and a Razorpay order is created. It tracks the full payment lifecycle.

`razorpay_order_id` — The ID Razorpay assigns when you create an order. The `unique=True` constraint means you can't accidentally create two payments for the same order.

`razorpay_payment_id` — Filled in only after the payment webhook arrives and is verified. This is Razorpay's confirmation that money actually moved.

`vibequeue_share_paise` / `venue_share_paise` — Pre-calculated 40/60 split stored at payment time. Used for the weekly settlement report that tells you how much to invoice each venue.

`settlement_status` — Tracks whether VibeQueue has collected its share from the venue. Goes from `"pending"` to `"settled"` after the weekly bank transfer.

---

### `app/models/playback_command.py`

**What it represents:** Instructions sent from the queue engine to the YouTube Playback Tab on the venue laptop.

**The flow:**
1. Queue engine decides song X should play next
2. Creates a `PlaybackCommand` row with `status="pending"`
3. Publishes the command to Redis pub/sub
4. The Playback Tab (listening via WebSocket) receives it
5. Tells YouTube IFrame Player to load video
6. YouTube fires `PLAYING` event
7. `PlaybackCommand` status updates to `"acknowledged"` / `"playing"`
8. YouTube fires `ENDED` event
9. `PlaybackCommand` status updates to `"completed"`

**`status="stalled"`** — Set by the hourly watchdog task if a command has been `"pending"` for longer than `PLAYBACK_WATCHDOG_SECONDS`. This triggers an alert to the founder's WhatsApp.

---

### `app/models/playback_event.py`

**What it represents:** Events received FROM the YouTube IFrame Player. The Playback Tab sends these to the backend.

`event_type` — `"PLAYING"` (song started), `"ENDED"` (song finished — billing trigger!), `"ERROR"` (something failed), `"PAUSED"`, `"BUFFERING"`

`error_code` — YouTube-specific error codes. `101` and `150` mean the video cannot be embedded. This code is logged here and used by the fallback logic.

**Why store these?** Full audit trail. If a venue owner claims "Kesariya played but we weren't charged," you can check the `playback_events` table and see whether an `"ENDED"` event was received. If it was, the charge should exist. If it wasn't, there was a legitimate technical failure and the charge was correctly not applied.

---

### `app/models/audit_log.py`

**What it represents:** An immutable record of important things that happened. Never updated, only appended.

**Why you need this:** Billing disputes are the most dangerous risk for VibeQueue. If a guest says "I was charged for a song I didn't request," you need to trace exactly what happened. The audit log records every action: `"boost.created"`, `"boost.confirmed"`, `"song.played"`, `"session.opened"`, `"payment.confirmed"`.

`actor_id` — `"system"` for automated actions, or a user ID for manual actions (e.g., a staff member removing a song).

`details` — A JSON string with any extra context. For a boost, this might be `{"amount_paise": 2500, "song": "Kesariya"}`.

---

### `app/models/__init__.py`

**What it does:** Imports all models in one place.

**Why it exists:** Alembic (the migration tool) needs to see all models before it can generate migrations. This file is imported in `alembic/env.py` to ensure all models are loaded before Alembic scans for changes.

Without this file, Alembic would not know about your new `Mood` model and would never generate a migration for it.

---

## 6. app/schemas/

Schemas are the "contracts" of your API — they define exactly what shape data must be in when it comes in (requests) and goes out (responses). They use Pydantic for automatic validation.

**The critical difference between models and schemas:**
- **Models** define how data is stored (database columns, relationships, constraints)
- **Schemas** define how data is communicated (API request bodies, response shapes)

The same data might have different shapes in the model vs the schema. For example, the `Boost` model stores `amount_paise` as an integer, but the schema might expose it as both `amount_paise: 2500` AND `amount_display: "₹25"` for the frontend's convenience.

---

### `app/schemas/queue.py`

**`SongRequestCreate`** — What the frontend sends when Arjun taps "Request":
```json
{"song_id": "uuid...", "youtube_video_id": "BVBWugH_aFE"}
```

**`SongRequestResponse`** — What the backend sends back:
```json
{
  "id": "uuid...",
  "position": 7,
  "youtube_video_id": "BVBWugH_aFE",
  "status": "active",
  "boost_total_paise": 0,
  "score": 10.5,
  "expires_at": "2026-06-28T23:30:00Z",
  "estimated_wait_minutes": 22.0
}
```

**`QueueState`** — The full queue snapshot sent to a guest when they first join (before WebSocket takes over):
```json
{
  "venue_id": "uuid...",
  "active_queue": [...8 songs...],
  "waiting_pool_count": 3,
  "now_playing": {...}
}
```

---

### `app/schemas/boost.py`

**`BoostCreate`** — Notice the validation:
```python
amount_paise: int = Field(..., ge=1500, le=3500)
```
`ge=1500` means "greater than or equal to 1500." `le=3500` means "less than or equal to 3500." Combined with the route-level check against the three valid amounts, this prevents any amount outside the fixed tiers from reaching the database.

**`BoostTier`** — The three options shown in the UI:
```json
[
  {"label": "Small Boost", "score_increase": 15, "amount_paise": 1500, "amount_display": "₹15"},
  {"label": "Medium Boost", "score_increase": 25, "amount_paise": 2500, "amount_display": "₹25"},
  {"label": "Priority Boost", "score_increase": 35, "amount_paise": 3500, "amount_display": "₹35"}
]
```
The frontend reads this from `GET /boosts/tiers` and renders the three buttons dynamically. This means you can change prices without touching the frontend.

---

### `app/schemas/session.py`

**`GuestJoinRequest`** — What the guest sends when they enter the table code:
```json
{"table_code": "482176"}
```

**`GuestJoinResponse`** — What they receive back:
```json
{
  "session_id": "uuid...",
  "table_number": "7",
  "access_token": "eyJ...",
  "expires_at": "2026-06-28T23:30:00Z",
  "spend_cap_paise": 15000,
  "spend_cap_display": "₹150",
  "venue_name": "Social Koramangala"
}
```
Everything the frontend needs to set up the guest's session is in this one response.

---

### `app/schemas/billing.py`

**`BillingReview`** — The pre-bill screen Arjun sees before paying:
```json
{
  "session_id": "uuid...",
  "table_number": "7",
  "items": [
    {
      "boost_id": "uuid...",
      "song_title": "Kesariya",
      "artist": "Arijit Singh",
      "amount_paise": 2500,
      "amount_display": "₹25",
      "status": "confirmed",
      "is_removable": false
    }
  ],
  "subtotal_paise": 2500,
  "gst_paise": 450,
  "total_paise": 2950,
  "subtotal_display": "₹25",
  "gst_display": "₹4",
  "total_display": "₹29"
}
```

`is_removable: false` for a confirmed (played) boost — the song played, the charge is real. `is_removable: true` for a pending (still in queue) boost — guest can remove it before confirming.

---

### `app/schemas/websocket.py`

**`WSMessage`** — The shape of every WebSocket message sent to clients. The `type` field tells the frontend what kind of update this is and therefore what UI change to make:

- `"queue_update"` → Re-render the queue list
- `"playback_started"` → Update "Now Playing" display
- `"venue_paused"` → Show "Queue paused" banner
- `"song_removed"` → Remove that song from the displayed queue
- `"session_expired"` → Show "Your session has ended" screen

---

## 7. app/repositories/

Repositories are the only place in the codebase that should ever touch the database directly. Think of them as the database's API — every query is a named function with a clear purpose.

**The rule:** No service, route, or worker should ever write a `select()` or `update()` statement. They call a repository method that does it.

**Why this isolation?** When you need to optimise a slow query, there's exactly one place to look. When you need to add an index, you look at which repository methods are called most often. When you need to add caching, you add it in the repository without changing any other layer.

---

### `app/repositories/base.py`

**What it does:** Provides standard CRUD operations that every repository inherits, eliminating repetition.

**`get_by_id(record_id)`** — Fetch a single row by UUID. Returns `None` if not found (the calling code decides whether that's an error).

**`create(**kwargs)`** — Insert a new row. Uses `flush()` instead of `commit()` — this sends the SQL to the database without committing the transaction. This allows multiple creates in one transaction that all succeed or all fail together. The `commit()` happens at the end of the request in `get_db()`.

**`update(instance, **kwargs)`** — Update specific fields on an existing row. Only the fields you pass in `kwargs` are changed — other fields are untouched.

---

### `app/repositories/queue_repo.py`

This is the most important repository. Every queue operation touches it.

**`get_active_queue(venue_id)`** — Returns songs in positions 1–8, ordered by position. Called every time the queue is displayed.

**`get_next_to_play(venue_id)`** — Returns only position 1. Called when the previous song ends to know what to play next.

**`count_active_for_venue(venue_id)`** — Returns how many songs are currently in positions 1–8. Used to decide whether a new request goes to the active queue or the waiting pool: if count < 8, it goes to the queue; if count = 8, it goes to the waiting pool (position = count + 1).

**`get_expired_entries(before)`** — Used by the nightly cleanup task. Finds all entries where `expires_at < now` and `status = "active"` — these should have been played but weren't.

**`mark_as_playing(entry_id)`** — Called when a `PLAYING` event arrives. Changes status from `"active"` to `"playing"`.

**`mark_as_played(entry_id)`** — Called when an `ENDED` event arrives. Changes status to `"played"` and records `played_at`. This is the trigger for billing confirmation.

---

### `app/repositories/boost_repo.py`

**`get_confirmed_by_session(session_id)`** — Returns only `status="confirmed"` boosts. This is what generates the billing total — only songs that actually played.

**`confirm_all_for_entry(queue_entry_id)`** — Called by `queue_engine.confirm_song_played()`. Bulk-updates all pending boosts for a queue entry to `status="confirmed"`. Returns the count updated — if this is 0, something went wrong (the song had no boosts, or they were already cancelled).

**`cancel_all_for_entry(queue_entry_id)`** — Called when a song is removed, skipped, or expires. Bulk-updates all pending boosts to `status="cancelled"`. Guests are not charged.

**`sum_confirmed_paise(session_id)`** — Returns the total billable amount for a table. Called when creating the Razorpay payment order: `sum([boost.amount_paise for boost in confirmed_boosts])`.

---

### `app/repositories/session_repo.py`

**`get_by_code(venue_id, table_code)`** — The most frequently called repository method. Called on every single guest API request to validate their session. The combined index on `venue_id + table_code` makes this a fast lookup even with thousands of sessions.

The query also checks `is_active=True` and `expires_at > now` in a single database call — no need for the application to do this check separately.

---

### `app/repositories/song_repo.py`

**`search(venue_id, query, limit=20)`** — Full-text search using PostgreSQL's `ilike` (case-insensitive `LIKE`). For pilot scale (hundreds of songs per venue), this is fast enough. The comment in the code marks the upgrade point: "Upgrade to Meilisearch at scale."

The query searches both `title` and `artist` fields. Searching for "arijit" returns Kesariya, Raataan Lambiyan, and all other Arijit Singh songs in the venue's catalogue.

**Important:** The search is scoped to `venue_id`. Arjun can only find songs in this venue's catalogue. He cannot find songs that are disabled or not embeddable. This is enforced at the database query level — it's not a frontend filter.

---

### `app/repositories/audit_repo.py`

**`log(action, ...)`** — The single function for all audit logging. Every significant action calls this:

```python
# In queue_engine.py after applying a boost
await audit_repo.log(
    action="boost.applied",
    venue_id=venue_id,
    session_id=session_id,
    actor_id="guest",
    resource_type="boost",
    resource_id=boost.id,
    details={"amount_paise": 2500, "queue_entry_id": str(queue_entry_id)}
)
```

The `details` field stores a JSON string with whatever extra context is relevant. This is queryable if you use PostgreSQL's JSON operators.

---

## 8. app/services/

Services contain the business logic — the "what should actually happen" layer. They don't know about HTTP requests (that's routes' job) and they don't know about SQL (that's repositories' job). They know about business rules.

---

### `app/services/queue_engine.py`

**This is the most important file in the entire codebase.** Everything VibeQueue does ultimately flows through here.

**`add_song_request(venue_id, session_id, song_id, youtube_video_id)`:**

Step 1 — Check the Redis rate limit key. If `vq:{venue_id}:ratelimit:{session_id}` exists, the table is in cooldown. Raise `CooldownActiveError` with the remaining seconds.

Step 2 — Count active queue entries. If < 8, the song joins the active queue. If = 8, it goes to the waiting pool.

Step 3 — Create the `QueueEntry` row in PostgreSQL via the repository.

Step 4 — Set the cooldown key in Redis with a TTL of `DEFAULT_REQUEST_COOLDOWN_SECONDS`.

Step 5 — Call `_recalculate_and_broadcast()`.

**`apply_boost(venue_id, session_id, queue_entry_id, amount_paise)`:**

Step 1 — Load the queue entry and verify it belongs to this venue.

Step 2 — Check the position. If > 8, it's in the waiting pool — raise `WaitingPoolBoostError`.

Step 3 — Check the Redis spend key. If adding this boost would exceed the venue's cap, raise `SpendCapExceededError`.

Step 4 — Create the `Boost` row (status=`"pending"`).

Step 5 — Update the queue entry's `boost_total_paise`.

Step 6 — Increment the spend total in Redis with `INCRBY` (atomic — no race conditions).

Step 7 — Call `_recalculate_and_broadcast()`.

**`confirm_song_played(venue_id, queue_entry_id)`:**

Step 1 — Mark the queue entry as `"played"` in PostgreSQL.

Step 2 — Bulk-confirm all pending boosts for this entry (they're now billable).

Step 3 — Call `_recalculate_and_broadcast()` so the next song moves to position 1.

**`_recalculate_and_broadcast(venue_id)` — The heart of it all:**

Every time anything changes in the queue, this runs:

1. Load all active entries and waiting pool entries from PostgreSQL
2. Run `sort_queue_entries()` (from `utils/scoring.py`) — recalculates scores, sorts by score descending, ties broken by oldest request first
3. Assign new positions (1, 2, 3... for active; 9, 10, 11... for waiting pool)
4. Write the new positions and scores back to PostgreSQL
5. Publish `"queue_updated"` to the Redis pub/sub channel `vq:{venue_id}:ws`

Step 5 is what makes the ambient display and guest phones update in real time. The WebSocket handler in `routes/websockets.py` is subscribed to this channel. When it receives `"queue_updated"`, it reads the fresh queue from PostgreSQL and sends it to all connected clients.

---

### `app/services/billing_service.py`

**`get_review(session_id)`** — Builds the pre-billing review screen.

1. Load all boosts for the session (both confirmed and pending, excluding cancelled)
2. Confirmed boosts → show with `is_removable=False`
3. Pending boosts → show with `is_removable=True`
4. Calculate: `subtotal = sum(confirmed_amounts)`, `gst = subtotal * 0.18`, `total = subtotal + gst`

**`remove_boost(boost_id)`** — Guest removes a pending charge.

Silently ignores if the boost is already confirmed (the song played, charge is real). Only pending boosts can be removed. Sets `status="cancelled"`.

**`calculate_total(session_id)`** — Called right before creating the Razorpay order. Returns the final numbers after all removals: `{subtotal_paise, gst_paise, total_paise}`.

**The GST_RATE constant:** `0.18` (18%). Music interaction fees are digital interactive service charges. This is not negotiable — GST must be collected and shown as a separate line item on the bill.

---

### `app/services/payment_service.py`

**`create_order(venue_id, session_id, total_paise, gst_paise)`:**

1. Calls `razorpay_client.order.create({"amount": total_paise, "currency": "INR", "receipt": ...})`
2. Creates a `Payment` row in PostgreSQL with `status="created"` and pre-calculated `vibequeue_share_paise` / `venue_share_paise`
3. Returns the `razorpay_order_id` and `amount_paise` for the frontend to open the Razorpay checkout modal

**`verify_and_confirm(order_id, payment_id, signature)`:**

Called from the Razorpay webhook. This is the most security-critical function in the codebase.

1. Calls `verify_razorpay_signature()` from `security.py`. If signature is invalid, raises `PaymentVerificationError` — the request is rejected.
2. Finds the `Payment` row by `razorpay_order_id`.
3. Updates `status="paid"`, records `razorpay_payment_id`, records `paid_at`.

**NEVER** call this based on frontend claims. The frontend might be spoofed. The Razorpay webhook is authenticated via signature verification.

---

### `app/services/playback_service.py`

**`issue_play_command(venue_id, queue_entry_id, youtube_video_id)`:**

1. Creates a `PlaybackCommand` row with `status="pending"`
2. Publishes the command details to Redis channel `vq:{venue_id}:playback_cmd`
3. The Playback Tab's WebSocket connection receives this and calls `loadVideoById(youtube_video_id)` on the IFrame Player

**`handle_event(venue_id, queue_entry_id, youtube_video_id, event_type, error_code)`:**

Called from `routes/playback.py` when the venue laptop's Playback Tab sends an event.

- `PLAYING` → Log it. (In full implementation: update `PlaybackCommand.status = "playing"`)
- `ENDED` → Call `queue_engine.confirm_song_played()`. This is THE billing trigger.
- `ERROR` → Log it with the error code. The hourly watchdog task checks for persistent errors.
- `PAUSED` / `BUFFERING` → Informational logging only.

---

### `app/services/catalogue_service.py`

**`check_videos_embeddable(video_ids)`:**

Calls the YouTube Data API `videos.list` endpoint, 50 IDs at a time (50 is the API's maximum per request, and each request costs 1 quota unit regardless of how many IDs you include — so batching is critical for staying under the 10,000 daily quota limit).

For each video, checks two things:
1. `status.embeddable == True` — Can this video be embedded on third-party sites?
2. `status.privacyStatus == "public"` — Is the video publicly accessible?

Both must be true. A video with `embeddable=True` but `privacyStatus="unlisted"` might work sometimes but cannot be relied on.

Videos not returned by the API at all (404) are treated as deleted/unavailable — `is_embeddable = False`.

---

### `app/services/notification_service.py`

**`send_weekly_report(owner_phone, venue_name, stats)`:**

Calls `send_whatsapp_template()` with the `weekly_revenue_report` template and dynamic parameters (song count, boost count, revenue, venue's share).

The template must be pre-approved in Meta Business Manager before it can be sent. The approval process takes 1-3 business days — do this before the pilot goes live.

**`send_catalogue_warning(owner_phone, venue_name, broken_count)`:**

Sent by the Monday morning validation job when videos are found to be no longer embeddable. Example: "3 songs in your VibeQueue catalogue may have become unavailable. Tap here to replace them."

**Why WhatsApp and not email?** Every venue owner in the target segment responds to WhatsApp within minutes. Email would be ignored for days. WhatsApp messages have ~95% open rates in India for business communications.

---

### `app/services/youtube_service.py`

**`get_video_metadata(video_id)`:**

Used when a venue owner adds a new song to their catalogue by YouTube video ID. Fetches the title, artist (channel name), duration, and embeddability in one API call. This pre-populates the song details so the owner doesn't have to type them.

**`_parse_duration(duration)`:**

YouTube returns duration in ISO 8601 format: `"PT3M45S"` means 3 minutes and 45 seconds. This regex parser converts it to `225` (seconds). Stored in the database so the frontend can show "3:45" next to song titles.

---

## 9. app/api/v1/

This is the HTTP layer — the publicly accessible surface of the application. It receives requests, validates identity, calls services, and returns responses.

---

### `app/api/v1/router.py`

**What it does:** Aggregates all 13 route files into a single router mounted at `/api/v1`.

This file is the "table of contents" for your API. Every URL the application serves is registered here. If you add a new feature, you'll add a new route file and register it here.

**The prefix organization:**
- `/api/v1/health/` — System health (no auth)
- `/api/v1/auth/` — Login/logout (no auth for login)
- `/api/v1/venues/` — Venue management (staff auth)
- `/api/v1/catalogue/` — Song pool management (owner auth)
- `/api/v1/songs/` — Song search (guest auth)
- `/api/v1/sessions/` — Table sessions (staff for open/close, guest for join)
- `/api/v1/queue/` — Queue operations (guest auth for request, staff for remove/mark-played)
- `/api/v1/boosts/` — Boost operations (guest auth)
- `/api/v1/billing/` — Pre-billing review (guest auth)
- `/api/v1/payments/` — Payment processing (guest + Razorpay webhook)
- `/api/v1/playback/` — Playback events from venue laptop (staff auth)
- `/api/v1/analytics/` — Revenue reports (owner auth)
- `/api/v1/ws/` — WebSocket connections (guest + staff)

---

### `app/api/v1/dependencies/auth.py`

**What it does:** Provides functions that validate JWT tokens and return the authenticated user. Injected into route functions that require authentication.

**`get_current_user(credentials, db)`:**

Reads the `Authorization: Bearer <token>` header. Decodes the JWT. Looks up the user in the database. Returns the `User` object.

**`get_current_venue_owner(current_user)`:**

Wraps `get_current_user`. Additionally checks that the role is `"venue_owner"` or `"superadmin"`. If a staff member tries to access an owner-only endpoint, they get `403 Forbidden`.

**`get_current_staff(current_user)`:**

Allows both `"venue_owner"` and `"venue_staff"`. Used for endpoints staff need during service (opening tables, marking songs as played).

**How dependency injection works in FastAPI:**
```python
@router.post("/catalogue/{venue_id}/songs")
async def add_song(
    venue_id: uuid.UUID,
    payload: SongCatalogueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_venue_owner),  # ← Auth enforced here
):
    # By the time this function body runs:
    # - current_user is the authenticated User object
    # - If auth failed, FastAPI already returned 401/403 — we never reach here
```

---

### `app/api/v1/dependencies/session.py`

**`get_guest_session(credentials, db)`:**

Validates the guest's JWT (issued when they entered the table code). Returns the active `TableSession` object.

**Critical checks in sequence:**
1. JWT signature is valid (not tampered with)
2. JWT role is `"guest"` (not a staff token being misused)
3. The `session_id` from the JWT exists in the database
4. The session is still `is_active=True`
5. `expires_at` hasn't passed

If any check fails, the guest sees `401 Unauthorized`. They're told to get the new table code from their waiter.

---

### `app/api/v1/dependencies/rate_limit.py`

**`rate_limit_guest(request, limit=30, window=60)`:**

IP-level rate limiting using Redis. Allows 30 requests per minute per IP by default. Uses Redis atomic increment: `INCR key → set expiry on first increment → reject if count > limit`.

This is a secondary defence layer. The primary defence against rapid requests is the per-table cooldown in `queue_engine.add_song_request()`. This layer protects against API scrapers and automated tools.

---

### `app/api/v1/middleware/error_handler.py`

**`register_exception_handlers(app)`:**

Catches any unhandled exception that bubbles up through all layers. Without this, FastAPI would return a raw Python traceback to the client — exposing your internal code structure to anyone who triggers an error.

With this, every unhandled exception returns:
```json
{"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred. Our team has been notified."}
```

The real error is logged by structlog and captured by Sentry. The client gets a safe, generic message.

**Domain exceptions (in `app/exceptions/`) are NOT caught here.** They're `HTTPException` subclasses that FastAPI handles automatically. Only truly unexpected exceptions (bugs, database connection failures, etc.) reach this handler.

---

### `app/api/v1/middleware/logging.py`

**`RequestLoggingMiddleware`:**

Wraps every request. For each request:
1. Generates a short 8-character `request_id`
2. Binds it to the structlog context (so every log line within this request shows it)
3. Measures execution time
4. Logs: `{"event": "http.request", "method": "POST", "path": "/api/v1/boosts/", "status_code": 201, "duration_ms": 45.2}`
5. Adds `X-Request-ID` header to the response (so the frontend can include it in bug reports)

**When you're debugging:** Find the request ID from the error report, filter logs by `request_id`, and you see the exact sequence of database calls, service calls, and log lines that produced the error.

---

### `app/api/v1/routes/auth.py`

**`POST /auth/login`:**

Accepts email + password. Checks the database for the user. Verifies the bcrypt hash. Returns access token + refresh token. Used by venue owners and staff to log into the dashboard.

**`POST /auth/refresh`:**

Accepts a refresh token. Verifies it. Returns a new access token. Called automatically by the frontend before the access token expires (60 minutes) so the user doesn't get logged out mid-shift.

**`POST /auth/logout`:**

Currently a no-op — just returns success. The real logout happens when the frontend discards the tokens. Token blacklisting (a Redis set of revoked token IDs) is marked as a post-pilot enhancement.

---

### `app/api/v1/routes/sessions.py`

**`POST /sessions/open` (staff only):**

The waiter hits this when a new group sits down at a table. Generates a 6-digit code and returns it. The waiter tells the guests verbally.

**`POST /sessions/join` (public):**

Arjun's phone hits this with `{"table_code": "482176"}` and the venue slug from the URL. Validates the code. Returns a JWT the phone uses for all subsequent requests, plus the venue name and spend cap.

**`GET /sessions/{session_id}/status` (public):**

Called by the guest app on resume (coming back to the browser tab after backgrounding the app). Checks if the session is still active. If expired, shows the "get new code" screen.

**`POST /sessions/{session_id}/close` (staff only):**

Called after billing is complete. Sets `is_active=False` on the session. The table's queue entries are expired. The night is done.

---

### `app/api/v1/routes/queue.py`

**`GET /queue/{venue_id}` (public):**

Returns the full queue state. Called once when a guest joins. After that, WebSocket pushes updates — this endpoint is just the initial load.

**`POST /queue/request` (guest auth):**

Arjun taps "Request" on Kesariya. This hits this endpoint with `{"song_id": "...", "youtube_video_id": "BVBWugH_aFE"}`. The endpoint calls `queue_engine.add_song_request()` and returns the new queue entry with its position.

**`DELETE /queue/{entry_id}` (staff auth):**

The staff dashboard's "remove" button. Silently removes the song. Cancels all pending boosts. Broadcasts queue update.

**`POST /queue/{entry_id}/mark-played` (staff auth):**

**Mode B only.** The staff taps this after playing the song on their own system. This is the billing trigger in Mode B — equivalent to the `ENDED` event in Mode A.

---

### `app/api/v1/routes/songs.py`

**`GET /songs/search?q=kesariya` (guest auth):**

Arjun types "kesariya" in the search box. This hits this endpoint. It searches the venue's approved catalogue using `song_repo.search()`. Returns up to 20 matching songs with their YouTube video IDs.

The search is scoped to the guest's venue by reading `guest_session.venue_id` from their JWT. Arjun cannot search another venue's catalogue.

---

### `app/api/v1/routes/boosts.py`

**`GET /boosts/tiers` (public):**

Returns the three fixed boost options. The frontend reads this to render the boost buttons. No auth required — the pricing is public information.

**`POST /boosts/` (guest auth):**

Arjun taps "Medium Boost ₹25." This hits this endpoint with `{"queue_entry_id": "...", "amount_paise": 2500}`.

Validates:
1. Amount is one of {1500, 2500, 3500} — reject custom amounts
2. Queue entry is in active queue (not waiting pool)
3. Spend cap not exceeded

Then calls `queue_engine.apply_boost()`.

---

### `app/api/v1/routes/billing.py`

**`GET /billing/review/{session_id}` (guest auth):**

Returns the pre-billing review. Called when the waiter says "bill please" and before the payment order is created.

**`DELETE /billing/boost/{boost_id}` (guest auth):**

Arjun sees "Tumse Milke Dil Ka — NOT PLAYED — ₹35" and taps remove. This endpoint cancels that pending boost.

**`POST /billing/confirm` (guest auth):**

Arjun reviews everything, confirms. This creates the Razorpay payment order and returns the order details for the payment modal.

---

### `app/api/v1/routes/payments.py`

**`POST /payments/create-order` (guest auth):**

Calls `billing_service.calculate_total()` to get the confirmed total. Calls `payment_service.create_order()`. Returns `{razorpay_order_id, amount_paise, razorpay_key_id}` for the frontend to open Razorpay checkout.

**`POST /payments/verify` (public — Razorpay calls this):**

The most security-critical route. Razorpay sends a POST here after payment. Verifies the HMAC signature. Marks the payment as paid.

**Register this webhook in Razorpay Dashboard:** Settings → Webhooks → Add URL → `https://api.vibequeue.in/api/v1/payments/verify` → Events: `payment.captured`

**`POST /payments/cash/{session_id}` (staff auth):**

Fallback if UPI fails repeatedly. Waiter marks payment as cash-collected. Table closes.

---

### `app/api/v1/routes/playback.py`

**`POST /playback/event` (staff auth):**

The Playback Tab on the venue laptop calls this endpoint with events from the YouTube IFrame Player. When Kesariya ends, it sends `{"event_type": "ENDED", "youtube_video_id": "BVBWugH_aFE", ...}`. This triggers `playback_service.handle_event()` which triggers billing confirmation.

**`GET /playback/next/{venue_id}` (staff auth):**

Polling fallback for the Playback Tab. If the WebSocket drops, the tab falls back to polling this endpoint every 5 seconds to know what to play next. Returns the next pending playback command.

---

### `app/api/v1/routes/catalogue.py`

**`GET /catalogue/{venue_id}` (owner auth):**

Returns the full catalogue including disabled songs. Used in the dashboard's "Manage Songs" view.

**`POST /catalogue/{venue_id}/songs` (owner auth):**

Venue owner adds a new song by YouTube video ID. In the full implementation, this calls `youtube_service.get_video_metadata()` to auto-fill the title and artist.

**`PATCH /catalogue/{venue_id}/songs/{song_id}/toggle` (owner auth):**

Toggle a song on or off. When a song is disabled (`is_enabled=False`), it immediately disappears from guest search results and cannot be requested.

**`POST /catalogue/{venue_id}/validate` (owner auth):**

Triggers an immediate catalogue validation for one venue. Used when the owner suspects some songs have been taken down. Dispatches a Celery task and returns immediately — the validation runs in the background.

---

### `app/api/v1/routes/analytics.py`

**`GET /analytics/{venue_id}/tonight` (owner auth):**

Live stats for the venue dashboard's revenue counter. Called every 30 seconds by the dashboard. Returns: songs requested tonight, boosts purchased, boost conversion rate, total revenue, venue's share.

**`GET /analytics/{venue_id}/weekly` (owner auth):**

The data behind the Sunday WhatsApp report. Also used to generate the on-demand report in the dashboard. The `week_offset` parameter lets owners view previous weeks (0=this week, 1=last week).

---

### `app/api/v1/routes/websockets.py`

**`/ws/venue/{venue_id}/queue`:**

The real-time channel every guest phone connects to. When a boost is applied and the queue reorders, this channel pushes the new queue to every connected client simultaneously without them refreshing.

**How it works:**
1. Guest phone connects (WebSocket handshake)
2. Server immediately sends the current queue state (so the phone has data right away)
3. Server subscribes to Redis channel `vq:{venue_id}:ws`
4. When `queue_engine._recalculate_and_broadcast()` publishes `"queue_updated"` to that channel:
5. The WebSocket handler receives it
6. Reads fresh queue from PostgreSQL
7. Sends to the connected client

If the connection drops (phone locks, loses signal), it reconnects and gets the current state immediately on reconnect.

---

## 10. app/workers/

Workers are Celery tasks — code that runs in the background, not in response to HTTP requests. They run in a separate process (`celery worker`) and are scheduled by Celery Beat.

---

### `app/workers/tasks/catalogue_tasks.py`

**`validate_all_catalogues` (runs every Monday 3am):**

Fetches all active venues from the database. For each venue, dispatches `validate_venue_catalogue` as a separate task. Using separate tasks means a failure for one venue doesn't affect others.

**`validate_venue_catalogue(venue_id)`:**

Loads all enabled songs for the venue. Calls `catalogue_service.check_videos_embeddable()` in batches of 50. For videos that fail: sets `is_embeddable=False` in the database (hides from guests immediately). Dispatches a WhatsApp notification to the venue owner. The owner has until Friday to replace the broken songs before the weekend rush.

---

### `app/workers/tasks/notification_tasks.py`

**`send_weekly_revenue_reports` (runs every Sunday 11pm):**

Fetches all active venues. For each, runs the same analytics calculation as the dashboard endpoint, then calls `notification_service.send_weekly_report()`. The owner wakes up Monday morning to a WhatsApp message with last week's numbers.

**`send_whatsapp_message(phone_number, template_name, template_params)`:**

The atomic unit of WhatsApp notification. All other notification tasks call this. Marked as `max_retries=3` — if the WhatsApp API returns a 5xx error (Meta's servers are down), it retries automatically up to 3 times with increasing delays.

---

### `app/workers/tasks/cleanup_tasks.py`

**`cleanup_expired_records` (runs every night 2am):**

1. Find all `QueueEntry` rows with `status="active"` and `expires_at < now`
2. For each: cancel all pending boosts (no charge to guests), set status to `"expired"`
3. Find all `TableSession` rows with `is_active=True` and `expires_at < now`
4. Set `is_active=False`
5. Clear stale Redis keys

This ensures the database doesn't accumulate dead data indefinitely. A bar that runs VibeQueue every night for a year would have thousands of expired queue entries without this cleanup.

---

### `app/workers/tasks/playback_tasks.py`

**`check_stalled_playback` (runs every hour):**

Finds `PlaybackCommand` rows with `status="pending"` and `created_at < (now - PLAYBACK_WATCHDOG_SECONDS)`.

If found: the venue laptop's Playback Tab isn't acknowledging commands. Possible causes: browser tab was closed, laptop was restarted, the Chrome kiosk tab crashed.

Action: Update status to `"stalled"`. Send a WhatsApp alert to the VibeQueue support contact (your phone number during the pilot). During pilot, you can call the venue in minutes.

---

### `app/workers/tasks/payment_tasks.py`

**`verify_razorpay_payment`:** Can be used as an async alternative to the webhook if needed. During the pilot, the webhook is the primary path.

**`settle_weekly_revenue`:** Future task — calculates the total VibeQueue share across all venues for the week and generates a settlement report. During the pilot, you do this manually using `scripts/generate_report.py`.

---

## 11. app/utils/

Small, stateless helper functions used across multiple layers. These have no database dependency and no business logic — they're pure computation.

---

### `app/utils/scoring.py`

**The most mathematically important file in the codebase.**

**`calculate_score(boost_total_paise, requested_at, now)`:**

The formula: `score = boost_total_paise + (1000 / minutes_since_request)`

- `1000` is `DECAY_BASE` — the time decay weighting factor in paise. It's set to 1000 so that a song requested right now gets a decay bonus of ~1000 (at 0.01 minutes), which a ₹15 boost (1500 paise) immediately overcomes.
- `minutes_since_request` has a minimum of 0.01 to prevent division by zero on brand-new requests.

**Example calculations:**
- Unbosted song, just requested: `0 + (1000/0.01) = ~100,000` (very high initially, falls fast)
- Actually at 1 minute: `0 + (1000/1) = 1000`
- At 5 minutes: `0 + (1000/5) = 200`
- At 30 minutes: `0 + (1000/30) = 33`
- ₹25 boost (2500 paise), 5 minutes old: `2500 + 200 = 2700`

This means an unbosted song naturally rises early on, then falls, while a boosted song dominates.

**`sort_queue_entries(entries, now)`:**

1. Calls `calculate_score()` for each entry and stores the score on the entry object
2. Sorts by `(-score, created_at)` — highest score first, oldest request as tiebreaker

The `-score` (negated) means higher scores sort first in Python's ascending sort.

---

### `app/utils/formatters.py`

**`paise_to_rupees_display(paise)`:** `2500 → "₹25"`. Used in schemas and WhatsApp messages.

**`format_duration(seconds)`:** `225 → "3:45"`. Shown next to song names in the catalogue.

**`format_conversion_rate(requested, boosted)`:** `(300, 45) → "15.0%"`. Used in the weekly report.

---

### `app/utils/validators.py`

**`is_valid_youtube_video_id(video_id)`:** YouTube video IDs are exactly 11 characters: letters, numbers, hyphens, underscores. A regex validates this before making any API calls. Catches typos early.

**`is_valid_phone_number(phone)`:** Basic validation for Indian numbers. Used in `create_venue.py` to validate the owner's WhatsApp number before storing it.

---

## 12. app/exceptions/

Domain exceptions are custom `HTTPException` subclasses. They carry a structured payload with a `code` (machine-readable) and a `message` (human-readable).

**Why not just use `HTTPException` directly?** Structured codes allow the frontend to respond differently to different errors. `COOLDOWN_ACTIVE` → show "Wait 45 seconds" UI. `SPEND_CAP_EXCEEDED` → show "You've reached your limit" UI. If you only have status codes (429), the frontend can't distinguish the reason.

**`CooldownActiveError`:** Carries `retry_after_seconds` so the frontend can show a countdown timer.

**`SpendCapExceededError`:** Carries `current_spend_paise` and `cap_paise` so the frontend can show "₹75 spent of ₹150 limit" without another API call.

**`WaitingPoolBoostError`:** The most common error for confused guests. The message is carefully worded: "Boost is available once your song enters the live queue." — not "you can't boost this."

---

## 13. alembic/

Alembic manages the database schema evolution. When you add a column to a model, Alembic generates a migration script that safely applies that change to the live database.

---

### `alembic/env.py`

**What it does:** Connects Alembic to your database and models.

The critical lines:
```python
from app.models import *  # Loads all model classes
target_metadata = Base.metadata  # Tells Alembic about your tables
```

With `target_metadata` set, running `alembic revision --autogenerate -m "description"` compares your current Python models to the current database schema and generates a migration script for the difference.

**How to use it:**
```bash
# After adding a new column to Song model:
alembic revision --autogenerate -m "add mood_tag to songs"
# This creates alembic/versions/abc123_add_mood_tag_to_songs.py
# Review the generated file, then:
alembic upgrade head
# This applies the migration to the database
```

---

### `alembic/script.py.mako`

**What it does:** The template for auto-generated migration files. Every `alembic revision` command uses this template to generate the Python file.

The generated file has two functions: `upgrade()` (what to do when applying the migration) and `downgrade()` (what to do when rolling back). Alembic fills these in based on the model changes it detected.

---

## 14. tests/

The safety net. Tests verify that the code does what you think it does, and catch regressions when you change something.

**Three levels of tests:**

1. **Unit tests** (`tests/unit/`) — Test individual functions with no database, no Redis, no HTTP. Pure Python function calls. Very fast (milliseconds each).

2. **Integration tests** (`tests/integration/`) — Test routes, services, and repositories together with a real (test) database. Slower but more realistic.

3. **End-to-end tests** (`tests/e2e/`) — Test the complete user journey: open table → join → search → request → boost → mark played → review billing → confirm payment. Slowest but most valuable.

---

### `tests/conftest.py`

The shared setup for all tests. Two key fixtures:

**`db_session`:** Creates a fresh in-memory SQLite database for each test function, creates all tables, yields the session, and tears everything down after. Each test gets a perfectly clean database — no data leaks between tests.

**`client`:** Creates an async HTTP test client pointed at the FastAPI application. The database dependency is overridden to use `db_session`. This means every HTTP request in the test uses the clean test database.

```python
# How tests use these fixtures:
async def test_guest_join(client: AsyncClient, db_session):
    # client is connected to the test app
    # db_session is the clean test database
    response = await client.post("/api/v1/sessions/join?venue_slug=test", ...)
    assert response.status_code == 200
```

---

### `tests/unit/utils/test_scoring.py`

**The most important unit test file.** Every test here validates the scoring formula — the engine of the entire priority system.

Tests verify:
- An unboosted song scores high immediately after request (time decay is large)
- A boosted song scores higher than an unboosted one (boost dominates)
- An older song scores lower than a newer one with same boost
- A small boost on a new song beats a large boost on an old song (at some point)
- Tie-breaking: equal scores → older request wins

Run these first. If they pass, the priority system is mathematically correct.

---

### `tests/fixtures/`

Factories for test data. Instead of repeating object creation in every test:

```python
# Without fixtures (bad):
async def test_something(db_session):
    venue = Venue(name="Test Bar", slug="test-bar", city="Bengaluru", mode="B", ...)
    db_session.add(venue)

# With fixtures (good):
from tests.fixtures.venues import make_venue
async def test_something(db_session):
    venue = make_venue(mode="A")  # All other fields have sensible defaults
    db_session.add(venue)
```

**`tests/fixtures/songs.py`** includes `SAMPLE_SONGS` — 5 real songs with real YouTube video IDs that you can use in tests. These are the same songs the seed script loads.

---

### `tests/load/locustfile.py`

**Before the pilot goes live, run this.**

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
       --users 200 --spawn-rate 10 --run-time 300s
```

This simulates 200 guests using VibeQueue simultaneously. The Locust web UI (at `localhost:8089`) shows:
- Requests per second
- Response time percentiles (p50, p95, p99)
- Failure rate
- Any errors

Target: p99 < 500ms, 0% failure rate. If this passes, the pilot won't have performance issues.

---

## 15. scripts/

One-shot scripts for operations tasks. They're not part of the application — they're tools you run manually.

---

### `scripts/seed_db.py`

**Run once** after the first `alembic upgrade head` to create the two pilot venues and their owner accounts.

Creates:
- `koramangala-social` venue (Mode B)
- `indiranagar-hammered` venue (Mode A)
- One venue_owner user per venue with default password `changeme123`

**After running:** Update the venue IDs in `seed_catalogue.py`, then run that.

---

### `scripts/seed_catalogue.py`

Loads 40 pre-curated songs (10 Bollywood, 8 Punjabi, 10 English Pop, 6 Chill Dinner) into each pilot venue's catalogue.

The songs include time-of-day availability rules:
- Chill/classical songs: `available_before_hour=22` (only before 10pm)
- High-energy songs: `available_after_hour=22` (only after 10pm)

**Before running:** Update the `venue_id` values to match those created by `seed_db.py`. The current values are placeholders.

---

### `scripts/validate_youtube_ids.py`

Checks every song in every venue's catalogue against the YouTube Data API. Flags broken videos. Run this after seeding to confirm all 40 songs are still embeddable.

**Run before every pilot venue goes live.** A broken video ID on Saturday night means a song fails to play in front of customers.

Output:
```
Checking 40 songs across all venues...
  ❌ BROKEN: Some Song — Some Artist (xxxxxxxxxxx)
==================================================
Total songs checked: 40
Embeddable (OK):     39
Broken (FLAGGED):    1
```

---

### `scripts/create_venue.py`

Interactive CLI for onboarding a new venue. Asks for name, slug, city, mode, spend cap, owner email/name/password/WhatsApp. Creates the venue and owner account. Prints the QR URL.

**During pilot:** You'll run this script in the 20-minute setup session before going live.

---

### `scripts/generate_report.py`

Generates a weekly report for a venue. Calculates songs requested, boosts purchased, boost conversion rate, total revenue, and venue share. Also prints the WhatsApp message text.

**During pilot:** Run this every Sunday and use the output to craft the WhatsApp message to venue owners until the automated system is fully working.

```bash
python scripts/generate_report.py --venue-id <uuid> --week-offset 0
# Output: Full report + WhatsApp message template
```

---

## 16. nginx/

Nginx sits in front of the FastAPI application in production. It handles SSL termination (when not using Cloudflare), load balancing, request compression, and rate limiting at the network level.

---

### `nginx/nginx.conf`

Development/basic production config. Key sections:

**Upstream block:** Points to `app:8000` — the Docker service name for the FastAPI container.

**WebSocket upgrade:** WebSocket connections require special headers (`Upgrade` and `Connection`). Without these, the connection is treated as a regular HTTP request and fails immediately. The `proxy_read_timeout 86400s` (24 hours) prevents Nginx from closing idle WebSocket connections — a guest connected at 9pm should still be connected at midnight.

**Health check location:** `access_log off` for health checks — you don't need 12 requests per minute from the load balancer polluting your logs.

---

### `nginx/nginx.prod.conf`

Production-hardened version. Key additions:

**JSON access logging:** Every request is logged in structured JSON format — parseable by log aggregators.

**Rate limiting with burst:** `limit_req zone=api burst=20 nodelay` — allows bursts of 20 requests per IP before throttling. Prevents API abuse while allowing legitimate users who click quickly.

**Webhook rate limiting:** Stricter limit for the Razorpay webhook endpoint — it should only be called by Razorpay's servers, not by anyone else.

---

## 17. Docker Files

---

### `Dockerfile`

Defines how to build the production container image.

Key decisions:
- `python:3.13-slim` — Minimal base image (no unnecessary packages = smaller attack surface)
- `PYTHONDONTWRITEBYTECODE=1` — Don't create `.pyc` files in the container
- `PYTHONUNBUFFERED=1` — Print logs immediately without buffering (critical for production log aggregation)
- Non-root user — The app runs as `appuser`, not root. If an attacker exploits the application, they have limited system privileges.
- `gunicorn` with `UvicornWorker` — Gunicorn manages multiple Uvicorn worker processes. 2 workers = the app handles 2 concurrent requests in the event that one blocks. In practice, async FastAPI handles thousands of concurrent requests per worker.

---

### `docker-compose.yml`

**Local development only.** Starts PostgreSQL and Redis. The FastAPI app runs locally with `uvicorn app.main:app --reload`.

The `healthcheck` sections ensure dependent services wait for PostgreSQL and Redis to be actually ready before starting. Without these, the app might start before the database is accepting connections.

---

### `docker-compose.prod.yml`

**Production deployment.** Extends the dev compose file with:
- The FastAPI `app` service (built from Dockerfile)
- `celery_worker` — Runs background tasks
- `celery_beat` — Runs the scheduler (triggers periodic tasks)
- `nginx` — The reverse proxy
- Full health checks on all services
- `restart: unless-stopped` — Auto-restarts crashed services

---

## 18. .github/workflows/

---

### `.github/workflows/ci.yml`

**Runs on every push and pull request to `main`.**

Pipeline steps:
1. Start PostgreSQL and Redis as GitHub Actions services
2. Install Python 3.13 and dependencies
3. Run `ruff check` — catches style issues and obvious bugs
4. Run `mypy` — type checking (non-blocking during pilot)
5. Run `pytest` with coverage — fails if coverage drops below 50%

If any step fails, the PR cannot be merged. This prevents broken code from reaching production.

---

### `.github/workflows/deploy.yml`

**Runs on push to `main` after CI passes.**

Uses Railway CLI to deploy the latest code. After deployment, runs `alembic upgrade head` to apply any pending database migrations. The deployment is zero-downtime on Railway — the new container starts before the old one stops.

**Before this works:** Add `RAILWAY_TOKEN` to GitHub Secrets (Settings → Secrets → Actions).

---

## 19. Complete Friday Night Request — Full Trace

Let's follow Arjun's ₹25 boost for Kesariya through every file:

**9:52pm — Arjun taps "Medium Boost ₹25"**

1. **Guest phone** sends: `POST /api/v1/boosts/` with `Authorization: Bearer <token>` and `{"queue_entry_id": "uuid...", "amount_paise": 2500}`

2. **nginx** receives the request, forwards to FastAPI, logs the request

3. **`app/api/v1/middleware/logging.py`** generates `request_id="a7f3bc"`, starts timer, binds to log context

4. **`app/api/v1/routes/boosts.py`** `apply_boost()` function starts

5. **`app/api/v1/dependencies/session.py`** `get_guest_session()` validates Arjun's JWT, looks up his session in PostgreSQL (via `session_repo`), returns the `TableSession` object

6. **`app/api/v1/routes/boosts.py`** validates `2500 in VALID_AMOUNTS` → passes

7. **`app/services/queue_engine.py`** `apply_boost()` is called:
   - Loads queue entry from `queue_repo.get_by_id(queue_entry_id)`
   - Checks position: 7 (< 8) → not in waiting pool → proceeds
   - Reads `vq:{venue_id}:spend:{session_id}` from Redis → 1500 (Arjun already spent ₹15 earlier)
   - `1500 + 2500 = 4000 < 15000` → under cap → proceeds
   - Calls `boost_repo.create(...)` → new `Boost` row with `status="pending"` in PostgreSQL
   - Calls `queue_repo.update(entry, boost_total_paise=0+2500=2500)` → updates the entry
   - Calls `redis_queue_client.incrby("vq:{venue_id}:spend:{session_id}", 2500)` → spend is now 4000

8. **`app/services/queue_engine.py`** `_recalculate_and_broadcast()` runs:
   - Loads all 8 active queue entries from PostgreSQL
   - Calls `sort_queue_entries()` from `app/utils/scoring.py`
   - Kesariya: `score = 2500 + (1000/30) = 2533.3` (requested 30 min ago)
   - Recalculates all positions — Kesariya moves from position 7 to position 3
   - Updates positions in PostgreSQL
   - Publishes `"queue_updated"` to `redis_queue_client.publish("vq:{venue_id}:ws", "queue_updated")`

9. **`app/api/v1/routes/websockets.py`** WebSocket handler receives `"queue_updated"`:
   - Reads fresh queue from PostgreSQL
   - Sends updated queue JSON to every connected client

10. **Arjun's phone** receives queue update via WebSocket. Kesariya jumps from 7 to 3. He watches it happen.

11. **Ambient display TV** also receives the same WebSocket update. The room sees Table 7's song move up.

12. **FastAPI returns** `201 Created` with the boost response to Arjun's phone

13. **`app/api/v1/middleware/logging.py`** logs: `{"event": "http.request", "status_code": 201, "duration_ms": 47.3, "request_id": "a7f3bc"}`

**Total time:** ~47ms from tap to Arjun's screen updating.

**10:31pm — Kesariya plays**

14. **YouTube IFrame Player** on venue laptop fires `ENDED` event (JavaScript)
15. **Playback Tab** (running on venue laptop) sends `POST /api/v1/playback/event` with `{"event_type": "ENDED", "queue_entry_id": "uuid...", ...}`
16. **`app/api/v1/routes/playback.py`** calls `playback_service.handle_event()`
17. **`app/services/playback_service.py`** sees `event_type="ENDED"` → calls `queue_engine.confirm_song_played()`
18. **`app/services/queue_engine.py`** `confirm_song_played()`:
    - Calls `queue_repo.mark_as_played(queue_entry_id)` → status="played", played_at=10:31pm
    - Calls `boost_repo.confirm_all_for_entry(queue_entry_id)` → Arjun's ₹25 boost: status="confirmed"
    - Calls `_recalculate_and_broadcast()` → next song moves to position 1

**11:47pm — Bill time**

19. **`GET /billing/review/{session_id}`** returns: Kesariya confirmed ₹25 ✓, subtotal ₹25, GST ₹4.50, total ₹29.50
20. Arjun confirms. **`POST /billing/confirm`** creates Razorpay order for ₹29.50
21. Arjun scans UPI QR. Razorpay collects ₹29.50.
22. **Razorpay sends webhook** to `POST /api/v1/payments/verify`
23. **`app/api/v1/routes/payments.py`** verifies signature → `payment_service.verify_and_confirm()` → `Payment.status="paid"`
24. Waiter closes the table. `POST /sessions/{session_id}/close` → `session.is_active=False`

Every file listed above played its exact role. Nothing more, nothing less.

---

## 20. How to Add a New Feature

Follow this exact pattern for any new feature. Example: adding "Song Reactions" (guests can react with 🔥 to a playing song).

**Step 1 — Model (`app/models/reaction.py`)**
```python
class SongReaction(BaseModel):
    __tablename__ = "song_reactions"
    queue_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("queue_entries.id"))
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("table_sessions.id"))
    emoji: Mapped[str] = mapped_column(String(10))
```

**Step 2 — Register in models/__init__.py**
```python
from app.models.reaction import SongReaction
```

**Step 3 — Generate and apply migration**
```bash
alembic revision --autogenerate -m "add song_reactions table"
alembic upgrade head
```

**Step 4 — Schema (`app/schemas/reaction.py`)**
```python
class ReactionCreate(BaseModel):
    queue_entry_id: uuid.UUID
    emoji: str

class ReactionResponse(BaseModel):
    id: uuid.UUID
    emoji: str
    created_at: datetime
    model_config = {"from_attributes": True}
```

**Step 5 — Repository (`app/repositories/reaction_repo.py`)**
```python
class ReactionRepository(BaseRepository[SongReaction]):
    async def get_counts_for_entry(self, entry_id: uuid.UUID) -> dict:
        # Returns {"🔥": 5, "❤️": 3}
```

**Step 6 — Service (if logic needed, otherwise skip)**
```python
# No complex logic here — just save and broadcast
```

**Step 7 — Route (`app/api/v1/routes/reactions.py`)**
```python
@router.post("/", response_model=ReactionResponse)
async def add_reaction(payload: ReactionCreate, guest_session = Depends(get_guest_session), ...):
    # Create reaction, publish to WebSocket channel
```

**Step 8 — Register route in `app/api/v1/router.py`**
```python
from app.api.v1.routes import reactions
api_v1_router.include_router(reactions.router, prefix="/reactions", tags=["Reactions"])
```

**Step 9 — Add to WebSocket message types in `app/schemas/websocket.py`**
```python
type: Literal[..., "reaction_added"]
```

**Step 10 — Write tests**
```
tests/unit/repositories/test_reaction_repo.py
tests/integration/api/v1/test_reactions.py
```

---

## 21. Common Tasks Reference

**Start the development server:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Start infrastructure:**
```bash
docker compose up -d
```

**Apply database migrations:**
```bash
alembic upgrade head
```

**Create a new migration after model changes:**
```bash
alembic revision --autogenerate -m "what changed"
```

**Rollback last migration:**
```bash
alembic downgrade -1
```

**Seed both pilot venues:**
```bash
python scripts/seed_db.py
# Update venue IDs in seed_catalogue.py
python scripts/seed_catalogue.py
```

**Validate all YouTube video IDs:**
```bash
python scripts/validate_youtube_ids.py
```

**Start Celery worker:**
```bash
celery -A app.core.celery.celery_app worker --loglevel=info
```

**Start Celery Beat (scheduler):**
```bash
celery -A app.core.celery.celery_app beat --loglevel=info
```

**Run unit tests only (fast):**
```bash
pytest tests/unit/ -v
```

**Run with coverage:**
```bash
pytest tests/unit/ tests/integration/ --cov=app --cov-report=html
```

**Run the scoring formula tests specifically:**
```bash
pytest tests/unit/utils/test_scoring.py -v
```

**Lint the codebase:**
```bash
ruff check app/ tests/
```

**Generate weekly report for a venue:**
```bash
python scripts/generate_report.py --venue-id <uuid>
```

**Trigger a manual catalogue validation:**
```bash
celery -A app.core.celery.celery_app call app.workers.tasks.catalogue_tasks.validate_all_catalogues
```

**Check if all services are healthy:**
```bash
curl http://localhost:8000/api/v1/health/
# Should return: {"status": "ok", "database": "ok", "redis": "ok"}
```

**View the API documentation:**
```bash
# In development:
open http://localhost:8000/docs
# Every endpoint, its request schema, its response schema, all in a browser UI
```

---

*VibeQueue Backend Codebase Guide · v1.0 · June 2026*
*156 files · FastAPI + PostgreSQL + Redis + Celery*