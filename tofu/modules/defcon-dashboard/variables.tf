# =============================================================================
# Defcon Dashboard module variables
# =============================================================================
#
# REQUIRED  — must be supplied by the caller
# CONFIG    — app behaviour with sensible defaults
# INFRA     — deployment / networking settings
# RESOURCES — per-container memory and CPU limits
#
# =============================================================================

# =============================================================================
# REQUIRED
# =============================================================================

variable "domain" {
  description = "Public domain for the dashboard (e.g. defcon.example.com)"
  type        = string
}

variable "admin_password" {
  description = "Password shown on the login screen"
  type        = string
  sensitive   = true
}

variable "traefik_network" {
  description = "Name of the shared Traefik Docker network"
  type        = string
}

# =============================================================================
# CONFIG
# =============================================================================

variable "fetch_interval_minutes" {
  description = "How often the aggregator fetches articles (minutes)"
  type        = number
  default     = 60
}

variable "log_level" {
  description = "Python log level for the news aggregator"
  type        = string
  default     = "INFO"
}

variable "redis_maxmemory" {
  description = "Redis maxmemory limit"
  type        = string
  default     = "128mb"
}

variable "redis_maxmemory_policy" {
  description = "Redis maxmemory eviction policy"
  type        = string
  default     = "allkeys-lru"
}

variable "postgres_image" {
  description = "PostgreSQL Docker image"
  type        = string
  default     = "postgres:16-alpine"
}

variable "redis_image" {
  description = "Redis Docker image"
  type        = string
  default     = "redis:7-alpine"
}

# =============================================================================
# INFRA
# =============================================================================

variable "name_prefix" {
  description = "Prefix used in all container, volume and network names"
  type        = string
  default     = "defcon"
}

variable "base_app_dir" {
  description = "Root directory on the host for application data"
  type        = string
  default     = "/opt"
}

variable "remote_host" {
  description = "SSH target for provisioners, format: user@host (empty = local)"
  type        = string
  default     = ""
}

variable "restart_policy" {
  description = "Docker restart policy for all containers"
  type        = string
  default     = "unless-stopped"
}

variable "security_opts" {
  description = "Docker security options for all containers"
  type        = list(string)
  default     = ["no-new-privileges:true"]
}

variable "traefik_enabled" {
  description = "Traefik label: enable routing for the frontend container"
  type        = string
  default     = "true"
}

variable "traefik_tls" {
  description = "Traefik label: enable TLS"
  type        = string
  default     = "true"
}

variable "traefik_entrypoint" {
  description = "Traefik label: entrypoint name"
  type        = string
  default     = "websecure"
}

variable "traefik_cert_resolver" {
  description = "Traefik label: certificate resolver name"
  type        = string
  default     = "letsencrypt"
}

variable "traefik_middlewares" {
  description = "Traefik label: comma-separated middleware chain"
  type        = string
  default     = "security-headers@file,rate-limit@file,compress@file"
}

# =============================================================================
# RESOURCES
# =============================================================================

variable "postgres_memory_limit" {
  description = "Memory limit for PostgreSQL in MiB"
  type        = number
  default     = 512
}

variable "postgres_cpu_shares" {
  description = "CPU shares for PostgreSQL"
  type        = number
  default     = 512
}

variable "redis_memory_limit" {
  description = "Memory limit for Redis in MiB"
  type        = number
  default     = 256
}

variable "redis_cpu_shares" {
  description = "CPU shares for Redis"
  type        = number
  default     = 256
}

variable "aggregator_memory_limit" {
  description = "Memory limit for the news aggregator in MiB"
  type        = number
  default     = 512
}

variable "aggregator_cpu_shares" {
  description = "CPU shares for the news aggregator"
  type        = number
  default     = 512
}

variable "api_gateway_memory_limit" {
  description = "Memory limit for the API gateway in MiB"
  type        = number
  default     = 256
}

variable "api_gateway_cpu_shares" {
  description = "CPU shares for the API gateway"
  type        = number
  default     = 512
}

variable "frontend_memory_limit" {
  description = "Memory limit for the frontend in MiB"
  type        = number
  default     = 128
}

variable "frontend_cpu_shares" {
  description = "CPU shares for the frontend"
  type        = number
  default     = 256
}
