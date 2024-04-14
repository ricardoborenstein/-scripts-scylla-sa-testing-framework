import boto3
import configparser
import yaml
import re

# File paths
scylla_servers_path = '../aws/ansible_install/scylla_servers.yml'
template_path = './templates/ott-audio-streaming.yaml.tpl'
benchmark_output_path = '././ott-audio-streaming.yaml'
insert_stress_output_path = './populate'
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
with open(benchmark_output_path, 'w') as file:
    file.write(modified_content)
# Write the modified content to a new populate.yml
with open(insert_stress_output_path, 'w') as file:
    file.write(insert_stress_output_path)

print(f"Modified template saved to: {benchmark_output_path}")


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
    nodes = [
        instance.public_dns_name for instance in instances 
        if instance.public_dns_name  # This filters out any instances without a public DNS name
    ]  
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
    loader_nodes = [
        instance.public_dns_name for instance in instances 
        if instance.public_dns_name  # This filters out any instances without a public DNS name
    ]   
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
    
    ops_part = f"ops\\(insert={total_write_ops}"
    for query, ops_count in read_operations.items():
        ops_part += f",{query}={ops_count}"
    ops_part += "\\)"
    
    nodes_part = ",".join(nodes)
    cmd = f"cassandra-stress user profile=stress.yaml no-warmup cl=local_quorum {ops_part} duration=24h -rate threads={variables['num_threads']} fixed={variables['throttle']} -node {nodes_part} -mode native cql3"
    return cmd

def construct_insert_only_cassandra_stress_cmd(nodes, variables):
    # Directly use the write operations count for inserts
    # Constructing the ops part of the command specifically for insert operations
    ops_part = "ops\\(insert=1\\)"

    nodes_part = ",".join(nodes)
    cmd = f"cassandra-stress user profile=stress.yaml no-warmup cl=local_quorum {ops_part} n={variables['num_of_ops']} -rate threads={variables['num_threads']} fixed={variables['throttle']} -node {nodes_part} -mode native cql3"
    return cmd


def parse_stress_template(template_path):
    with open(template_path, 'r') as file:
        data = yaml.safe_load(file)

    # Extract table definition and partition keys
    table_definition = data['table_definition']
    primary_key_pattern = r"PRIMARY KEY \(\((.*?)\)"
    match = re.search(primary_key_pattern, table_definition, re.DOTALL)

    if match:
        partition_keys_string = match.group(1)
        partition_keys = [key.strip() for key in partition_keys_string.split(',')]
    else:
        print("No PRIMARY KEY definition found.")
        partition_keys = []

    column_specs = data.get('columnspec', [])
    partition_key_populations = {}

    for column in column_specs:
        if column['name'] in partition_keys:
            partition_key_populations[column['name']] = column.get('population', 'Unknown')

    return partition_keys, column_specs, partition_key_populations

def adjust_population_range(column_specs, num_loaders):
    adjusted_specs = []

    for spec in column_specs:
        name = spec.get('name')
        population = spec.get('population')

        if population:
            pattern = r"(\w+)\((\d+)\.\.(\d+)\)"  # Matches strings like "UNIFORM(1..100)"
            match = re.match(pattern, population)

            if match:
                pop_type, start, end = match.groups()
                start, end = int(start), int(end)

                step = (end - start + 1) // num_loaders
                adjusted_population = f"{pop_type}({start}..{end}/{num_loaders})"  # Example adjustment
                spec['adjusted_population'] = adjusted_population

        adjusted_specs.append(spec)

    return adjusted_specs

import yaml

def create_populate_files(base_output_path, num_loaders, primary_keys, adjusted_specs, template_content):
    """
    Generates YAML files for loader-specific configurations, adjusting column populations.
    Args:
    - base_output_path: Base path for output files.
    - num_loaders: Number of loader files to create.
    - primary_keys: Primary keys from the table definition.
    - adjusted_specs: Adjusted column specifications.
    - template_content: The original YAML template content as a string.
    """
    for loader_index in range(num_loaders):
        modified_data = yaml.safe_load(template_content)
        # Adjust column specifications for each loader
        for spec in adjusted_specs:
            if 'adjusted_population' in spec:
                pattern = r"(\w+)\((\d+)\.\.(\d+)/" + str(num_loaders) + r"\)"
                match = re.match(pattern, spec['adjusted_population'])
                if match:
                    pop_type, start, end = match.groups()
                    range_per_loader = (int(end) - int(start) + 1) // num_loaders
                    loader_start = int(start) + range_per_loader * loader_index
                    loader_end = loader_start + range_per_loader - 1
                    if loader_index == num_loaders - 1:  # Ensure last loader covers any remaining range
                        loader_end = end
                    spec['population'] = f"{pop_type}({loader_start}..{loader_end})"
        # Update the template with loader-specific column specs
        modified_data['columnspec'] = [spec for spec in adjusted_specs if 'name' in spec]

        # Write to a separate file for each loader
        output_file_path = f"{base_output_path}_{loader_index+1}.yaml"
        with open(output_file_path, 'w') as file:
            yaml.dump(modified_data, file, default_flow_style=False)

        print(f"Config for loader {loader_index + 1} saved to: {output_file_path}")



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
print(loader_nodes)
num_nodes = len(loader_nodes)
adjusted_throttle = str(original_throttle // num_nodes) + '/s'
variables_cfg['throttle'] = adjusted_throttle

# Assuming you want to parse the queries from the generated YAML file after template processing
# If you're looking to parse from the template before processing, adjust the path accordingly.
output_path = './ott-audio-streaming.yaml'
queries = parse_yaml_for_queries(output_path)

# Construct and print the cassandra-stress command
insert_cmd = construct_insert_only_cassandra_stress_cmd(nodes, variables_cfg)
cmd = construct_cassandra_stress_cmd(nodes, variables_cfg, queries)

print(cmd)

primary_keys, column_specs, partition_key_populations = parse_stress_template(template_path)
adjusted_specs = adjust_population_range(column_specs, len(loader_nodes))
print("Number of Loaders: ",len(loader_nodes))
create_populate_files(insert_stress_output_path, len(loader_nodes), primary_keys, adjusted_specs, template_content)

# Define the path to the .tpl file and the output path for the new YAML file
template_path = '../aws/ansible_install/benchmark_start_load.yml.tpl'
output_yaml_path = '../aws/ansible_install/benchmark_start_load.yml'

# Read the .tpl file
with open(template_path, 'r') as file:
    benchmark_template_content = file.read()

# Replace the placeholder with the generated Cassandra stress command
modified_content = benchmark_template_content.replace('{{ insert_command }}', insert_cmd).replace('{{ command }}', cmd)

# Write the modified content to a new YAML file
with open(output_yaml_path, 'w') as file:
    file.write(modified_content)

#print(f"New YAML file created at: {output_yaml_path}")