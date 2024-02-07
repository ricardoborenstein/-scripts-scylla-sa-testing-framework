provider "aws" {
  region                   = var.aws_region
  shared_credentials_files = ["${var.aws_creds}"]
  profile                  = "${var.aws_creds_profile}"
}