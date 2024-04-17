import json
from terrascript import Terrascript
import terrascript.provider as provider
from terrascript.aws.r import aws_vpc, aws_subnet, aws_instance, aws_vpc_peering_connection, aws_vpc_peering_connection_accepter,aws_security_group
from terrascript.aws.d import aws_ami , aws_availability_zones


# Define the ingress rules as a local variable
# Define the ingress rules as a local variable
ingress_rules = [
    {"from_port": 443, "to_port": 443, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "HTTPS access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 3000, "to_port": 3000, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "Monitoring access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 80, "to_port": 80, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "HTTP access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 22, "to_port": 22, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "SSH access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 9042, "to_port": 9042, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "CQL access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 9142, "to_port": 9142, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "SSL CQL access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 7000, "to_port": 7000, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "RPC access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 7001, "to_port": 7001, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "RPC SSL access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 7199, "to_port": 7199, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "JMX access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 10000, "to_port": 10000, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "REST access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 9180, "to_port": 9180, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "Prometheus access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 9100, "to_port": 9100, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "Node exp access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 9160, "to_port": 9160, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "Thrift access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
    {"from_port": 19042, "to_port": 19042, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"], "description": "Shard-aware access", "ipv6_cidr_blocks": [], "prefix_list_ids": [], "security_groups": [], "self": False},
]

egress_rules = [
    {
        "from_port": 0,
        "to_port": 0,
        "protocol": "-1",
        "cidr_blocks": ["0.0.0.0/0"],
        "description": "Allow all outbound traffic",
        "ipv6_cidr_blocks": [],
        "prefix_list_ids": [],
        "security_groups": [],
        "self": False
    }
]

def get_azs(region, ts):
    azs = aws_availability_zones(f"azs_{region}", provider=region)
    ts += azs  # This adds the data source to the script
    return azs.names

def create_infrastructure(config):
    ts = Terrascript()

    # Initialize AWS provider for each specified region
    for region in config['regions']:
        ts += provider.aws(alias=region, region=region)

    resources = {
        "aws_vpc": {},
        "aws_subnet": {},
        "aws_instance": {},
        "aws_vpc_peering_connection": {},
        "aws_vpc_peering_connection_accepter": {},
        "aws_security_group": {}
    }
    data = {"aws_ami": {}}
    vpc_ids = {}  # Correctly initializing the dictionary to store VPC IDs.
    seed_instances = {}
    for region in config['regions']:
        details = config['regions'][region]
        num_nodes = details['nodes']
        num_loaders = details['loaders']
        loaders_type = details['loaders_type']
        cidr = details['cidr']
        tags = {"Name": f"{config["cluster_name"]}"+ "_" + f"{region}-VPC", "Type": "VPC"}
        vpc_id = f"vpc_{region}"
        vpc = aws_vpc(vpc_id, provider=region, cidr_block=cidr, enable_dns_support=True, enable_dns_hostnames=True,tags=tags)
        ts += vpc
        resources["aws_vpc"][vpc_id] = {
            "provider": f"aws.{region}",
            "cidr_block": cidr,
            "enable_dns_support": True,
            "enable_dns_hostnames": True,
            "tags": tags
        }
        azs = aws_availability_zones(f"azs_{region}",state="available")
        ts += azs
        az_mode = details.get('az_mode', 'single-az')
        # Define specific AZs manually for multi-AZ or single-AZ
        if az_mode == 'multi-az':
            azs = [f"{region}a", f"{region}b", f"{region}c"]  # Specific AZs for multi-AZ
        else:
            azs = [f"{region}a"]  # Only the first AZ for single-AZ
        vpc_ids[region] = vpc_id  # Storing each VPC ID with its respective region as key

        # Create security group resource
        sg = aws_security_group(
            f"sg_{region}",
            provider=f"aws.{region}",
            name=f"{config['cluster_name']}-sg-{region}",
            vpc_id=f"${{aws_vpc.{vpc_id}.id}}",
            ingress=ingress_rules,
            egress=egress_rules,
            tags={
                "Name": f"{config['cluster_name']}-SG-{region}",
                "Project": config['cluster_name'],
                "Type": "Security Group",
                "Region": region
            }
        )
        ts += sg
        
        # Add security group to resources dictionary
        resources["aws_security_group"][f"sg_{region}"] = {
            "name": f"{config['cluster_name']}-sg-{region}",
            "provider": f"aws.{region}",
            "vpc_id": f"${{aws_vpc.{vpc_id}.id}}",
            "ingress": ingress_rules,
            "egress": egress_rules,
            "tags": {
                "Name": f"{config['cluster_name']}-SG-{region}",
                "Project": config['cluster_name'],
                "Type": "Security Group",
                "Region": region
            }
        }

        # Create subnets within each VPC
        base_octet = int(cidr.split('.')[2])

        for i in range(num_nodes):
            az = azs[i % len(azs)]
            subnet_id = f"subnet_{region}_{i}"
            subnet_cidr = f"{cidr.rsplit('.', 2)[0]}.{i}.0/24"  # Example subnet CIDR
            subnet = aws_subnet(
                subnet_id, provider=region, 
                vpc_id=vpc_id,
                cidr_block=subnet_cidr, 
                availability_zone=az,
                map_public_ip_on_launch=True,
                tags={"Name": f"{config['cluster_name']}_{region}_subnet_{i}", "Type": "Subnet"}
            )
            ts += subnet
            resources["aws_subnet"][subnet_id] = {
                "provider": f"aws.{region}",
                "vpc_id": f"${{aws_vpc.{vpc_id}.id}}",
                "cidr_block": subnet_cidr,
                "map_public_ip_on_launch": True,
                "availability_zone": az,
                "tags": tags
            }
  
        # ScyllaDB AMI
        scylla_ami_id = f"scylla_ami_{region}"
        scylla_ami = aws_ami(scylla_ami_id, provider=region, most_recent=True,
                             filter=[{"name": "name", "values": [f"ScyllaDB Enterprise* {config['scylla_version']}"]},
                                      {"name": "virtualization-type", "values": ["hvm"]},
                                      {"name": "root-device-type", "values": ["ebs"]},
                                      {"name": "architecture", "values": ["x86_64"]}],
                             owners=["158855661827"])
        ts += scylla_ami
        data["aws_ami"][scylla_ami_id] = {
            "provider": f"aws.{region}",
            "most_recent": True,
            "filter": [
                {"name": "name", "values": [f"ScyllaDB Enterprise* {config['scylla_version']}"]},
                {"name": "virtualization-type", "values": ["hvm"]},
                {"name": "root-device-type", "values": ["ebs"]},
                {"name": "architecture", "values": ["x86_64"]}
            ],
            "owners": ["158855661827"]
        }

        # Ubuntu AMI
        ubuntu_ami_id = f"ubuntu_ami_{region}"
        ubuntu_ami = aws_ami(ubuntu_ami_id, provider=region, most_recent=True,
                             filter=[{"name": "name", "values": ['ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*']},
                                      {"name": "state", "values": ["available"]},
                                      {"name": "architecture", "values": ["x86_64"]},
                                      {"name": "root-device-type", "values": ["ebs"]}],
                             owners=["099720109477"])
        ts += ubuntu_ami
        data["aws_ami"][ubuntu_ami_id] = {
            "provider": f"aws.{region}",
            "most_recent": True,
            "filter": [
                {"name": "name", "values": ['ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*']},
                {"name": "state", "values": ["available"]},
                {"name": "architecture", "values": ["x86_64"]},
                {"name": "root-device-type", "values": ["ebs"]}
            ],
            "owners": ["099720109477"]
        }
        
        for i in range(num_nodes):
            instance_id = f"instance_{region}_{i}"
            
            seed_instances[region] = f"${{aws_instance.{instance_id}.private_ip}}"
            # Check if this is the first instance (seed instance) for the region
            if i != 0:
                instance_id_seed = f"instance_{region}_0"
                seed_instances[region] = f"${{aws_instance.{instance_id_seed}.private_ip}}"
                tags = {"Name": f"{config["cluster_name"]}"+ "_" + f"instance_{region}_{i}", "Type": "Peer"}
                user_data_script = f"""\
                #!/bin/bash
                echo '
                {{
                "scylla_yaml": {{
                    "cluster_name": "{config['cluster_name']}",
                    "seed_provider": [{{
                    "class_name": "org.apache.cassandra.locator.SimpleSeedProvider",
                    "parameters": [{{
                        "seeds": "{seed_instances[region]}"
                    }}]
                    }}],
                    "start_scylla_on_first_boot": false
                }}
                }}' > /etc/scylla/scylla.yaml
                """
            if i == 0:
                tags = {"Name": f"{config["cluster_name"]}"+ "_" + f"instance_{region}_{i}", "Type": "Seed"}
                user_data_script = f"""\
                #!/bin/bash
                echo '
                {{
                "scylla_yaml": {{
                    "cluster_name": "{config['cluster_name']}",
                    "start_scylla_on_first_boot": false
                }}
                }}' > /etc/scylla/scylla.yaml
                """
            
            instance_id = f"instance_{region}_{i}"
            instance = aws_instance(instance_id, provider=region,
                                    ami=f"${{data.aws_ami.{scylla_ami_id}.id}}", instance_type="i4i.large",
                                    subnet_id=f"${{aws_subnet.{subnet_id}.id}}",user_data=user_data_script,tags=tags)
            ts += instance
            resources["aws_instance"][instance_id] = {
                "provider": f"aws.{region}",
                "ami": f"${{data.aws_ami.{scylla_ami_id}.id}}",
                "instance_type": "i4i.large",
                "subnet_id": f"${{aws_subnet.{subnet_id}.id}}",
                "user_data": user_data_script,
                "tags": tags
            }

    for i in range(num_loaders):            
            instance_id = f"loader_{region}_{i}"
            tags = {"Name": f"{config["cluster_name"]}"+ "_" + f"loader_{region}_0", "Type": "Loader"}
            instance = aws_instance(instance_id, provider=region,
                                    ami=f"${{data.aws_ami.{ubuntu_ami_id}.id}}", instance_type=loaders_type,
                                    subnet_id=f"${{aws_subnet.{subnet_id}.id}}",tags=tags)
            ts += instance
            resources["aws_instance"][instance_id] = {
                "provider": f"aws.{region}",
                "ami": f"${{data.aws_ami.{ubuntu_ami_id}.id}}",
                "instance_type": loaders_type,
                "subnet_id": f"${{aws_subnet.{subnet_id}.id}}",
                "tags": tags
            }

    # Configure VPC Peering Connections if multiple regions are specified
    if len(config['regions']) > 1:
        regions = list(config['regions'].keys())
        for i, region_i in enumerate(regions):
            for j in range(i + 1, len(regions)):
                region_j = regions[j]
                peering_id = f"peer_{region_i}_to_{region_j}"
                tags = {"Name": f"{config["cluster_name"]}"+ "_" + f"peer_{region_i}_to_{region_j}", "Type": "Peering"}

                peering = aws_vpc_peering_connection(peering_id, provider=region_i,
                                                     vpc_id=f"${{aws_vpc.{vpc_ids[region_i]}.id}}",
                                                     peer_vpc_id=f"${{aws_vpc.{vpc_ids[region_j]}.id}}",
                                                     peer_region=region_j,  # Specify the peer VPC's region
                                                     auto_accept=True,tags=tags)
                ts += peering
                resources["aws_vpc_peering_connection"][peering_id] = {
                    "provider": f"aws.{region_i}",
                    "vpc_id": f"${{aws_vpc.{vpc_ids[region_i]}.id}}",
                    "peer_vpc_id": f"${{aws_vpc.{vpc_ids[region_j]}.id}}",
                    "peer_region": region_j,
                    "tags": tags  # This is critical for cross-region peering
                    #"auto_accept": True
                }
                                # Peering connection acceptance in the peer region
                accepter_id = f"peer_accept_{region_j}_from_{region_i}"
                tags = {"Name": f"{config["cluster_name"]}"+ "_" + f"peer_accept_{region_j}_from_{region_i}", "Type": "peer_accept"}

                accepter = aws_vpc_peering_connection_accepter(accepter_id, provider=region_j,
                                                               vpc_peering_connection_id=f"${{aws_vpc_peering_connection.{peering_id}.id}}",
                                                               auto_accept=True,tags=tags)
                ts += accepter
                resources["aws_vpc_peering_connection_accepter"][accepter_id] = {
                    "provider": f"aws.{region_j}",
                    "vpc_peering_connection_id": f"${{aws_vpc_peering_connection.{peering_id}.id}}",
                    "auto_accept": True,
                    "tags": tags
                }

    tf_config = {
        "terraform": {
            "required_providers": {
                "aws": {
                    "source": "hashicorp/aws",
                    "version": "~> 5.0"
                }
            }
        },
        "provider": {
            "aws": [{"alias": region, "region": region} for region in config['regions']]
        },
        "resource": resources,
        "data": data
    }

    return json.dumps(tf_config, indent=4)

if __name__ == "__main__":
    config = {
        "cluster_name": "Ricardo-ScyllaCluster1",
        "scylla_version": "2024.1.2",
        "regions": {
            "us-east-1": {"nodes": 3, "scylla_node_type": "i4i.large" , "loaders": 3 , "loaders_type": "m5.large" ,"cidr": "10.0.0.0/16", "az_mode": "multi-az"},
            "us-west-2": {"nodes": 2, "scylla_node_type": "i4i.large" , "loaders": 3 , "loaders_type": "m5.large" ,"cidr": "10.1.0.0/16", "az_mode": "single-az"}
        }
    }

    terraform_script = create_infrastructure(config)
    with open('main.tf.json', 'w') as file:
        file.write(terraform_script)
