# =============================================================================
# Outputs
# =============================================================================

output "dashboard_url" {
  description = "URL of the Defcon Dashboard"
  value       = "https://${var.defcon_domain}"
}

output "get_credentials" {
  description = "How to retrieve the auto-generated secrets after first apply"
  value       = <<-EOT

    DEFCON DASHBOARD CREDENTIALS
    =============================

    Dashboard URL  : https://${var.defcon_domain}
    Admin password : set in terraform.tfvars as defcon_admin_password

    Retrieve the auto-generated secrets (postgres password, JWT signing key):

      tofu output -json defcon_secrets | jq

  EOT
}

output "defcon_secrets" {
  description = "Auto-generated secrets for the dashboard stack"
  value       = module.defcon.secrets
  sensitive   = true
}
