- name: YCSB Prepare
  hosts: "scylla_seed"
  user: "ubuntu"
  roles:
    - { role: cassandra-ycsb-prepare }

- name: Run stress
  hosts: gcp_loader
  user: "ubuntu"
  vars:
    iteration: 0
    server: "scylla"
    prepare: true
    workload: workloada
    load_name: "ricardo-testing"
    output_format: "ycsb.{{{{ workload }}}}.{{{{ load_name }}}}.{{{{ ansible_date_time.date }}}}"
    output_file: "{{{{ output_format }}}}"
    remote_path: /home/ubuntu/
    home_path: /tmp/cassandra-results/
    stress_options:
      sleep_between_runs: 1
      threads: {num_threads}
    clean_data: false
    profile_dir: /tmp/cassandra-stress-profiles/
    prepare_options: ""
    run_options: ""
    seq_populate: {num_of_rows}

  tasks:
    - name: Gather facts
      setup:

    - name: Copy YCSB workload template to remote host
      copy:
        src: ../../benchmark/templates/ycsb-workload
        dest: /home/ubuntu/ycsb-workload.yaml

    - set_fact:
        index: "{{{{ ansible_host.index }}}}"
    
    - name: Set range start for sequence population
      set_fact:
        range_start: "{{{{ 1 + (seq_populate | int) * (index | int) }}}}"
      when: seq_populate is defined

    - name: Set range end for sequence population
      set_fact:
        range_end: "{{{{ (seq_populate | int) * (1 + (index | int)) }}}}"
      when: seq_populate is defined

    - name: Set range for sequence population
      set_fact:
        range: "{{{{ range_start }}}}..{{{{ range_end }}}}"
      when: seq_populate is defined
    
    - debug:
        msg: "Client key range: {{{{ range }}}}"
      when: seq_populate is defined
    
    - set_fact:
        loader_ip: "{{{{ ansible_default_ipv4.address }}}}"

    - debug:
        msg: "Loader IP is {{{{ loader_ip }}}}"

    - name: Collect internal IPs of Scylla nodes
      set_fact:
        ip_list: "{{{{ groups['scylla'] | map('extract', hostvars, 'ansible_host') | join(',') }}}}"

    - debug:
        msg: "IP list is {{{{ ip_list }}}}"
    
    - name: Get total number of CPUs
      shell: "lscpu | grep '^CPU(s):' | awk '{{{{print $2}}}}'"
      register: total_cpus_result

    - name: Set total number of CPUs
      set_fact:
        num_cpus: "{{{{ total_cpus_result.stdout | int }}}}"

    - name: Setting network IRQ affinity to CPU0
      shell: |
        for irq in $(cat /proc/interrupts | grep eth0 | cut -d":" -f1); do
          echo 1 | sudo tee /proc/irq/$irq/smp_affinity;
        done
      when: num_cpus is defined
      become: true

    - name: Kill Java if already running
      shell: pkill java
      become: true
      ignore_errors: true
    
    - set_fact:
        log_file: "{{{{ remote_path }}}}{{{{ output_file }}}}.{{{{ zone }}}}.{{{{ loader_ip }}}}"

    - name: Run YCSB Populate on each CPU 
      shell: |
        for i in $(seq 0 $(({{{{ num_cpus }}}} - 1))); do
          taskset -c $i sh /home/ubuntu/YCSB/bin/ycsb.sh load scylla -P /home/ubuntu/ycsb-workload.yaml -s -threads {{{{ stress_options.threads }}}} -p scylla.hosts={{{{ ip_list }}}} -p insertstart=$(( {{{{ range_start }}}} + i * {{{{ seq_populate }}}} / {{{{ num_cpus }}}} )) -p insertcount=$(( {{{{ seq_populate }}}} / {{{{ num_cpus }}}} )) {{{{ run_options }}}} > {{{{ remote_path }}}}{{{{ output_file }}}}.$i.data  &
        done
        wait
      when: seq_populate is defined
    
    - name: Run YCSB on each CPU
      shell: |
        for i in $(seq 0 $(({{{{ num_cpus }}}} - 1))); do
          taskset -c $i sh /home/ubuntu/YCSB/bin/ycsb.sh run scylla -P /home/ubuntu/ycsb-workload.yaml -s -threads {{{{ stress_options.threads }}}} -p scylla.hosts={{{{ ip_list }}}} > {{{{ remote_path }}}}{{{{ output_file }}}}.$i.data &
        done
        wait
      when: seq_populate is defined
