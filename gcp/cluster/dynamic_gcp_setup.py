import json
import terrascript
import terrascript.provider as provider
import terrascript.resource as resource
import terrascript.data as data
import yaml 
import os
import math
from google.cloud import compute_v1

# Define the ingress rules as a local variable
ingress_rules = [
    {"ports": ["443"], "protocol": "tcp", "description": "HTTPS access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["3000"], "protocol": "tcp", "description": "Monitoring access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["80"], "protocol": "tcp", "description": "HTTP access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["22"], "protocol": "tcp", "description": "SSH access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["9042"], "protocol": "tcp", "description": "CQL access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["9142"], "protocol": "tcp", "description": "SSL CQL access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["7000"], "protocol": "tcp", "description": "RPC access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["7001"], "protocol": "tcp", "description": "RPC SSL access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["7199"], "protocol": "tcp", "description": "JMX access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["10000"], "protocol": "tcp", "description": "REST access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["9180"], "protocol": "tcp", "description": "Prometheus access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["9100"], "protocol": "tcp", "description": "Node exp access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["9160"], "protocol": "tcp", "description": "Thrift access", "ranges": ["0.0.0.0/0"]},
    {"ports": ["19042"], "protocol": "tcp", "description": "Shard-aware access", "ranges": ["0.0.0.0/0"]}
]


egress_rules = [
    {"protocol": "all", "ports": [], "description": "Allow all outbound traffic", "ranges": ["0.0.0.0/0"]}
]


def list_available_zones(project_id, region):
    """
    Lists all available zones in a given region for the specified project.

    Args:
    project_id (str): Google Cloud project ID.
    region (str): The region to query for available zones.
    """
    # Create a Compute Engine client
    client = compute_v1.ZonesClient()

    # Construct the full region path required by the API
    region_name = f"projects/{project_id}/regions/{region}"

    # List zones in the specified region
    print(f"Available zones in the region {region}:")
    request = compute_v1.ListZonesRequest(project=project_id, filter=f"name:{region}-*")
    return [zone.name for zone in client.list(request=request)]  # This ensures the list contains only strings.


def add_firewall_rules(ts, ingress_rules, egress_rules, network):
    # Process ingress rules
    for rule in ingress_rules:
        if isinstance(rule, dict) and 'description' in rule:
            rule_name = f"{config["cluster_name"]}-" + rule['description'].lower().replace(' ', '-') + '-ingress'
            firewall_rule = resource.google_compute_firewall(
                rule_name,
                name= rule_name,
                project=config['gcp_project_id'],
                network=network,
                direction="INGRESS",
                allow=[{
                    'protocol': rule['protocol'],
                    'ports': rule['ports']
                }],
                source_ranges=rule['ranges'],
                priority=1000,
                description=rule['description'],
                depends_on=[f"google_compute_network.{network}"] 

            )
            ts += firewall_rule
        else:
            print("Error: Rule format is incorrect or rule is not a dictionary")

    # Process egress rules
    for rule in egress_rules:
        if isinstance(rule, dict) and 'description' in rule:
            rule_name = f"{config["cluster_name"]}-"+ rule['description'].lower().replace(' ', '-') + '-egress'
            firewall_rule = resource.google_compute_firewall(
                rule_name, name=rule_name,
                network=network,
                project=config['gcp_project_id'],
                direction="EGRESS",
                allow=[{
                    'protocol': rule['protocol'],
                    'ports': rule['ports']  # This will usually be an empty list for egress rules
                }],
                destination_ranges=rule['ranges'],
                priority=1000,
                description=rule['description'],
                depends_on=[f"google_compute_network.{network}"] 
            )
            ts += firewall_rule
        else:
            print

