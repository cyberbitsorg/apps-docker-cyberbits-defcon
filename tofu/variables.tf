# =============================================================================
# Variables
# =============================================================================
#
# WHERE TO SET THINGS:
#   Required values  → terraform.tfvars
#   Global tuning    → here (defaults are production-ready)
#   Module internals → the relevant module's variables.tf
#
# =============================================================================

# =============================================================================
# CONNECTION
# =============================================================================
# docker_host  → Docker provider (container management, image builds)
# remote_host  → SSH provisioner (config file uploads via SSH)
# Both must reference the same server for remote deployments.

variable "docker_host" {
  description = "Docker daemon connection string (e.g. ssh://user@host or unix:///var/run/docker.sock)"
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "remote_host" {
  description = "SSH target for provisioners, format: user@host (leave empty for local deployment)"
  type        = string
  default     = ""
}

# =============================================================================
# GLOBAL SETTINGS
# =============================================================================

variable "admin_email" {
  description = "Email for Let's Encrypt certificate notifications"
  type        = string
}

variable "base_app_dir" {
  description = "Root directory on the host for all application data"
  type        = string
  default     = "/opt"
}

variable "restart_policy" {
  description = "Docker restart policy applied to all containers"
  type        = string
  default     = "unless-stopped"
  validation {
    condition     = contains(["unless-stopped", "always", "on-failure", "no"], var.restart_policy)
    error_message = "restart_policy must be one of: no, always, on-failure, unless-stopped."
  }
}

variable "security_opts" {
  description = "Docker security options applied to all containers"
  type        = list(string)
  default     = ["no-new-privileges:true"]
}

# =============================================================================
# TRAEFIK GATEWAY
# =============================================================================

variable "deploy_traefik" {
  description = "Set to false when Traefik is already running on this server (e.g. deployed by another OpenTofu stack). The traefik_network must already exist."
  type        = bool
  default     = true
}

variable "traefik_network" {
  description = "Name of the shared Docker bridge network Traefik and app containers join"
  type        = string
  default     = "traefik"
}

variable "traefik_version" {
  description = "Traefik Docker image tag"
  type        = string
  default     = "v3.6"
}

variable "traefik_config_dir" {
  description = "Directory on the host that holds traefik.yml and the config/ subdirectory"
  type        = string
  default     = "/opt/traefik"
}

variable "traefik_container_name" {
  description = "Docker container name for the Traefik gateway"
  type        = string
  default     = "gw-traefik"
}

variable "traefik_ssl_volume_name" {
  description = "Docker volume name for Let's Encrypt certificate storage"
  type        = string
  default     = "gw-traefik-ssl"
}

variable "traefik_dashboard_enabled" {
  description = "Enable the Traefik dashboard (disable in production)"
  type        = bool
  default     = false
}

variable "traefik_memory_limit" {
  description = "Memory limit for the Traefik container in MiB"
  type        = number
  default     = 128
}

variable "traefik_cpu_shares" {
  description = "CPU shares for the Traefik container"
  type        = number
  default     = 512
}

variable "traefik_docker_socket" {
  description = "Path to the Docker socket on the host (mounted read-only into Traefik)"
  type        = string
  default     = "/var/run/docker.sock"
}

variable "traefik_docker_api_version" {
  description = "Docker API version negotiated between Traefik and the daemon"
  type        = string
  default     = "1.45"
}

# =============================================================================
# TRAEFIK ROUTING
# =============================================================================

variable "traefik_router" {
  description = "Traefik routing settings applied to the dashboard container"
  type = object({
    enabled       = optional(string, "true")
    tls           = optional(string, "true")
    entrypoint    = optional(string, "websecure")
    cert_resolver = optional(string, "letsencrypt")
    middlewares   = optional(string, "security-headers@file,rate-limit@file,compress@file")
  })
  default = {}
}

# =============================================================================
# DEFCON DASHBOARD
# =============================================================================

variable "defcon_domain" {
  description = "Public domain for the Defcon Dashboard (e.g. defcon.example.com)"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]*\\.[a-z]{2,}$", var.defcon_domain))
    error_message = "defcon_domain must be a valid fully-qualified domain name."
  }
}

variable "defcon_admin_password" {
  description = "Password for the dashboard login screen"
  type        = string
  sensitive   = true
}

variable "defcon_name_prefix" {
  description = "Short prefix used in container, volume and network names"
  type        = string
  default     = "defcon"
}

variable "defcon_fetch_interval_minutes" {
  description = "How often the news aggregator fetches new articles"
  type        = number
  default     = 60
}

variable "defcon_log_level" {
  description = "Python log level for the news aggregator"
  type        = string
  default     = "INFO"
}

variable "defcon_redis_maxmemory" {
  description = "Redis maxmemory limit"
  type        = string
  default     = "128mb"
}

variable "defcon_redis_maxmemory_policy" {
  description = "Redis maxmemory eviction policy"
  type        = string
  default     = "allkeys-lru"
}

variable "defcon_postgres_memory_limit" {
  description = "Memory limit for the PostgreSQL container in MiB"
  type        = number
  default     = 512
}

variable "defcon_postgres_cpu_shares" {
  description = "CPU shares for the PostgreSQL container"
  type        = number
  default     = 512
}

variable "defcon_redis_memory_limit" {
  description = "Memory limit for the Redis container in MiB"
  type        = number
  default     = 256
}

variable "defcon_redis_cpu_shares" {
  description = "CPU shares for the Redis container"
  type        = number
  default     = 256
}

variable "defcon_aggregator_memory_limit" {
  description = "Memory limit for the news aggregator container in MiB"
  type        = number
  default     = 512
}

variable "defcon_aggregator_cpu_shares" {
  description = "CPU shares for the news aggregator container"
  type        = number
  default     = 512
}

variable "defcon_api_gateway_memory_limit" {
  description = "Memory limit for the API gateway container in MiB"
  type        = number
  default     = 256
}

variable "defcon_api_gateway_cpu_shares" {
  description = "CPU shares for the API gateway container"
  type        = number
  default     = 512
}

variable "defcon_frontend_memory_limit" {
  description = "Memory limit for the frontend container in MiB"
  type        = number
  default     = 128
}

variable "defcon_frontend_cpu_shares" {
  description = "CPU shares for the frontend container"
  type        = number
  default     = 256
}
