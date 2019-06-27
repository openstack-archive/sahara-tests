<%page args="is_proxy_gateway='true', use_auto_security_group='true', ci_flavor_id='m1.small', medium_flavor_id='m1.medium'"/>

clusters:
  - plugin_name: storm
    plugin_version: '1.2'
    image: ${storm_120_image}
    node_group_templates:
      - name: master
        flavor: ${ci_flavor_id}
        node_processes:
          - nimbus
        auto_security_group: ${use_auto_security_group}
        is_proxy_gateway: ${is_proxy_gateway}
      - name: worker
        flavor: ${ci_flavor_id}
        node_processes:
          - supervisor
        auto_security_group: ${use_auto_security_group}
      - name: zookeeper
        flavor: ${medium_flavor_id}
        node_processes:
          - zookeeper
        auto_security_group: ${use_auto_security_group}
    cluster_template:
      name: storm120
      node_group_templates:
        master: 1
        worker: 1
        zookeeper: 1
    cluster:
      name: ${cluster_name}
    scaling:
      - operation: add
        node_group: worker
        size: 1
    scenario:
       - scale
