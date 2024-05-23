plugin: gcp_compute
projects:
  - {{gcp_project_id}}
filters:
 # - "status = RUNNING"
  - labels.project:{{cluster_name}}
auth_kind: application
#service_account_email: "/Users/ricardo/.config/gcloud/application_default_credentials.json"

scopes:
  - 'https://www.googleapis.com/auth/cloud-platform'

hostnames:
  - name

compose:
  ansible_host: networkInterfaces[0].accessConfigs[0].natIP

groups:
  scylla:   (labels['type'] is defined and labels['type'] == 'scylla')
  loader: (labels['type'] is defined and labels['type'] == 'loader')
  monitor: (labels['type'] is defined and labels['type'] == 'monitoring')
  scylla_nonseed: (labels['group'] is defined and labels['group'] == 'nonseed')
  scylla_seed: (labels['group'] is defined and labels['group'] == 'seed')
  scylla_seed2: (labels['group'] is defined and labels['group'] == 'seed2')
