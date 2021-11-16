terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.27"
    }
  }
}

provider "aws" {
  region  = var.region
}

module "module-network-linux-web" {
    source = "github.com/xmartlabs/terraform.git?ref=main/modules/module-network-linux-web"
    region = var.region
    tags = var.tags
    vpc = var.vpc
    subnet_prefix = var.subnet_prefix
    security_group = var.security_group
    route_table = var.route_table
    network_interface = var.network_interface
}

module "module-ec2-linux-web"{
    source = "github.com/xmartlabs/terraform.git?ref=main/modules/module-ec2-linux-web"
    region = var.region
    amiid  = var.amiid
    tags= var.tags
    id_network_interface= module.module-network-linux-web.network_interface_id
    user_data_path= "user_data.tmpl"
    key_name= var.key_name
    ec2name = var.ec2name
    size = var.size
    root_disk = var.root_disk
}
