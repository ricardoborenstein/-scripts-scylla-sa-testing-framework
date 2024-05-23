import yaml

# Read the YAML configuration file
with open('../variables.yml', 'r') as file:
    config = yaml.safe_load(file)

# Extract values from the configuration file
cluster_name = config['cluster_name']
num_threads = config['ycsb']['num_threads']
num_of_rows = config['ycsb']['num_of_rows']
throttle = config['ycsb']['throttle']
ratio = config['ycsb']['ratio']
template = config['ycsb']['template']
scylla_login = config['ycsb']['scylla_login']
scylla_password = config['ycsb']['scylla_password']

# Read the YCSB template file
with open('ycsb.yml.tpl', 'r') as file:
    ycsb_template = file.read()

# Replace variables in the template
ycsb_config = ycsb_template.replace('{num_threads}', str(num_threads)) \
    .replace('{num_of_rows}', str(num_of_rows)) \
    .replace('{template}', template) \
    .replace('{scylla_login}', scylla_login) \
    .replace('{scylla_password}', scylla_password)\
    .replace('{cluster_name}', cluster_name)\
    .replace('{throttle}', throttle)\


# Write the new YCSB configuration to a file
with open('../gcp/ansible_install/ycsb.yml', 'w') as file:
    file.write(ycsb_config)

print("YCSB configuration file has been generated successfully.")


