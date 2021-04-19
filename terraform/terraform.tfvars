
#If you don't specify the values from some variables, this takes the default values described in the variable.tf file.
#The variables region,key_name and amiid are required.

# Generics
region = 
 
tags = 

# Networking

vpc = 

subnet_prefix = 

security_group = 

route_table = 

network_interface = 

# EC2

ec2name = 

key_name = 

#We recomend use g4dn.xlarge size.
size =

#We recomend use [{ volume_size = "100",volume_type = "gp2"}] values.
root_disk = 

#We recomend use "ami-012e9f6aa634f84f8", this ami have ndrivia drivers and gpu.
amiid = 

# To be run after creation
user_data_path = 