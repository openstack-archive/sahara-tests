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

import time

from oslo_utils import timeutils
from keystoneauth1.identity import v3
from keystoneauth1 import session
from saharaclient.api import base as sab
from saharaclient import client as sahara_client
from tempest import config
from tempest.lib import exceptions
import tempest.test

from sahara_tempest_plugin.common import plugin_utils

TEMPEST_CONF = config.CONF

# cluster status
CLUSTER_STATUS_ACTIVE = "Active"
CLUSTER_STATUS_ERROR = "Error"


class ClusterErrorException(exceptions.TempestException):
    message = "Cluster failed to build and is in ERROR status"


class BaseDataProcessingTest(tempest.test.BaseTestCase):

    credentials = ('admin', 'primary')

    @classmethod
    def resource_setup(cls):
        super(BaseDataProcessingTest, cls).resource_setup()

        endpoint_type = TEMPEST_CONF.data_processing.endpoint_type
        catalog_type = TEMPEST_CONF.data_processing.catalog_type
        auth_url = TEMPEST_CONF.identity.uri_v3

        credentials = cls.os_admin.credentials

        auth = v3.Password(auth_url=auth_url,
                           username=credentials.username,
                           password=credentials.password,
                           project_name=credentials.tenant_name,
                           user_domain_name='default',
                           project_domain_name='default')

        ses = session.Session(auth=auth)

        cls.client = sahara_client.Client(
            TEMPEST_CONF.data_processing.api_version_saharaclient,
            session=ses,
            service_type=catalog_type,
            endpoint_type=endpoint_type)

        if TEMPEST_CONF.data_processing.api_version_saharaclient == '1.1':
            sahara_api_version = '1.1'
        else:
            sahara_api_version = '2.0'

        if TEMPEST_CONF.service_available.glance:
            # Check if glance v1 is available to determine which client to use.
            if TEMPEST_CONF.image_feature_enabled.api_v1:
                cls.image_client = cls.os_admin.image_client
            elif TEMPEST_CONF.image_feature_enabled.api_v2:
                cls.image_client = cls.os_admin.image_client_v2
            else:
                raise lib_exc.InvalidConfiguration(
                    'Either api_v1 or api_v2 must be True in '
                    '[image-feature-enabled].')
        cls.object_client = cls.os_primary.object_client
        cls.container_client = cls.os_primary.container_client
        cls.networks_client = cls.os_primary.compute_networks_client

        if TEMPEST_CONF.network.floating_network_name:
            cls.floating_ip_pool = TEMPEST_CONF.network.floating_network_name
            if TEMPEST_CONF.service_available.neutron:
                cls.floating_ip_pool = \
                    cls.get_floating_ip_pool_id_for_neutron()
        else:
            cls.floating_ip_pool = TEMPEST_CONF.network.public_network_id

        test_image_name = TEMPEST_CONF.data_processing.test_image_name

        cls.test_image_id = cls.get_image_id(test_image_name)

        default_plugin = cls.get_plugin()
        plugin_dict = default_plugin.to_dict()
        default_version = plugin_utils.get_default_version(plugin_dict)

        cls.worker_template = (
            plugin_utils.get_node_group_template('worker1',
                                                 default_version,
                                                 cls.floating_ip_pool,
                                                 sahara_api_version))

        cls.master_template = (
            plugin_utils.get_node_group_template('master1',
                                                 default_version,
                                                 cls.floating_ip_pool,
                                                 sahara_api_version))

        cls.cluster_template = (
            plugin_utils.get_cluster_template(
                default_version=default_version,
                api_version=sahara_api_version))

        cls.swift_data_source_with_creds = {
            'url': 'swift://sahara-container/input-source',
            'description': 'Test data source',
            'type': 'swift',
            'credentials': {
                'user': 'test',
                'password': '123'
            }
        }

        cls.local_hdfs_data_source = {
            'url': 'input-source',
            'description': 'Test data source',
            'type': 'hdfs',
        }

        cls.external_hdfs_data_source = {
            'url': 'hdfs://test-master-node/usr/hadoop/input-source',
            'description': 'Test data source',
            'type': 'hdfs'
        }

    @classmethod
    def get_floating_ip_pool_id_for_neutron(cls):
        net_id = cls._find_network_by_name(
            TEMPEST_CONF.network.floating_network_name)
        if not net_id:
            raise exceptions.NotFound(
                'Floating IP pool \'%s\' not found in pool list.'
                % TEMPEST_CONF.network.floating_network_name)
        return net_id

    @classmethod
    def get_private_network_id(cls):
        net_id = cls._find_network_by_name(
            TEMPEST_CONF.compute.fixed_network_name)
        if not net_id:
            raise exceptions.NotFound(
                'Private network \'%s\' not found in network list.'
                % TEMPEST_CONF.compute.fixed_network_name)
        return net_id

    @classmethod
    def _find_network_by_name(cls, network_name):
        for network in cls.networks_client.list_networks()['networks']:
            if network['label'] == network_name:
                return network['id']
        return None

    @classmethod
    def get_image_id(cls, image_name):
        for image in cls.image_client.list_images()['images']:
            if image['name'] == image_name:
                return image['id']
        raise exceptions.NotFound('Image \'%s\' not found in the image list.'
                                  % (image_name))

    @classmethod
    def get_plugin(cls):
        plugins = cls.client.plugins.list()
        plugin_name = plugin_utils.get_default_plugin()
        for plugin in plugins:
            if plugin.name == plugin_name:
                return plugin
        raise exceptions.NotFound('No available plugins for testing')

    def create_node_group_template(self, name, **kwargs):

        resp_body = self.client.node_group_templates.create(
            name, **kwargs)

        self.addCleanup(self.delete_resource,
                        self.client.node_group_templates, resp_body.id)

        return resp_body

    def create_cluster_template(self, name, **kwargs):

        resp_body = self.client.cluster_templates.create(
            name, **kwargs)

        self.addCleanup(self.delete_resource,
                        self.client.cluster_templates, resp_body.id)

        return resp_body

    def create_data_source(self, name, url, description, type,
                           credentials=None):

        user = credentials['user'] if credentials else None
        pas = credentials['password'] if credentials else None

        resp_body = self.client.data_sources.create(
            name, description, type, url, credential_user=user,
            credential_pass=pas)

        self.addCleanup(self.delete_resource,
                        self.client.data_sources, resp_body.id)

        return resp_body

    def create_job_binary(self, name, url, description, extra=None):

        resp_body = self.client.job_binaries.create(
            name, url, description, extra)

        self.addCleanup(self.delete_resource,
                        self.client.job_binaries, resp_body.id)

        return resp_body

    def create_job_binary_internal(self, name, data):

        resp_body = self.client.job_binary_internals.create(name, data)

        self.addCleanup(self.delete_resource,
                        self.client.job_binary_internals, resp_body.id)

        return resp_body

    def create_job(self, name, job_type, mains, libs=None, description=None):
        if TEMPEST_CONF.data_processing.api_version_saharaclient == '1.1':
            base_client_class = self.client.jobs
        else:
            base_client_class = self.client.job_templates
        libs = libs or ()
        description = description or ''

        resp_body = base_client_class.create(
            name, job_type, mains, libs, description)

        self.addCleanup(self.delete_resource, base_client_class, resp_body.id)

        return resp_body

    def create_cluster(self, name, **kwargs):

        resp_body = self.client.clusters.create(name, **kwargs)

        self.addCleanup(self.delete_resource, self.client.clusters,
                        resp_body.id)

        return resp_body

    def check_cluster_active(self, cluster_id):
        timeout = TEMPEST_CONF.data_processing.cluster_timeout
        s_time = timeutils.utcnow()
        while timeutils.delta_seconds(s_time, timeutils.utcnow()) < timeout:
            cluster = self.client.clusters.get(cluster_id)
            if cluster.status == CLUSTER_STATUS_ACTIVE:
                return
            if cluster.status == CLUSTER_STATUS_ERROR:
                raise ClusterErrorException(
                    'Cluster failed to build and is in %s status.' %
                    CLUSTER_STATUS_ERROR)
            time.sleep(TEMPEST_CONF.data_processing.request_timeout)
        raise exceptions.TimeoutException(
            'Cluster failed to get to %s status within %d seconds.'
            % (CLUSTER_STATUS_ACTIVE, timeout))

    def create_job_execution(self, **kwargs):
        if TEMPEST_CONF.data_processing.api_version_saharaclient == '1.1':
            base_client_class = self.client.job_executions
        else:
            base_client_class = self.client.jobs

        resp_body = base_client_class.create(**kwargs)

        self.addCleanup(self.delete_resource, base_client_class, resp_body.id)

        return resp_body

    def create_container(self, name):

        self.container_client.create_container(name)

        self.addCleanup(self.delete_swift_container, name)

    def delete_resource(self, resource_client, resource_id):
        try:
            resource_client.delete(resource_id)
        except sab.APIException:
            pass
        else:
            self.delete_timeout(resource_client, resource_id)

    def delete_timeout(
            self, resource_client, resource_id,
            timeout=TEMPEST_CONF.data_processing.cluster_timeout):

        start = timeutils.utcnow()
        while timeutils.delta_seconds(start, timeutils.utcnow()) < timeout:
            try:
                resource_client.get(resource_id)
            except sab.APIException as sahara_api_exception:
                if 'not found' in str(sahara_api_exception):
                    return
                raise sahara_api_exception

            time.sleep(TEMPEST_CONF.data_processing.request_timeout)

        raise exceptions.TimeoutException(
            'Failed to delete resource "%s" in %d seconds.'
            % (resource_id, timeout))

    def delete_swift_container(self, container):
        objects = ([obj['name'] for obj in
                    self.container_client.list_all_container_objects(
                        container)])
        for obj in objects:
            self.object_client.delete_object(container, obj)
        self.container_client.delete_container(container)
