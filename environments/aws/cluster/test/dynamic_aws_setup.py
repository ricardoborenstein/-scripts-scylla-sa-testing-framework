import json
from terrascript import Terrascript
import terrascript.provider as provider
from terrascript.aws.r import aws_vpc, aws_subnet, aws_instance, aws_vpc_peering_connection, aws_vpc_peering_connection_accepter
from terrascript.aws.d import aws_ami

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
        "aws_vpc_peering_connection_accepter": {}
    }
    data = {"aws_ami": {}}
    vpc_ids = {}  # Correctly initializing the dictionary to store VPC IDs.
    seed_instances = {}
    for region in config['regions']:
        details = config['regions'][region]
        num_nodes = details['nodes']
        cidr = details['cidr']

        vpc_id = f"vpc_{region}"
        vpc = aws_vpc(vpc_id, provider=region, cidr_block=cidr, enable_dns_support=True, enable_dns_hostnames=True)
        ts += vpc
        resources["aws_vpc"][vpc_id] = {
            "provider": f"aws.{region}",
            "cidr_block": cidr,
            "enable_dns_support": True,
            "enable_dns_hostnames": True
        }
        vpc_ids[region] = vpc_id  # Storing each VPC ID with its respective region as key

        # Create subnets within each VPC
        base_octet = int(cidr.split('.')[2])
        for i in range(num_nodes):
            subnet_octet = base_octet + i
            subnet_cidr = f"{cidr.rsplit('.', 2)[0]}.{subnet_octet}.0/24"
            subnet_id = f"subnet_{region}_{i}"
            subnet = aws_subnet(subnet_id, provider=region, vpc_id=f"${{aws_vpc.{vpc_id}.id}}",
                                cidr_block=subnet_cidr, map_public_ip_on_launch=True, 
                                availability_zone=f"{region}a")
            ts += subnet
            resources["aws_subnet"][subnet_id] = {
                "provider": f"aws.{region}",
                "vpc_id": f"${{aws_vpc.{vpc_id}.id}}",
                "cidr_block": subnet_cidr,
                "map_public_ip_on_launch": True,
                "availability_zone": f"{region}a"
            }

        ami_id = f"ami_{region}"
        ami = aws_ami(ami_id, provider=region, most_recent=True,
                      filters=[{"name": "name", "values": [f"ScyllaDB Enterprise* {config["scylla_version"]}"]},
                               {"name": "virtualization-type", "values": ["hvm"]},
                               {"name": "root-device-type", "values": ["ebs"]},
                               {"name": "architecture", "values": ["x86_64"]}],
                      owners=["158855661827"])
        ts += ami
        data["aws_ami"][ami_id] = {
            "provider": f"aws.{region}",
            "most_recent": True,
            "filter": [
                {"name": "name", "values": [f"ScyllaDB Enterprise* {config["scylla_version"]}"]},
                {"name": "virtualization-type", "values": ["hvm"]},
                {"name": "root-device-type", "values": ["ebs"]},
                {"name": "architecture", "values": ["x86_64"]}
            ],
            "owners": ["158855661827"]
        }
        
        for i in range(num_nodes):
            instance_id = f"instance_{region}_{i}"
            
            seed_instances[region] = f"${{aws_instance.{instance_id}.private_ip}}"
            # Check if this is the first instance (seed instance) for the region
            if i != 0:
                instance_id_seed = f"instance_{region}_0"
                seed_instances[region] = f"${{aws_instance.{instance_id_seed}.private_ip}}"
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
                                    ami=f"${{data.aws_ami.{ami_id}.id}}", instance_type="i4i.large",
                                    subnet_id=f"${{aws_subnet.{subnet_id}.id}}",user_data=user_data_script)
            ts += instance
            resources["aws_instance"][instance_id] = {
                "provider": f"aws.{region}",
                "ami": f"${{data.aws_ami.{ami_id}.id}}",
                "instance_type": "i4i.large",
                "subnet_id": f"${{aws_subnet.{subnet_id}.id}}",
                "user_data": user_data_script
            }

    # Configure VPC Peering Connections if multiple regions are specified
    if len(config['regions']) > 1:
        regions = list(config['regions'].keys())
        for i, region_i in enumerate(regions):
            for j in range(i + 1, len(regions)):
                region_j = regions[j]
                peering_id = f"peer_{region_i}_to_{region_j}"
                peering = aws_vpc_peering_connection(peering_id, provider=region_i,
                                                     vpc_id=f"${{aws_vpc.{vpc_ids[region_i]}.id}}",
                                                     peer_vpc_id=f"${{aws_vpc.{vpc_ids[region_j]}.id}}",
                                                     peer_region=region_j,  # Specify the peer VPC's region
                                                     auto_accept=True)
                ts += peering
                resources["aws_vpc_peering_connection"][peering_id] = {
                    "provider": f"aws.{region_i}",
                    "vpc_id": f"${{aws_vpc.{vpc_ids[region_i]}.id}}",
                    "peer_vpc_id": f"${{aws_vpc.{vpc_ids[region_j]}.id}}",
                    "peer_region": region_j,  # This is critical for cross-region peering
                    #"auto_accept": True
                }
                                # Peering connection acceptance in the peer region
                accepter_id = f"peer_accept_{region_j}_from_{region_i}"
                accepter = aws_vpc_peering_connection_accepter(accepter_id, provider=region_j,
                                                               vpc_peering_connection_id=f"${{aws_vpc_peering_connection.{peering_id}.id}}",
                                                               auto_accept=True)
                ts += accepter
                resources["aws_vpc_peering_connection_accepter"][accepter_id] = {
                    "provider": f"aws.{region_j}",
                    "vpc_peering_connection_id": f"${{aws_vpc_peering_connection.{peering_id}.id}}",
                    "auto_accept": True
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
        "cluster_name": "ScyllaCluster1",
        "scylla_version": "2024.1.2",
        "regions": {
            "us-east-1": {"nodes": 2, "cidr": "10.0.0.0/16"},
            "us-west-2": {"nodes": 1, "cidr": "10.1.0.0/16"}
        }
    }

    terraform_script = create_infrastructure(config)
    with open('main.tf.json', 'w') as file:
        file.write(terraform_script)
