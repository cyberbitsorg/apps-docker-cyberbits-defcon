# =============================================================================
# Cybersecurity Defcon Dashboard — OpenTofu Root Module
# =============================================================================
#
# BEFORE FIRST RUN
#   1. Copy terraform.tfvars.example → terraform.tfvars and fill in values.
#   2. Ensure the DNS A record for defcon_domain points to your server.
#      Let's Encrypt validates DNS; repeated failures trigger a temporary ban.
#   3. Run: tofu init && tofu plan && tofu apply
#
# =============================================================================

# =============================================================================
# Traefik Network (shared by Traefik + dashboard containers)
# =============================================================================

resource "docker_network" "traefik" {
  count  = var.deploy_traefik ? 1 : 0
  name   = var.traefik_network
  driver = "bridge"

  lifecycle {
    prevent_destroy = false
  }
}

# =============================================================================
# Traefik Reverse Proxy
# =============================================================================

module "traefik" {
  count  = var.deploy_traefik ? 1 : 0
  source = "./modules/traefik"

  remote_host               = var.remote_host
  traefik_version           = var.traefik_version
  traefik_network           = var.traefik_network
  traefik_config_dir        = var.traefik_config_dir
  traefik_letsencrypt_email = var.admin_email
  traefik_dashboard_enabled = var.traefik_dashboard_enabled
  container_name            = var.traefik_container_name
  ssl_volume_name           = var.traefik_ssl_volume_name
  docker_socket             = var.traefik_docker_socket
  docker_api_version        = var.traefik_docker_api_version
  restart_policy            = var.restart_policy
  security_opts             = var.security_opts
  memory_limit              = var.traefik_memory_limit
  cpu_shares                = var.traefik_cpu_shares
}

# =============================================================================
# Defcon Dashboard
# =============================================================================

module "defcon" {
  source = "./modules/defcon-dashboard"

  domain         = var.defcon_domain
  admin_password = var.defcon_admin_password
  name_prefix    = var.defcon_name_prefix

  base_app_dir   = var.base_app_dir
  remote_host    = var.remote_host
  restart_policy = var.restart_policy
  security_opts  = var.security_opts

  traefik_network       = var.traefik_network
  traefik_enabled       = var.traefik_router.enabled
  traefik_tls           = var.traefik_router.tls
  traefik_entrypoint    = var.traefik_router.entrypoint
  traefik_cert_resolver = var.traefik_router.cert_resolver
  traefik_middlewares   = var.traefik_router.middlewares

  fetch_interval_minutes = var.defcon_fetch_interval_minutes
  log_level              = var.defcon_log_level
  redis_maxmemory        = var.defcon_redis_maxmemory
  redis_maxmemory_policy = var.defcon_redis_maxmemory_policy

  postgres_memory_limit    = var.defcon_postgres_memory_limit
  postgres_cpu_shares      = var.defcon_postgres_cpu_shares
  redis_memory_limit       = var.defcon_redis_memory_limit
  redis_cpu_shares         = var.defcon_redis_cpu_shares
  aggregator_memory_limit  = var.defcon_aggregator_memory_limit
  aggregator_cpu_shares    = var.defcon_aggregator_cpu_shares
  api_gateway_memory_limit = var.defcon_api_gateway_memory_limit
  api_gateway_cpu_shares   = var.defcon_api_gateway_cpu_shares
  frontend_memory_limit    = var.defcon_frontend_memory_limit
  frontend_cpu_shares      = var.defcon_frontend_cpu_shares

  depends_on = [module.traefik, docker_network.traefik]
}
