<%page args="is_proxy_gateway='true', use_auto_security_group='true', cluster_name='ct', ci_flavor_id='m1.small'"/>

clusters:
  - plugin_name: spark
    plugin_version: 1.6.0
    image: ${plugin_image}
    node_group_templates:
      - name: master
        flavor: ${ci_flavor_id}
        node_processes:
          - master
          - namenode
          - datanode
          - slave
        auto_security_group: ${use_auto_security_group}
        is_proxy_gateway: ${is_proxy_gateway}
      - name: worker
        flavor: ${ci_flavor_id}
        node_processes:
          - datanode
          - slave
        auto_security_group: ${use_auto_security_group}
    cluster_template:
      name: spark160
      node_group_templates:
        master: 1
      cluster_configs:
        HDFS:
          dfs.replication: 1
    scaling:
      - operation: add
        node_group: worker
        size: 1
    scenario:
      - run_jobs
      - scale
    edp_jobs_flow:
      - spark_pi
      - spark_wordcount
    cluster:
      name: ${cluster_name}
