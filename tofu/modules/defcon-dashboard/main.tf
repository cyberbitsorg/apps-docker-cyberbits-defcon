# =============================================================================
# Defcon Dashboard module main
# =============================================================================

# =============================================================================
# Secrets (auto-generated)
# =============================================================================

resource "random_password" "postgres" {
  length  = 32
  special = false
}

resource "random_password" "auth_secret" {
  length  = 64
  special = false
}

# =============================================================================
# Configuration Files
# =============================================================================

resource "null_resource" "deploy_config" {
  triggers = {
    content_hash = sha256(join("|", [local.env_content, local.init_sql_content]))
  }

  provisioner "local-exec" {
    command = local.is_remote ? local.remote_cmd : local.local_cmd
  }
}

# =============================================================================
# Networks
# =============================================================================

resource "docker_network" "internal" {
  name     = "${var.name_prefix}-internal"
  driver   = "bridge"
  internal = true
}

# =============================================================================
# Volumes
# =============================================================================

resource "docker_volume" "postgres_data" {
  name = "${var.name_prefix}-postgres-data"
}

resource "docker_volume" "redis_data" {
  name = "${var.name_prefix}-redis-data"
}

# =============================================================================
# Images (built on the remote Docker host from local source)
# =============================================================================

resource "docker_image" "news_aggregator" {
  name = "${var.name_prefix}-news-aggregator:latest"

  build {
    context    = "${local.services_root}/news-aggregator"
    dockerfile = "Dockerfile"
  }

  triggers = {
    src_hash = local.news_aggregator_hash
  }
}

resource "docker_image" "api_gateway" {
  name = "${var.name_prefix}-api-gateway:latest"

  build {
    context    = "${local.services_root}/api-gateway"
    dockerfile = "Dockerfile"
  }

  triggers = {
    src_hash = local.api_gateway_hash
  }
}

resource "docker_image" "frontend" {
  name = "${var.name_prefix}-frontend:latest"

  build {
    context    = "${local.services_root}/frontend"
    dockerfile = "Dockerfile"
    build_args = {
      # Empty string → nginx proxies /api/ internally; no origin baked in
      VITE_API_BASE_URL = ""
    }
  }

  triggers = {
    src_hash = local.frontend_hash
  }
}

# =============================================================================
# PostgreSQL
# =============================================================================

resource "docker_container" "postgres" {
  name          = "${var.name_prefix}-postgres"
  image         = var.postgres_image
  restart       = var.restart_policy
  memory        = var.postgres_memory_limit
  memory_swap   = var.postgres_memory_limit
  cpu_shares    = var.postgres_cpu_shares
  security_opts = var.security_opts

  env = [
    "POSTGRES_DB=defcon_db",
    "POSTGRES_USER=defcon",
    "POSTGRES_PASSWORD=${random_password.postgres.result}",
  ]

  mounts {
    target = "/var/lib/postgresql/data"
    source = docker_volume.postgres_data.name
    type   = "volume"
  }

  mounts {
    target    = "/docker-entrypoint-initdb.d/init.sql"
    source    = "${local.app_dir}/db/init.sql"
    type      = "bind"
    read_only = true
  }

  networks_advanced {
    name    = docker_network.internal.name
    aliases = ["postgres"]
  }

  healthcheck {
    test         = ["CMD-SHELL", "pg_isready -U defcon -d defcon_db"]
    interval     = "10s"
    timeout      = "5s"
    retries      = 5
    start_period = "10s"
  }

  lifecycle {
    ignore_changes = [log_driver, log_opts]
  }

  depends_on = [null_resource.deploy_config]
}

# =============================================================================
# Redis
# =============================================================================

resource "docker_container" "redis" {
  name          = "${var.name_prefix}-redis"
  image         = var.redis_image
  restart       = var.restart_policy
  memory        = var.redis_memory_limit
  memory_swap   = var.redis_memory_limit
  cpu_shares    = var.redis_cpu_shares
  security_opts = var.security_opts

  command = [
    "redis-server",
    "--appendonly", "yes",
    "--maxmemory", var.redis_maxmemory,
    "--maxmemory-policy", var.redis_maxmemory_policy,
  ]

  mounts {
    target = "/data"
    source = docker_volume.redis_data.name
    type   = "volume"
  }

  networks_advanced {
    name    = docker_network.internal.name
    aliases = ["redis"]
  }

  healthcheck {
    test         = ["CMD", "redis-cli", "ping"]
    interval     = "10s"
    timeout      = "3s"
    retries      = 5
    start_period = "5s"
  }

  lifecycle {
    ignore_changes = [log_driver, log_opts]
  }
}

# =============================================================================
# News Aggregator
# =============================================================================

