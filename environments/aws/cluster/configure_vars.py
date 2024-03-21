import re
import boto3
# Define file paths
CFG_FILE = "./../../variables.cfg"
VAR_TEMPLATE_FILE = "./variables.tf.tpl"
VAR_OUTPUT_FILE = "./variables.tf"

def find_ubuntu_ami(region, version='22.04'):
    """
    Find the latest Ubuntu 22.04 AMI in a specific AWS region.

    :param region: The AWS region to search in.
    :param version: Ubuntu version (default is 22.04).
    :return: The AMI ID of the latest Ubuntu 22.04 image.
    """
    ec2 = boto3.client('ec2', region_name=region)

    filters = [
        {'Name': 'name', 'Values': [f'ubuntu/images/hvm-ssd/ubuntu-jammy-{version}-amd64-server-*']},
        {'Name': 'state', 'Values': ['available']},
        {'Name': 'architecture', 'Values': ['x86_64']},
        {'Name': 'root-device-type', 'Values': ['ebs']}
    ]

    amis = ec2.describe_images(Filters=filters, Owners=['099720109477'])  # Canonical's owner ID
    amis = sorted(amis['Images'], key=lambda x: x['CreationDate'], reverse=True)

    if amis:
        return amis[0]['ImageId']
    else:
        return None
    
def find_scylla_ami(region, version=None):
    """
    Find the latest Scylla AMI in a specific AWS region. If a version is specified, find the AMI for that version.

    :param region: The AWS region to search in.
    :param version: Scylla version (optional). If not specified, finds the latest version.
    :return: The AMI ID of the latest Scylla image or the specified version.
    """
    ec2 = boto3.client('ec2', region_name=region)
    
    if version:
        name_pattern = f'ScyllaDB*{version}*'
    else:
        name_pattern = 'ScyllaDB*-amd64-*'
    
    filters = [
        {'Name': 'name', 'Values': [name_pattern]},
        {'Name': 'state', 'Values': ['available']},
        {'Name': 'architecture', 'Values': ['x86_64']},
        {'Name': 'root-device-type', 'Values': ['ebs']}
    ]

    # Replace with Scylla's owner ID if known, or remove if it's under different ownerships
    amis = ec2.describe_images(Filters=filters, Owners=['158855661827'])
    amis = sorted(amis['Images'], key=lambda x: x['CreationDate'], reverse=True)

    if amis:
        return amis[0]['ImageId']
    else:
        return None
    
# Function to clean variable values
def clean_value(value):
    value = value.split('#')[0].strip()  # Remove everything after "#" to ignore comments
    value = value.strip('"').strip("'")  # Remove any surrounding quotes
    return value

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

if "aws_region" in variables:
    ami_id = find_ubuntu_ami(variables["aws_region"])
    if ami_id:
        variables["ami_id"] = ami_id
        print(f"Found Ubuntu 22.04 AMI ID for region {variables['aws_region']}: {ami_id}")
    else:
        print(f"Unable to find Ubuntu 22.04 AMI for region {variables['aws_region']}.")
else:
    print("AWS region not specified in configuration.")

if "aws_region" in variables:
    scylla_ami_id = find_scylla_ami(variables["aws_region"],variables["scylla_version"])
    if scylla_ami_id:
        variables["scylla_ami_id"] = scylla_ami_id
        print(f"Found Scylla AMI ID for region {variables['aws_region']}: {scylla_ami_id}")
    else:
        print(f"Unable to Scylla AMI for region {variables['aws_region']}.")
else:
    print("AWS region not specified in configuration.")
# Process the template file
with open(VAR_TEMPLATE_FILE, "r") as template_file:
    content = template_file.read()
    for key, value in variables.items():
        # Directly replace placeholders in the template without escaping
        # Ensure to trim the variable values to remove any leading/trailing whitespace
        trimmed_value = value.strip()
        content = re.sub(f"\\{{{{ {key} \\}}}}", trimmed_value, content)

# Write the updated content to the output file
with open(VAR_OUTPUT_FILE, "w") as output_file:
    output_file.write(content)

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