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

from sahara_tempest_plugin.tests.cli import base
from tempest.lib.common.utils import data_utils


class SaharaClusterTemplateCLITest(base.ClientTestBase):

    def openstack_cluster_template_list(self):
        self.assertTableStruct(self.listing_result('cluster template list'), [
            'Name',
            'Id',
            'Plugin name',
            'Plugin version'
        ])

    def openstack_cluster_template_create(self, ng_master, ng_worker):
        cluster_template_name = data_utils.rand_name('cl-tmp')
        flag = ("%(ct_name)s %(ngm)s %(ngw)s "
                % {'ngw': ''.join([ng_worker, ':3']),
                   'ngm': ''.join([' --node-groups ', ng_master, ':1 ']),
                   'ct_name': ''.join(['--name ', cluster_template_name])})
        self.assertTableStruct(
            self.listing_result(''.join(['cluster template create ', flag])),
            [
                'Field',
                'Value'
            ])
        return cluster_template_name

    def openstack_cluster_template_show(self, cluster_template_name):
        self.find_in_listing(
            self.listing_result(
                ''.join(['cluster template show ', cluster_template_name])),
            cluster_template_name)

    def openstack_cluster_template_update(self, cluster_template_name):
        cmd = 'cluster template'
        new_template_name = self.update_resource_value(cmd,
                                                       cluster_template_name,
                                                       '--name')
        return new_template_name

    def openstack_cluster_template_delete(self, cluster_template_name):
        self.check_if_delete('cluster template', cluster_template_name)
