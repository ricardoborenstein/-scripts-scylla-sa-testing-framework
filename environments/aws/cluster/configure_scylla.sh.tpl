#!/bin/bash
set -e

CLUSTER_NAME="${cluster_name}"
SEED_IP="${seed_ip}"
LISTEN_ADDRESS="${listen_address}"
RPC_ADDRESS="${rpc_address}"

# Update scylla.yaml file
sudo sed -i "s/^#cluster_name: .*/cluster_name: '$CLUSTER_NAME'/" /etc/scylla/scylla.yaml
sudo sed -i "s/- seeds: \".*\"/- seeds: \"$SEED_IP\"/" /etc/scylla/scylla.yaml
sudo sed -i "s/^listen_address:.*/listen_address: $LISTEN_ADDRESS/" /etc/scylla/scylla.yaml
sudo sed -i "s/^rpc_address:.*/rpc_address: $RPC_ADDRESS/" /etc/scylla/scylla.yaml

sudo cat > /etc/scylla/object-storage-config-file.yaml <<EOF
endpoints:
  - name: s3.amazonaws.com
    https: True
    port: 443
    aws_region: eu-west-1
    aws_access_key_id: secret
    aws_secret_access_key: secret
EOF

# endpoint_snitch
# Additional configuration commands...
