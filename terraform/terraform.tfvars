# Generics
region = "us-east-1"
 
tags = [{ Project = "lanthorn",State = "Deploy EC2 with nvidia drivers and docker installed"}]


# Networking
vpc = [{ name = "lanthorn_vpc", cidr_block = "10.0.0.0/16" , instance_tenancy = "default", enable_dns_hostnames = true, enable_dns_support = true}]

subnet_prefix = [{ name = "langthron_module_subnet", cidr_block = "10.0.1.0/24", availability_zone = "us-east-1a", map_public_ip_on_launch = true }]

security_group = [{ name = "langthron_module_security_group" }]

route_table = [{ name = "langthron_module_route_table", cidr_block = "0.0.0.0/0", ipv6_cidr_block = "::/0" }]

network_interface = [{ name = "langthron_module_network_interface", private_ips = ["10.0.1.50"], device_index = 0 }]


# EC2
ec2name = "langthron-smart-social-distancing"

key_name = "lanthornkey"

size = "g4dn.xlarge"

root_disk = [{ volume_size = "100",volume_type = "gp2"}]

amiid = "ami-012e9f6aa634f84f8"

# To be run after creation
user_data_path = "user_data.tmpl"