# =============================================================================
# Traefik module main
# =============================================================================

# =============================================================================
# Configuration Files
# =============================================================================

resource "null_resource" "deploy_config" {
  triggers = {
    content_hash = sha256(join("|", [local.traefik_yml_content, local.dynamic_yml_content]))
  }

  provisioner "local-exec" {
    command = local.is_remote ? local.remote_cmd : local.local_cmd
  }
}

# =============================================================================
# Docker volume for Let's Encrypt certificates
# =============================================================================

resource "docker_volume" "traefik_ssl" {
  name = var.ssl_volume_name
}

# =============================================================================
# Traefik container
# =============================================================================

resource "docker_container" "traefik" {
  name  = var.container_name
  image = local.traefik_image

  restart = var.restart_policy

  memory      = var.memory_limit
  memory_swap = var.memory_limit
  cpu_shares  = var.cpu_shares

  security_opts = var.security_opts

  ports {
    internal = var.http_port
    external = var.http_port
    protocol = local.protocol_tcp
  }

  ports {
    internal = var.https_port
    external = var.https_port
    protocol = local.protocol_tcp
  }

  env = local.env

  mounts {
    target    = var.docker_sock_target
    source    = var.docker_socket
    type      = local.mount_bind
    read_only = true
  }

  mounts {
    target    = var.config_file_target
    source    = local.config_file_source
    type      = local.mount_bind
    read_only = true
  }

  mounts {
    target    = var.config_dir_target
    source    = local.config_dir_source
    type      = local.mount_bind
    read_only = true
  }

  mounts {
    target = var.letsencrypt_target
    source = docker_volume.traefik_ssl.name
    type   = local.mount_volume
  }

  networks_advanced {
    name = var.traefik_network
  }

  healthcheck {
    test         = var.healthcheck_test
    interval     = var.healthcheck_interval
    timeout      = var.healthcheck_timeout
    retries      = var.healthcheck_retries
    start_period = var.healthcheck_start_period
  }

  lifecycle {
    ignore_changes = [log_driver, log_opts]
  }

  depends_on = [
    null_resource.deploy_config,
    docker_volume.traefik_ssl
  ]
}
