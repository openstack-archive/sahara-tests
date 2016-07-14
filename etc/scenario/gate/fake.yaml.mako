<%page args="is_transient='false', use_auto_security_group='true'"/>

clusters:
  - plugin_name: fake
    plugin_version: "0.1"
    image: ${fake_plugin_image}
    node_group_templates:
      - name: aio
        flavor: ${ci_flavor_id}
        node_processes:
          - namenode
          - jobtracker
          - datanode
          - tasktracker
        volumes_per_node: 2
        volumes_size: 1
        auto_security_group: ${use_auto_security_group}
      - name: worker
        flavor: ${ci_flavor_id}
        node_processes:
          - datanode
          - jobtracker
        auto_security_group: ${use_auto_security_group}
    cluster_template:
      name: fake01
      node_group_templates:
        aio: 1
    cluster:
      name: ${cluster_name}
      is_transient: ${is_transient}
    scaling:
      - operation: add
        node_group: worker
        size: 1
    edp_jobs_flow: fake
