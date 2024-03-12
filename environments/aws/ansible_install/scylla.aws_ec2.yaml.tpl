---
plugin: aws_ec2

regions:
 - {{ aws_region }}

filters:
 instance-state-name: 'running'
 tag:Project:
   - '{{ custom_name }}'

groups:
  scylla:   (tags['Type'] is defined and tags['Type'] == 'Scylla')
  aws_loader: (tags['Type'] is defined and tags['Type'] == 'Loader')
  aws_monitor: (tags['Type'] is defined and tags['Type'] == 'Monitoring')

keyed_groups:
  # Add hosts to tag_Name_Value groups for each Name/Value tag pair
  - prefix: tag
    key: tags
