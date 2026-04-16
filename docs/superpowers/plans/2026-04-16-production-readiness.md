# Production Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the project fully ready for production deployment via OpenTofu, with accurate example files and a complete README.

**Architecture:** Four existing files are edited, one directory + gitkeep is created. No tofu modules change. Changes are purely documentation and dev-stack config. Tasks are independent and can be committed separately.

**Tech Stack:** OpenTofu (HCL), Docker Compose (YAML), Markdown

**Spec:** `docs/superpowers/specs/2026-04-16-production-readiness-design.md`

---

## File Map

| Action | File | What changes |
|---|---|---|
| Modify | `README.md` | Remove override ref, add Screenshots section, add Production Deployment section |
| Modify | `.env.example` | Add dev-only comment, add `FETCH_INTERVAL_MINUTES` + `LOG_LEVEL` |
| Modify | `docker-compose.yml` | Un-hardcode `FETCH_INTERVAL_MINUTES` and `LOG_LEVEL` |
| Modify | `tofu/terraform.tfvars.example` | Shared-Traefik scenario, `traefik_router` docs, memory guidance |
| Create | `docs/screenshots/.gitkeep` | Empty file so directory is tracked by git |

---

### Task 1: Create screenshots directory

**Files:**
- Create: `docs/screenshots/.gitkeep`

- [ ] **Step 1: Create the file**

```bash
mkdir -p docs/screenshots && touch docs/screenshots/.gitkeep
```

- [ ] **Step 2: Verify**

```bash
ls docs/screenshots/
```
Expected output: `.gitkeep`

- [ ] **Step 3: Commit**

```bash
git add docs/screenshots/.gitkeep
git commit -m "chore: add docs/screenshots placeholder directory"
```

---

### Task 2: Fix `.env.example`

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Replace the file content**

Replace the entire file with:

```
# Local development only — production uses tofu-generated values
# cp .env.example .env

# PostgreSQL
POSTGRES_PASSWORD=changeme_strong_password

# CORS — the origin your browser uses to reach the frontend
CORS_ORIGIN=http://localhost:3000

# Frontend → API URL (used at build time by Vite)
VITE_API_BASE_URL=http://localhost:4000

# Authentication — change both before deploying
AUTH_SECRET=changeme_long_random_secret_key
ADMIN_PASSWORD=changeme_admin_password

# News aggregator scheduler interval (minutes)
FETCH_INTERVAL_MINUTES=60

# Python log level for the news aggregator
LOG_LEVEL=INFO
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "chore: add FETCH_INTERVAL_MINUTES and LOG_LEVEL to .env.example"
```

---

### Task 3: Fix `docker-compose.yml` — un-hardcode env vars

**Files:**
- Modify: `docker-compose.yml` (news-aggregator service, lines ~49-50)

The `news-aggregator` service currently has:
```yaml
      FETCH_INTERVAL_MINUTES: "60"
      LOG_LEVEL: INFO
```

- [ ] **Step 1: Replace hardcoded values with env var references**

Change those two lines to:
```yaml
      FETCH_INTERVAL_MINUTES: "${FETCH_INTERVAL_MINUTES:-60}"
      LOG_LEVEL: "${LOG_LEVEL:-INFO}"
```

- [ ] **Step 2: Verify the compose file is valid**

```bash
docker compose config --quiet
```
Expected: no output (valid), or `podman compose config --quiet` if using podman.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "fix: read FETCH_INTERVAL_MINUTES and LOG_LEVEL from env in compose"
```

---

### Task 4: Improve `tofu/terraform.tfvars.example`

**Files:**
- Modify: `tofu/terraform.tfvars.example`

- [ ] **Step 1: Replace the file content**

Replace the entire file with:

```hcl
# =============================================================================
# terraform.tfvars.example — Configuration Reference
# =============================================================================
#
# Copy this file to terraform.tfvars and fill in the required values.
# Commented-out variables show their default — uncomment only to override.
#
# BEFORE FIRST RUN
#   1. Set DNS A record for defcon_domain → your server IP.
#   2. Verify DNS resolves: dig +short defcon.example.com @1.1.1.1
#   3. Fill in the required fields below.
#   4. tofu init && tofu plan && tofu apply
#
# SENSITIVE
#   Keep terraform.tfvars out of version control (.gitignore already covers it).
#
# =============================================================================

