# =============================================================================
# Defcon Dashboard module locals
# =============================================================================

locals {
  is_remote     = var.remote_host != ""
  app_dir       = "${var.base_app_dir}/defcon-dashboard"
  router_name   = var.name_prefix
  services_root = "${path.module}/../../../services"

  # ==========================================================================
  # Config file content
  # ==========================================================================

  env_content = templatefile("${path.module}/templates/defcon.env.tftpl", {
    postgres_password = random_password.postgres.result
    auth_secret       = random_password.auth_secret.result
    admin_password    = var.admin_password
    domain            = var.domain
  })

  init_sql_content = file("${path.module}/../../../db/init.sql")

  # ==========================================================================
  # Config file deployment commands
  # ==========================================================================

  remote_cmd = <<-EOT
    ssh ${var.remote_host} 'mkdir -p ${local.app_dir}/db'
    printf '%s' '${base64encode(local.env_content)}' | ssh ${var.remote_host} 'base64 -d > ${local.app_dir}/.env && chmod 600 ${local.app_dir}/.env'
    printf '%s' '${base64encode(local.init_sql_content)}' | ssh ${var.remote_host} 'base64 -d > ${local.app_dir}/db/init.sql'
  EOT

  local_cmd = <<-EOT
    mkdir -p ${local.app_dir}/db
    printf '%s' '${base64encode(local.env_content)}' | base64 -d > ${local.app_dir}/.env && chmod 600 ${local.app_dir}/.env
    printf '%s' '${base64encode(local.init_sql_content)}' | base64 -d > ${local.app_dir}/db/init.sql
  EOT

  # ==========================================================================
  # Source file hashes — trigger image rebuilds on code changes
  # ==========================================================================

  news_aggregator_hash = sha1(join("", concat(
    [filesha1("${local.services_root}/news-aggregator/Dockerfile")],
    [filesha1("${local.services_root}/news-aggregator/requirements.txt")],
    [for f in fileset("${local.services_root}/news-aggregator", "**/*.py") :
    filesha1("${local.services_root}/news-aggregator/${f}")]
  )))

  api_gateway_hash = sha1(join("", concat(
    [filesha1("${local.services_root}/api-gateway/Dockerfile")],
    [filesha1("${local.services_root}/api-gateway/package.json")],
    [for f in fileset("${local.services_root}/api-gateway/src", "**") :
    filesha1("${local.services_root}/api-gateway/src/${f}")]
  )))

  frontend_hash = sha1(join("", concat(
    [filesha1("${local.services_root}/frontend/Dockerfile")],
    [filesha1("${local.services_root}/frontend/package.json")],
    [filesha1("${local.services_root}/frontend/nginx.conf")],
    [for f in fileset("${local.services_root}/frontend/src", "**") :
    filesha1("${local.services_root}/frontend/src/${f}")]
  )))
}
