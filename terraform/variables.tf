# Generics
variable "region" {
  description = "required - region"
}

variable "tags" {
  description = "required - default important tags for resources"
  default     = [{ Project = "not created", State = "not created" }]
}

# Networking
variable "vpc" {
  description = "The definition of vpc"
  default     = [{ name = "terraform_module_vpc", cidr_block = "10.0.0.0/16", instance_tenancy = "default", enable_dns_hostnames = true, enable_dns_support = true }]
}

variable "subnet_prefix" {
  description = "The subnet prefix"
  default     = [{ name = "terraform_module_subnet", cidr_block = "10.0.1.0/24", availability_zone = "us-east-1a", map_public_ip_on_launch = true }]
}

variable "security_group" {
  description = "security group definition"
  default     = [{ name = "terraform_module_security_group" }]
}

variable "route_table" {
  description = "route table definition"
  default     = [{ name = "terraform_module_route_table", cidr_block = "0.0.0.0/0", ipv6_cidr_block = "::/0" }]
}

variable "network_interface" {
  description = "network interface definition"
  default     = [{ name = "terraform_module_network_interface", private_ips = ["10.0.1.50"], device_index = 0 }]
}

# EC2
variable "ec2name" {
  description = "name for the EC2 instance"
  default     = "default-ec2name"
}
variable "key_name" {
  description = "key to be used by the EC2"
  default     = "default-key_name"
}
variable "size" {
  description = "instance type for the EC2"
  default     = "t2-micro"
}
variable "root_disk" {
  description = "root disk definition"
  default     = [{ volume_size = "100", volume_type = "gp2" }]
}
variable "amiid" {
  description = "amazon-linux"
}

# To be run after creation
variable "user_data_path" {
  description = "User data file path"
}