import re

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



# # Process the template file
# with open(VPC_TEMPLATE_FILE, "r") as template_file:
#     content = template_file.read()
#     for key, value in variables.items():
#         # Directly replace placeholders in the template without escaping
#         # Ensure to trim the variable values to remove any leading/trailing whitespace
#         trimmed_value = value.strip()
#         content = re.sub(f"\\{{{{ {key} \\}}}}", trimmed_value, content)

# # Write the updated content to the output file
# with open(VPC_OUTPUT_FILE, "w") as output_file:
#     output_file.write(content)