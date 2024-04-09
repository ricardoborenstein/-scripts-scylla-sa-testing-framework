# Create three EC2 instances based on the specified AMI, instance type, subnet ID, and security groups. 
# Create tags to identify the instances and sets timeouts for creating the instances.

resource "aws_instance" "instance" {
  count           = var.loader_node_count
  ami             = var.ami_id
  instance_type   = var.loader_instance_type
  subnet_id       = element(aws_subnet.public_subnet.*.id, count.index)
  security_groups = [aws_security_group.sg.id,]
  key_name        = var.aws_key_pair_name
  tags = {
    "Name"      = "${var.custom_name}-Loader-${count.index}"
    "Project"   = "${var.custom_name}"
    "Type" =  "Loader"
  }

  timeouts {
    create = "10m"
  }

  # Provision files to each instance. Copy three files from the current directory 
  # to the remote instance: stress-0.yml, cassandra-stress.service, and cassandra-stress-benchmark.service.

#   provisioner "file" {
#     source      = "./profile/stress-${count.index}.yml"
#     destination = "/home/scyllaadm/stress.yml"
#   }
#   provisioner "file" {
#     source      = "./service/cassandra-stress.service"
#     destination = "/home/scyllaadm/cassandra-stress.service"
#   }
#   provisioner "file" {
#     source      = "./service/cassandra-stress-benchmark.service"
#     destination = "/home/scyllaadm/cassandra-stress-benchmark.service"
#   }

  # Run remote-exec commands on each instance. It stops the scylla-server, creates a start.sh script, 
  # creates a benchmark.sh script, sets permissions on the scripts, moves two files to /etc/systemd/system/, 
  # runs daemon-reload, and starts the cassandra-stress service.

#   provisioner "remote-exec" {
#     inline = [
#       "sudo systemctl stop scylla-server |tee scylla.log",
#       "echo '/usr/bin/cassandra-stress user profile=./stress.yml n=${var.num_of_ops} cl=local_quorum no-warmup \"ops(insert=1)\" -rate threads=${var.num_threads} fixed=550000/s -mode native cql3  -log file=populating.log  -node ${join(",", aws_instance.scylladb.*.private_ip)}' > start.sh",
#       "echo '/usr/bin/cassandra-stress user profile=./stress.yml duration=24h no-warmup cl=local_quorum \"ops(insert=1,simple_select=2,select_by_show=2,select_by_story=2,select_sum_duration=1,select_max_updated=1,select_count_story=1,select_sum_playtime=1)\" -rate threads=${var.num_threads} fixed=${var.throttle} -mode native cql3  -log file=benchmarking.log -node ${join(",", aws_instance.scylladb.*.private_ip)}' > benchmark.sh",
#       "sudo chmod +x start.sh benchmark.sh",
#       "sudo mv /home/scyllaadm/cassandra-stress.service /etc/systemd/system/cassandra-stress.service ",
#       "sudo mv /home/scyllaadm/cassandra-stress-benchmark.service /etc/systemd/system/cassandra-stress-benchmark.service ", "sudo systemctl daemon-reload ",
#       "sudo systemctl start cassandra-stress.service",
#     ]
#   }

#   # Set up an SSH connection to each EC2 instance using the scyllaadm user and the private key. 
#   # The coalesce function is used to select the public IP address of ScyllaDB Nodes.
#   connection {
#     type        = "ssh"
#     user        = "scyllaadm"
#     private_key = file(var.ssh_private_key)
#     host        = coalesce(self.public_ip, self.private_ip)
#     agent       = true
#   }

}

