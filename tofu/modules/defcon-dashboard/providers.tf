# =============================================================================
# Defcon Dashboard module providers
# =============================================================================

terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
    random = {
      source = "hashicorp/random"
    }
    null = {
      source = "hashicorp/null"
    }
  }
}
