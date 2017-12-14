<%page args="use_auto_security_group='true', ci_flavor_id='m1.small', medium_flavor_id='m1.medium', large_flavor_id='m1.large', availability_zone='nova', volumes_availability_zone='nova'"/>

clusters:
  - plugin_name: cdh
    plugin_version: 5.4.0
    image: ${cdh_540_image}
    node_group_templates:
      - name: worker-dn
        flavor: ${ci_flavor_id}
        node_processes:
          - HDFS_DATANODE
          - HDFS_JOURNALNODE
        volumes_per_node: 2
        volumes_size: 2
        availability_zone: ${availability_zone}
        volumes_availability_zone: ${volumes_availability_zone}
        auto_security_group: ${use_auto_security_group}
        node_configs:
          &ng_configs
          DATANODE:
            dfs_datanode_du_reserved: 0
      - name: worker-nm
        flavor: ${ci_flavor_id}
        node_processes:
          - YARN_NODEMANAGER
        auto_security_group: ${use_auto_security_group}
      - name: worker-nm-dn
        flavor: ${ci_flavor_id}
        node_processes:
          - YARN_NODEMANAGER
          - HDFS_DATANODE
          - HDFS_JOURNALNODE
        volumes_per_node: 2
        volumes_size: 2
        availability_zone: ${availability_zone}
        volumes_availability_zone: ${volumes_availability_zone}
        auto_security_group: ${use_auto_security_group}
        node_configs:
          *ng_configs
      - name: manager
        flavor: ${large_flavor_id}
        node_processes:
          - CLOUDERA_MANAGER
        auto_security_group: ${use_auto_security_group}
      - name: master-core
        flavor: ${medium_flavor_id}
        node_processes:
          - HDFS_NAMENODE
          - YARN_RESOURCEMANAGER
          - ZOOKEEPER_SERVER
        auto_security_group: ${use_auto_security_group}
      - name: master-additional
        flavor: ${large_flavor_id}
        node_processes:
          - OOZIE_SERVER
          - ZOOKEEPER_SERVER
          - YARN_JOBHISTORY
          - HDFS_SECONDARYNAMENODE
          - HDFS_JOURNALNODE
        auto_security_group: ${use_auto_security_group}
    cluster_template:
      name: cdh540
      node_group_templates:
        manager: 1
        master-core: 1
        master-additional: 1
        worker-nm-dn: 1
        worker-nm: 2
        worker-dn: 1
      cluster_configs:
        HDFS:
          dfs_replication: 1
        general:
          'Require Anti Affinity': False
    cluster:
      name: ${cluster_name}
    scenario:
      - run_jobs
    edp_jobs_flow:
      - mapreduce_job
      - java_job
