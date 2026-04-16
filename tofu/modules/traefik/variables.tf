# =============================================================================
# Traefik module variables
# =============================================================================
#
# REQUIRED  — must be supplied by the caller (no default)
# CONFIG    — gateway configuration with sensible defaults
# INFRA     — deployment settings (restart, security, ports, socket)
# ADVANCED  — internal container paths and healthcheck config
#             Change only if your setup is non-standard
#
# =============================================================================

# =============================================================================
# REQUIRED
# =============================================================================

variable "traefik_network" {
  description = "Name of the Docker network Traefik and app containers share"
  type        = string
}

variable "traefik_letsencrypt_email" {
  description = "Email address for Let's Encrypt certificate notifications"
  type        = string
}

# =============================================================================
# CONFIG
# =============================================================================

variable "traefik_version" {
  description = "Traefik Docker image tag"
  type        = string
  default     = "v3.6"
}

variable "traefik_config_dir" {
  description = "Directory on the host holding traefik.yml and config/ subdirectory"
  type        = string
  default     = "/opt/traefik"
}

variable "traefik_dashboard_enabled" {
  description = "Enable the Traefik dashboard (disable in production)"
  type        = bool
  default     = false
}

variable "container_name" {
  description = "Docker container name for the Traefik gateway"
  type        = string
  default     = "gw-traefik"
}

variable "ssl_volume_name" {
  description = "Docker volume name for Let's Encrypt certificate storage"
  type        = string
  default     = "gw-traefik-ssl"
}

variable "memory_limit" {
  description = "Memory limit for the Traefik container in MiB (0 = unlimited)"
  type        = number
  default     = 128
}

variable "cpu_shares" {
  description = "CPU shares for the Traefik container (relative weight; 1024 ≈ 1 CPU under contention)"
  type        = number
  default     = 512
}

# =============================================================================
# INFRA
# =============================================================================

variable "remote_host" {
  description = "SSH target for provisioners, format: user@host (empty = local)"
  type        = string
  default     = ""
}

variable "http_port" {
  description = "Host port bound for HTTP traffic (port 80 redirect)"
  type        = number
  default     = 80
  validation {
    condition     = var.http_port >= 1 && var.http_port <= 65535
    error_message = "http_port must be between 1 and 65535."
  }
}

variable "https_port" {
  description = "Host port bound for HTTPS traffic"
  type        = number
  default     = 443
  validation {
    condition     = var.https_port >= 1 && var.https_port <= 65535
    error_message = "https_port must be between 1 and 65535."
  }
}

variable "docker_socket" {
  description = "Path to the Docker socket on the host (mounted read-only into Traefik)"
  type        = string
  default     = "/var/run/docker.sock"
}

variable "docker_api_version" {
  description = "Docker API version negotiated between Traefik and the daemon"
  type        = string
  default     = "1.45"
}

variable "restart_policy" {
  description = "Docker restart policy for the Traefik container"
  type        = string
  default     = "unless-stopped"
  validation {
    condition     = contains(["unless-stopped", "always", "on-failure", "no"], var.restart_policy)
    error_message = "restart_policy must be one of: no, always, on-failure, unless-stopped."
  }
}

variable "security_opts" {
  description = "Docker security options for the Traefik container"
  type        = list(string)
  default     = ["no-new-privileges:true"]
}

# =============================================================================
# ADVANCED
# =============================================================================

variable "docker_sock_target" {
  description = "Docker socket path inside the Traefik container"
  type        = string
  default     = "/var/run/docker.sock"
}

variable "config_file_target" {
  description = "Path to traefik.yml inside the Traefik container"
  type        = string
  default     = "/etc/traefik/traefik.yml"
}

variable "config_dir_target" {
  description = "Path to the dynamic config directory inside the Traefik container"
  type        = string
  default     = "/etc/traefik/config"
}

variable "letsencrypt_target" {
  description = "Path to the Let's Encrypt directory inside the Traefik container"
  type        = string
  default     = "/letsencrypt"
}

variable "healthcheck_test" {
  description = "Healthcheck test command for the Traefik container"
  type        = list(string)
  default     = ["CMD", "traefik", "healthcheck", "--ping"]
}

variable "healthcheck_interval" {
  description = "Healthcheck interval"
  type        = string
  default     = "30s"
}

variable "healthcheck_timeout" {
  description = "Healthcheck timeout"
  type        = string
  default     = "5s"
}

variable "healthcheck_retries" {
  description = "Healthcheck retry count before marking the container unhealthy"
  type        = number
  default     = 3
}

variable "healthcheck_start_period" {
  description = "Healthcheck grace period before retries count"
  type        = string
  default     = "10s"
}
