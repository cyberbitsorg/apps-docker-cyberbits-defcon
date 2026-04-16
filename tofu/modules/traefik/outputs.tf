# =============================================================================
# Traefik module outputs
# =============================================================================

output "container_name" {
  description = "Name of the Traefik container"
  value       = docker_container.traefik.name
}

output "container_id" {
  description = "ID of the Traefik container"
  value       = docker_container.traefik.id
}

output "config_dir" {
  description = "Path to Traefik configuration directory"
  value       = var.traefik_config_dir
}

output "ssl_volume_name" {
  description = "Name of the SSL certificates volume"
  value       = docker_volume.traefik_ssl.name
}
