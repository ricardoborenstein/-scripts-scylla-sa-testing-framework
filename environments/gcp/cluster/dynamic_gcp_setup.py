import json
import terrascript
import terrascript.provider as provider
import terrascript.resource as resource
import terrascript.data as data
import yaml 
import os
import math

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


def get_azs(region, ts):
    azs = data.google.google_compute_zones(provider=region,version = "~> 5.0.0")
    ts += azs  # This adds the data source to the script
    return azs.names

def add_firewall_rules(ts, ingress_rules, egress_rules, network):
    # Process ingress rules
    for rule in ingress_rules:
        if isinstance(rule, dict) and 'description' in rule:
            rule_name = rule['description'].lower().replace(' ', '-') + '-ingress'
            firewall_rule = resource.google_compute_firewall(
                rule_name,
                name= rule_name,
                network=network,
                direction="INGRESS",
                allow=[{
                    'protocol': rule['protocol'],
                    'ports': rule['ports']
                }],
                source_ranges=rule['ranges'],
                priority=1000,
                description=rule['description']
            )
            ts += firewall_rule
        else:
            print("Error: Rule format is incorrect or rule is not a dictionary")

    # Process egress rules
    for rule in egress_rules:
        if isinstance(rule, dict) and 'description' in rule:
            rule_name = rule['description'].lower().replace(' ', '-') + '-egress'
            firewall_rule = resource.google_compute_firewall(
                rule_name,
                network=network,
                direction="EGRESS",
                allowed=[{
                    'IPProtocol': rule['protocol'],
                    'ports': rule['ports']  # This will usually be an empty list for egress rules
                }],
                destination_ranges=rule['ranges'],
                priority=1000,
                description=rule['description']
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



    for region, details in config['regions'].items():
        ssh_keys_metadata = f"{config['key_pair_name']}:{open(os.path.expanduser(config['path_to_key']), 'r').read().strip()}"
        az_count = 3 if details.get('az_mode', 'single-az') == 'multi-az' else 1
        azs = [f"{region}-a", f"{region}-b", f"{region}-c"][:az_count]

        for i, az in enumerate(azs):
            subnetwork_name = f"{config["cluster_name"]}-subnet-{region}-{i}"
            subnetwork = resource.google_compute_subnetwork(subnetwork_name,
                project=config['gcp_project_id'],
                name=f"{config["cluster_name"]}-subnet-{region}-{i}",
                ip_cidr_range=f"10.0.{i}.0/24",  # Example CIDR, should be planned according to IPAM
                region=region,
                network=network_name,
                private_ip_google_access=True,
                depends_on=[f"google_compute_network.{network_name}"] 
            )
            ts += subnetwork


        for i in range(details['nodes']):
            node_name = f"{config['cluster_name']}-scylla-node-{region}-{i}"
            disk_size_gb = details.get('disk_size_gb', 0)
            num_local_ssds = math.ceil(disk_size_gb / 375)
            disks = [{
                "device_name": f"local-ssd-{j}",
                "interface": "NVME",
            } for j in range(1, num_local_ssds + 1)]  # Include at least 1 local SSD

            node_instance = resource.google_compute_instance(
                node_name,
                name=node_name,
                project=config['gcp_project_id'],
                machine_type=details['scylla_node_type'],  # Define this in your config
                zone=f"{region}-a",  # Adjust zone based on your setup
                min_cpu_platform = "Intel Ice Lake",
                allow_stopping_for_update = "true",
                network_interface=[{
                    "network": network_name,
                    "subnetwork": f"{config['cluster_name']}-subnet-{region}-0",
                    "subnetwork_project": config['gcp_project_id'],
                    "access_config": [{}],
                }],
                boot_disk=[{
                    "initialize_params": {
                        "image": f"projects/scylla-images/global/images/scylladb-enterprise-{config['scylla_version']}",
                    },
                }],
                scratch_disk = disks,
                labels={
                    "name": f"{config['cluster_name']}-{region}-scylla-node-{i}",
                    "type": "scylla",
                    "project": config['cluster_name'],
                },
                metadata={
                    'ssh-keys': ssh_keys_metadata,  # Make sure to define this
                },
                service_account={
                    "email": "default",
                    "scopes": ["https://www.googleapis.com/auth/cloud-platform"]
                },
                # discard_local_ssd= "true",
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

                zone=f"{region}-a",  # Choose the zone, generally region followed by '-a', '-b', etc.
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
