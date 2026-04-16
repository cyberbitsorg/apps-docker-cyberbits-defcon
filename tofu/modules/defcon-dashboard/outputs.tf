# =============================================================================
# Defcon Dashboard module outputs
# =============================================================================

output "domain" {
  description = "Public domain of the dashboard"
  value       = var.domain
}

output "frontend_container" {
  description = "Name of the frontend container"
  value       = docker_container.frontend.name
}

output "api_gateway_container" {
  description = "Name of the API gateway container"
  value       = docker_container.api_gateway.name
}

output "secrets" {
  description = "Auto-generated secrets for the stack"
  sensitive   = true
  value = {
    postgres_password = random_password.postgres.result
    auth_secret       = random_password.auth_secret.result
  }
}
