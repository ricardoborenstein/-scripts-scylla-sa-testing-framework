resource "aws_instance" "scylladb" {
  count           = var.scylla_num_nodes
  ami             = var.ami_id # Replace with your desired AMI
  instance_type   = var.instance_type
  key_name        = var.aws_key_pair_name     # Replace with your EC2 key pair name

  subnet_id       = element(aws_subnet.public_subnet.*.id, count.index)  # Assign to a subnet within the VPC
  security_groups = [aws_security_group.sg.id]  # Replace with your VPC security group ID

  tags = {
    Name = "${var.custom_name}-ScyllaDBInstance-${count.index}"
    "Project"   = "${var.custom_name}"
    "Type" =  "Scylla"
  }

#   # Provisioner to install Scylla and its dependencies
#   provisioner "remote-exec" {
#     inline = [
#       "sudo mkdir -p /etc/apt/keyrings",
#       "sudo gpg --homedir /tmp --no-default-keyring --keyring /etc/apt/keyrings/scylladb.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys ${var.gpg_scylla}",
#       "sudo wget -O /etc/apt/sources.list.d/scylla.list ${var.gpg_source_list}",
#       "sudo apt-get update",
#       "sudo apt-get install -y openjdk-11-jre-headless",
#       "sudo update-java-alternatives --jre-headless -s java-1.11.0-openjdk-amd64",
#       "sudo apt-get update",
#       "sudo apt-get install -y scylla"
#     ]

#     connection {
#       type        = "ssh"
#       user        = var.instance_username
#       private_key = file(var.ssh_private_key)
#       host        = self.public_ip
#     }
#   }

#   # Provisioner to configure Scylla
#   provisioner "remote-exec" {
#     inline = [
#       "sudo scylla_setup --disks ${var.disk_path} --online-discard 1 --nic ens5 --io-setup 1 --no-fstrim-setup --no-rsyslog-setup || true"
#     ]

#     connection {
#       type        = "ssh"
#       user        = var.instance_username
#       private_key = file(var.ssh_private_key)
#       host        = self.public_ip
#     }
#   }

#   # Transfer and execute the configuration script
#   provisioner "file" {
#     content = templatefile("./configure_scylla.sh.tpl", {
#       cluster_name   = var.custom_name,
#       seed_ip        = aws_instance.scylladb[0].private_ip,
#       listen_address = self.private_ip,
#       rpc_address    = self.private_ip
#     })
#     destination = "/home/${var.instance_username}/configure_scylla.sh"

#     connection {
#       type        = "ssh"
#       user        = var.instance_username
#       private_key = file(var.ssh_private_key)
#       host        = self.public_ip
#     }
#   }

#   provisioner "remote-exec" {
#     inline = [
#       "sudo chmod +x /home/${var.instance_username}/configure_scylla.sh",
#       "sudo /home/${var.instance_username}/configure_scylla.sh"
#     ]

#     connection {
#       type        = "ssh"
#       user        = var.instance_username
#       private_key = file(var.ssh_private_key)
#       host        = self.public_ip
#     }
#   }
}

output "scylla_ips" {
  value = join(",", aws_instance.scylladb.*.private_ip)
}
