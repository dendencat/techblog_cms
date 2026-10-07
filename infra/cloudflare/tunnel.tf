# オリジンは受信ポートを一切開けず、cloudflared からの外向き接続だけで公開する。
resource "cloudflare_zero_trust_tunnel_cloudflared" "techblog" {
  account_id = var.account_id
  name       = var.tunnel_name
  config_src = "cloudflare"
}

locals {
  # Access で保護する管理系パス。access.tf の destinations と揃えること。
  protected_path_regex = "^/(login|logout|dashboard|api|admin)(/|$)"
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "techblog" {
  account_id = var.account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.techblog.id

  config = {
    ingress = [
      {
        # 管理系パスはエッジの Access に加え、cloudflared でも Access JWT を検証する(多層防御)。
        hostname = var.hostname
        path     = local.protected_path_regex
        service  = var.origin_service
        origin_request = {
          access = {
            required  = true
            team_name = var.access_team_name
            aud_tag   = [cloudflare_zero_trust_access_application.admin.aud]
          }
        }
      },
      {
        hostname = var.hostname
        service  = var.origin_service
      },
      {
        # どのルールにも一致しないリクエストは 404
        service = "http_status:404"
      },
    ]
  }
}

data "cloudflare_zero_trust_tunnel_cloudflared_token" "techblog" {
  account_id = var.account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.techblog.id
}

resource "cloudflare_dns_record" "blog" {
  zone_id = var.zone_id
  name    = var.hostname
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.techblog.id}.cfargotunnel.com"
  proxied = true
  ttl     = 1
  comment = "techblog_cms (Cloudflare Tunnel, managed by Terraform)"
}
