# ═══════════════════════════════════════════════════════════════
# HashiCorp Vault Configuration - Nexus Data Platform
# ═══════════════════════════════════════════════════════════════

ui = true

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

storage "file" {
  path = "/vault/data"
}

api_addr = "http://0.0.0.0:8200"
cluster_addr = "http://0.0.0.0:8201"

# Disable mlock for development
disable_mlock = true