resource "docker_container" "news_aggregator" {
  name          = "${var.name_prefix}-news-aggregator"
  image         = docker_image.news_aggregator.name
  restart       = var.restart_policy
  memory        = var.aggregator_memory_limit
  memory_swap   = var.aggregator_memory_limit
  cpu_shares    = var.aggregator_cpu_shares
  security_opts = var.security_opts

  env = [
    "DATABASE_URL=postgresql://defcon:${random_password.postgres.result}@postgres:5432/defcon_db",
    "REDIS_URL=redis://redis:6379",
    "API_GATEWAY_URL=http://api-gateway:4000",
    "FETCH_INTERVAL_MINUTES=${var.fetch_interval_minutes}",
    "LOG_LEVEL=${var.log_level}",
  ]

  networks_advanced {
    name    = docker_network.internal.name
    aliases = ["news-aggregator"]
  }

  # Needs internet access to fetch RSS feeds from external sources
  networks_advanced {
    name    = var.traefik_network
    aliases = ["news-aggregator"]
  }

  healthcheck {
    test         = ["CMD-SHELL", "python3 -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')\""]
    interval     = "30s"
    timeout      = "10s"
    retries      = 3
    start_period = "30s"
  }

  lifecycle {
    ignore_changes       = [log_driver, log_opts]
    replace_triggered_by = [docker_image.news_aggregator.image_id]
  }

  depends_on = [docker_container.postgres, docker_container.redis]
}

# =============================================================================
# API Gateway
# =============================================================================

resource "docker_container" "api_gateway" {
  name          = "${var.name_prefix}-api-gateway"
  image         = docker_image.api_gateway.name
  restart       = var.restart_policy
  memory        = var.api_gateway_memory_limit
  memory_swap   = var.api_gateway_memory_limit
  cpu_shares    = var.api_gateway_cpu_shares
  security_opts = var.security_opts

  env = [
    "DATABASE_URL=postgresql://defcon:${random_password.postgres.result}@postgres:5432/defcon_db",
    "REDIS_URL=redis://redis:6379",
    "AGGREGATOR_URL=http://news-aggregator:8000",
    "PORT=4000",
    "NODE_ENV=production",
    "CORS_ORIGIN=https://${var.domain}",
    "AUTH_SECRET=${random_password.auth_secret.result}",
    "ADMIN_PASSWORD=${var.admin_password}",
  ]

  # Internal network — reachable by news-aggregator and for DB/Redis access
  networks_advanced {
    name    = docker_network.internal.name
    aliases = ["api-gateway"]
  }

  # Traefik network — reachable by the frontend nginx proxy (http://api-gateway:4000)
  # No Traefik label here; nginx handles external routing internally
  networks_advanced {
    name    = var.traefik_network
    aliases = ["api-gateway"]
  }

  healthcheck {
    test         = ["CMD-SHELL", "wget -qO- http://127.0.0.1:4000/api/v1/health || exit 1"]
    interval     = "30s"
    timeout      = "5s"
    retries      = 3
    start_period = "15s"
  }

  lifecycle {
    ignore_changes       = [log_driver, log_opts]
    replace_triggered_by = [docker_image.api_gateway.image_id]
  }

  depends_on = [docker_container.postgres, docker_container.redis]
}

# =============================================================================
# Frontend (Nginx)
# =============================================================================

resource "docker_container" "frontend" {
  name          = "${var.name_prefix}-frontend"
  image         = docker_image.frontend.name
  restart       = var.restart_policy
  memory        = var.frontend_memory_limit
  memory_swap   = var.frontend_memory_limit
  cpu_shares    = var.frontend_cpu_shares
  security_opts = var.security_opts

  # Traefik routing labels
  labels {
    label = "traefik.enable"
    value = var.traefik_enabled
  }
  labels {
    label = "traefik.http.routers.${local.router_name}.rule"
    value = "Host(`${var.domain}`)"
  }
  labels {
    label = "traefik.http.routers.${local.router_name}.entrypoints"
    value = var.traefik_entrypoint
  }
  labels {
    label = "traefik.http.routers.${local.router_name}.tls"
    value = var.traefik_tls
  }
  labels {
    label = "traefik.http.routers.${local.router_name}.tls.certresolver"
    value = var.traefik_cert_resolver
  }
  labels {
    label = "traefik.http.routers.${local.router_name}.middlewares"
    value = var.traefik_middlewares
  }
  labels {
    label = "traefik.http.services.${local.router_name}.loadbalancer.server.port"
    value = "80"
  }

  networks_advanced {
    name = var.traefik_network
  }

  healthcheck {
    test         = ["CMD-SHELL", "wget -qO /dev/null http://127.0.0.1/ || exit 1"]
    interval     = "30s"
    timeout      = "5s"
    retries      = 3
    start_period = "10s"
  }

  lifecycle {
    ignore_changes       = [log_driver, log_opts]
    replace_triggered_by = [docker_image.frontend.image_id]
  }

  depends_on = [docker_container.api_gateway]
}
