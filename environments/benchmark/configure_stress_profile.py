import boto3
import configparser
import yaml

# File paths
scylla_servers_path = '../aws/ansible_install/scylla_servers.yml'
template_path = './templates/ott-audio-streaming.yaml.tpl'
output_path = './stress.yaml'

# Read the scylla_servers.yml file to extract the datacenter information
with open(scylla_servers_path, 'r') as file:
    scylla_servers_data = yaml.safe_load(file)
    # Assuming the datacenter info is in the first item's 'labels' under 'dc'
    datacenter = scylla_servers_data[0]['labels']['dc']

# Read the template file
with open(template_path, 'r') as file:
    template_content = file.read()

# Replace the 'datacenter' placeholder with the actual datacenter value
modified_content = template_content.replace('{{ datacenter }}', datacenter)

# Write the modified content to a new file
with open(output_path, 'w') as file:
    file.write(modified_content)

print(f"Modified template saved to: {output_path}")


## Configure cassandra stress command
# Assuming the variables.cfg is in a simple key=value format
def load_variables(cfg_path):
    variables = {}
    with open(cfg_path, 'r') as file:
        for line in file:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                # Remove any inline comments and extra quotes from the value, then strip leading/trailing whitespace
                clean_value = value.split("#")[0].strip().strip('\'"')
                variables[key.strip()] = clean_value
    return variables

# Fetch nodes addresses from AWS EC2 instances
def fetch_nodes_from_aws(custom_name, aws_region):
    session = boto3.session.Session(region_name=aws_region)
    ec2 = session.resource('ec2')
    instances = ec2.instances.filter(
        Filters=[
            {'Name': 'tag:Project', 'Values': [custom_name]},
            {'Name': 'tag:Type', 'Values': ['Scylla']}
        ]
    )
    nodes = [instance.public_dns_name for instance in instances]
    return nodes

def fetch_loaders_from_aws(custom_name, aws_region):
    session = boto3.session.Session(region_name=aws_region)
    ec2 = session.resource('ec2')
    instances = ec2.instances.filter(
        Filters=[
            {'Name': 'tag:Project', 'Values': [custom_name]},
            {'Name': 'tag:Type', 'Values': ['Loader']}
        ]
    )
    loader_nodes = [instance.public_dns_name for instance in instances]
    return loader_nodes
# Function to parse ott-audio-streaming.yaml and extract query names
def parse_yaml_for_queries(file_path):
    with open(file_path, 'r') as file:
        content = yaml.safe_load(file)
        queries = content['queries'] if 'queries' in content else []
    return queries

# Construct cassandra-stress command
def distribute_operations(read_ratio, queries):
    operations = {query: 1 for query in queries}  # Start with 1 operation per query
    total_assigned_ops = len(queries)  # One operation per query initially assigned
    additional_ops = read_ratio - total_assigned_ops
    
    # Distribute remaining operations based on the ratio
    while additional_ops > 0:
        for query in queries:
            if additional_ops <= 0:
                break
            operations[query] += 1
            additional_ops -= 1
    
    return operations

def construct_cassandra_stress_cmd(nodes, variables, queries):
    # Parse the ratio
    read_ratio, write_ratio = map(int, variables['ratio'].split(':'))
    
    # Starting with insert hardcoded to 2 operations per write
    total_write_ops = 2 * write_ratio
    
    # Distribute read operations among queries
    read_operations = distribute_operations(read_ratio, queries)
    
    ops_part = f"ops\(insert={total_write_ops}"
    for query, ops_count in read_operations.items():
        ops_part += f",{query}={ops_count}"
    ops_part += "\)"
    
    nodes_part = ",".join(nodes)
    cmd = f"cassandra-stress user profile=stress.yaml no-warmup cl=local_quorum {ops_part} n={variables['num_of_ops']} -rate threads={variables['num_threads']} fixed={variables['throttle']} -node {nodes_part} -mode native cql3"
    return cmd



# Assuming paths
variables_cfg_path = '../variables.cfg'  # Update this path as necessary

# Load variables from variables.cfg
variables_cfg = load_variables(variables_cfg_path)

# Extract 'custom_name' and 'aws_region' from loaded variables for AWS data fetching
custom_name = variables_cfg.get('custom_name')
aws_region = variables_cfg.get('aws_region')
original_throttle = int(variables_cfg['throttle'].replace('/s', ''))

# Check if 'custom_name' or 'aws_region' is missing and raise an exception if so
if not custom_name:
    raise ValueError("The 'custom_name' variable is missing from the configuration file.")
if not aws_region:
    raise ValueError("The 'aws_region' variable is missing from the configuration file.")

# Fetch AWS nodes
nodes = fetch_nodes_from_aws(custom_name, aws_region)
loader_nodes = fetch_loaders_from_aws(custom_name, aws_region)
num_nodes = len(loader_nodes)
adjusted_throttle = str(original_throttle // num_nodes) + '/s'
variables_cfg['throttle'] = adjusted_throttle

# Assuming you want to parse the queries from the generated YAML file after template processing
# If you're looking to parse from the template before processing, adjust the path accordingly.
output_path = './ott-audio-streaming.yaml'
queries = parse_yaml_for_queries(output_path)

# Construct and print the cassandra-stress command
cmd = construct_cassandra_stress_cmd(nodes, variables_cfg, queries)
print(cmd)


# Define the path to the .tpl file and the output path for the new YAML file
template_path = '../aws/ansible_install/benchmark_start_load.yml.tpl'
output_yaml_path = '../aws/ansible_install/benchmark_start_load.yml'

# Read the .tpl file
with open(template_path, 'r') as file:
    template_content = file.read()

# Replace the placeholder with the generated Cassandra stress command
modified_content = template_content.replace('{{ command }}', cmd)

# Write the modified content to a new YAML file
with open(output_yaml_path, 'w') as file:
    file.write(modified_content)

#print(f"New YAML file created at: {output_yaml_path}")