def create_infrastructure(config):

    ts = terrascript.Terrascript()


    for region in config['regions']:
        ts += provider.google(project=config['gcp_project_id'],region=region,alias=region)
        
    # Determine network type based on az_mode across all regions (simplified assumption)
    global_network = any(details.get('az_mode', 'single-az') == 'multi-az' for details in config['regions'].values())
    routing_mode = "GLOBAL" if global_network else "REGIONAL"

    # Definitions of GCP network and Subnetwork
    labels = {"name": f"{config["cluster_name"]}"+ "-" + f"{region}-networking", "type": "networking","project": config['cluster_name']}
    network_name = f"{config['cluster_name']}-network"
    network = resource.google_compute_network(network_name,
                                     name = network_name,
                                     auto_create_subnetworks=False,  # Set to False to manage subnetworks manually
                                     project=config['gcp_project_id'],
                                     #la=labels,
                                     routing_mode=routing_mode)
    ts += network

    add_firewall_rules(ts, ingress_rules, egress_rules, network_name)


    with open(os.path.expanduser(config['path_to_key']), 'r') as file:
        key_content = file.read().strip().replace('\n', '')
    ssh_keys_metadata = f"ubuntu:{key_content}"
    #azs = list_available_zones(config['gcp_project_id'], region)


    for region, details in config['regions'].items():
        # Ensure provider for each region (if needed, else move this outside the loop)
        ts += provider.google(project=config['gcp_project_id'], region=region)

        azs = list_available_zones(config['gcp_project_id'], region)
        print(azs)
        # Determine number of AZs to use based on mode
        if details.get('az_mode') == 'multi-az':
            # Use all available zones up to a maximum of 3
            az_count = min(len(azs), 3)
        else:
            # Use only one zone, typically the first available
            az_count = 1
        # Create subnetworks and instances
        for i in range(az_count):
            subnetwork_name = f"{config['cluster_name']}-subnet-{region}-{i}"
            subnetwork = resource.google_compute_subnetwork(
                subnetwork_name,
                project=config['gcp_project_id'],
                name=subnetwork_name,
                ip_cidr_range=f"10.0.{i}.0/24",
                region=region,
                network=network_name,
                private_ip_google_access=True,
                depends_on=[f"google_compute_network.{network_name}"]
            )
            ts += subnetwork

            # Create nodes in this subnetwork
            for j in range(details['nodes']):
                zone_index = j % az_count
                node_name = f"{config['cluster_name']}-scylla-node-{region}-{j}"
                disk_size_gb = details.get('disk_size_gb', 0)
                num_local_ssds = math.ceil(disk_size_gb / 375)
                disks = [{"device_name": f"local-ssd-{k}", "interface": "NVME"} for k in range(num_local_ssds)]

                node_instance = resource.google_compute_instance(
                    node_name,
                    name=node_name,
                    project=config['gcp_project_id'],
                    machine_type=details['scylla_node_type'],
                    zone=azs[zone_index],
                    min_cpu_platform="Intel Ice Lake",
                    allow_stopping_for_update=True,
                    network_interface=[{
                        "network": network_name,
                        "subnetwork": subnetwork_name,
                        "access_config": [{}],  # For external IP if required
                    }],
                    boot_disk=[{
                        "initialize_params": {
                            "image": f"projects/scylla-images/global/images/scylladb-enterprise-{config['scylla_version']}",
                        },
                    }],
                    scratch_disk=disks,
                    labels={
                        "name": f"{config['cluster_name']}-{region}-scylla-node-{j}",
                        "type": "scylla",
                        "project": config['cluster_name'],
                    },
                    metadata={'ssh-keys': ssh_keys_metadata},
                    service_account={
                        "email": "default",
                        "scopes": ["https://www.googleapis.com/auth/cloud-platform"]
                    },
                    depends_on=[f"google_compute_subnetwork.{subnetwork_name}"]
                )
                ts += node_instance


    first_region = next(iter(config['regions']))  # Get the first region key from the dictionary

    for region, details in config['regions'].items():
        if region == first_region:
            # Create monitoring instance only for the first region
            monitoring_instance_id = f"{config['cluster_name']}-monitoring-{region}"
            

            monitoring_tags = {
                "name": f"{config['cluster_name']}-{region}-monitoring",
                "type": "monitoring",
                "project": config['cluster_name']
            }
            
            monitoring_instance = resource.google_compute_instance(monitoring_instance_id,
                name=monitoring_instance_id,
                project = config['gcp_project_id'],
                machine_type=config['monitoring_type'],  # `monitoring_type` should be defined in your config for the region
                allow_stopping_for_update = "true",

                zone=azs[i % len(azs)],  # Choose the zone, generally region followed by '-a', '-b', etc.
                network_interface=[{
                "network": network_name,
                    "subnetwork": f"{subnetwork_name}",
                "subnetwork_project": config['gcp_project_id'],
                "access_config": [{}],  # For external IP
                }], # This section assigns a public IP
                boot_disk=[{
                    "initialize_params": {
                        "image": f"projects/ubuntu-os-cloud/global/images/family/ubuntu-minimal-2204-lts"
                    }
                }],
                labels=monitoring_tags,
                metadata={'ssh-keys': ssh_keys_metadata,},            

                service_account={
                    "email": "default",
                    "scopes": ["https://www.googleapis.com/auth/cloud-platform"]
                },
                depends_on=[f"google_compute_subnetwork.{subnetwork_name}"] 
            )
            
            ts += monitoring_instance
 
    return ts

def read_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

if __name__ == "__main__":
    # config = {
    #     "cluster_name": "Ricardo-ScyllaCluster1",
    #     "scylla_version": "2024.1.2",
    #     "regions": {
    #         "us-east-1": {"nodes": 3, "scylla_node_type": "i3en.3xlarge" , "loaders": 3 , "loaders_type": "m5.2xlarge" ,"cidr": "10.0.0.0/16", "az_mode": "single-az"},
    #        # "us-west-2": {"nodes": 2, "scylla_node_type": "i4i.large" , "loaders": 0 , "loaders_type": "m5.large" ,"cidr": "10.1.0.0/16", "az_mode": "single-az"}
    #     },
    #     "aws_key_pair_name" : "ricardo-terraform",
    #     "monitoring_type" : "m5.xlarge"
    # }
    config = read_config("../../variables.yml")

    terraform_script = create_infrastructure(config)
    #print(terraform_script)
    with open('main.tf.json', 'w') as file:
        file.write(str(terraform_script))
