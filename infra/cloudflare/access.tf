# 管理画面は Cloudflare Access(Zero Trust)の後ろに置き、許可したメールアドレスだけが
# Django のログイン画面に到達できるようにする。公開記事のパスは対象外。
resource "cloudflare_zero_trust_access_policy" "admins" {
  account_id = var.account_id
  name       = "techblog-cms admins"
  decision   = "allow"

  include = [
    for email in var.access_allowed_emails : {
      email = { email = email }
    }
  ]
}

resource "cloudflare_zero_trust_access_application" "admin" {
  account_id       = var.account_id
  name             = "techblog-cms admin"
  type             = "self_hosted"
  session_duration = var.access_session_duration

  destinations = [
    for p in ["login", "logout", "dashboard", "api", "admin"] : {
      type = "public"
      uri  = "${var.hostname}/${p}"
    }
  ]

  http_only_cookie_attribute = true
  same_site_cookie_attribute = "lax"
  auto_redirect_to_identity  = false

  policies = [
    {
      id         = cloudflare_zero_trust_access_policy.admins.id
      precedence = 1
    },
  ]
}
