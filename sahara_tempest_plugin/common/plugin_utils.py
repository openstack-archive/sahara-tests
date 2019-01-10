# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from collections import OrderedDict
import copy

from tempest import config


CONF = config.CONF


"""Default templates.
There should always be at least a master1 and a worker1 node
group template."""
BASE_VANILLA_DESC = {
    'NODES': {
        'master1': {
            'count': 1,
            'node_processes': ['namenode', 'resourcemanager',
                               'hiveserver']
        },
        'master2': {
            'count': 1,
            'node_processes': ['oozie', 'historyserver',
                               'secondarynamenode']
        },
        'worker1': {
            'count': 1,
            'node_processes': ['datanode', 'nodemanager'],
            'node_configs': {
                'MapReduce': {
                    'yarn.app.mapreduce.am.resource.mb': 256,
                    'yarn.app.mapreduce.am.command-opts': '-Xmx256m'
                },
                'YARN': {
                    'yarn.scheduler.minimum-allocation-mb': 256,
                    'yarn.scheduler.maximum-allocation-mb': 1024,
                    'yarn.nodemanager.vmem-check-enabled': False
                }
            }
        }
    },
    'cluster_configs': {
        'HDFS': {
            'dfs.replication': 1
        }
    }
}

BASE_SPARK_DESC = {
    'NODES': {
        'master1': {
            'count': 1,
            'node_processes': ['namenode', 'master']
        },
        'worker1': {
            'count': 1,
            'node_processes': ['datanode', 'slave']
        }
    },
    'cluster_configs': {
        'HDFS': {
            'dfs.replication': 1
        }
    }
}

BASE_CDH_DESC = {
    'NODES': {
        'master1': {
            'count': 1,
            'node_processes': ['CLOUDERA_MANAGER']
        },
        'master2': {
            'count': 1,
            'node_processes': ['HDFS_NAMENODE',
                               'YARN_RESOURCEMANAGER']
        },
        'master3': {
            'count': 1,
            'node_processes': ['OOZIE_SERVER', 'YARN_JOBHISTORY',
                               'HDFS_SECONDARYNAMENODE',
                               'HIVE_METASTORE', 'HIVE_SERVER2']
        },
        'worker1': {
            'count': 1,
            'node_processes': ['YARN_NODEMANAGER', 'HDFS_DATANODE']
        }
    },
    'cluster_configs': {
        'HDFS': {
            'dfs_replication': 1
        }
    }
}

BASE_AMBARI_HDP_DESC = {
    'NODES': {
        'master1': {
            'count': 1,
            'node_processes': ['Ambari', 'MapReduce History Server',
                               'Spark History Server', 'NameNode',
                               'ResourceManager', 'SecondaryNameNode',
                               'YARN Timeline Server', 'ZooKeeper',
                               'Kafka Broker']
        },
        'master2': {
            'count': 1,
            'node_processes': ['Hive Metastore', 'HiveServer', 'Oozie']
        },
        'worker1': {
            'count': 3,
            'node_processes': ['DataNode', 'NodeManager']
        }
    },
    'cluster_configs': {
        'HDFS': {
            'dfs.datanode.du.reserved': 0
        }
    }
}

BASE_MAPR_DESC = {
    'NODES': {
        'master1': {
            'count': 1,
            'node_processes': ['Metrics', 'Webserver', 'ZooKeeper',
                               'HTTPFS', 'Oozie', 'FileServer', 'CLDB',
                               'Flume', 'Hue', 'NodeManager', 'HistoryServer',
                               'ResourceManager', 'HiveServer2',
                               'HiveMetastore',
                               'Sqoop2-Client', 'Sqoop2-Server']
        },
        'worker1': {
            'count': 1,
            'node_processes': ['NodeManager', 'FileServer']
        }
    }
}

BASE_STORM_DESC = {
    'NODES': {
        'master1': {
            'count': 1,
            'node_processes': ['nimbus']
        },
        'master2': {
            'count': 1,
            'node_processes': ['zookeeper']
        },
        'worker1': {
            'count': 1,
            'node_processes': ['supervisor']
        }
    }
}


