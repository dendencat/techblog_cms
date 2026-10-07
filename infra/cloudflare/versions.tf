terraform {
  required_version = ">= 1.10"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.27"
    }
  }

  # State は Cloudflare R2(S3 互換)に置く。Tunnel トークンが state に入るため、
  # 公開リポジトリやローカルの共有フォルダには置かないこと。
  # 接続情報は `terraform init -backend-config=backend.hcl` で渡す(backend.hcl.example 参照)。
  backend "s3" {}
}

# 認証は環境変数 CLOUDFLARE_API_TOKEN で渡す(リポジトリには書かない)。
provider "cloudflare" {}