# =============================================================================
# CONNECTION
# =============================================================================

# Remote Docker daemon over SSH (recommended for VPS deployments):
docker_host = "ssh://deploy@your-server.example.com"
remote_host = "deploy@your-server.example.com"

# Local Docker socket (for local testing only):
# docker_host = "unix:///var/run/docker.sock"
# remote_host = ""

# =============================================================================
# GLOBAL SETTINGS
# =============================================================================

# Email for Let's Encrypt certificate notifications.
admin_email = "you@example.com"

# Root directory on the server for all application data.
# base_app_dir = "/opt"

# =============================================================================
# TRAEFIK GATEWAY
# =============================================================================

# Traefik already running on this server (e.g. from another OpenTofu stack):
deploy_traefik = false
# The traefik network must already exist on the server.

# Fresh server — deploy Traefik as part of this stack:
# deploy_traefik = true

# Traefik image tag — update here to upgrade.
# traefik_version = "v3.6"

# Enable the Traefik dashboard — keep false in production.
# traefik_dashboard_enabled = false

# =============================================================================
# TRAEFIK ROUTING
# =============================================================================

# Override individual routing settings (all have sensible defaults):
# traefik_router = {
#   enabled       = "true"
#   tls           = "true"
#   entrypoint    = "websecure"
#   cert_resolver = "letsencrypt"
#   middlewares   = "security-headers@file,rate-limit@file,compress@file"
# }

# =============================================================================
# DEFCON DASHBOARD
# =============================================================================

# Public domain — must have a valid DNS A record before applying.
defcon_domain = "defcon.example.com"

# Login password for the dashboard.
defcon_admin_password = "change-me-strong-password"

# How often to fetch new articles (minutes).
# defcon_fetch_interval_minutes = 60

# =============================================================================
# MEMORY LIMITS
# =============================================================================

# Tune for your VPS size (values in MiB):
#
#   1 GB VPS → postgres=256  redis=128  aggregator=256  api=128  frontend=64
#   2 GB VPS → postgres=512  redis=256  aggregator=512  api=256  frontend=128  (defaults)
#   4 GB VPS → postgres=512  redis=256  aggregator=512  api=256  frontend=128  (same, more headroom)
#
# defcon_postgres_memory_limit    = 512
# defcon_redis_memory_limit       = 256
# defcon_aggregator_memory_limit  = 512
# defcon_api_gateway_memory_limit = 256
# defcon_frontend_memory_limit    = 128
```

- [ ] **Step 2: Commit**

```bash
git add tofu/terraform.tfvars.example
git commit -m "docs: improve tfvars.example with shared-Traefik scenario and memory guidance"
```

---

### Task 5: Rewrite `README.md`

**Files:**
- Modify: `README.md`

This is the biggest change. The file is rewritten top-to-bottom. All existing content is preserved
except: the `docker-compose.override.yml` reference and hot-reload paragraph (lines ~140-144) are
removed, a Screenshots section is added after the intro, and a full Production Deployment section
is added before the Environment Variables table.

- [ ] **Step 1: Replace the entire file**

Replace `README.md` with:

````markdown
# Cybersecurity DEFCON Dashboard

A self-hosted dashboard that aggregates cybersecurity news from RSS feeds, deduplicates articles, scores them on a DEFCON-style threat scale (1–5), and presents everything through a real-time web interface.

## Screenshots

![DEFCON Dashboard](docs/screenshots/dashboard.png)
![DEFCON Gauge](docs/screenshots/defcon-gauge.png)

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

## Quick Start (local / dev)

```bash
cp .env.example .env        # Edit POSTGRES_PASSWORD and AUTH_SECRET
podman compose up -d        # or: docker compose up -d
```

The dashboard is available at **http://localhost:3000**. The aggregator fetches articles on startup and then every 60 minutes.

Clean reset (drops all data):

```bash
podman compose down -v && podman compose up --build -d
```

## Production Deployment (OpenTofu)

### Requirements

- OpenTofu 1.6+
- Target server with Docker installed
- Deploy user in the `docker` group
- SSH access to the target server
- DNS A record pointing your domain to the server IP

### DNS — do this first

Before running `tofu apply`, your domain must resolve to the server:

```bash
# Create an A record: defcon.example.com → your server IP
# Then verify propagation:
dig +short defcon.example.com @1.1.1.1
```

Let's Encrypt validates DNS during certificate issuance. Repeated failures trigger a temporary ban — confirm the record resolves before applying.

### Secrets & State

Postgres password and JWT signing key are auto-generated by OpenTofu on first apply. They are written to `/opt/defcon-dashboard/.env` on the server (permissions: `0600`) and stored in `terraform.tfstate`.

The state file contains all secrets in plaintext. It is gitignored — treat it like a password store.

> **Optional (teams/CI):** Use remote state with encryption — S3 with server-side encryption or Terraform Cloud — so the state file never sits on a workstation.

### Quick Start

```bash
cd tofu/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — see comments inside
tofu init
tofu plan
tofu apply
```

Minimum required values in `terraform.tfvars`:

| Variable | Example |
|---|---|
| `docker_host` | `ssh://deploy@your-server.example.com` |
| `remote_host` | `deploy@your-server.example.com` |
| `admin_email` | `you@example.com` |
| `defcon_domain` | `defcon.example.com` |
| `defcon_admin_password` | `a-strong-password` |

