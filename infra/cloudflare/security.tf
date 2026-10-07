# ── ゾーン設定(iohub.link 全体に効く。manage_zone_settings = false で無効化) ──
locals {
  zone_settings = var.manage_zone_settings ? {
    ssl                      = "strict"
    always_use_https         = "on"
    min_tls_version          = "1.2"
    tls_1_3                  = "on"
    automatic_https_rewrites = "on"
  } : {}
}

resource "cloudflare_zone_setting" "this" {
  for_each   = local.zone_settings
  zone_id    = var.zone_id
  setting_id = each.key
  value      = each.value
}

# ── WAF カスタムルール(Free プランで利用可) ──
# 注意: ゾーンの各フェーズのエントリポイント ruleset は 1 つだけ。ダッシュボードで
# 既にカスタムルールを作っている場合は import するか、先に削除してから apply する。
resource "cloudflare_ruleset" "custom_firewall" {
  zone_id     = var.zone_id
  name        = "techblog-cms custom rules"
  description = "techblog_cms 用の WAF カスタムルール"
  kind        = "zone"
  phase       = "http_request_firewall_custom"

  rules = [
    {
      description = "内部用の readiness エンドポイント(DB/キャッシュ状態)を外部に出さない"
      expression  = "(http.host eq \"${var.hostname}\" and http.request.uri.path eq \"/ready/\")"
      action      = "block"
    },
    {
      description = "ブログが受け付けない HTTP メソッドを遮断"
      expression  = "(http.host eq \"${var.hostname}\" and not http.request.method in {\"GET\" \"HEAD\" \"POST\" \"OPTIONS\"})"
      action      = "block"
    },
  ]
}

# ── レート制限(Free プランは 1 ルール、period/mitigation_timeout は 10 秒固定) ──
resource "cloudflare_ruleset" "rate_limit" {
  zone_id     = var.zone_id
  name        = "techblog-cms rate limit"
  description = "ログインへの総当たり対策"
  kind        = "zone"
  phase       = "http_ratelimit"

  rules = [
    {
      description = "ログイン POST の連打をブロック"
      expression  = "(http.host eq \"${var.hostname}\" and http.request.uri.path eq \"/login/\" and http.request.method eq \"POST\")"
      action      = "block"
      ratelimit = {
        characteristics     = ["cf.colo.id", "ip.src"]
        period              = 10
        requests_per_period = var.login_rate_limit_requests
        mitigation_timeout  = 10
      }
    },
  ]
}

# ── キャッシュルール: 静的ファイルと画像はエッジでキャッシュ、HTML は既定どおりキャッシュしない ──
resource "cloudflare_ruleset" "cache" {
  zone_id     = var.zone_id
  name        = "techblog-cms cache rules"
  description = "静的ファイルとメディアのエッジキャッシュ"
  kind        = "zone"
  phase       = "http_request_cache_settings"

  rules = [
    {
      description = "/static/ と /media/ をキャッシュ"
      expression  = "(http.host eq \"${var.hostname}\" and (starts_with(http.request.uri.path, \"/static/\") or starts_with(http.request.uri.path, \"/media/\")))"
      action      = "set_cache_settings"
      action_parameters = {
        cache = true
        edge_ttl = {
          mode    = "override_origin"
          default = 2592000
        }
        browser_ttl = {
          mode = "respect_origin"
        }
      }
    },
  ]
}