DEFAULT_TEMPLATES = {
    'fake': OrderedDict([
        ('0.1', {
            'NODES': {
                'master1': {
                    'count': 1,
                    'node_processes': ['namenode', 'jobtracker']
                },
                'worker1': {
                    'count': 1,
                    'node_processes': ['datanode', 'tasktracker'],
                }
            }
        })
    ]),
    'vanilla': OrderedDict([
        ('2.7.1', copy.deepcopy(BASE_VANILLA_DESC)),
        ('2.7.5', copy.deepcopy(BASE_VANILLA_DESC)),
        ('2.8.2', copy.deepcopy(BASE_VANILLA_DESC))
    ]),
    'ambari': OrderedDict([
        ('2.3', copy.deepcopy(BASE_AMBARI_HDP_DESC)),
        ('2.4', copy.deepcopy(BASE_AMBARI_HDP_DESC)),
        ('2.5', copy.deepcopy(BASE_AMBARI_HDP_DESC)),
        ('2.6', copy.deepcopy(BASE_AMBARI_HDP_DESC))
    ]),
    'spark': OrderedDict([
        ('1.3.1', copy.deepcopy(BASE_SPARK_DESC)),
        ('1.6.0', copy.deepcopy(BASE_SPARK_DESC)),
        ('2.1.0', copy.deepcopy(BASE_SPARK_DESC)),
        ('2.2', copy.deepcopy(BASE_SPARK_DESC)),
        ('2.3', copy.deepcopy(BASE_SPARK_DESC))
    ]),
    'cdh': OrderedDict([
        ('5.4.0', copy.deepcopy(BASE_CDH_DESC)),
        ('5.5.0', copy.deepcopy(BASE_CDH_DESC)),
        ('5.7.0', copy.deepcopy(BASE_CDH_DESC)),
        ('5.9.0', copy.deepcopy(BASE_CDH_DESC)),
        ('5.11.0', copy.deepcopy(BASE_CDH_DESC)),
        ('5.13.0', copy.deepcopy(BASE_CDH_DESC))
    ]),
    'mapr': OrderedDict([
        ('5.1.0.mrv2', copy.deepcopy(BASE_MAPR_DESC)),
        ('5.2.0.mrv2', copy.deepcopy(BASE_MAPR_DESC))
    ]),
    'storm': OrderedDict([
        ('1.0.1', copy.deepcopy(BASE_STORM_DESC)),
        ('1.1.0', copy.deepcopy(BASE_STORM_DESC)),
        ('1.2', copy.deepcopy(BASE_STORM_DESC))
    ])
}


def get_plugin_data(plugin_name, plugin_version):
    return DEFAULT_TEMPLATES[plugin_name][plugin_version]


def get_default_plugin():
    """Returns the default plugin used for testing."""
    enabled_plugins = CONF.data_processing_feature_enabled.plugins

    if len(enabled_plugins) == 0:
        return None

    # NOTE(raissa) if fake is available, use it first.
    # this is to reduce load and should be removed
    # once the fake plugin is no longer needed
    if 'fake' in enabled_plugins:
        return 'fake'

    for plugin in enabled_plugins:
        if plugin in DEFAULT_TEMPLATES.keys():
            break
    else:
        plugin = ''
    return plugin


def get_default_version(plugin):
    """Returns the default plugin version used for testing.

    This is gathered separately from the plugin to allow
    the usage of plugin name in skip_checks. This method is
    rather invoked into resource_setup, which allows API calls
    and exceptions.
    """
    default_plugin_name = get_default_plugin()

    if not (plugin and default_plugin_name):
        return None

    for version in DEFAULT_TEMPLATES[default_plugin_name].keys():
        if version in plugin['versions']:
            break
    else:
        version = None

    return version


def get_node_group_template(nodegroup='worker1',
                            default_version=None,
                            floating_ip_pool=None,
                            api_version='1.1'):
    """Returns a node group template for the default plugin."""
    try:
        flavor = CONF.compute.flavor_ref
        default_plugin_name = get_default_plugin()
        plugin_data = (
            get_plugin_data(default_plugin_name, default_version)
        )
        nodegroup_data = plugin_data['NODES'][nodegroup]
        node_group_template = {
            'description': 'Test node group template',
            'plugin_name': default_plugin_name,
            'node_processes': nodegroup_data['node_processes'],
            'flavor_id': flavor,
            'floating_ip_pool': floating_ip_pool,
            'node_configs': nodegroup_data.get('node_configs', {})
        }
        if api_version == '1.1':
            node_group_template['hadoop_version'] = default_version
        else:
            node_group_template['plugin_version'] = default_version
        return node_group_template
    except (IndexError, KeyError):
        return None


def get_cluster_template(node_group_template_ids=None,
                         default_version=None,
                         api_version='1.1'):
    """Returns a cluster template for the default plugin.

    node_group_template_ids contains the type and ID of pre-defined
    node group templates that have to be used in the cluster template
    (instead of dynamically defining them with 'node_processes').
    """
    flavor = CONF.compute.flavor_ref
    default_plugin_name = get_default_plugin()

    if node_group_template_ids is None:
        node_group_template_ids = {}
    try:
        plugin_data = (
            get_plugin_data(default_plugin_name, default_version)
        )

        all_node_groups = []
        for ng_name, ng_data in plugin_data['NODES'].items():
            node_group = {
                'name': '%s-node' % (ng_name),
                'flavor_id': flavor,
                'count': ng_data['count']
            }
            if ng_name in node_group_template_ids.keys():
                # node group already defined, use it
                node_group['node_group_template_id'] = (
                    node_group_template_ids[ng_name]
                )
            else:
                # node_processes list defined on-the-fly
                node_group['node_processes'] = ng_data['node_processes']
            if 'node_configs' in ng_data:
                node_group['node_configs'] = ng_data['node_configs']
            all_node_groups.append(node_group)

        cluster_template = {
            'description': 'Test cluster template',
            'plugin_name': default_plugin_name,
            'cluster_configs': plugin_data.get('cluster_configs', {}),
            'node_groups': all_node_groups,
        }
        if api_version == '1.1':
            cluster_template['hadoop_version'] = default_version
        else:
            cluster_template['plugin_version'] = default_version
        return cluster_template
    except (IndexError, KeyError):
        return None
