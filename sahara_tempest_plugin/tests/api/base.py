# Copyright (c) 2014 Mirantis Inc.
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

from tempest import config
from tempest.lib import exceptions
import tempest.test

from sahara_tempest_plugin import clients
from sahara_tempest_plugin.common import plugin_utils


CONF = config.CONF


class InvalidSaharaTestConfiguration(exceptions.TempestException):
    message = "Invalid configuration for Sahara tests"


class BaseDataProcessingTest(tempest.test.BaseTestCase):

    credentials = ['primary']

    client_manager = clients.Manager

    @classmethod
    def skip_checks(cls):
        super(BaseDataProcessingTest, cls).skip_checks()
        if not CONF.service_available.sahara:
            raise cls.skipException('Sahara support is required')
        cls.default_plugin = plugin_utils.get_default_plugin()

    @classmethod
    def setup_clients(cls):
        super(BaseDataProcessingTest, cls).setup_clients()
        if not CONF.data_processing.use_api_v2:
            cls.api_version = '1.1'
            cls.client = cls.os_primary.data_processing.DataProcessingClient()
        else:
            cls.api_version = '2.0'
            cls.client = \
                cls.os_primary.data_processing_v2.DataProcessingClient()

    @classmethod
    def resource_setup(cls):
        super(BaseDataProcessingTest, cls).resource_setup()

        plugin = None
        if cls.default_plugin:
            plugin = cls.client.get_plugin(cls.default_plugin)['plugin']
        cls.default_version = plugin_utils.get_default_version(plugin)

        if cls.default_plugin is not None and cls.default_version is None:
            raise InvalidSaharaTestConfiguration(
                message="No known Sahara plugin version was found")

        # add lists for watched resources
        cls._node_group_templates = []
        cls._cluster_templates = []
        cls._data_sources = []
        cls._job_binary_internals = []
        cls._job_binaries = []
        cls._jobs = []

    @classmethod
    def resource_cleanup(cls):
        cls.cleanup_resources(getattr(cls, '_cluster_templates', []),
                              cls.client.delete_cluster_template)
        cls.cleanup_resources(getattr(cls, '_node_group_templates', []),
                              cls.client.delete_node_group_template)
        if cls.api_version == '1.1':
            cls.cleanup_resources(getattr(cls, '_jobs', []),
                                  cls.client.delete_job)
        else:
            cls.cleanup_resources(getattr(cls, '_jobs', []),
                                  cls.client.delete_job_template)
        cls.cleanup_resources(getattr(cls, '_job_binaries', []),
                              cls.client.delete_job_binary)
        if cls.api_version == '1.1':
            cls.cleanup_resources(getattr(cls, '_job_binary_internals', []),
                                  cls.client.delete_job_binary_internal)
        cls.cleanup_resources(getattr(cls, '_data_sources', []),
                              cls.client.delete_data_source)
        super(BaseDataProcessingTest, cls).resource_cleanup()

    @staticmethod
    def cleanup_resources(resource_id_list, method):
        for resource_id in resource_id_list:
            try:
                method(resource_id)
            except exceptions.NotFound:
                # ignore errors while auto removing created resource
                pass

    @classmethod
    def create_node_group_template(cls, name, plugin_name, hadoop_version,
                                   node_processes, flavor_id,
                                   node_configs=None, **kwargs):
        """Creates watched node group template with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_node_group_template(name, plugin_name,
                                                          hadoop_version,
                                                          node_processes,
                                                          flavor_id,
                                                          node_configs,
                                                          **kwargs)
        resp_body = resp_body['node_group_template']
        # store id of created node group template
        cls._node_group_templates.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_cluster_template(cls, name, plugin_name, hadoop_version,
                                node_groups, cluster_configs=None, **kwargs):
        """Creates watched cluster template with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_cluster_template(name, plugin_name,
                                                       hadoop_version,
                                                       node_groups,
                                                       cluster_configs,
                                                       **kwargs)
        resp_body = resp_body['cluster_template']
        # store id of created cluster template
        cls._cluster_templates.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_data_source(cls, name, type, url, **kwargs):
        """Creates watched data source with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_data_source(name, type, url, **kwargs)
        resp_body = resp_body['data_source']
        # store id of created data source
        cls._data_sources.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_job_binary_internal(cls, name, data):
        """Creates watched job binary internal with specified params.

        It returns created object. All resources created in this method will
        be automatically removed in tearDownClass method.
        """
        resp_body = cls.client.create_job_binary_internal(name, data)
        resp_body = resp_body['job_binary_internal']
        # store id of created job binary internal
        cls._job_binary_internals.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_job_binary(cls, name, url, extra=None, **kwargs):
        """Creates watched job binary with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_job_binary(name, url, extra, **kwargs)
        resp_body = resp_body['job_binary']
        # store id of created job binary
        cls._job_binaries.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_job(cls, name, job_type, mains, libs=None, **kwargs):
        """Creates watched job (v1) with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_job(name,
                                          job_type, mains, libs, **kwargs)
        resp_body = resp_body['job']
        # store id of created job
        cls._jobs.append(resp_body['id'])

        return resp_body

    @classmethod
    def create_job_template(cls, name, job_type, mains, libs=None, **kwargs):
        """Creates watched job template (v2) with specified params.

        It supports passing additional params using kwargs and returns created
        object. All resources created in this method will be automatically
        removed in tearDownClass method.
        """
        resp_body = cls.client.create_job_template(name, job_type, mains,
                                                   libs, **kwargs)
        resp_body = resp_body['job_template']
        # store id of created job
        cls._jobs.append(resp_body['id'])

        return resp_body

    @classmethod
    def get_node_group_template(cls, nodegroup='worker1'):
        """Returns a node group template for the default plugin."""
        return plugin_utils.get_node_group_template(nodegroup,
                                                    cls.default_version,
                                                    None,
                                                    cls.api_version)

    @classmethod
    def get_cluster_template(cls, node_group_template_ids=None):
        """Returns a cluster template for the default plugin.

        node_group_template_defined contains the type and ID of pre-defined
        node group templates that have to be used in the cluster template
        (instead of dynamically defining them with 'node_processes').
        """
        return plugin_utils.get_cluster_template(node_group_template_ids,
                                                 cls.default_version,
                                                 cls.api_version)

    @classmethod
    def wait_for_resource_deletion(cls, resource_id, get_resource):
        """Waits for a resource to be deleted.

        The deletion of a resource depends on the client is_resource_deleted
        implementation. This implementation will vary slightly from resource
        to resource. get_resource param should be the function used to
        retrieve that type of resource.
        """
        def is_resource_deleted(resource_id):
            try:
                get_resource(resource_id)
            except exceptions.NotFound:
                return True
            return False

        cls.client.is_resource_deleted = is_resource_deleted
        cls.client.wait_for_resource_deletion(resource_id)
