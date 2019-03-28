<%page args="is_proxy_gateway='true', use_auto_security_group='true', ci_flavor_id='m1.small', large_flavor_id='m1.large', availability_zone='nova', volumes_availability_zone='nova'"/>

clusters:
  - plugin_name: cdh
    plugin_version: 5.9.0
    image: ${cdh_590_image}
    node_group_templates:
      - name: worker-dn
        flavor: ${ci_flavor_id}
        node_processes:
          - HDFS_DATANODE
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
          - KMS
        is_proxy_gateway: ${is_proxy_gateway}
        auto_security_group: ${use_auto_security_group}
      - name: master-core
        flavor: ${large_flavor_id}
        node_processes:
          - HDFS_NAMENODE
          - YARN_RESOURCEMANAGER
          - SENTRY_SERVER
          - YARN_NODEMANAGER
          - ZOOKEEPER_SERVER
        auto_security_group: ${use_auto_security_group}
      - name: master-additional
        flavor: ${large_flavor_id}
        node_processes:
          - OOZIE_SERVER
          - YARN_JOBHISTORY
          - YARN_NODEMANAGER
          - HDFS_SECONDARYNAMENODE
          - HIVE_METASTORE
          - HIVE_SERVER2
          - SPARK_YARN_HISTORY_SERVER
        auto_security_group: ${use_auto_security_group}
        # In 5.9 the defaults of following configs are too large,
        # restrict them to save memory for scenario testing.
        node_configs:
            HIVEMETASTORE:
                hive_metastore_java_heapsize: 2147483648
            HIVESERVER:
                hiveserver2_java_heapsize: 2147483648
    cluster_template:
      name: cdh590
      node_group_templates:
        manager: 1
        master-core: 1
        master-additional: 1
        worker-nm-dn: 1
        worker-nm: 1
        worker-dn: 1
      cluster_configs:
        HDFS:
          dfs_replication: 1
    cluster:
      name: ${cluster_name}
    scenario:
      - run_jobs
      - sentry
    edp_jobs_flow:
      - pig_job
      - mapreduce_job
      - name: mapreduce_job_s3
        features:
          - s3
      - mapreduce_streaming_job
      - java_job
      - spark_wordcount
