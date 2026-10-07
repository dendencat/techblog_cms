terraform {
  required_version = ">= 1.10"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.27"
    }
  }

  # 既定は手元のローカル state(費用ゼロ・追加サービス不要)。Tunnel トークンが入るため
  # terraform.tfstate はコミットしない(.gitignore 済み)。複数台から操作したくなったら
  # backend_r2.tf.example を参照して R2 に移せる(R2 無料枠内)。
}

# 認証は環境変数 CLOUDFLARE_API_TOKEN で渡す(リポジトリには書かない)。
provider "cloudflare" {}
