output "tunnel_id" {
  value = cloudflare_zero_trust_tunnel_cloudflared.techblog.id
}

output "tunnel_token" {
  description = "オリジンの .env に CLOUDFLARE_TUNNEL_TOKEN として設定する値(`terraform output -raw tunnel_token`)"
  value       = data.cloudflare_zero_trust_tunnel_cloudflared_token.techblog.token
  sensitive   = true
}

output "access_aud" {
  description = "管理画面用 Access アプリケーションの AUD タグ"
  value       = cloudflare_zero_trust_access_application.admin.aud
}