### Shared Traefik

If Traefik is already running on the server (deployed by another stack), set:

```hcl
deploy_traefik = false
```

The `traefik` Docker network must already exist on the server. The dashboard containers join it automatically.

### Retrieve credentials

```bash
tofu output -json defcon_secrets | jq
```

### Update images

Use `-replace` to rebuild and redeploy a container. Docker volumes (your data) are preserved.

```bash
tofu apply -replace='module.defcon.docker_image.news_aggregator'
tofu apply -replace='module.defcon.docker_image.api_gateway'
tofu apply -replace='module.defcon.docker_image.frontend'
```

Do not use `tofu destroy` to update images — it removes volumes and permanently deletes all data.

### Backup

Volume names use `defcon_name_prefix` (default: `defcon`):

```bash
# PostgreSQL data
docker run --rm -v defcon-postgres-data:/data -v $(pwd):/backup \
  alpine tar -czf /backup/postgres-backup.tar.gz -C /data .

# Redis data
docker run --rm -v defcon-redis-data:/data -v $(pwd):/backup \
  alpine tar -czf /backup/redis-backup.tar.gz -C /data .
```

### Destroy

**Warning:** This removes all containers and volumes. All data is permanently deleted.

```bash
tofu destroy
```

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

## Environment Variables

| Variable | Used By | Description |
|---|---|---|
| `POSTGRES_PASSWORD` | PostgreSQL | Database password |
| `CORS_ORIGIN` | API Gateway | Allowed browser origin (default: `http://localhost:3000`) |
| `VITE_API_BASE_URL` | Frontend | API URL baked in at build time (default: `http://localhost:4000`) |
| `AUTH_SECRET` | API Gateway | JWT signing key |
| `ADMIN_PASSWORD` | API Gateway | Dashboard login password |
| `FETCH_INTERVAL_MINUTES` | Aggregator | Scheduler interval in minutes (default: `60`) |
| `LOG_LEVEL` | Aggregator | Python logging level (default: `INFO`) |
````

- [ ] **Step 2: Verify the file looks right**

Open `README.md` and confirm:
- No mention of `docker-compose.override.yml`
- Screenshots section present after intro
- Production Deployment section present with all subsections
- Environment Variables table includes `AUTH_SECRET`, `ADMIN_PASSWORD`, `FETCH_INTERVAL_MINUTES`, `LOG_LEVEL`

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add production deployment section, screenshots placeholder, clean up dev section"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| Remove docker-compose.override.yml reference | Task 5 |
| Screenshots section with 2 placeholders | Task 5 |
| Create docs/screenshots/ directory | Task 1 |
| Production Deployment section (all 9 subsections) | Task 5 |
| .env.example dev-only comment | Task 2 |
| .env.example FETCH_INTERVAL_MINUTES + LOG_LEVEL | Task 2 |
| docker-compose.yml un-hardcode env vars | Task 3 |
| tfvars.example deploy_traefik = false primary | Task 4 |
| tfvars.example traefik_router documented | Task 4 |
| tfvars.example memory tuning guidance | Task 4 |
| State file security documented in README | Task 5 |
| Remote state as optional step | Task 5 |
| Redis backup in README | Task 5 |

All spec requirements covered. No placeholders, no TBDs. README environment variables table now
includes `AUTH_SECRET` and `ADMIN_PASSWORD` which were missing from the original.
