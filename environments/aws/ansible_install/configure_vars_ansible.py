import re
import requests
import yaml
from packaging import version
from pathlib import Path
# Define file paths
CFG_FILE = "./../../variables.cfg"
ANSIBLE_INVENTORY_TEMPLATE_FILE = "./scylla.aws_ec2.yaml.tpl"
ANSIBLE_INVENTORY_OUTPUT_FILE = "./inventory/scylla.aws_ec2.yaml"
ANSIBLE_CONFIG_TEMPLATE_FILE = "./ansible.cfg.tpl"
ANSIBLE_CONFIG_OUTPUT_FILE = "./ansible.cfg"
ANSIBLE_GET_MONITORING_CONFIG_FILE = "./get_monitoring_config.yml.tpl"
ANSIBLE_GET_MONITORING_CONFIG_OUTPUT_FILE = "./get_monitoring_config.yml"

# Function to clean variable values
def clean_value(value):
    value = value.split('#')[0].strip()  # Remove everything after "#" to ignore comments
    value = value.strip('"').strip("'")  # Remove any surrounding quotes
    return value

def write_output_file(PATH, contents):
    # Write the updated content to the output file
    with open(PATH, "w") as output_file:
        output_file.write(contents)

def load_template_file(PATH, variables):
    # Process the template file
    with open(PATH, "r") as template_file:
        content = template_file.read()
        for key, value in variables.items():
            # Directly replace placeholders in the template without escaping
            # Ensure to trim the variable values to remove any leading/trailing whitespace
            trimmed_value = value.strip()
            content = re.sub(f"\\{{{{ {key} \\}}}}", trimmed_value, content)
        return content

# Load variables from the cfg file
variables = {}
with open(CFG_FILE, "r") as cfg_file:
    for line in cfg_file:
        if '=' in line:
            parts = line.strip().split('=', 1)  # Split by the first '=' found
            key = parts[0].strip()  # Remove any leading/trailing whitespace from the key
            value = clean_value(parts[1].strip())  # Clean the value using the defined function
            variables[key] = value

# Check the 'availability_zone' variable and set 'subnet_count' accordingly
#print(variables.get("availability_zone"))
if variables.get("availability_zone") == "Multi":
    variables["subnet_count"] = "3"
elif variables.get("availability_zone") == "Single":
    variables["subnet_count"] = "1"
else:
    # Default or error handling if needed
    print("Warning: 'availability_zone' not set to 'Multi' or 'Single'. Please check your variables.cfg.")

content = load_template_file(ANSIBLE_INVENTORY_TEMPLATE_FILE, variables)
write_output_file(ANSIBLE_INVENTORY_OUTPUT_FILE, content)

content = load_template_file(ANSIBLE_CONFIG_TEMPLATE_FILE, variables)
write_output_file(ANSIBLE_CONFIG_OUTPUT_FILE, content)

content = load_template_file(ANSIBLE_GET_MONITORING_CONFIG_FILE, variables)
write_output_file(ANSIBLE_GET_MONITORING_CONFIG_OUTPUT_FILE, content)



### Getting Latest Monitoring Version
def get_latest_tag(repo_owner, repo_name):
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/tags"
    response = requests.get(api_url)
    tags = response.json()
    version_tags = [tag['name'] for tag in tags]
    semantic_versions = [ver for ver in version_tags if ver.replace(f"{repo_name}-", "").replace("scylla-monitoring-", "").replace('v', '').replace('_', '.').count('.') == 2]
    semantic_versions.sort(key=lambda x: version.parse(x.replace(f"{repo_name}-", "").replace("scylla-monitoring-", "").replace('v', '').replace('_', '.')))
    return semantic_versions[-1] if semantic_versions else "No valid semantic versions found."

# Fetch the latest tag
latest_tag = get_latest_tag("scylladb", "scylla-monitoring")
if latest_tag == "No valid semantic versions found.":
    print(latest_tag)
    exit()

# Construct the new archive URL with the latest tag
new_url = f"https://github.com/scylladb/scylla-monitoring/archive/refs/tags/{latest_tag}.tar.gz"

# Path to the playbook file
playbook_file_path = Path('./install_monitoring.yml')

# Load the existing content of the playbook
with open(playbook_file_path, 'r') as file:
    playbook_content = yaml.safe_load(file)

# Update the scylla_monitoring_archive_url in the playbook content
# This part needs to be adapted based on the actual structure of your YAML.
# For demonstration, I'm assuming it's a direct key under some task's vars. You might need to navigate the structure accordingly.
updated = False
for task in playbook_content:
    if 'vars' in task and 'scylla_monitoring_archive_url' in task['vars']:
        task['vars']['scylla_monitoring_archive_url'] = new_url
        updated = True
        break

if updated:
    # Write the updated content back to the file
    with open(playbook_file_path, 'w') as file:
        yaml.dump(playbook_content, file)
  #  print("Updated install_monitoring.yml with the latest Scylla Monitoring archive URL.")
# else:
  #  print("Did not find scylla_monitoring_archive_url in the playbook.")