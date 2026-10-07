variable "account_id" {
  description = "Cloudflare アカウント ID"
  type        = string
}

variable "zone_id" {
  description = "iohub.link ゾーンの Zone ID"
  type        = string
}

variable "hostname" {
  description = "ブログの公開ホスト名"
  type        = string
  default     = "blog.iohub.link"
}

variable "tunnel_name" {
  description = "Cloudflare Tunnel の名前"
  type        = string
  default     = "techblog-cms"
}

variable "origin_service" {
  description = "cloudflared から見たオリジン(docker compose 内の nginx)"
  type        = string
  default     = "http://nginx:80"
}

variable "access_team_name" {
  description = "Zero Trust のチーム名(<team>.cloudflareaccess.com の <team> 部分)"
  type        = string
}

variable "access_allowed_emails" {
  description = "管理画面(/login, /dashboard など)へのアクセスを許可するメールアドレス"
  type        = list(string)

  validation {
    condition     = length(var.access_allowed_emails) > 0
    error_message = "少なくとも 1 件のメールアドレスを指定してください。"
  }
}

variable "access_session_duration" {
  description = "Access セッションの有効期間"
  type        = string
  default     = "12h"
}

variable "manage_zone_settings" {
  description = "ゾーン全体の TLS/HTTPS 設定を Terraform で管理するか。iohub.link の他サブドメインにも影響する"
  type        = bool
  default     = true
}

variable "login_rate_limit_requests" {
  description = "ログイン POST の 10 秒あたり許容回数(IP + コロ単位)"
  type        = number
  default     = 5
}
