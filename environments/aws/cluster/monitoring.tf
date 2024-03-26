resource "aws_instance" "scylladb-monitoring" {
  ami           = var.ami_id
  instance_type = var.monitoring_instance_type
  key_name        = var.aws_key_pair_name 

  security_groups = [aws_security_group.sg.id]
  subnet_id       = element(aws_subnet.public_subnet.*.id, 0)
  tags = {
    Name = "${var.custom_name}-Monitoring"
    "Project"   = "${var.custom_name}"
    "Type" =  "Monitoring"
  }
  depends_on = [ aws_instance.scylladb_seed ]

  # user_data = <<-EOF
  #               #!/bin/bash
  #               # Update and install prerequisites
  #               sudo apt-get update
  #               sudo apt-get install -y ca-certificates curl gnupg

  #               # Add Docker's official GPG key
  #               sudo install -m 0755 -d /etc/apt/keyrings
  #               curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  #               sudo chmod a+r /etc/apt/keyrings/docker.gpg

  #               # Add Docker repository
  #               echo \
  #                 "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  #                 $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  #                 sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  #               # Install Docker packages
  #               sudo apt-get update
  #               sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  #               # Add 'ubuntu' user to the docker group
  #               sudo usermod -aG docker ubuntu
  #               sudo systemctl enable docker
  #               sudo reboot now
  #               EOF
  # # Provisioner to install and run Scylla Monitoring
  # provisioner "remote-exec" {
  #   inline = [
  #     "sudo systemctl start docker",
  #     "latest_branch=$(git ls-remote --heads https://github.com/scylladb/scylla-monitoring.git | grep 'refs/heads/branch-' | sort -t '-' -k 2,2V | tail -1 | awk '{print $2}' | cut -d '/' -f 3)",
  #     "git clone --branch $latest_branch https://github.com/scylladb/scylla-monitoring.git", # Add additional run options here
  #   ]

  #   connection {
  #     type        = "ssh"
  #     user        = var.instance_username
  #     private_key = file(var.ssh_private_key)
  #     host        = self.public_ip
  #   }
  # }

  # provisioner "file" {
  #   content     = templatefile("configure_monitoring.sh.tpl", {
  #     CLUSTER_NAME   = var.custom_name,
  #     scylla_servers = join("\n", formatlist("  - %s:9180", data.aws_instances.scylladb.private_ips)),
  #     DC_NAME        = var.aws_region
  #   })
  #   destination = "/tmp/configure_monitoring.sh"

  #   connection {
  #     type        = "ssh"
  #     user        = var.instance_username
  #     private_key = file(var.ssh_private_key)
  #     host        = self.public_ip
  #   }
  # }

  # provisioner "remote-exec" {
  #   inline = [
  #     "sudo chmod +x /tmp/configure_monitoring.sh",
  #     "sudo /tmp/configure_monitoring.sh"
  #   ]

  #   connection {
  #     type        = "ssh"
  #     user        = var.instance_username
  #     private_key = file(var.ssh_private_key)
  #     host        = self.public_ip
  #   }
  # }

  # provisioner "remote-exec" {
  #   inline = [
  #     "cd scylla-monitoring",
  #     "export docker=/usr/bin/docker",
  #     "chmod +x ./start-all.sh",
  #     "chmod +x ./env.sh",
  #     "chmod +x ./versions.sh",
  #     "bash ./start-all.sh -v ${var.scylla_version} -d prometheus_data",
  #     "echo 'done'", # Add additional run options here
  #   ]

  #   connection {
  #     type        = "ssh"
  #     user        = var.instance_username
  #     private_key = file(var.ssh_private_key)
  #     host        = self.public_ip
  #   }
  # }

  connection {
    type        = "ssh"
    user        = var.instance_username
    private_key = file(var.ssh_private_key)
    host        = self.public_ip
  }
}
