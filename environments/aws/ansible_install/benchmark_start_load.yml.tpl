- name: Initiate ingestion for benchmark
  hosts: aws_loader
  tasks:
    - name: Copy Cassandra Stress Profile to loader servers
      copy:
        src: ../../benchmark/stress.yaml
        dest: stress.yaml
    - name: Start cassandra-stress population on all loaders in parallel
      shell: |
        {{ insert_command }}
    - name: Start cassandra-stress on all loaders in parallel
      shell: |
        {{ command }}        