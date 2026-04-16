# =============================================================================
# Traefik module providers
# =============================================================================

terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
    null = {
      source = "hashicorp/null"
    }
  }
}
