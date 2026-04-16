# =============================================================================
# Traefik module locals
# =============================================================================

locals {
  is_remote     = var.remote_host != ""
  traefik_image = "traefik:${var.traefik_version}"

  # Mount and port type constants
  mount_bind   = "bind"
  mount_volume = "volume"
  protocol_tcp = "tcp"

  # Computed source paths
  config_file_source = "${var.traefik_config_dir}/traefik.yml"
  config_dir_source  = "${var.traefik_config_dir}/config"

  # Environment variables
  env = ["DOCKER_API_VERSION=${var.docker_api_version}"]

  traefik_yml_content = templatefile("${path.module}/templates/traefik.yml.tftpl", {
    traefik_dashboard_enabled = var.traefik_dashboard_enabled
    traefik_letsencrypt_email = var.traefik_letsencrypt_email
    traefik_network           = var.traefik_network
  })
  dynamic_yml_content = templatefile("${path.module}/templates/dynamic.yml.tftpl", {})

  remote_cmd = <<-EOT
    ssh ${var.remote_host} 'mkdir -p ${var.traefik_config_dir}/config'
    printf '%s' '${base64encode(local.traefik_yml_content)}' | ssh ${var.remote_host} 'base64 -d > ${var.traefik_config_dir}/traefik.yml'
    printf '%s' '${base64encode(local.dynamic_yml_content)}' | ssh ${var.remote_host} 'base64 -d > ${var.traefik_config_dir}/config/dynamic.yml'
  EOT
  local_cmd  = <<-EOT
    mkdir -p ${var.traefik_config_dir}/config
    printf '%s' '${base64encode(local.traefik_yml_content)}' | base64 -d > ${var.traefik_config_dir}/traefik.yml
    printf '%s' '${base64encode(local.dynamic_yml_content)}' | base64 -d > ${var.traefik_config_dir}/config/dynamic.yml
  EOT
}
