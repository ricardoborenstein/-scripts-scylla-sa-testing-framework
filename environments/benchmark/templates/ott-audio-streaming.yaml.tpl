# cassandra-stress user profile=stress.yaml no-warmup cl=local_quorum ops\(insert=2,simple1=1,simple2=1,simple3=1,simple4=1,simple5=1,simple6=1,simple7=1\) n=1B -rate threads=128 fixed=60000/s -node node-0.aws-us-east-1.e86fbe94119db3f6881a.clusters.scylla.cloud,node-1.aws-us-east-1.e86fbe94119db3f6881a.clusters.scylla.cloud -mode native cql3 user=scylla password=n3vOd5rLi4xSjwg 
keyspace: audio_playtime

keyspace_definition: |
  CREATE KEYSPACE audio_playtime WITH replication = { 'class': 'NetworkTopologyStrategy', '{{ datacenter }}': 3};
# Define the schema
table: device_story_playtime

table_definition: |
  CREATE TABLE audio_playtime.device_story_playtime (
      device_id text,
      bucket_id text,
      show_id text,
      story_id text,
      duration float,
      playtime int,
      seq_no int,
      updated_at timestamp,
      PRIMARY KEY ((device_id, bucket_id ),show_id, story_id)
  ) WITH CLUSTERING ORDER BY ( show_id asc,story_id ASC)
      AND bloom_filter_fp_chance = 0.01
      AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
      AND comment = ''
      AND compaction = {'class': 'IncrementalCompactionStrategy'};

columnspec:
  - name: device_id
    population: UNIFORM(1..100M)  # Simulate a wide range of device IDs
  - name: bucket_id
    population: UNIFORM(1..1825)  # Simulate a range of 5y - bucketing by dd-yyyy
  - name: show_id
    population: UNIFORM(1..1M)  # Simulate a variety of show IDs
  - name: story_id
    population: UNIFORM(1..100000)  # Simulate a large number of story IDs
  - name: duration
    population: GAUSSIAN(60..360)  # Assume duration ranges from 1 to 6 minutes
  - name: playtime
    population: GAUSSIAN(0..360)  # Assume playtime ranges similarly
  - name: seq_no
    size: fixed(10)  # Assuming a fixed sequence number for simplicity
  - name: updated_at
    population: uniform(100000..10000000)  # Generate time-based UUIDs for timestamps

queries:
  simple1:
    cql: select * from device_story_playtime where device_id = ? and bucket_id  = ? limit 100;
    fields: samerow
  simple2:
    cql: select * from device_story_playtime where device_id = ? and bucket_id  = ? and show_id = ?
    fields: samerow
  simple3:
    cql: select * from device_story_playtime where device_id = ?  and bucket_id  = ? and show_id = ? and story_id = ?
    fields: samerow
  simple4:
    cql: select show_id, sum(duration) as duration from device_story_playtime where device_id = ? and bucket_id  = ? 
    fields: samerow
  simple5:
    cql: select show_id, max(updated_at) as last_listen_time from device_story_playtime where device_id = ? and bucket_id  = ? group by show_id
    fields: samerow
  simple6:
    cql: select count(story_id) as listened_episode_count from device_story_playtime where device_id = ? and bucket_id  = ? and show_id = ?
    fields: samerow
  simple7:
    cql: select show_id, sum(playtime) as playtime from device_story_playtime where device_id = ? and bucket_id  = ? and show_id = ? group by show_id
    fields: samerow
