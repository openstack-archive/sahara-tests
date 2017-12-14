<%page args="is_proxy_gateway='true', use_auto_security_group='true', ci_flavor_id='m1.small', cluster_name='vanilla-271', availability_zone='nova', volumes_availability_zone='nova'"/>

clusters:
  - plugin_name: vanilla
    plugin_version: 2.7.1
    image: ${vanilla_271_image}
    node_group_templates:
      - name: worker-dn-nm
        flavor: ${ci_flavor_id}
        node_processes:
          - datanode
          - nodemanager
        volumes_per_node: 2
        volumes_size: 2
        availability_zone: ${availability_zone}
        volumes_availability_zone: ${volumes_availability_zone}
        auto_security_group: ${use_auto_security_group}
      - name: worker-nm
        flavor: ${ci_flavor_id}
        node_processes:
          - nodemanager
        auto_security_group: ${use_auto_security_group}
      - name: worker-dn
        flavor: ${ci_flavor_id}
        node_processes:
          - datanode
        volumes_per_node: 2
        volumes_size: 2
        availability_zone: ${availability_zone}
        volumes_availability_zone: ${volumes_availability_zone}
        auto_security_group: ${use_auto_security_group}
      - name: master-rm-nn-hvs-sp
        flavor: ${ci_flavor_id}
        node_processes:
          - namenode
          - resourcemanager
          - hiveserver
          - nodemanager
          - spark history server
        auto_security_group: ${use_auto_security_group}
      - name: master-oo-hs-sn
        flavor: ${ci_flavor_id}
        node_processes:
          - oozie
          - historyserver
          - secondarynamenode
          - nodemanager
        auto_security_group: ${use_auto_security_group}
        is_proxy_gateway: ${is_proxy_gateway}
    cluster_template:
      node_group_templates:
        master-rm-nn-hvs-sp: 1
        master-oo-hs-sn: 1
        worker-dn-nm: 2
        worker-dn: 1
        worker-nm: 1
      cluster_configs:
        HDFS:
          dfs.replication: 1
    cluster:
      name: ${cluster_name}
    scaling:
      - operation: resize
        node_group: worker-dn-nm
        size: 1
      - operation: resize
        node_group: worker-dn
        size: 0
      - operation: resize
        node_group: worker-nm
        size: 0
      - operation: add
        node_group: worker-dn
        size: 1
      - operation: add
        node_group: worker-nm
        size: 2
    edp_jobs_flow:
      - pig_job
      - mapreduce_job
      - mapreduce_streaming_job
      - java_job
      - hive_job
      - spark_wordcount
