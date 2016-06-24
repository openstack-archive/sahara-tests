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

from sahara_cli_tests import base


class SaharaImageCLITest(base.ClientTestBase):

    def test_images_register(self):
        image_name = self.openstack_image_register()
        self.openstack_image_tags_add(image_name)
        self.openstack_image_show(image_name)
        self.openstack_image_list()
        self.openstack_image_tags_remove(image_name)
        self.openstack_image_unregister(image_name)

    def openstack_image_list(self):
        image_list = self.openstack('dataprocessing image list')
        result = self.parser.listing(image_list)
        self.assertTableStruct(result, [
            'Name',
            'Id',
            'Username',
            'Tags'
        ])

    def openstack_image_register(self):
        image_list = self.openstack('image list')
        images = self.parser.listing(image_list)
        images_name = [p['Name'] for p in images]
        for image_name in images_name:
            if image_name == 'fedora-heat-test-image':
                flag = '--username admin ' + image_name
                image = self.openstack('dataprocessing image register',
                                       params=flag)
                result = self.parser.listing(image)
                self.assertTableStruct(result, [
                    'Field',
                    'Value'
                ])
                return image_name
        raise self.skipException('No available image for testing')

    def openstack_image_show(self, image_name):
        image = self.openstack('dataprocessing image show',
                               params=image_name)
        result = self.parser.listing(image)
        self.assertTableStruct(result, [
            'Field',
            'Value'
        ])

    def openstack_image_tags_add(self, image_name):
        flag = image_name + ' --tags test'
        tags_add = self.openstack('dataprocessing image tags add', params=flag)
        result = self.parser.listing(tags_add)
        self.assertTableStruct(result, [
            'Field',
            'Value'
        ])

    def openstack_image_tags_remove(self, image_name):
        flag = image_name + ' --tags test'
        tags_remove = self.openstack('dataprocessing image tags remove',
                                     params=flag)
        result = self.parser.listing(tags_remove)
        self.assertTableStruct(result, [
            'Field',
            'Value'
        ])

    def openstack_image_unregister(self, image_name):
        unregister_image = self.openstack('dataprocessing image unregister',
                                          params=image_name)
        result = self.parser.listing(unregister_image)
        self.assertTableStruct(result, [
            'Field',
            'Value'
        ])


class SaharaNodeGroupCLITest(base.ClientTestBase):

    def test_openstack_node_group_template_list(self):
        node_group = self.openstack('dataprocessing node group template list')
        result = self.parser.listing(node_group)
        self.assertTableStruct(result, [
            'Name',
            'Id',
            'Plugin version',
            'Plugin name'
        ])


class SaharaClusterTemplateCLITest(base.ClientTestBase):

    def test_openstack_cluster_template_list(self):
        result = self.openstack('dataprocessing cluster template list')
        templates = self.parser.listing(result)
        self.assertTableStruct(templates, [
            'Name',
            'Id',
            'Plugin name',
            'Plugin version'
        ])


class SaharaClusterCLITest(base.ClientTestBase):

    def test_openstack_cluster_list(self):
        result = self.openstack('dataprocessing cluster list')
        clusters = self.parser.listing(result)
        self.assertTableStruct(clusters, [
            'Name',
            'Id',
            'Plugin name',
            'Plugin version',
            'Status'
        ])


class SaharaJobBinaryCLITest(base.ClientTestBase):

    def test_openstack_job_binary_list(self):
        result = self.openstack('dataprocessing job binary list')
        job_binary = self.parser.listing(result)
        self.assertTableStruct(job_binary, [
            'Name',
            'Id',
            'Url'
        ])


class SaharaJobCLITest(base.ClientTestBase):

    def test_openstack_job_list(self):
        result = self.openstack('dataprocessing job list')
        jobs = self.parser.listing(result)
        self.assertTableStruct(jobs, [
            'Id',
            'Cluster id',
            'Job id',
            'Status'
        ])


class SaharaJobTemplateCLITest(base.ClientTestBase):

    def test_openstack_job_template_list(self):
        result = self.openstack('dataprocessing job template list')
        job_template = self.parser.listing(result)
        self.assertTableStruct(job_template, [
            'Name',
            'Id',
            'Type'
        ])


class SaharaDataSourceCLITest(base.ClientTestBase):

    def test_openstack_job_template_list(self):
        result = self.openstack('dataprocessing job template list')
        job_template = self.parser.listing(result)
        self.assertTableStruct(job_template, [
            'Name',
            'Type'
        ])


class SaharaJobTypeCLITest(base.ClientTestBase):

    def test_openstack_job_type_list(self):
        result = self.openstack('dataprocessing job type list')
        job_type = self.parser.listing(result)
        self.assertTableStruct(job_type, [
            'Name',
            'Plugins'
        ])


# TODO(anesterova): add get plugin configs method
class SaharaPluginCLITest(base.ClientTestBase):

    def test_openstack_plugin_list(self):
        result = self.openstack('dataprocessing plugin list')
        plugin = self.parser.listing(result)
        self.assertTableStruct(plugin, [
            'Name',
            'Versions'
        ])

    def test_openstack_plugin_show(self):
        pl_list = self.openstack('dataprocessing plugin list')
        plugin = self.parser.listing(pl_list)
        name = [p['Name'] for p in plugin]
        show_pl = self.openstack('dataprocessing plugin show', params=name[0])
        result = self.parser.listing(show_pl)
        self.assertTableStruct(result, [
            'Field',
            'Value'
        ])
