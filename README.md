# Cybersecurity DEFCON Dashboard

A self-hosted dashboard that aggregates cybersecurity news from RSS feeds, deduplicates articles, scores them on a DEFCON-style threat scale (1–5), and presents everything through a real-time web interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                           │
│                                                                 │
│  ┌──────────┐   ┌──────────────────┐   ┌────────────────────┐  │
│  │ Frontend │──>│   API Gateway    │──>│  News Aggregator   │  │
│  │ :3000    │   │   :4000          │   │   :8000            │  │
│  │ React    │   │   Express        │   │   FastAPI          │  │
│  └──────────┘   └────────┬─────────┘   └────────┬───────────┘  │
│                          │                      │              │
│                   ┌──────┴──────┐        ┌──────┴──────┐       │
│                   │  PostgreSQL │        │    Redis     │       │
│                   │     :5432   │        │    :6379     │       │
│                   └─────────────┘        └─────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Services

| Service | Stack | Port | Purpose |
|---|---|---|---|
| **Frontend** | React 18 + Vite + Tailwind, served by Nginx | `:3000` | Dashboard UI with DEFCON gauge, article feed, widgets |
| **API Gateway** | Node.js 20 + Express | `:4000` | REST API for articles, DEFCON status, read state, admin triggers |
| **News Aggregator** | Python 3.12 + FastAPI + APScheduler | `:8000` | Fetches RSS feeds, deduplicates, scores, stores articles |
| **PostgreSQL 16** | postgres:16-alpine | `:5432` | Articles, read state, DEFCON history, dedup audit log |
| **Redis 7** | redis:7-alpine | `:6379` | Deduplication fingerprints and recent title tracking |

### Networks

- **internal** — PostgreSQL and Redis are isolated; only accessible by the aggregator and API gateway
- **external** — Frontend reaches the API gateway; API gateway reaches the aggregator

## Quick Start

```bash
cp .env.example .env        # Edit POSTGRES_PASSWORD
podman compose up -d        # or docker compose up -d
```

The dashboard is available at **http://localhost:3000**. The aggregator fetches articles on startup and then every 60 minutes.

## News Sources

| Source | Feed URL |
|---|---|
| Bleeping Computer | `https://www.bleepingcomputer.com/feed/` |
| Dark Reading | `https://www.darkreading.com/rss.xml` |
| Help Net Security | `https://www.helpnetsecurity.com/feed/` |
| Security Week | `https://feeds.feedburner.com/Securityweek` |
| The Hacker News | `https://feeds.feedburner.com/TheHackersNews` |

## Data Pipeline

### 1. Fetch

Each RSS feed is fetched via `httpx` and parsed with `feedparser`. Raw articles are normalized into a `RawArticle` dataclass.

### 2. Deduplicate (two layers)

| Layer | Method | Threshold |
|---|---|---|
| **L1 — Fast** | SHA-256 fingerprint of normalized title tokens | Exact match via Redis SET |
| **L2 — Semantic** | Jaccard token overlap + TF-IDF cosine similarity (scikit-learn) | Jaccard >= 0.35, cosine >= 0.55 |

Temporal conflicts (different months/years in titles) are never flagged as duplicates. Cross-feed duplicates are caught within a batch before Redis state is updated.

### 3. Score (DEFCON 0–100)

Each article gets a composite score from four equally weighted dimensions (25 points each):

| Dimension | Logic |
|---|---|
| **Volume** | New articles in the last hour / 12 |
| **CVE Severity** | CVSS scores extracted from text, or inferred from severity keywords |
| **Impact** | Regex scan for: millions affected, critical infrastructure, active exploitation, large breaches |
| **Keywords** | 3-tier threat vocabulary: tier 1 (+5), tier 2 (+3), tier 3 (+1) |

The global DEFCON level is computed from the same dimensions across the recent article window:

| Score | Level | Label | Color |
|---|---|---|---|
| 0–19 | 1 | LOW | Green |
| 20–39 | 2 | GUARDED | Blue |
| 40–59 | 3 | ELEVATED | Amber |
| 60–79 | 4 | HIGH | Orange |
| 80–100 | 5 | CRITICAL | Red |

### 4. Store

Articles are upserted into PostgreSQL. Old articles are trimmed to keep 200 total / 15 per source.

## API Endpoints

All public routes are prefixed with `/api/v1/`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/articles` | List articles (`limit`, `offset`, `source`, `unread_only`) |
| `PATCH` | `/articles/:id/read` | Mark article read/unread (`{ is_read: bool }`) |
| `PATCH` | `/articles/read-all` | Mark all articles as read for this session |
| `GET` | `/defcon` | Current DEFCON status (score, level, trend, factors) |
| `GET` | `/defcon/history` | Score history (`hours` param, max 168) |
| `POST` | `/admin/refresh` | Trigger a manual fetch cycle (rate-limited) |
| `GET` | `/health` | Health check (PostgreSQL + Redis + aggregator) |

Session-based read state is managed via the `X-Session-ID` header (auto-generated UUID persisted in localStorage).

## Database Schema

| Table | Purpose |
|---|---|
| `articles` | Core article store with source, DEFCON score, categories |
| `article_read_state` | Per-session read/unread tracking |
| `defcon_history` | Time-series of computed DEFCON scores with contributing factors |
| `dedup_log` | Audit log of duplicate detection |
| `last_refresh` | Singleton tracking the last refresh timestamp |

## Frontend Widgets

| Widget | Description |
|---|---|
| DEFCON Gauge | Circular gauge with current threat level and history sparkline |
| Threat Indicators | Score, level, trend, article count |
| Severity Breakdown | Stacked bar showing article count per DEFCON level |
| Top Threats | 5 highest-scoring articles as clickable links |
| Sources | Per-source article counts |
| Source Distribution | Donut chart of article share per source |
| Trending Keywords | Most frequent threat terms across articles |
| Recent CVEs | CVE IDs extracted from article text, linking to NVD |

## Development

The `docker-compose.override.yml` enables hot-reload for all services and exposes the aggregator port:

```bash
podman compose up          # dev mode (auto-applied override)
```

To do a clean reset (drops all data):

```bash
podman compose down -v && podman compose up --build -d
```

## Environment Variables

| Variable | Used By | Description |
|---|---|---|
| `POSTGRES_PASSWORD` | PostgreSQL | Database password |
| `CORS_ORIGIN` | API Gateway | Allowed browser origin (default: `http://localhost:3000`) |
| `VITE_API_BASE_URL` | Frontend | API URL baked in at build time (default: `http://localhost:4000`) |
| `FETCH_INTERVAL_MINUTES` | Aggregator | Scheduler interval in minutes (default: `60`) |
| `LOG_LEVEL` | Aggregator | Python logging level (default: `INFO`) |
