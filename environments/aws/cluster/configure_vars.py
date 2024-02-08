import re

# Define file paths
CFG_FILE = "./../../variables.cfg"
TEMPLATE_FILE = "./variables.tf.tpl"
OUTPUT_FILE = "./variables.tf"
# Load variables from the cfg file
variables = {}
with open(CFG_FILE, "r") as cfg_file:
    for line in cfg_file:
        if '=' in line:
            parts = line.strip().split('=', 1)  # Split by the first '=' found
            key = parts[0].strip()  # Remove any leading/trailing whitespace from the key
            value = parts[1].strip().strip('"')  # Remove whitespace and quotes from the value
            variables[key] = value

# Process the template file
with open(TEMPLATE_FILE, "r") as template_file:
    content = template_file.read()
    for key, value in variables.items():
        # Directly replace placeholders in the template without escaping
        content = re.sub(f"\\{{{{ {key} \\}}}}", value, content)

# Write the updated content to the output file
with open(OUTPUT_FILE, "w") as output_file:
    output_file.write(content)