<%page args="use_auto_security_group='true', ci_flavor_id='m1.small', medium_flavor_id='m1.medium', availability_zone='nova', volumes_availability_zone='nova'"/>

clusters:
  - plugin_name: ambari
    plugin_version: '2.5'
    image: ${ambari_25_image}
    node_group_templates:
      - name: master
        flavor: ${medium_flavor_id}
        node_processes:
          - Ambari
          - MapReduce History Server
          - Spark History Server
          - NameNode
          - ResourceManager
          - SecondaryNameNode
          - YARN Timeline Server
          - ZooKeeper
          - Kafka Broker
        auto_security_group: ${use_auto_security_group}
      - name: master-edp
        flavor: ${ci_flavor_id}
        node_processes:
          - Hive Metastore
          - HiveServer
          - Oozie
        auto_security_group: ${use_auto_security_group}
      - name: worker
        flavor: ${ci_flavor_id}
        node_processes:
          - DataNode
          - NodeManager
        volumes_per_node: 2
        volumes_size: 2
        availability_zone: ${availability_zone}
        volumes_availability_zone: ${volumes_availability_zone}
        auto_security_group: ${use_auto_security_group}
    cluster_template:
      name: ambari21
      node_group_templates:
        master: 1
        master-edp: 1
        worker: 3
      cluster_configs:
        HDFS:
          dfs.datanode.du.reserved: 0
    custom_checks:
      check_kafka:
        zookeeper_process: ZooKeeper
        kafka_process: Kafka Broker
        spark_flow:
          - type: Spark
            main_lib:
              type: database
              source: edp-examples/edp-spark/spark-kafka-example.jar
            args:
              - '{zookeeper_list}'
              - '{topic}'
              - '{timeout}'
            timeout: 30
    cluster:
      name: ${cluster_name}
    scaling:
      - operation: add
        node_group: worker
        size: 1
    edp_jobs_flow:
      - java_job
      - name: mapreduce_job_s3
        features:
          - s3
      - spark_pi
