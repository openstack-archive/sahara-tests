<%page args="is_proxy_gateway='true', use_auto_security_group='true', ci_flavor_id='m1.small', availability_zone='nova', volumes_availability_zone='nova'"/>

clusters:
  - plugin_name: fake
    plugin_version: "0.1"
    image: ${fake_plugin_image}
    node_group_templates:
      - name: worker
        flavor: ${ci_flavor_id}
        node_processes:
          - datanode
          - tasktracker
        volumes_per_node: 2
        volumes_size: 2
        availability_zone: ${availability_zone}
        volumes_availability_zone: ${volumes_availability_zone}
        auto_security_group: ${use_auto_security_group}
      - name: master
        flavor: ${ci_flavor_id}
        node_processes:
          - jobtracker
          - namenode
        auto_security_group: ${use_auto_security_group}
        is_proxy_gateway: ${is_proxy_gateway}
    cluster_template:
      name: fake01
      node_group_templates:
        master: 1
        worker: 1
    cluster:
      name: ${cluster_name}
    scaling:
      - operation: add
        node_group: worker
        size: 1
    edp_jobs_flow: pig_job
