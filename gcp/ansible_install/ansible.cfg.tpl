[defaults]
inventory = ./inventory
pipelining = true
remote_user = ubuntu
stdout_callback = yaml
callbacks_enabled = profile_tasks
host_key_checking = False
private_key_file = {{ path_to_private }} 

[ssh_connection]
identityonly = yes
