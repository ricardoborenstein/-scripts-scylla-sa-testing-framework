import boto3
import configparser
import yaml
import re

# File paths
scylla_servers_path = '../aws/ansible_install/scylla_servers.yml'

insert_stress_output_path = './populate'
# Read the scylla_servers.yml file to extract the datacenter information


## Configure cassandra stress command
# Assuming the variables.cfg is in a simple key=value format
def load_variables_from_yaml(yaml_path):
    with open(yaml_path, 'r') as file:
        variables = yaml.safe_load(file)
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
    
    ops_part = f"\"ops\\(insert={total_write_ops}"
    for query, ops_count in read_operations.items():
        ops_part += f",{query}={ops_count}"
    ops_part += "\\)\""
    
    nodes_part = ",".join(nodes)
    cmd = f"cassandra-stress user profile=stress.yaml no-warmup cl=local_quorum {ops_part} duration=24h -rate threads={variables['num_threads']} fixed={variables['throttle']} -node {nodes_part} -mode native cql3"
    return cmd

def construct_insert_only_cassandra_stress_cmd(nodes, variables):
    # Directly use the write operations count for inserts
    # Constructing the ops part of the command specifically for insert operations
    ops_part = "ops\\(insert=1\\)"
    num_ops = str(round(int(variables['num_of_ops']) // len(nodes)))
    print("num_ops ",str(round(int(variables['num_of_ops']) // len(nodes))))
    nodes_part = ",".join(nodes)
    cmd = f"cassandra-stress user profile=stress.yaml no-warmup cl=local_quorum {ops_part} n={num_ops} -rate threads={variables['num_threads']} fixed={variables['throttle']} -node {nodes_part} -mode native cql3"
    return cmd

def parse_stress_template(template_path):
    with open(template_path, 'r') as file:
        data = yaml.safe_load(file)

    table_definition = data['table_definition']
    primary_key_pattern = r"PRIMARY KEY \(\((.*?)\)"
    match = re.search(primary_key_pattern, table_definition, re.DOTALL)
    partition_keys = [key.strip() for key in match.group(1).split(',')] if match else []

    column_specs = data.get('columnspec', [])
    for spec in column_specs:
        spec['is_partition_key'] = spec['name'] in partition_keys

    return column_specs, data

def adjust_population_range(column_specs, num_loaders):
    adjusted_specs = []
    regex_pattern = r"(\w+)\s*\(\s*(-?\d+)\s*\.\.\s*(-?\d+)\s*\)"  # Regex to include negative numbers

    for spec in column_specs:
        new_spec = {'name': spec['name']}  # Always include the name
        if 'population' in spec:
            if 'is_partition_key' in spec and spec['is_partition_key']:
                match = re.match(regex_pattern, spec['population'])
                if match:
                    pop_type, start, end = match.groups()
                    start, end = int(start), int(end)
                    total_range = end - start + 1
                    range_per_loader = total_range // num_loaders
                    remainder = total_range % num_loaders

                    new_ranges = []
                    current_start = start
                    for i in range(num_loaders):
                        current_end = current_start + range_per_loader - 1
                        if i < remainder:
                            current_end += 1
                        new_ranges.append(f"{pop_type}({current_start}..{current_end})")
                        current_start = current_end + 1

                    new_spec['population'] = new_ranges  # Adjusted ranges replace the original population
                else:
                    new_spec['population'] = [spec['population']] * num_loaders  # Non-matching but partition key, replicate original
            else:
                new_spec['population'] = [spec['population']] * num_loaders  # Non-partition keys, replicate original
        adjusted_specs.append(new_spec)
    
    return adjusted_specs



def create_populate_files(base_output_path, num_loaders, adjusted_specs, base_data, datacenter):
    for i in range(num_loaders):
        loader_data = dict(base_data)  # Deep copy of the base data
        loader_data['columnspec'] = [
            {k: (v[i] if k == 'population' else v) for k, v in spec.items()} for spec in adjusted_specs
        ]

        if 'keyspace_definition' in loader_data:
            loader_data['keyspace_definition'] = loader_data['keyspace_definition'].replace('{{ datacenter }}', datacenter)

        file_path = f"{base_output_path}_loader{i+1}.yaml"
        with open(file_path, 'w') as file:
            yaml.safe_dump(loader_data, file, default_flow_style=False)
        print(f"Configuration file for loader {i+1} saved to: {file_path}")


# This should be adjusted so that population for non-partition keys doesn't replicate or divide among loaders.


def construct_playbook(loader_nodes, template_path, output_path, cmd, insert_cmd):
    with open(template_path, 'r') as file:
        template_content = file.read()

    # Generate the tasks for copying populate.yaml files
    populate_tasks_content = ""
    for i, loader in enumerate(loader_nodes, start=1):
        populate_tasks_content += f"""
  - name: Copy populate_{i}.yaml to loader {i}
    copy:
      src: ../../benchmark/populate_loader{i}.yaml
      dest: ./stress.yaml
    delegate_to: {loader}"""

    # Properly format commands to maintain YAML structure
    formatted_cmd = '\n        '.join(cmd.split('\n'))  # Ensures new lines in cmd start correctly indented
    formatted_insert_cmd = '\n        '.join(insert_cmd.split('\n'))  # Same for insert_cmd

    # Replace the placeholders in the template with the generated tasks and commands
    final_content = template_content.replace('{{ insert_populate_tasks_here }}', populate_tasks_content.strip())
    final_content = final_content.replace('{{ command }}', formatted_cmd)
    final_content = final_content.replace('{{ insert_command }}', formatted_insert_cmd)

    with open(output_path, 'w') as file:
        file.write(final_content)
    return output_path



# Assuming paths
variables_cfg_path = '../variables.yml'  # Update this path as necessary

# Load variables from variables.cfg
variables_cfg = load_variables_from_yaml(variables_cfg_path)

# Extract 'custom_name' and 'aws_region' from loaded variables for AWS data fetching
cluster_name = variables_cfg['cluster_name']
aws_key_pair_name = variables_cfg['aws_key_pair_name']
cassandra_stress_config = variables_cfg['cassandra-stress']
original_throttle = int(cassandra_stress_config['throttle'].replace('/s', ''))
template_path = f'./templates/{cassandra_stress_config['template']}.yaml.tpl'
benchmark_output_path = f'././{cassandra_stress_config['template']}.yaml'

def process_regions(variables):
    all_nodes = []
    all_loaders = []
    for region, details in variables['regions'].items():
        region_name = region  # e.g., 'us-east-1'
        nodes = fetch_nodes_from_aws(variables['cluster_name'], region_name)
        loaders = fetch_loaders_from_aws(variables['cluster_name'], region_name)
        all_nodes.extend(nodes)
        all_loaders.extend(loaders)
        print(f"Region: {region_name}, Nodes: {nodes}, Loaders: {loaders}")
    return all_nodes, all_loaders

def process_template(template_path, output_path, datacenter):
    with open(template_path, 'r') as file:
        template = file.read()
    modified_content = template.replace('{{ datacenter }}', datacenter)
    with open(output_path, 'w') as file:
        file.write(modified_content)
    print(f"Template processed and saved to: {output_path}")


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

# Fetch AWS nodes
nodes, loaders = process_regions(variables_cfg)
num_nodes = len(loaders)
adjusted_throttle = str(original_throttle // num_nodes) + '/s'
cassandra_stress_config['throttle'] = adjusted_throttle

# Assuming you want to parse the queries from the generated YAML file after template processing
# If you're looking to parse from the template before processing, adjust the path accordingly.
output_path = f'./{cassandra_stress_config['template']+".yaml"}'
queries = parse_yaml_for_queries(output_path)

# Construct and print the cassandra-stress command
insert_cmd = construct_insert_only_cassandra_stress_cmd(nodes, cassandra_stress_config)
cmd = construct_cassandra_stress_cmd(nodes, cassandra_stress_config, queries)

print(cmd)
print(insert_cmd)

column_specs ,base_data= parse_stress_template(template_path)
adjusted_specs = adjust_population_range(column_specs, len(loaders))
print("Number of Loaders: ",len(loaders))
create_populate_files(insert_stress_output_path, len(loaders), adjusted_specs, base_data,datacenter)

# Define the path to the .tpl file and the output path for the new YAML file
template_path = '../aws/ansible_install/benchmark_start_load.yml.tpl'
output_yaml_path = '../aws/ansible_install/benchmark_start_load.yml'

constructed_path = construct_playbook(loaders, template_path, output_yaml_path,cmd,insert_cmd)
#print(f"New YAML file created at: {output_yaml_path}")
    
