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

import testtools

from tempest import config
from tempest.lib import decorators

from sahara_tempest_plugin.tests.cli import clusters
from sahara_tempest_plugin.tests.cli import cluster_templates
from sahara_tempest_plugin.tests.cli import images
from sahara_tempest_plugin.tests.cli import node_group_templates
from sahara_tempest_plugin.tests.cli import plugins
from sahara_tempest_plugin.tests.cli import job_binaries
from sahara_tempest_plugin.tests.cli import jobs
from sahara_tempest_plugin.tests.cli import job_templates
from sahara_tempest_plugin.tests.cli import data_sources
from sahara_tempest_plugin.tests.cli import job_types

TEMPEST_CONF = config.CONF
NODE_GROUP_TEMPLATE = 'node group template'


class Scenario(images.SaharaImageCLITest,
               node_group_templates.SaharaNodeGroupCLITest,
               cluster_templates.SaharaClusterTemplateCLITest,
               clusters.SaharaClusterCLITest,
               plugins.SaharaPluginCLITest,
               job_binaries.SaharaJobBinaryCLITest,
               jobs.SaharaJobCLITest,
               job_templates.SaharaJobTemplateCLITest,
               data_sources.SaharaDataSourceCLITest,
               job_types.SaharaJobTypeCLITest):

    def test_plugin_cli(self):
        self.openstack_plugin_list()
        self.openstack_plugin_show()
        self.openstack_plugin_configs_get()
        if TEMPEST_CONF.data_processing.plugin_update_support:
            self.openstack_plugin_update()

    def test_node_group_cli(self):
        master_ngt = self.openstack_node_group_template_create('master', '4')
        worker_ngt = self.openstack_node_group_template_create('worker', '3')
        self.addCleanup(self.delete_resource, NODE_GROUP_TEMPLATE, master_ngt)
        self.addCleanup(self.delete_resource, NODE_GROUP_TEMPLATE, worker_ngt)
        self.filter_node_group_list_with_plugin()
        self.openstack_node_group_template_list()
        new_master_ngt = self.openstack_node_group_template_update(
            master_ngt, update_field='name')
        self.addCleanup(self.delete_resource, NODE_GROUP_TEMPLATE,
                        new_master_ngt)

        self.openstack_node_group_template_show(new_master_ngt)
        self.openstack_node_group_template_delete(new_master_ngt)
        self.negative_try_to_delete_protected_node_group(worker_ngt)
        self.openstack_node_group_template_delete(worker_ngt)
        self.wait_for_resource_deletion(new_master_ngt, NODE_GROUP_TEMPLATE)
        self.wait_for_resource_deletion(worker_ngt, NODE_GROUP_TEMPLATE)
        self.negative_delete_removed_node_group(worker_ngt)

    def test_cluster_template_cli(self):
        cluster_template_cmd = 'cluster template'
        ng_master = (
            self.openstack_node_group_template_create('tmp-master', '4'))
        ng_worker = (
            self.openstack_node_group_template_create('tmp-worker', '3'))
        self.addCleanup(self.delete_resource, NODE_GROUP_TEMPLATE,
                        ng_master)
        self.addCleanup(self.delete_resource, NODE_GROUP_TEMPLATE,
                        ng_worker)

        cluster_template_name = (
            self.openstack_cluster_template_create(ng_master, ng_worker))
        self.addCleanup(self.delete_resource, cluster_template_cmd,
                        cluster_template_name)

        self.openstack_cluster_template_list()
        self.openstack_cluster_template_show(cluster_template_name)
        new_cluster_template_name = self.openstack_cluster_template_update(
            cluster_template_name)
        self.addCleanup(self.delete_resource, cluster_template_cmd,
                        new_cluster_template_name)

        self.openstack_cluster_template_delete(new_cluster_template_name)
        self.wait_for_resource_deletion(new_cluster_template_name,
                                        cluster_template_cmd)
        self.openstack_node_group_template_delete(ng_master)
        self.openstack_node_group_template_delete(ng_worker)
        self.wait_for_resource_deletion(ng_master, NODE_GROUP_TEMPLATE)
        self.wait_for_resource_deletion(ng_worker, NODE_GROUP_TEMPLATE)

    @decorators.skip_because(bug="1629295")
    def test_cluster_cli(self):
        image_name = self.openstack_image_register(
            TEMPEST_CONF.data_processing.test_image_name,
            TEMPEST_CONF.data_processing.test_ssh_user)
        self.openstack_image_tags_set(image_name)
        self.openstack_image_tags_remove(image_name)
        self.openstack_image_tags_add(image_name)
        self.openstack_image_show(image_name)
        self.openstack_image_list()
        flavors_client = self.client_manager_admin.flavors_client
        flavor_ref = flavors_client.create_flavor(name='sahara-flavor',
                                                  ram=512, vcpus=1, disk=4,
                                                  id=20)['flavor']
        self.addCleanup(flavors_client.delete_flavor, flavor_ref['id'])
        self.addCleanup(self.openstack_image_unregister, image_name)

        ng_master = self.openstack_node_group_template_create('cli-cluster'
                                                              '-master',
                                                              'sahara-flavor')
        ng_worker = self.openstack_node_group_template_create('cli-cluster'
                                                              '-worker',
                                                              'sahara-flavor')
        self.addCleanup(self.delete_resource, 'node group template',
                        ng_master)
        self.addCleanup(self.delete_resource, 'node group template',
                        ng_worker)

        cluster_template_name = (
            self.openstack_cluster_template_create(ng_master, ng_worker))
        self.addCleanup(self.delete_resource, 'cluster template',
                        cluster_template_name)

        cluster_name = (
            self.openstack_cluster_create(cluster_template_name, image_name))
        self.addCleanup(self.delete_resource, 'cluster',
                        cluster_name)

        self._run_job_on_cluster(cluster_name)
        self.openstack_cluster_list()
        self.openstack_cluster_show(cluster_name)
        self.openstack_cluster_update(cluster_name)
        self.openstack_cluster_verification_show(cluster_name)
        self.openstack_cluster_verification_start(cluster_name)
        self.openstack_cluster_scale(cluster_name, ng_worker)
        self.openstack_cluster_delete(cluster_name)
        self.wait_for_resource_deletion(cluster_name, 'cluster')
        self.openstack_cluster_template_delete(cluster_template_name)
        self.wait_for_resource_deletion(cluster_template_name, 'cluster '
                                                               'template')
        self.openstack_node_group_template_delete(ng_master)
        self.openstack_node_group_template_delete(ng_worker)
        self.wait_for_resource_deletion(ng_master, 'node group template')
        self.wait_for_resource_deletion(ng_worker, 'node group template')
        self.openstack_image_unregister(image_name)
        self.negative_unregister_not_existing_image(image_name)

    @testtools.skipIf(TEMPEST_CONF.data_processing.api_version_saharaclient !=
                      '1.1', "Full job binaries testing requires API v1.1")
    def test_job_binary_cli(self):
        job_binary_name, original_file = self.openstack_job_binary_create()
        self.addCleanup(self.delete_resource, 'job binary', job_binary_name)

        self.openstack_job_binary_list()
        self.openstack_job_binary_show(job_binary_name)
        self.openstack_job_binary_update(job_binary_name, flag='description')
        self.openstack_job_binary_download(job_binary_name, original_file)
        self.filter_job_binaries_in_list()
        self.negative_try_to_update_protected_jb(job_binary_name)
        self.openstack_job_binary_update(job_binary_name, flag='unprotected')
        self.openstack_job_binary_delete(job_binary_name)
        self.negative_delete_removed_job_binary(job_binary_name)

    def test_job_template_cli(self):
        job_binary_name, _ = self.openstack_job_binary_create(
            job_internal=False)
        self.addCleanup(self.delete_resource, 'job binary', job_binary_name)

        job_template_name = self.openstack_job_template_create(job_binary_name)
        self.addCleanup(self.delete_resource, 'job template',
                        job_template_name)

        self.openstack_job_template_list()
        self.openstack_job_template_show(job_template_name)
        self.openstack_job_template_update(job_template_name)
        self.openstack_job_template_delete(job_template_name)
        self.openstack_job_binary_delete(job_binary_name)

    def test_data_source_cli(self):
        data_source_name = self.openstack_data_source_create()
        self.addCleanup(self.delete_resource, 'data source', data_source_name)

        self.openstack_data_source_list()
        self.openstack_data_source_show(data_source_name)
        self.openstack_data_source_update(data_source_name)
        self.openstack_data_source_delete(data_source_name)

    def test_job_type_cli(self):
        self.openstack_job_type_list()
        self.openstack_job_type_configs_get(flag='file')
        self.filter_job_type_in_list()

    def _run_job_on_cluster(self, cluster_name):
        job_template_name = self.openstack_job_template_name()
        self.addCleanup(self.delete_resource, 'job template',
                        job_template_name)

        input_file = self.openstack_data_source_create()
        output_file = self.openstack_data_source_create()
        self.addCleanup(self.delete_resource, 'data source', input_file)
        self.addCleanup(self.delete_resource, 'data source', output_file)
        job_id = self.openstack_job_execute(cluster_name, job_template_name,
                                            input_file, output_file)
        self.addCleanup(self.delete_resource, 'job', job_id)

        self.openstack_job_list()
        self.openstack_job_show(job_id)
        self.openstack_job_update(job_id)
        self.openstack_job_delete(job_id)
        self.openstack_data_source_delete(input_file)
        self.openstack_data_source_delete(output_file)
        self.openstack_job_template_delete(job_template_name)
