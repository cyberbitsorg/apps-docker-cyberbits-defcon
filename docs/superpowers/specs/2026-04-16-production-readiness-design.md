# Production Readiness Design — Cybersecurity DEFCON Dashboard

Date: 2026-04-16
Status: Approved

## Context

The project needs to be ready for production deployment via OpenTofu. The OpenTofu setup is already
structurally complete (modules for Traefik + defcon-dashboard, providers, variables, outputs). What
is missing is: a production deployment section in the README, complete example files, and two small
code fixes in the dev stack.

The reference project is `../apps-docker-cyberbits-opentofu`. The primary deployment scenario is a
remote VPS where Traefik is already running (deployed by that reference project), so
`deploy_traefik = false` is the expected default for this project.

## Scope

Three files change, one file is fixed:

1. `README.md` — add production deployment section, remove docker-compose.override.yml reference
2. `.env.example` — add two missing env vars, add dev-only note
3. `docker-compose.yml` — un-hardcode two env vars to respect `.env`
4. `tofu/terraform.tfvars.example` — improve for the shared-Traefik scenario

No tofu modules are changed. No new files are created.

## README.md changes

### Remove
- The `docker-compose.override.yml` reference and the hot-reload explanation
- The "podman compose up (dev mode, auto-applied override)" distinction

### Dev section (keep, simplify)
```
## Quick Start (local / dev)

cp .env.example .env        # edit POSTGRES_PASSWORD and AUTH_SECRET
podman compose up -d        # or: docker compose up -d

Clean reset (drops all data):
podman compose down -v && podman compose up --build -d
```

### New section: Production Deployment (OpenTofu)

Order:
1. **Requirements** — OpenTofu 1.6+, Docker on target server, deploy user in `docker` group,
   SSH access, DNS A record pointing to server IP
2. **DNS warning** — Let's Encrypt validates DNS; repeated failures trigger a temporary ban.
   Verify with `dig +short defcon.example.com @1.1.1.1` before applying.
3. **Secrets & State** — Postgres password and JWT signing key are auto-generated on first
   `tofu apply`. They live in the `.env` on the server (`/opt/defcon-dashboard/.env`, 0600)
   and in `terraform.tfstate`. The state file is gitignored. Treat it like a password store.
   Optional: remote state with S3 or Terraform Cloud for team/CI use.
4. **Quick Start** (step by step):
   ```
   cd tofu/
   cp terraform.tfvars.example terraform.tfvars
   # edit terraform.tfvars — set docker_host, remote_host, admin_email, defcon_domain,
   # defcon_admin_password. Set deploy_traefik = false if Traefik already runs on the server.
   tofu init
   tofu plan
   tofu apply
   ```
5. **Shared Traefik** — If Traefik is already running on the server (e.g. from another stack):
   ```hcl
   deploy_traefik = false
   # The traefik network must already exist on the server.
   ```
6. **Retrieve credentials** — `tofu output -json defcon_secrets | jq`
7. **Update images** — use `-replace`, never `destroy`:
   ```
   tofu apply -replace='module.defcon.docker_image.frontend'
   tofu apply -replace='module.defcon.docker_image.api_gateway'
   tofu apply -replace='module.defcon.docker_image.news_aggregator'
   ```
8. **Backup** — volumes (volume names use `defcon_name_prefix`, default `defcon`):
   ```
   docker run --rm -v defcon-postgres-data:/data -v $(pwd):/backup \
     alpine tar -czf /backup/postgres-backup.tar.gz -C /data .
   docker run --rm -v defcon-redis-data:/data -v $(pwd):/backup \
     alpine tar -czf /backup/redis-backup.tar.gz -C /data .
   ```
9. **Destroy** — warning: removes containers AND volumes (all data lost):
   ```
   tofu destroy
   ```

## .env.example changes

Add at top:
```
# Local development only — production uses tofu-generated values
```

Add two new variables (currently hardcoded in docker-compose.yml):
```
# News aggregator scheduler interval (minutes)
FETCH_INTERVAL_MINUTES=60

# Python log level for the news aggregator
LOG_LEVEL=INFO
```

## docker-compose.yml changes

In the `news-aggregator` service, replace hardcoded values:

```yaml
# Before
FETCH_INTERVAL_MINUTES: "60"
LOG_LEVEL: INFO

# After
FETCH_INTERVAL_MINUTES: "${FETCH_INTERVAL_MINUTES:-60}"
LOG_LEVEL: "${LOG_LEVEL:-INFO}"
```

This makes the compose stack work without a `.env` file (fallback to defaults) while respecting
the env file when present.

## terraform.tfvars.example changes

### 1. deploy_traefik scenario — make prominent

Add a clear two-option block near the top of the Traefik section:

```hcl
# Traefik already running on this server (e.g. from another OpenTofu stack):
deploy_traefik = false

# Fresh server — deploy Traefik as part of this stack:
# deploy_traefik = true
```

### 2. traefik_router — document all sub-keys

```hcl
# traefik_router = {
#   enabled       = "true"
#   tls           = "true"
#   entrypoint    = "websecure"
#   cert_resolver = "letsencrypt"
#   middlewares   = "security-headers@file,rate-limit@file,compress@file"
# }
```

### 3. Memory tuning guidance (comment block)

```hcl
# Memory limits (MiB) — tune for your VPS size:
#
#   1 GB VPS  → postgres=256  redis=128  aggregator=256  api=128  frontend=64
#   2 GB VPS  → postgres=512  redis=256  aggregator=512  api=256  frontend=128  (defaults)
#   4 GB VPS  → postgres=512  redis=256  aggregator=512  api=256  frontend=128  (same, headroom)
#
# defcon_postgres_memory_limit    = 512
# defcon_redis_memory_limit       = 256
# defcon_aggregator_memory_limit  = 512
# defcon_api_gateway_memory_limit = 256
# defcon_frontend_memory_limit    = 128
```

## Screenshots

A `docs/screenshots/` directory is created (with a `.gitkeep` so it's tracked). The README gets
a placeholder section directly after the intro paragraph:

```markdown
## Screenshots

![DEFCON Dashboard](docs/screenshots/dashboard.png)
![DEFCON Gauge](docs/screenshots/defcon-gauge.png)
```

Two placeholders: `dashboard.png` (full dashboard view) and `defcon-gauge.png` (gauge close-up).
The user drops screenshots into `docs/screenshots/` and the links work immediately.

## Out of scope

- No changes to tofu modules
- No remote state backend configuration (documented as optional in README only)
- No docker-compose.override.yml (removed from README, not created)
- No changes to service Dockerfiles or source code
