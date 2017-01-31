<%page args="use_auto_security_group='true', mapr_master_flavor_id='mapr.master', mapr_worker_flavor_id='mapr.worker'"/>

clusters:
  - plugin_name: mapr
    plugin_version: 5.2.0.mrv2
    image: ${mapr_520mrv2_image}
    node_group_templates:
      - name: master
        flavor:
          name: ${mapr_master_flavor_id}
          vcpus: 4
          ram: 8192
          root_disk: 80
          ephemeral_disk: 40
        node_processes:
          - Metrics
          - Webserver
          - ZooKeeper
          - HTTPFS
          - Oozie
          - FileServer
          - CLDB
          - Flume
          - Hue
          - NodeManager
          - HistoryServer
          - ResourceManager
          - HiveServer2
          - HiveMetastore
          - Sqoop2-Client
          - Sqoop2-Server
        auto_security_group: ${use_auto_security_group}
      - name: worker
        flavor:
          name: ${mapr_worker_flavor_id}
          vcpus: 2
          ram: 4096
          root_disk: 40
          ephemeral_disk: 40
        node_processes:
          - NodeManager
          - FileServer
        auto_security_group: ${use_auto_security_group}
    cluster_template:
      name: mapr520mrv2
      node_group_templates:
        master: 1
        worker: 1
    cluster:
      name: ${cluster_name}
    scaling:
      - operation: add
        node_group: worker
        size: 1
    edp_jobs_flow:
      - mapr
