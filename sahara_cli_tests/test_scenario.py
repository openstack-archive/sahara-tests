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

from sahara_cli_tests import clusters
from sahara_cli_tests import cluster_templates
from sahara_cli_tests import images
from sahara_cli_tests import node_group_templates
from sahara_cli_tests import plugins
from sahara_cli_tests import job_binaries
from sahara_cli_tests import jobs
from sahara_cli_tests import job_templates
from sahara_cli_tests import data_sources
from sahara_cli_tests import job_types


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

    def test_node_group_cli(self):
        master_ngt = self.openstack_node_group_template_create('master', '4')
        worker_ngt = self.openstack_node_group_template_create('worker', '3')
        self.openstack_node_group_template_list()
        self.openstack_node_group_template_update(master_ngt)
        self.openstack_node_group_template_show(master_ngt)
        self.openstack_node_group_template_delete(master_ngt)
        self.openstack_node_group_template_delete(worker_ngt)

    def test_cluster_template_cli(self):
        ng_master = (
            self.openstack_node_group_template_create('tmp-master', '4'))
        ng_worker = (
            self.openstack_node_group_template_create('tmp-worker', '3'))
        cluster_template_name = (
            self.openstack_cluster_template_create(ng_master, ng_worker))
        self.openstack_cluster_template_list()
        self.openstack_cluster_template_show(cluster_template_name)
        self.openstack_cluster_template_update(cluster_template_name)
        self.openstack_cluster_template_delete(cluster_template_name)
        self.openstack_node_group_template_delete(ng_master)
        self.openstack_node_group_template_delete(ng_worker)

    def test_cluster_cli(self):
        image_name = self.openstack_image_register('fedora-heat-test-image')
        self.openstack_image_tags_add(image_name)
        self.openstack_image_show(image_name)
        self.openstack_image_list()
        ng_master = self.openstack_node_group_template_create('cli-cluster'
                                                              '-master',
                                                              'sahara-flavor')
        ng_worker = self.openstack_node_group_template_create('cli-cluster'
                                                              '-worker',
                                                              'sahara-flavor')
        cluster_template_name = (
            self.openstack_cluster_template_create(ng_master, ng_worker))
        cluster_name = (
            self.openstack_cluster_create(cluster_template_name, image_name))
        self.openstack_cluster_list()
        self.openstack_cluster_show(cluster_name)
        self.openstack_cluster_delete(cluster_name)
        self.openstack_cluster_template_delete(cluster_template_name)
        self.openstack_node_group_template_delete(ng_master)
        self.openstack_node_group_template_delete(ng_worker)
        self.openstack_image_tags_remove(image_name)
        self.openstack_image_unregister(image_name)

    def test_job_binary_cli(self):
        self.openstack_job_binary_list()

    def test_job_cli(self):
        self.openstack_job_list()

    def test_job_template_cli(self):
        self.openstack_job_template_list()

    def test_data_source_cli(self):
        self.openstack_data_source_list()

    def test_job_type_cli(self):
        self.openstack_job_type_list()
